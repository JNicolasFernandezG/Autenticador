from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.security import hash_password

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


def get_database() -> AsyncIOMotorDatabase:
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
        _db = _client[settings.DATABASE_NAME]
    return _db


async def connect_to_mongo() -> None:
    db = get_database()
    await db["usuarios"].create_index("id", unique=True)
    await db["usuarios"].create_index("email", unique=True)
    await db["usuarios"].create_index("codigo_acceso")
    await db["estados_usuario"].create_index("id", unique=True)
    await db["estados_usuario"].create_index("codigo", unique=True)
    await db["servicios_catalogo"].create_index("clave", unique=True)
    await db["sso_tickets"].create_index("ticket", unique=True)
    await db["sso_tickets"].create_index("expira_en", expireAfterSeconds=0)
    await seed_initial_data(db)


async def close_mongo_connection() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None


async def seed_initial_data(db: AsyncIOMotorDatabase) -> None:
    # 1. Seed catálogo de estados de usuario
    estados_count = await db["estados_usuario"].count_documents({})
    if estados_count == 0:
        estados_iniciales = [
            {
                "id": 1,
                "codigo": "PENDIENTE_VERIFICACION",
                "nombre": "Pendiente de Verificación",
                "descripcion": "Cuenta creada pendiente de activación",
                "permite_login": False,
                "color": "amber",
                "habilitado": True,
            },
            {
                "id": 2,
                "codigo": "ACTIVO",
                "nombre": "Activo",
                "descripcion": "Usuario con acceso habilitado a sus servicios",
                "permite_login": True,
                "color": "emerald",
                "habilitado": True,
            },
            {
                "id": 3,
                "codigo": "SUSPENDIDO",
                "nombre": "Suspendido",
                "descripcion": "Acceso suspendido temporalmente o por falta de pago",
                "permite_login": False,
                "color": "rose",
                "habilitado": True,
            },
            {
                "id": 4,
                "codigo": "BAJA",
                "nombre": "Dado de Baja",
                "descripcion": "Usuario dado de baja de la plataforma",
                "permite_login": False,
                "color": "slate",
                "habilitado": True,
            },
        ]
        await db["estados_usuario"].insert_many(estados_iniciales)

    # 2. Seed catálogo de servicios conectados al Autenticador (con URL base para Magic Links independientes)
    servicios_count = await db["servicios_catalogo"].count_documents({})
    if servicios_count == 0:
        servicios_iniciales = [
            {
                "clave": "mayoresactualizaciones",
                "nombre": "Mayores Actualizaciones",
                "descripcion": "Plataforma principal de cursos y actualizaciones (SIPI)",
                "url_base": settings.MAYORES_FRONTEND_URL,
                "ruta_magic_link": "/acceso",
                "color": "indigo",
                "activo": True,
            },
            {
                "clave": "conmijuegos",
                "nombre": "ConmiJuegos",
                "descripcion": "Plataforma de entrenamiento cognitivo diario (Wordle, Sudoku, Sopa, Crucigrama)",
                "url_base": settings.CONMIJUEGOS_FRONTEND_URL,
                "ruta_magic_link": "/acceso",
                "color": "teal",
                "activo": True,
            },
        ]
        await db["servicios_catalogo"].insert_many(servicios_iniciales)
    else:
        # Sincronizar url_base desde las variables de entorno (.env) si tenían el valor local por defecto o no existían
        await db["servicios_catalogo"].update_one(
            {
                "clave": "mayoresactualizaciones",
                "$or": [
                    {"url_base": {"$exists": False}},
                    {"url_base": "http://localhost:3000"},
                ],
            },
            {
                "$set": {
                    "url_base": settings.MAYORES_FRONTEND_URL,
                    "ruta_magic_link": "/acceso",
                }
            },
        )
        await db["servicios_catalogo"].update_one(
            {
                "clave": "conmijuegos",
                "$or": [
                    {"url_base": {"$exists": False}},
                    {"url_base": "http://localhost:5174"},
                ],
            },
            {
                "$set": {
                    "url_base": settings.CONMIJUEGOS_FRONTEND_URL,
                    "ruta_magic_link": "/acceso",
                }
            },
        )

    # Limpiar campo obsoleto `black` si existía en documentos previos
    await db["usuarios"].update_many({"black": {"$exists": True}}, {"$unset": {"black": ""}})

    # 3. Seed usuario Administrador y usuarios de ejemplo SOLO si se habilita explícitamente en .env
    admin_exists = await db["usuarios"].find_one({"email": "admin@autenticador.com"})
    should_seed = os.getenv("SEED_INITIAL_DATA", "false").lower() in ("true", "1", "yes")
    if not admin_exists and should_seed:
        admin_password = os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123")
        admin_pin = os.getenv("ADMIN_DEFAULT_PIN", "999999")
        now = datetime.utcnow()
        usuarios_semilla = [
            {
                "id": 1,
                "name": "Administrador Central",
                "email": "admin@autenticador.com",
                "password_hash": hash_password(admin_password),
                "codigo_acceso": admin_pin,
                "tipo_usuario": 2,
                "activo": True,
                "estado_id": 2,
                "estado_codigo": "ACTIVO",
                "servicios": {
                    "mayoresactualizaciones": True,
                    "conmijuegos": True,
                },
                "date_start": now,
                "date_end": None,
            },
            {
                "id": 2,
                "name": "Marta González",
                "email": "marta.gonzalez@ejemplo.com",
                "password_hash": hash_password("123456"),
                "codigo_acceso": "123456",
                "tipo_usuario": 1,
                "activo": True,
                "estado_id": 2,
                "estado_codigo": "ACTIVO",
                "servicios": {
                    "mayoresactualizaciones": True,
                    "conmijuegos": True,
                },
                "date_start": now,
                "date_end": None,
            },
            {
                "id": 3,
                "name": "Roberto Carlos Méndez",
                "email": "roberto.mendez@ejemplo.com",
                "password_hash": hash_password("654321"),
                "codigo_acceso": "654321",
                "tipo_usuario": 1,
                "activo": True,
                "estado_id": 2,
                "estado_codigo": "ACTIVO",
                "servicios": {
                    "mayoresactualizaciones": False,
                    "conmijuegos": True,
                },
                "date_start": now,
                "date_end": None,
            },
            {
                "id": 4,
                "name": "Elena Beatriz Gómez",
                "email": "elena.gomez@ejemplo.com",
                "password_hash": hash_password("112233"),
                "codigo_acceso": "112233",
                "tipo_usuario": 1,
                "activo": False,
                "estado_id": 3,
                "estado_codigo": "SUSPENDIDO",
                "servicios": {
                    "mayoresactualizaciones": True,
                    "conmijuegos": False,
                },
                "date_start": now,
                "date_end": None,
            },
        ]
        await db["usuarios"].insert_many(usuarios_semilla)
