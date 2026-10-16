from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class RegisterRequest(BaseModel):
    name: str = Field(..., description="Nombre completo del usuario")
    email: str = Field(..., description="Correo electrónico del usuario")
    password: Optional[str] = Field(None, description="Contraseña opcional o PIN")
    codigoAcceso: Optional[str] = Field(None, description="PIN de 6 dígitos (se autogenera si se omite)")
    tipoUsuario: int = Field(1, description="1: Alumno/Usuario, 2: Administrador")
    black: bool = Field(False, description="Suscripción Black")
    activo: bool = Field(True, description="Estado inicial de la cuenta")
    servicioOrigen: Optional[str] = Field(
        None,
        description="Clave del servicio desde donde se registra (ej: mayoresactualizaciones, conmijuegos)",
    )
    servicios: Optional[Dict[str, bool]] = Field(
        None,
        description="Mapa de servicios habilitados para el usuario",
    )


class LoginRequest(BaseModel):
    email: Optional[str] = Field(None, description="Email del usuario o administrador")
    password: Optional[str] = Field(None, description="Contraseña o PIN")
    codigoAcceso: Optional[str] = Field(None, description="Ingreso directo por PIN de 6 dígitos")
    servicio: Optional[str] = Field(
        None,
        description="Clave del servicio que solicita el login (ej: mayoresactualizaciones, conmijuegos)",
    )


class ValidateServiceAccessRequest(BaseModel):
    email: Optional[str] = None
    codigoAcceso: Optional[str] = None
    userId: Optional[int] = None
    token: Optional[str] = None
    servicio: str = Field(..., description="Clave del servicio a validar (ej: mayoresactualizaciones, conmijuegos)")


class BajaServicioRequest(BaseModel):
    email: Optional[str] = None
    userId: Optional[int] = None
    servicio: Optional[str] = Field(
        None,
        description="Si se indica, da de baja solo ese servicio; si se omite, da de baja la cuenta global",
    )
    motivo: Optional[str] = None


class AuthResponse(BaseModel):
    success: bool
    allowed: bool = True
    message: str
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
