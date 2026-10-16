from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.features.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    ValidateServiceAccessRequest,
    BajaServicioRequest,
    AuthResponse,
)
from app.features.auth.service import (
    register_usuario,
    authenticate_user,
    validate_service_access,
    dar_baja_usuario_servicio,
    format_user_response,
)
from app.core.dependencies import get_current_user
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticación Central y Microservicios"])


@router.post("/login", response_model=AuthResponse, summary="Login de Administrador o de Usuario desde un Servicio")
async def endpoint_login(req: LoginRequest):
    return await authenticate_user(req)


@router.post("/register", response_model=AuthResponse, summary="Registro de nuevo usuario desde un servicio externo")
async def endpoint_register(req: RegisterRequest):
    user_data = await register_usuario(req, is_admin_creation=False)
    token = create_access_token(user_data)
    return {
        "success": True,
        "allowed": True,
        "message": "Usuario registrado o vinculado exitosamente en el Autenticador Central.",
        "token": token,
        "user": user_data,
    }


@router.post(
    "/validar-acceso",
    response_model=AuthResponse,
    summary="Verifica si un usuario existe, está activo y tiene permiso en un servicio (mayoresactualizaciones, conmijuegos, etc.)",
)
async def endpoint_validar_acceso(req: ValidateServiceAccessRequest):
    return await validate_service_access(req)


@router.post(
    "/baja",
    response_model=AuthResponse,
    summary="Dar de baja a un usuario de un servicio específico o de forma global",
)
async def endpoint_baja_servicio(req: BajaServicioRequest):
    return await dar_baja_usuario_servicio(req)


@router.get("/me", summary="Obtener sesión actual a partir del JWT")
async def endpoint_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "success": True,
        "user": format_user_response(current_user),
    }
