from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.features.auth.router import router as auth_router
from app.features.usuario.router import router as usuario_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Microservicio Central de Autenticación y Torre de Control de Usuarios. "
        "Valida el ingreso, registro y baja de cuentas para mayoresactualizaciones, conmijuegos y futuros servicios."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(usuario_router)


@app.get("/health", tags=["Healthcheck"])
async def health_check():
    db = get_database()
    total_users = await db["usuarios"].count_documents({})
    return {
        "status": "ok",
        "service": "autenticador-central",
        "database": settings.DATABASE_NAME,
        "totalUsuarios": total_users,
    }
