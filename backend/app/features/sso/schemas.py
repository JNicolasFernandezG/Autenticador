from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class CreateSSOTicketRequest(BaseModel):
    servicio: str = Field(..., description="Servicio destino al que saltará el administrador (ej: mayoresactualizaciones)")


class CreateSSOTicketResponse(BaseModel):
    success: bool = True
    ticket: str
    expiresInSeconds: int = 30
    servicio: str


class ConsumeSSOTicketRequest(BaseModel):
    ticket: str = Field(..., description="Ticket efímero descartable recibido")
    servicio: str = Field(..., description="Servicio que solicita el canje para validar correspondencia")


class ConsumeSSOTicketResponse(BaseModel):
    success: bool
    token: str
    user: Dict[str, Any]
    message: str = "Ticket canjeado exitosamente"
