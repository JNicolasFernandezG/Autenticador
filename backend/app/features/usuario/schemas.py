from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Generic, TypeVar
from datetime import datetime, date

T = TypeVar("T")


class EstadoUsuarioSchema(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str
    permite_login: bool = False
    color: str = "slate"
    habilitado: bool = True


class ServicioCatalogoSchema(BaseModel):
    clave: str
    nombre: str
    descripcion: str = ""
    color: str = "indigo"
    activo: bool = True


class CrearServicioCatalogoRequest(BaseModel):
    clave: str = Field(..., description="Clave única del servicio (ej: mayoresactualizaciones, conmijuegos)")
    nombre: str = Field(..., description="Nombre visible del servicio")
    descripcion: Optional[str] = ""
    color: Optional[str] = "indigo"


class CambiarEstadoUsuarioRequest(BaseModel):
    estado_id: int


class CrearEstadoRequest(BaseModel):
    nombre: str
    codigo: Optional[str] = None
    descripcion: Optional[str] = ""
    color: Optional[str] = "indigo"
    permite_login: Optional[bool] = False


class CambiarEstadoUsuarioResponse(BaseModel):
    success: bool
    message: str
    estado_id: int
    estado_codigo: str
    activo: bool


class UsuarioResponse(BaseModel):
    id: int
    name: str
    email: str
    codigoAcceso: Optional[str] = ""
    tipoUsuario: int = 1
    black: bool = False
    activo: bool = True
    estadoId: int = 2
    estadoCodigo: str = "ACTIVO"
    estado: Optional[EstadoUsuarioSchema] = None
    servicios: Dict[str, bool] = Field(default_factory=dict)
    dateStart: Optional[str] = None
    dateEnd: Optional[str] = None


class ListEstadosResponse(BaseModel):
    success: bool
    estados: List[EstadoUsuarioSchema]


class ListServiciosResponse(BaseModel):
    success: bool
    servicios: List[ServicioCatalogoSchema]


class PaginatedUsuariosResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[UsuarioResponse]


class EstadoActivoResponse(BaseModel):
    success: bool
    message: str
    activo: bool


class SuscripcionResponse(BaseModel):
    success: bool
    message: str
    black: bool


class ToggleServicioUsuarioResponse(BaseModel):
    success: bool
    message: str
    servicio: str
    habilitado: bool
    servicios: Dict[str, bool]
