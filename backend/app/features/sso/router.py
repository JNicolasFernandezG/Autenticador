from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.core.dependencies import get_current_admin
from app.features.sso.schemas import (
    CreateSSOTicketRequest,
    CreateSSOTicketResponse,
    ConsumeSSOTicketRequest,
    ConsumeSSOTicketResponse,
)
from app.features.sso.service import crear_ticket_sso, consumir_ticket_sso

router = APIRouter(prefix="/auth/sso", tags=["Single Sign-On (SSO)"])


@router.post(
    "/create-ticket",
    response_model=CreateSSOTicketResponse,
    summary="Generar un ticket SSO descartable de 30 segundos para saltar a otra plataforma (Solo Admin)",
)
async def endpoint_create_ticket(
    req: CreateSSOTicketRequest,
    admin: Dict[str, Any] = Depends(get_current_admin),
):
    return await crear_ticket_sso(admin, req.servicio)


@router.post(
    "/consume-ticket",
    response_model=ConsumeSSOTicketResponse,
    summary="Canjear y quemar un ticket SSO descartable (Consumo interno entre microservicios)",
)
async def endpoint_consume_ticket(req: ConsumeSSOTicketRequest):
    return await consumir_ticket_sso(req.ticket, req.servicio)
