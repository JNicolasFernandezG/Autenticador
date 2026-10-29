import os
import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from app.core.security import hash_password

logger = logging.getLogger("Database")

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


async def get_next_sequence_value(sequence_name: str) -> int:
    """Genera IDs numéricos autoincrementales."""
    db = get_database()
    res = await db["counters"].find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return res["sequence_value"]


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

    # 2. Migración y Seed de catálogo de servicios conectados al Autenticador
    # Paso A: Eliminar definitivamente cualquier registro obsoleto o erróneo de 'conmijuegos'
    await db["servicios_catalogo"].delete_many({"clave": "conmijuegos"})

    # Paso B: Garantizar que existan y estén actualizados los servicios oficiales
    servicios_oficiales = [
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
            "clave": "cognijuegos",
            "nombre": "CogniJuegos",
            "descripcion": "Plataforma de entrenamiento cognitivo diario (Wordle, Sudoku, Sopa, Crucigrama)",
            "url_base": settings.COGNIJUEGOS_FRONTEND_URL,
            "ruta_magic_link": "/acceso",
            "color": "teal",
            "activo": True,
        },
    ]

    for srv in servicios_oficiales:
        await db["servicios_catalogo"].update_one(
            {"clave": srv["clave"]},
            {"$set": srv},
            upsert=True,
        )

    # Paso C: Migrar usuarios existentes con 'servicios.conmijuegos' hacia 'servicios.cognijuegos'
    cursor_conmi = db["usuarios"].find({"servicios.conmijuegos": {"$exists": True}})
    async for u in cursor_conmi:
        servicios = dict(u.get("servicios") or {})
        val = servicios.pop("conmijuegos", False)
        if "cognijuegos" not in servicios:
            servicios["cognijuegos"] = bool(val)
        await db["usuarios"].update_one(
            {"_id": u["_id"]},
            {"$set": {"servicios": servicios}},
        )

    # Eliminar permanentemente la clave 'servicios.conmijuegos' en cualquier usuario residual
    await db["usuarios"].update_many(
        {"servicios.conmijuegos": {"$exists": True}},
        {"$unset": {"servicios.conmijuegos": ""}},
    )

    # Asegurar que todos los usuarios tengan 'servicios.cognijuegos' definido
    await db["usuarios"].update_many(
        {"servicios.cognijuegos": {"$exists": False}},
        {"$set": {"servicios.cognijuegos": False}},
    )

    # Limpiar campo obsoleto `black` si existía en documentos previos
    await db["usuarios"].update_many({"black": {"$exists": True}}, {"$unset": {"black": ""}})

    # 3. Inicialización y blindaje obligatorio del Administrador Central desde variables de entorno (.env)
    admin_email = (getattr(settings, "ADMIN_EMAIL", None) or os.getenv("ADMIN_EMAIL") or "admin@autenticador.com").strip().lower()
    admin_password = getattr(settings, "ADMIN_PASSWORD", None) or os.getenv("ADMIN_PASSWORD") or "admin123456"
    admin_pin = getattr(settings, "ADMIN_PIN", None) or os.getenv("ADMIN_PIN") or "123456"
    admin_name = getattr(settings, "ADMIN_NAME", None) or os.getenv("ADMIN_NAME") or "Administrador Central"

    existing_admin = await db["usuarios"].find_one({"email": admin_email})
    now = datetime.utcnow()
    if not existing_admin:
        next_id = await get_next_sequence_value("usuarios_id")
        admin_doc = {
            "id": next_id if next_id else 1,
            "name": admin_name,
            "email": admin_email,
            "password_hash": hash_password(admin_password.strip()),
            "codigo_acceso": admin_pin.strip(),
            "tipo_usuario": 2,
            "activo": True,
            "estado_id": 2,
            "estado_codigo": "ACTIVO",
            "servicios": {
                "mayoresactualizaciones": True,
                "cognijuegos": True,
            },
            "date_start": now,
            "date_end": None,
        }
        await db["usuarios"].insert_one(admin_doc)
        logger.info(f"[INIT] Administrador Central creado exitosamente: {admin_email}")
    else:
        # Asegurar blindaje permanente del rol administrador y estado activo
        update_doc = {
            "tipo_usuario": 2,
            "activo": True,
            "estado_id": 2,
            "estado_codigo": "ACTIVO",
            "servicios.mayoresactualizaciones": True,
            "servicios.cognijuegos": True,
        }
        if admin_password:
            update_doc["password_hash"] = hash_password(admin_password.strip())
        if admin_pin:
            update_doc["codigo_acceso"] = admin_pin.strip()

        await db["usuarios"].update_one(
            {"email": admin_email},
            {"$set": update_doc}
        )
        logger.info(f"[INIT] Administrador Central verificado y blindado como permanente: {admin_email}")
