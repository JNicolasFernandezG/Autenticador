import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Deque, Dict
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.features.auth.router import router as auth_router
from app.features.usuario.router import router as usuario_router
from app.features.sso import router as sso_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Microservicio Central de Autenticación y Torre de Control de Usuarios. "
        "Valida el ingreso, registro, Magic Links por servicio y baja de cuentas."
    ),
    version="1.2.0",
    lifespan=lifespan,
)

# CORS restringido a orígenes autorizados (Punto 9 y 18 de Seguridad)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Service-Key"],
)

# Rate Limiting en memoria por IP (Puntos 11 y 12: Rate Limiting + Protección contra Bots/Fuerza Bruta)
_ip_requests: Dict[str, Deque[float]] = defaultdict(deque)
_ip_auth_requests: Dict[str, Deque[float]] = defaultdict(deque)
MAX_GENERAL_REQ_PER_MIN = 120
MAX_AUTH_REQ_PER_MIN = 25
MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB


@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    path = request.url.path

    # 1. Bloqueo de archivos y directorios ocultos (/.env, /.git, etc.) (Punto 16)
    if "/." in path:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})

    # 2. Límite de tamaño de payload (10 MB)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_BYTES:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "El tamaño de la petición supera el límite permitido de 10MB."},
        )

    # 3. Rate Limiting por IP
    client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
    now = time.time()
    window_start = now - 60.0

    q_gen = _ip_requests[client_ip]
    while q_gen and q_gen[0] < window_start:
        q_gen.popleft()
    if len(q_gen) >= MAX_GENERAL_REQ_PER_MIN:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Demasiadas peticiones. Por favor, aguarde un minuto."},
        )
    q_gen.append(now)

    if path.startswith("/auth/login") or path.startswith("/api/auth/login"):
        q_auth = _ip_auth_requests[client_ip]
        while q_auth and q_auth[0] < window_start:
            q_auth.popleft()
        if len(q_auth) >= MAX_AUTH_REQ_PER_MIN:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Demasiados intentos de inicio de sesión. Intente nuevamente en 1 minuto."},
            )
        q_auth.append(now)

    response = await call_next(request)

    # 4. Cabeceras de Seguridad en defensa en profundidad (Punto 18)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if "server" in response.headers:
        del response.headers["server"]

    return response


app.include_router(auth_router)
app.include_router(auth_router, prefix="/api", include_in_schema=False)
app.include_router(usuario_router)
app.include_router(usuario_router, prefix="/api", include_in_schema=False)
app.include_router(sso_router)
app.include_router(sso_router, prefix="/api", include_in_schema=False)


@app.get("/health", tags=["Healthcheck"])
async def health_check():
    db = get_database()
    total_users = await db["usuarios"].count_documents({})
    return {
        "status": "ok",
        "service": "autenticador-central",
        "totalUsuarios": total_users,
    }
