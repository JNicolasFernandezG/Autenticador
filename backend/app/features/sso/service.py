import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import HTTPException, status
from app.core.database import get_database
from app.core.security import create_access_token
from app.features.auth.service import format_user_response


async def crear_ticket_sso(admin_user: Dict[str, Any], servicio_destino: str) -> Dict[str, Any]:
    """
    Genera un ticket descartable de un solo uso con 30 segundos de vigencia.
    Solo puede ser solicitado por administradores con sesión activa.
    """
    if admin_user.get("tipo_usuario") != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden generar tickets SSO de acceso directo.",
        )

    clave_srv = servicio_destino.strip().lower()
    ticket_code = f"sso_tk_{secrets.token_urlsafe(32)}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=30)

    db = get_database()
    ticket_doc = {
        "ticket": ticket_code,
        "user_id": int(admin_user["id"]),
        "email": admin_user.get("email"),
        "servicio_destino": clave_srv,
        "creado_en": now,
        "expira_en": expires_at,
    }

    await db["sso_tickets"].insert_one(ticket_doc)

    return {
        "success": True,
        "ticket": ticket_code,
        "expiresInSeconds": 30,
        "servicio": clave_srv,
    }


async def consumir_ticket_sso(ticket_code: str, servicio_solicitante: str) -> Dict[str, Any]:
    """
    Valida y consume atómicamente un ticket SSO.
    - Quema el ticket en el instante (un solo uso, imposible reutilizarlo).
    - Valida que no haya expirado.
    - Valida que el servicio destino coincida con el servicio solicitante.
    - Emite un JWT válido con permisos para la plataforma destino.
    """
    if not ticket_code or not ticket_code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ticket es obligatorio.",
        )

    db = get_database()
    clave_srv = servicio_solicitante.strip().lower()

    # Consumo atómico: find_one_and_delete lo retira en la misma operación
    ticket_doc = await db["sso_tickets"].find_one_and_delete({"ticket": ticket_code.strip()})

    if not ticket_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El ticket es inválido, ya fue utilizado o ha expirado.",
        )

    # Validar expiración temporal
    now = datetime.now(timezone.utc)
    expira_en = ticket_doc.get("expira_en")
    if expira_en and expira_en.tzinfo is None:
        expira_en = expira_en.replace(tzinfo=timezone.utc)

    if expira_en and now > expira_en:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El ticket de acceso ha expirado (vigencia máxima 30 segundos).",
        )

    # Validar audiencia / servicio de destino
    destino_asignado = ticket_doc.get("servicio_destino", "")
    if destino_asignado != clave_srv:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Restricción de destino: este ticket fue emitido para '{destino_asignado}', no para '{clave_srv}'.",
        )

    # Obtener el usuario en su estado actual más fresco
    user = await db["usuarios"].find_one({"id": int(ticket_doc["user_id"])})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario asociado al ticket no existe.",
        )

    if not user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta del usuario administrador se encuentra desactivada.",
        )

    if user.get("tipo_usuario") != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no posee permisos de administrador.",
        )

    # Generar token JWT con permisos para este servicio
    token = create_access_token(user)

    return {
        "success": True,
        "token": token,
        "user": format_user_response(user),
        "message": "Ticket canjeado exitosamente.",
    }
