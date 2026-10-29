import re
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Generic, TypeVar

T = TypeVar("T")


def _clean_str(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    return re.sub(r"[<>\"'`]", "", val).strip()


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
    url_base: str = "https://mayoresactualizaciones.asistodo.com.ar"
    ruta_magic_link: str = "/acceso"
    color: str = "indigo"
    activo: bool = True


class CrearServicioCatalogoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clave: str = Field(
        ...,
        min_length=2,
        max_length=64,
        description="Clave única del servicio (ej: mayoresactualizaciones, cognijuegos)",
    )
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre visible del servicio")
    url_base: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="URL del frontend de este servicio (ej: https://mayoresactualizaciones.asistodo.com.ar)",
    )
    ruta_magic_link: Optional[str] = Field(
        "/acceso",
        max_length=80,
        description="Ruta del frontend que recibe ?token= (por defecto /acceso)",
    )
    descripcion: Optional[str] = Field("", max_length=250)
    color: Optional[str] = Field("indigo", max_length=32)

    @field_validator("nombre", "descripcion")
    @classmethod
    def sanitize_fields(cls, v: Optional[str]) -> Optional[str]:
        return _clean_str(v)


class ActualizarServicioCatalogoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = Field(None, max_length=100)
    url_base: Optional[str] = Field(None, max_length=255)
    ruta_magic_link: Optional[str] = Field(None, max_length=80)
    descripcion: Optional[str] = Field(None, max_length=250)
    color: Optional[str] = Field(None, max_length=32)


class CambiarEstadoUsuarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado_id: int = Field(..., ge=1)


class CrearEstadoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=2, max_length=80)
    codigo: Optional[str] = Field(None, max_length=64)
    descripcion: Optional[str] = Field("", max_length=250)
    color: Optional[str] = Field("indigo", max_length=32)
    permite_login: Optional[bool] = False

    @field_validator("nombre", "descripcion")
    @classmethod
    def sanitize_fields(cls, v: Optional[str]) -> Optional[str]:
        return _clean_str(v)


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


class ToggleServicioUsuarioResponse(BaseModel):
    success: bool
    message: str
    servicio: str
    habilitado: bool
    servicios: Dict[str, bool]
