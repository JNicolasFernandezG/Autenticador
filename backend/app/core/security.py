import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import jwt
from fastapi import HTTPException, status
from app.core.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if "$" not in hashed_password:
        return plain_password == hashed_password
    salt, digest = hashed_password.split("$", 1)
    check = hashlib.sha256(f"{salt}:{plain_password}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(check, digest)


def create_access_token(user: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera un token JWT permanente (sin fecha de expiración `exp` por defecto)
    para que el Magic Link y la sesión del alumno no caduquen con el paso del tiempo.
    El control de acceso se valida en tiempo real contra MongoDB (`activo` y `servicios`).
    """
    payload: Dict[str, Any] = {
        "sub": str(user.get("id")),
        "id": user.get("id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "tipo_usuario": user.get("tipo_usuario", user.get("tipoUsuario", 1)),
        "servicios": user.get("servicios", {}),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    if expires_delta is not None:
        payload["exp"] = datetime.now(timezone.utc) + expires_delta

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido.",
        )
