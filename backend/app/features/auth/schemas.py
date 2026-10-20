import re
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any


def _sanitize_text(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    # Elimina etiquetas HTML y caracteres de control para prevenir XSS almacenado (Punto 15)
    cleaned = re.sub(r"[<>\"'`]", "", val)
    return cleaned.strip()


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=120, description="Nombre completo del usuario")
    email: str = Field(..., min_length=5, max_length=160, description="Correo electrónico del usuario")
    password: Optional[str] = Field(None, max_length=128, description="Contraseña opcional o PIN")
    codigoAcceso: Optional[str] = Field(
        None, max_length=12, description="PIN de 6 dígitos (se autogenera si se omite)"
    )
    tipoUsuario: int = Field(1, ge=1, le=2, description="1: Alumno/Usuario, 2: Administrador")
    activo: bool = Field(True, description="Estado inicial de la cuenta")
    servicioOrigen: Optional[str] = Field(
        None,
        max_length=64,
        description="Clave del servicio desde donde se registra (ej: mayoresactualizaciones, conmijuegos)",
    )
    servicios: Optional[Dict[str, bool]] = Field(
        None,
        description="Mapa de servicios habilitados para el usuario",
    )

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return _sanitize_text(v) or ""


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Optional[str] = Field(None, max_length=160, description="Email del usuario o administrador")
    password: Optional[str] = Field(None, max_length=128, description="Contraseña o PIN")
    codigoAcceso: Optional[str] = Field(None, max_length=12, description="Ingreso directo por PIN de 6 dígitos")
    servicio: Optional[str] = Field(
        None,
        max_length=64,
        description="Clave del servicio que solicita el login (ej: mayoresactualizaciones, conmijuegos)",
    )


class VerificarTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., max_length=2048, description="Token JWT recibido desde el Magic Link (/acceso?token=...)")
    servicio: Optional[str] = Field(
        None,
        max_length=64,
        description="Clave del servicio donde se abrió el Magic Link (ej: mayoresactualizaciones, conmijuegos)",
    )


class ValidateServiceAccessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Optional[str] = Field(None, max_length=160)
    codigoAcceso: Optional[str] = Field(None, max_length=12)
    userId: Optional[int] = Field(None, ge=1)
    token: Optional[str] = Field(None, max_length=2048)
    servicio: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Clave del servicio a validar (ej: mayoresactualizaciones, conmijuegos)",
    )


class BajaServicioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Optional[str] = Field(None, max_length=160)
    userId: Optional[int] = Field(None, ge=1)
    servicio: Optional[str] = Field(
        None,
        max_length=64,
        description="Si se indica, da de baja solo ese servicio; si se omite, da de baja la cuenta global",
    )
    motivo: Optional[str] = Field(None, max_length=250)


class AuthResponse(BaseModel):
    success: bool
    allowed: bool = True
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
