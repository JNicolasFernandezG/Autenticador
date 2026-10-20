# 🛡️ Autenticador Central — Torre de Control de Usuarios y Servicios

Microservicio centralizado de autenticación, registro, baja, Magic Links por plataforma y control de permisos por servicio para múltiples aplicaciones que conviven en un mismo servidor Linux (`mayoresactualizaciones`, `conmijuegos` y futuros servicios).

---

## 📌 ¿Qué es y cómo funciona este proyecto?

En el servidor conviven distintos sistemas independientes (por ejemplo, **Mayores Actualizaciones** y **ConmiJuegos**), cada uno dentro de su propio contenedor de Docker Compose con su propio backend y su propio dominio/URL.

El **Autenticador Central** actúa como la **única fuente de verdad de usuarios y permisos**:
1. **Validación de ingreso (`POST /auth/validar-acceso` / `POST /auth/login`)**: Cuando una persona intenta ingresar a `mayoresactualizaciones` o a `conmijuegos` (con Email/Contraseña, PIN de 6 dígitos o Token JWT), el backend de ese servicio consulta al Autenticador enviando la clave del servicio (`"mayoresactualizaciones"`, `"conmijuegos"`, etc.). El Autenticador verifica en MongoDB:
   - Si el usuario existe.
   - Si su cuenta global está `ACTIVA` (`activo: true`).
   - Si tiene habilitada la clave de ese servicio específico en su mapa de permisos (`servicios.<clave>: true`).
2. **Magic Links independientes por servicio (`POST /usuario/{id}/magic-link` y `POST /auth/verificar-token`)**:
   - Cada servicio registrado en `servicios_catalogo` tiene su propia `url_base` y `ruta_magic_link` (por defecto `/acceso`).
   - Al generar los enlaces de un usuario, el Autenticador devuelve **un Magic Link distinto por cada servicio** compartiendo el mismo token JWT y PIN de 6 dígitos:
     - **Magic Link Mayores Actualizaciones**: `<URL_MAYORES>/acceso?token=<JWT>` → Abre `AccesoToken.jsx` en Mayores Actualizaciones, valida contra su backend / Autenticador y entra directo a la pantalla de inicio de Mayores Actualizaciones.
     - **Magic Link ConmiJuegos**: `<URL_CONMIJUEGOS>/acceso?token=<JWT>` → Abre la ruta de acceso de ConmiJuegos, valida contra su backend / Autenticador y entra directo al menú de juegos cognitivos.
3. **Registro unificado (`POST /auth/register`)**: Cuando un servicio registra a un usuario nuevo, el Autenticador crea la cuenta en MongoDB, le genera su PIN de 6 dígitos (`codigoAcceso`) y le activa la clave del servicio de origen (`servicioOrigen`). Si el email ya existía por otro servicio, vincula y habilita automáticamente el nuevo servicio sobre la misma cuenta.
4. **Baja de servicio o baja global (`POST /auth/baja`)**: Permite que un servicio externo desactive únicamente su clave de acceso para ese usuario o procese la baja global de la cuenta.
5. **Consola Web exclusiva para el Administrador (Torre de Control)**: Un frontend en React + Tailwind desde donde el administrador puede visualizar todas las cuentas, filtrar por servicio (`mayoresactualizaciones`, `conmijuegos`, etc.), activar o desactivar el permiso de cada servicio con un clic, cambiar estados (`ACTIVO`, `SUSPENDIDO`, `BAJA`), copiar los **Magic Links individuales de cada servicio** y configurar las URLs base de cada plataforma.

---

## 🔄 Diferencia entre `PUT` y `PATCH` en la API

- **`PUT` (Reemplazo total)**: Reemplaza el documento o recurso **completo**. Si enviás un objeto omitiendo propiedades, las propiedades omitidas se pisan con valores por defecto o `null`.
- **`PATCH` (Actualización parcial)**: Modifica **únicamente los campos específicos** indicados (por ejemplo, cambiar solo el estado `activo`, alternar solo el permiso de un servicio `servicios.conmijuegos` o actualizar solo la `url_base` de un servicio).
- En este backend todos los endpoints de modificación puntual (`toggle-activo`, `toggle-servicio`, `estado`, `servicios/catalogo/{clave}`) utilizan **`PATCH`** como método principal siguiendo el estándar REST, manteniendo `PUT` como alias oculto para retrocompatibilidad.

---

## 🐳 Arquitectura de Contenedores (Base de Datos Aislada)

Para evitar que una actualización, reconstrucción o `docker compose down` del código del Autenticador afecte o elimine por error los datos de los usuarios, la infraestructura está separada en **dos archivos Docker Compose independientes** unidos por la red externa `autenticador_net`:

| Archivo | Contenedores que incluye | Propósito |
| :--- | :--- | :--- |
| **`docker-compose.db.yml`** | `autenticador_mongodb` (`mongo:7.0`) | Mantiene la base de datos en un ciclo de vida aislado con el volumen persistente `autenticador_mongo_data`. **No se detiene ni se toca** cuando se actualiza el backend o el frontend. |
| **`docker-compose.yml`** | `autenticador_backend` + `autenticador_frontend` | Contiene la API FastAPI y la interfaz de administración. Puede actualizarse y reconstruirse (`up -d --build`) en cualquier momento sin riesgo para MongoDB. |

---

## 🗄️ Estructura de Datos en MongoDB (`autenticador_db`)

### 1. Colección `usuarios`
```json
{
  "id": 2,
  "name": "Marta González",
  "email": "marta.gonzalez@ejemplo.com",
  "codigo_acceso": "123456",
  "tipo_usuario": 1,
  "activo": true,
  "estado_id": 2,
  "estado_codigo": "ACTIVO",
  "servicios": {
    "mayoresactualizaciones": true,
    "conmijuegos": true
  },
  "date_start": "2026-10-16T19:47:26.275Z",
  "date_end": null
}
```

### 2. Colección `servicios_catalogo`
Contiene las claves y URLs de cada servicio para construir sus respectivos Magic Links:
```json
[
  {
    "clave": "mayoresactualizaciones",
    "nombre": "Mayores Actualizaciones",
    "url_base": "http://localhost:3000",
    "ruta_magic_link": "/acceso",
    "activo": true
  },
  {
    "clave": "conmijuegos",
    "nombre": "ConmiJuegos",
    "url_base": "http://localhost:5174",
    "ruta_magic_link": "/acceso",
    "activo": true
  }
]
```

---

## 🔌 Endpoints Principales de la API

### A. Endpoints para los Backends de otros Servicios (`/auth` y alias `/api/auth`)

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `POST` | `/auth/validar-acceso` | Valida por `email`, `codigoAcceso`, `userId` o `token` si el usuario existe, está activo y tiene permiso en `servicio` (`mayoresactualizaciones`, `conmijuegos`, etc.). |
| `POST` | `/auth/verificar-token` | *(También disponible en `/api/auth/verificar-token`)* Verifica el token JWT recibido desde un Magic Link (`/acceso?token=...`) y valida que el usuario tenga permiso en el servicio destino. |
| `POST` | `/auth/login` | Login por `email` + `password` o por `codigoAcceso` (PIN de 6 dígitos), validando el permiso en `servicio`. |
| `POST` | `/auth/register` | Registra un nuevo usuario o le habilita el `servicioOrigen` si el email ya existía en la base central. |
| `POST` | `/auth/baja` | Da de baja un servicio específico para el usuario o da de baja la cuenta globalmente. |

### B. Endpoints de Administración — Torre de Control (`/usuario`)

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/usuario` | Lista paginada con filtros por `nombre` (nombre, email o PIN), `servicio`, `activo`, `tipoUsuario`, `fechaDesde`, `fechaHasta` y `orden`. |
| `POST` | `/usuario` | Crea un nuevo usuario desde la Torre de Control eligiendo qué servicios tiene activos. |
| `PATCH` | `/usuario/{user_id}/toggle-servicio/{servicio_clave}` | Habilita o deshabilita el permiso de un usuario en un servicio específico (`mayoresactualizaciones`, `conmijuegos`, etc.). |
| `PATCH` | `/usuario/{user_id}/toggle-activo` | Activa o suspende la cuenta global del usuario. |
| `PATCH` | `/usuario/{user_id}/estado` | Cambia el estado de la cuenta según el catálogo (`ACTIVO`, `SUSPENDIDO`, `BAJA`). |
| `POST` | `/usuario/{user_id}/magic-link` | Genera el PIN y **un Magic Link distinto por cada servicio** (`magicLinks.mayoresactualizaciones.accessUrl`, `magicLinks.conmijuegos.accessUrl`, etc.). |
| `GET` | `/usuario/servicios/catalogo` | Lista los servicios registrados con sus respectivas `url_base`. |
| `POST` | `/usuario/servicios/catalogo` | Registra un nuevo servicio con su clave y `url_base`. |
| `PATCH` | `/usuario/servicios/catalogo/{clave}` | Actualiza parcialmente la `url_base`, ruta o nombre de un servicio del catálogo. |

---

## 🚀 Cómo Ejecutar el Proyecto

### Ejecución Local
1. **Backend (`http://localhost:8000`)**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Frontend Admin (`http://localhost:5173`)**:
   ```bash
   cd frontend
   npm run dev
   ```

### Credenciales Iniciales de Administrador
- **Email**: `admin@autenticador.com`
- **Contraseña**: `admin123` (o PIN: `999999`)
