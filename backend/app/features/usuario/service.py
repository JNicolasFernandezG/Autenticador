import re
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from pymongo import ASCENDING, DESCENDING
from app.core.database import get_database
from app.core.config import settings
from app.core.security import create_access_token
from app.features.auth.service import format_user_response


async def get_usuarios_paginados(
    limit: int = 10,
    skip: int = 0,
    nombre: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    tipo_usuario: Optional[int] = None,
    activo: Optional[bool] = None,
    servicio: Optional[str] = None,
    orden: str = "desc",
) -> Dict[str, Any]:
    db = get_database()
    query: Dict[str, Any] = {}
    if nombre and nombre.strip():
        term = re.escape(nombre.strip())
        query["$or"] = [
            {"name": {"$regex": term, "$options": "i"}},
            {"email": {"$regex": term, "$options": "i"}},
            {"codigo_acceso": {"$regex": term, "$options": "i"}},
        ]
    if fecha_desde or fecha_hasta:
        date_query = {}
        if fecha_desde:
            dt_desde = datetime.combine(fecha_desde, time.min)
            date_query["$gte"] = dt_desde
        if fecha_hasta:
            dt_hasta = datetime.combine(fecha_hasta, time.max)
            date_query["$lte"] = dt_hasta
        query["date_start"] = date_query
    if tipo_usuario is not None:
        query["tipo_usuario"] = tipo_usuario
    if activo is not None:
        query["activo"] = activo
    if servicio and servicio.strip():
        clave_srv = servicio.strip().lower()
        query[f"servicios.{clave_srv}"] = True

    total = await db["usuarios"].count_documents(query)
    sort_direction = DESCENDING if orden.lower() == "desc" else ASCENDING
    cursor = db["usuarios"].find(query).sort("id", sort_direction).skip(skip).limit(limit)

    docs = await cursor.to_list(length=limit)
    items = [format_user_response(doc) for doc in docs]
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": items,
    }


async def get_usuario_by_id(user_id: int) -> Dict[str, Any]:
    db = get_database()
    user = await db["usuarios"].find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )
    return format_user_response(user)


async def toggle_activo(user_id: int) -> Dict[str, Any]:
    db = get_database()
    user = await db["usuarios"].find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )
    current_state = bool(user.get("activo", True))
    new_state = not current_state
    new_estado_id = 2 if new_state else 3
    new_estado_codigo = "ACTIVO" if new_state else "SUSPENDIDO"
    await db["usuarios"].update_one(
        {"id": user_id},
        {
            "$set": {
                "activo": new_state,
                "estado_id": new_estado_id,
                "estado_codigo": new_estado_codigo,
            }
        },
    )
    action_text = "activado" if new_state else "desactivado"
    return {
        "success": True,
        "message": f"Usuario '{user.get('name')}' {action_text} con éxito.",
        "activo": new_state,
    }


async def toggle_servicio_usuario(user_id: int, servicio_clave: str) -> Dict[str, Any]:
    db = get_database()
    user = await db["usuarios"].find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )
    clave = re.sub(r"[^a-z0-9_-]+", "", servicio_clave.strip().lower())
    if not clave:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Clave de servicio inválida.",
        )

    servicios = dict(user.get("servicios") or {})
    nuevo_valor = not bool(servicios.get(clave, False))
    servicios[clave] = nuevo_valor

    await db["usuarios"].update_one(
        {"id": user_id},
        {"$set": {"servicios": servicios}},
    )
    accion = "habilitado" if nuevo_valor else "inhabilitado"
    return {
        "success": True,
        "message": f"Servicio '{clave}' {accion} para '{user.get('name')}'.",
        "servicio": clave,
        "habilitado": nuevo_valor,
        "servicios": servicios,
    }


async def get_servicios_catalogo() -> Dict[str, Any]:
    db = get_database()
    cursor = db["servicios_catalogo"].find({}, {"_id": 0}).sort("clave", ASCENDING)
    docs = await cursor.to_list(length=100)
    for d in docs:
        if d.get("clave") == "mayoresactualizaciones":
            d.setdefault("url_base", settings.MAYORES_FRONTEND_URL)
        elif d.get("clave") == "conmijuegos":
            d.setdefault("url_base", settings.CONMIJUEGOS_FRONTEND_URL)
        else:
            d.setdefault("url_base", settings.FRONTEND_URL)
        d.setdefault("ruta_magic_link", "/acceso")
    return {"success": True, "servicios": docs}


async def crear_servicio_catalogo(
    clave: str,
    nombre: str,
    url_base: str,
    ruta_magic_link: Optional[str] = "/acceso",
    descripcion: Optional[str] = "",
    color: Optional[str] = "indigo",
) -> Dict[str, Any]:
    db = get_database()
    clave_limpia = re.sub(r"[^a-z0-9_-]+", "", clave.strip().lower())
    nombre_limpio = nombre.strip()
    url_limpia = url_base.strip().rstrip("/")
    ruta_limpia = "/" + (ruta_magic_link or "/acceso").strip().lstrip("/")

    if not clave_limpia or not nombre_limpio or not url_limpia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La clave, el nombre y la URL base del servicio son obligatorios.",
        )
    existente = await db["servicios_catalogo"].find_one({"clave": clave_limpia})
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un servicio registrado con la clave '{clave_limpia}'.",
        )
    doc = {
        "clave": clave_limpia,
        "nombre": nombre_limpio,
        "descripcion": (descripcion or "").strip(),
        "url_base": url_limpia,
        "ruta_magic_link": ruta_limpia,
        "color": color or "indigo",
        "activo": True,
    }
    await db["servicios_catalogo"].insert_one(doc)
    return {
        "success": True,
        "message": f"Servicio '{nombre_limpio}' ({clave_limpia}) registrado con URL '{url_limpia}'.",
        "servicio": {k: v for k, v in doc.items() if k != "_id"},
    }


async def actualizar_servicio_catalogo(
    clave: str,
    nombre: Optional[str] = None,
    url_base: Optional[str] = None,
    ruta_magic_link: Optional[str] = None,
    descripcion: Optional[str] = None,
    color: Optional[str] = None,
) -> Dict[str, Any]:
    db = get_database()
    clave_limpia = clave.strip().lower()
    srv = await db["servicios_catalogo"].find_one({"clave": clave_limpia})
    if not srv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Servicio '{clave_limpia}' no encontrado en el catálogo.",
        )

    updates: Dict[str, Any] = {}
    if nombre is not None and nombre.strip():
        updates["nombre"] = nombre.strip()
    if url_base is not None and url_base.strip():
        updates["url_base"] = url_base.strip().rstrip("/")
    if ruta_magic_link is not None and ruta_magic_link.strip():
        updates["ruta_magic_link"] = "/" + ruta_magic_link.strip().lstrip("/")
    if descripcion is not None:
        updates["descripcion"] = descripcion.strip()
    if color is not None and color.strip():
        updates["color"] = color.strip()

    if updates:
        await db["servicios_catalogo"].update_one({"clave": clave_limpia}, {"$set": updates})

    actualizado = await db["servicios_catalogo"].find_one({"clave": clave_limpia}, {"_id": 0})
    return {
        "success": True,
        "message": f"Configuración de '{clave_limpia}' actualizada.",
        "servicio": actualizado,
    }


async def generar_magic_links_por_servicio(
    user_id: int,
    servicio_especifico: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Genera los Magic Links distintos para cada servicio registrado (mayoresactualizaciones, conmijuegos, etc.).
    Cada Magic Link apunta a la URL de ese servicio + su ruta (/acceso?token=<JWT>) para que al abrirlo
    choque contra el autenticador de ese servicio e ingrese directo a su pantalla de inicio.
    """
    db = get_database()
    user = await db["usuarios"].find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )

    token = create_access_token(user)
    catalogo_res = await get_servicios_catalogo()
    servicios_catalogo = catalogo_res["servicios"]
    servicios_usuario = user.get("servicios") or {}

    magic_links_map: Dict[str, Dict[str, Any]] = {}
    magic_links_list: List[Dict[str, Any]] = []

    for srv in servicios_catalogo:
        clave = srv["clave"]
        base_url = srv.get("url_base", settings.FRONTEND_URL).rstrip("/")
        ruta = "/" + srv.get("ruta_magic_link", "/acceso").lstrip("/")
        url_completa = f"{base_url}{ruta}?token={token}"
        habilitado = bool(user.get("tipo_usuario") == 2 or servicios_usuario.get(clave, False))

        item = {
            "clave": clave,
            "nombre": srv.get("nombre", clave),
            "urlBase": base_url,
            "accessUrl": url_completa,
            "habilitado": habilitado,
        }
        magic_links_map[clave] = item
        magic_links_list.append(item)

    # Si se pidió un servicio puntual o por defecto el primero habilitado
    clave_seleccionada = (servicio_especifico or "").strip().lower()
    if clave_seleccionada and clave_seleccionada in magic_links_map:
        primary_url = magic_links_map[clave_seleccionada]["accessUrl"]
    elif "mayoresactualizaciones" in magic_links_map:
        primary_url = magic_links_map["mayoresactualizaciones"]["accessUrl"]
    elif magic_links_list:
        primary_url = magic_links_list[0]["accessUrl"]
    else:
        primary_url = f"{settings.FRONTEND_URL.rstrip('/')}/acceso?token={token}"

    return {
        "success": True,
        "token": token,
        "codigoAcceso": user.get("codigo_acceso"),
        "activo": bool(user.get("activo", True)),
        "accessUrl": primary_url,
        "magicLinks": magic_links_map,
        "magicLinksList": magic_links_list,
        "message": "Enlaces de acceso directo (Magic Links) generados por servicio exitosamente.",
    }


async def get_estados_usuario(solo_habilitados: bool = False) -> Dict[str, Any]:
    db = get_database()
    query = {"habilitado": {"$ne": False}} if solo_habilitados else {}
    cursor = db["estados_usuario"].find(query, {"_id": 0}).sort("id", ASCENDING)
    docs = await cursor.to_list(length=100)
    estados = []
    for doc in docs:
        doc.setdefault("habilitado", True)
        doc.setdefault("permite_login", False)
        doc.setdefault("color", "slate")
        estados.append(doc)
    return {"success": True, "estados": estados}


async def cambiar_estado_usuario(user_id: int, estado_id: int) -> Dict[str, Any]:
    db = get_database()
    user = await db["usuarios"].find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado",
        )
    estado = await db["estados_usuario"].find_one({"id": estado_id})
    if not estado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estado con ID {estado_id} no existe en el catálogo",
        )
    if estado.get("habilitado", True) is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El estado '{estado.get('nombre')}' está inhabilitado en el catálogo y no puede ser asignado",
        )
    estado_codigo = estado.get("codigo", "ACTIVO")
    es_activo = bool(estado.get("permite_login", False) or estado_codigo == "ACTIVO")
    await db["usuarios"].update_one(
        {"id": user_id},
        {
            "$set": {
                "estado_id": estado_id,
                "estado_codigo": estado_codigo,
                "activo": es_activo,
            }
        },
    )
    return {
        "success": True,
        "message": f"Estado del usuario '{user.get('name')}' actualizado a '{estado.get('nombre')}'.",
        "estado_id": estado_id,
        "estado_codigo": estado_codigo,
        "activo": es_activo,
    }


async def crear_estado_usuario(
    nombre: str,
    codigo: Optional[str] = None,
    descripcion: Optional[str] = "",
    color: Optional[str] = "indigo",
    permite_login: bool = False,
) -> Dict[str, Any]:
    db = get_database()
    nombre_limpio = nombre.strip()
    if not nombre_limpio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre del estado no puede estar vacío",
        )
    if codigo and codigo.strip():
        cod = re.sub(r"[^A-Za-z0-9_]+", "_", codigo.strip().upper()).strip("_")
    else:
        cod = re.sub(r"[^A-Za-z0-9_]+", "_", nombre_limpio.upper()).strip("_")
    if not cod:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de estado inválido",
        )
    existente = await db["estados_usuario"].find_one({"codigo": cod})
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un estado con el código '{cod}'",
        )
    ultimo = await db["estados_usuario"].find().sort("id", DESCENDING).limit(1).to_list(length=1)
    nuevo_id = (ultimo[0]["id"] + 1) if ultimo else 1
    nuevo_doc = {
        "id": nuevo_id,
        "codigo": cod,
        "nombre": nombre_limpio,
        "descripcion": (descripcion or "").strip(),
        "permite_login": bool(permite_login),
        "color": color or "indigo",
        "habilitado": True,
    }
    await db["estados_usuario"].insert_one(nuevo_doc)
    return {
        "success": True,
        "message": f"Estado '{nombre_limpio}' creado exitosamente con código '{cod}'.",
        "estado": {k: v for k, v in nuevo_doc.items() if k != "_id"}
    }


async def toggle_habilitado_estado(estado_id: int) -> Dict[str, Any]:
    if estado_id in (1, 2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los estados esenciales del sistema (PENDIENTE_VERIFICACION y ACTIVO) no pueden ser inhabilitados.",
        )
    db = get_database()
    estado = await db["estados_usuario"].find_one({"id": estado_id})
    if not estado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estado con ID {estado_id} no encontrado en el catálogo",
        )
    nuevo_habilitado = not estado.get("habilitado", True)
    await db["estados_usuario"].update_one(
        {"id": estado_id},
        {"$set": {"habilitado": nuevo_habilitado}},
    )
    action_text = "habilitado" if nuevo_habilitado else "inhabilitado"
    return {
        "success": True,
        "message": f"Estado '{estado.get('nombre')}' {action_text} en el catálogo.",
        "estado_id": estado_id,
        "habilitado": nuevo_habilitado,
    }
