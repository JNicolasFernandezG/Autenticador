import random
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from pymongo import DESCENDING
from app.core.database import get_database
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.features.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    VerificarTokenRequest,
    ValidateServiceAccessRequest,
    BajaServicioRequest,
)


def format_user_response(doc: Dict[str, Any]) -> Dict[str, Any]:
    date_start = doc.get("date_start")
    date_end = doc.get("date_end")

    if isinstance(date_start, datetime):
        date_start_str = date_start.isoformat()
    else:
        date_start_str = str(date_start) if date_start else None

    if isinstance(date_end, datetime):
        date_end_str = date_end.isoformat()
    else:
        date_end_str = str(date_end) if date_end else None

    raw_servicios = doc.get("servicios") or {}
    servicios = {
        "mayoresactualizaciones": bool(raw_servicios.get("mayoresactualizaciones", False)),
        "cognijuegos": bool(raw_servicios.get("cognijuegos", False)),
    }

    return {
        "id": int(doc.get("id", 0)),
        "name": doc.get("name", ""),
        "email": doc.get("email", ""),
        "codigoAcceso": doc.get("codigo_acceso", ""),
        "tipoUsuario": int(doc.get("tipo_usuario", 1)),
        "activo": bool(doc.get("activo", True)),
        "estadoId": int(doc.get("estado_id", 2)),
        "estadoCodigo": doc.get("estado_codigo", "ACTIVO"),
        "estado": doc.get("estado"),
        "servicios": servicios,
        "dateStart": date_start_str,
        "dateEnd": date_end_str,
    }


def check_service_permission(servicios_user: Dict[str, Any], tipo_usuario: int, clave_srv: str) -> bool:
    if tipo_usuario == 2:
        return True
    clave = (clave_srv or "").strip().lower()
    return bool(servicios_user.get(clave, False))


async def _generate_unique_pin(db) -> str:
    for _ in range(25):
        pin = f"{random.randint(100000, 999999)}"
        exists = await db["usuarios"].find_one({"codigo_acceso": pin})
        if not exists:
            return pin
    return f"{random.randint(100000, 999999)}"


async def register_usuario(req: RegisterRequest, is_admin_creation: bool = False) -> Dict[str, Any]:
    db = get_database()
    email_clean = req.email.strip().lower()
    name_clean = req.name.strip()

    if not email_clean or not name_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre y el email son obligatorios.",
        )

    existing = await db["usuarios"].find_one({"email": email_clean})
    if existing:
        if not is_admin_creation and req.servicioOrigen:
            clave = req.servicioOrigen.strip().lower()
            servicios_actuales = existing.get("servicios") or {}
            servicios_actuales[clave] = True
            await db["usuarios"].update_one(
                {"id": existing["id"]},
                {"$set": {"servicios": servicios_actuales}},
            )
            existing["servicios"] = servicios_actuales
            return format_user_response(existing)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario registrado con el email '{email_clean}'.",
        )

    ultimo = await db["usuarios"].find().sort("id", DESCENDING).limit(1).to_list(length=1)
    nuevo_id = (int(ultimo[0]["id"]) + 1) if ultimo else 1

    pin = (
        req.codigoAcceso.strip()
        if (req.codigoAcceso and req.codigoAcceso.strip())
        else await _generate_unique_pin(db)
    )
    raw_password = req.password.strip() if (req.password and req.password.strip()) else pin

    catalogo_cursor = db["servicios_catalogo"].find({}, {"_id": 0, "clave": 1})
    catalogo_docs = await catalogo_cursor.to_list(length=100)
    servicios_map: Dict[str, bool] = {d["clave"]: False for d in catalogo_docs}
    servicios_map.setdefault("mayoresactualizaciones", False)
    servicios_map.setdefault("cognijuegos", False)

    if req.servicios:
        for k, v in req.servicios.items():
            servicios_map[k.strip().lower()] = bool(v)

    if req.servicioOrigen:
        clave_origen = req.servicioOrigen.strip().lower()
        servicios_map[clave_origen] = True
    elif not req.servicios:
        servicios_map["mayoresactualizaciones"] = True
        servicios_map["cognijuegos"] = True

    es_activo = bool(req.activo)
    estado_id = 2 if es_activo else 3
    estado_codigo = "ACTIVO" if es_activo else "SUSPENDIDO"

    nuevo_usuario = {
        "id": nuevo_id,
        "name": name_clean,
        "email": email_clean,
        "password_hash": hash_password(raw_password),
        "codigo_acceso": pin,
        "tipo_usuario": int(req.tipoUsuario),
        "activo": es_activo,
        "estado_id": estado_id,
        "estado_codigo": estado_codigo,
        "servicios": servicios_map,
        "date_start": datetime.utcnow(),
        "date_end": None,
    }

    await db["usuarios"].insert_one(nuevo_usuario)
    return format_user_response(nuevo_usuario)


async def authenticate_user(req: LoginRequest) -> Dict[str, Any]:
    db = get_database()
    user: Optional[Dict[str, Any]] = None

    if req.email and req.email.strip():
        user = await db["usuarios"].find_one({"email": req.email.strip().lower()})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no se encuentra registrado en la base de datos central.",
            )
        credential = req.password or req.codigoAcceso or ""
        valid_pass = verify_password(credential, user.get("password_hash", ""))
        valid_pin = bool(credential and credential == user.get("codigo_acceso"))
        if not (valid_pass or valid_pin):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas (contraseña o código de acceso incorrecto).",
            )
    elif req.codigoAcceso and req.codigoAcceso.strip():
        user = await db["usuarios"].find_one({"codigo_acceso": req.codigoAcceso.strip()})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Código de acceso (PIN) no encontrado en la base de datos.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar 'email' o 'codigoAcceso' para iniciar sesión.",
        )

    if not user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"La cuenta de '{user.get('name')}' está inactiva ({user.get('estado_codigo', 'SUSPENDIDO')}).",
        )

    if req.servicio and req.servicio.strip():
        clave_srv = req.servicio.strip().lower()
        servicios_user = user.get("servicios") or {}
        if not check_service_permission(servicios_user, user.get("tipo_usuario", 1), clave_srv):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El usuario no posee permisos activos para el servicio '{clave_srv}'.",
            )

    token = create_access_token(user)
    return {
        "success": True,
        "allowed": True,
        "message": "Ingreso validado correctamente por el Autenticador Central.",
        "token": token,
        "user": format_user_response(user),
    }


async def verificar_token_magic_link(req: VerificarTokenRequest) -> Dict[str, Any]:
    """
    Valida el token JWT recibido desde un Magic Link (/acceso?token=...)
    cuando el alumno ingresa a MayoresActualizaciones o a CogniJuegos.
    """
    payload = decode_access_token(req.token)
    user_id = payload.get("id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: no contiene identificador de usuario.",
        )

    db = get_database()
    user = await db["usuarios"].find_one({"id": int(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado en la base de datos central.",
        )

    if not user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"La cuenta de '{user.get('name')}' se encuentra inactiva ({user.get('estado_codigo', 'SUSPENDIDO')}).",
        )

    clave_srv = (req.servicio or payload.get("servicio_destino") or "").strip().lower()
    if clave_srv:
        servicios_user = user.get("servicios") or {}
        if not check_service_permission(servicios_user, user.get("tipo_usuario", 1), clave_srv):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El usuario '{user.get('name')}' no tiene habilitado el acceso a '{clave_srv}'.",
            )

    fresh_token = create_access_token(user)
    return {
        "success": True,
        "allowed": True,
        "message": "Token de Magic Link verificado exitosamente.",
        "token": fresh_token,
        "user": format_user_response(user),
    }


async def validate_service_access(req: ValidateServiceAccessRequest) -> Dict[str, Any]:
    db = get_database()
    user: Optional[Dict[str, Any]] = None

    if req.token:
        payload = decode_access_token(req.token)
        user = await db["usuarios"].find_one({"id": int(payload.get("id", 0))})
    elif req.userId is not None:
        user = await db["usuarios"].find_one({"id": int(req.userId)})
    elif req.email and req.codigoAcceso:
        user = await db["usuarios"].find_one({
            "email": req.email.strip().lower(),
            "codigo_acceso": req.codigoAcceso.strip()
        })
    elif req.email:
        user = await db["usuarios"].find_one({"email": req.email.strip().lower()})
    elif req.codigoAcceso:
        user = await db["usuarios"].find_one({"codigo_acceso": req.codigoAcceso.strip()})

    if not user:
        msg = "El usuario no existe en la base de datos del Autenticador."
        if req.email and req.codigoAcceso:
            msg = "El correo electrónico o la clave de 6 dígitos es incorrecta."
        elif req.codigoAcceso:
            msg = "Código de acceso no encontrado."
        return {
            "success": False,
            "allowed": False,
            "message": msg,
            "token": None,
            "user": None,
        }

    if not user.get("activo", True):
        return {
            "success": True,
            "allowed": False,
            "message": f"El usuario existe pero su cuenta global está inactiva ({user.get('estado_codigo', 'SUSPENDIDO')}).",
            "token": None,
            "user": format_user_response(user),
        }

    clave_srv = req.servicio.strip().lower()
    servicios_user = user.get("servicios") or {}
    tiene_permiso = check_service_permission(servicios_user, user.get("tipo_usuario", 1), clave_srv)

    if not tiene_permiso:
        return {
            "success": True,
            "allowed": False,
            "message": f"El usuario '{user.get('name')}' no tiene habilitado el servicio '{clave_srv}'.",
            "token": None,
            "user": format_user_response(user),
        }

    token = create_access_token(user)
    return {
        "success": True,
        "allowed": True,
        "message": f"Acceso permitido al servicio '{clave_srv}'.",
        "token": token,
        "user": format_user_response(user),
    }


async def dar_baja_usuario_servicio(req: BajaServicioRequest) -> Dict[str, Any]:
    db = get_database()
    user: Optional[Dict[str, Any]] = None
    if req.userId is not None:
        user = await db["usuarios"].find_one({"id": int(req.userId)})
    elif req.email:
        user = await db["usuarios"].find_one({"email": req.email.strip().lower()})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado para procesar la baja.",
        )

    if req.servicio and req.servicio.strip():
        clave_srv = req.servicio.strip().lower()
        servicios_user = user.get("servicios") or {}
        servicios_user[clave_srv] = False
        await db["usuarios"].update_one(
            {"id": user["id"]},
            {"$set": {"servicios": servicios_user}},
        )
        user["servicios"] = servicios_user
        return {
            "success": True,
            "allowed": False,
            "message": f"Baja del servicio '{clave_srv}' aplicada al usuario '{user.get('name')}'.",
            "user": format_user_response(user),
        }
    else:
        await db["usuarios"].update_one(
            {"id": user["id"]},
            {
                "$set": {
                    "activo": False,
                    "estado_id": 4,
                    "estado_codigo": "BAJA",
                    "date_end": datetime.utcnow(),
                }
            },
        )
        updated = await db["usuarios"].find_one({"id": user["id"]})
        return {
            "success": True,
            "allowed": False,
            "message": f"Usuario '{user.get('name')}' dado de baja globalmente.",
            "user": format_user_response(updated),
        }
