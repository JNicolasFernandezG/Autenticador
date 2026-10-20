# 🚀 Guía de Comandos: Arranque Local del Proyecto

> **Nota sobre el error previo (`ENOENT: no such file or directory, open '...package.json'`)**:
> La raíz del proyecto no contiene un archivo `package.json` porque la arquitectura está modularizada:
> - **`backend/`**: Desarrollado en **Python (FastAPI)**.
> - **`frontend/`**: Desarrollado en **Node.js (React + TypeScript + Vite)**.
>
> Para instalar dependencias y levantar cada servicio, debes ingresar a sus carpetas correspondientes.

---

## 📋 Requisitos Previos

1. **Python 3.10 o superior** (`python --version`)
2. **Node.js 18 o superior** y npm (`node -v`, `npm -v`)
3. **MongoDB** en el puerto `27017` (puedes usar Docker mediante el archivo incluido `docker-compose.db.yml` o una instancia local de MongoDB).

---

## 🛠️ Método 1: Desarrollo Local Paso a Paso (Recomendado)

Necesitarás **3 terminales** abiertas: una para la base de datos (MongoDB), una para el Backend y otra para el Frontend.

---

### Terminal 1: Base de Datos (MongoDB con Docker)

Si utilizas Docker para la base de datos, ejecuta desde la **raíz del proyecto** (`Autenticador/`):

```powershell
# 1. Crear la red Docker si aún no existe
docker network create autenticador_net

# 2. Iniciar el contenedor aislado de MongoDB (puerto 27017)
docker compose -f docker-compose.db.yml up -d
```

*(Si ya cuentas con MongoDB instalado de forma nativa en tu Windows corriendo en `localhost:27017`, puedes omitir este paso).*

---

### Terminal 2: Backend (Python + FastAPI)

Desde la raíz del proyecto, ingresa a la carpeta `backend`:

```powershell
# 1. Navegar a la carpeta del backend
cd backend

# 2. Crear el entorno virtual de Python
python -m venv venv

# 3. Activar el entorno virtual
# En PowerShell:
.\venv\Scripts\Activate.ps1
# (Si PowerShell bloquea scripts, ejecuta primero: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
# En CMD convencional:
# venv\Scripts\activate.bat

# 4. Instalar todas las dependencias
pip install -r requirements.txt

# 5. Iniciar el servidor FastAPI con recarga en caliente
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **API Backend**: [http://localhost:8000](http://localhost:8000)
- **Documentación Swagger interactiva**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Terminal 3: Frontend (React + Vite)

Desde la raíz del proyecto, abre una nueva terminal e ingresa a la carpeta `frontend`:

```powershell
# 1. Navegar a la carpeta del frontend
cd frontend

# 2. Instalar las dependencias de Node.js
npm install

# 3. Iniciar el servidor de desarrollo de Vite
npm run dev
```

- **Consola Web de Administración**: [http://localhost:5173](http://localhost:5173)

---

## 🐳 Método 2: Levantar Todo con Docker Compose (Sin instalar Python ni Node)

Si prefieres no instalar dependencias en tu máquina física y correr todo encapsulado en contenedores Docker:

```powershell
# 1. Crear la red de comunicación compartida (solo la primera vez)
docker network create autenticador_net

# 2. Iniciar MongoDB persistente
docker compose -f docker-compose.db.yml up -d

# 3. Construir y levantar Backend y Frontend
docker compose up -d --build
```

Para ver los logs en tiempo real:
```powershell
docker compose logs -f
```

Para detener los contenedores de la app:
```powershell
docker compose down
```

---

## 🔑 Credenciales Iniciales de Prueba

El backend carga automáticamente en MongoDB los siguientes usuarios de prueba:

| Perfil | Email | Contraseña | PIN (`codigoAcceso`) | Servicios Habilitados |
| :--- | :--- | :--- | :--- | :--- |
| **Administrador** | `admin@autenticador.com` | `admin123` | `999999` | `mayoresactualizaciones`, `conmijuegos` |
| **Usuario Black** | `marta.gonzalez@ejemplo.com` | `123456` | `123456` | `mayoresactualizaciones`, `conmijuegos` |
| **Usuario Estándar** | `roberto.mendez@ejemplo.com` | `654321` | `654321` | Solo `conmijuegos` |
| **Usuario Suspendido** | `elena.gomez@ejemplo.com` | `112233` | `112233` | Inactivo |

---

## 🛑 Detención de los Servicios Locales

- Para detener **Backend** o **Frontend** en ejecución local: presiona `Ctrl + C` en sus respectivas terminales.
- Para apagar el contenedor de **MongoDB**:
  ```powershell
  docker compose -f docker-compose.db.yml down
  ```
