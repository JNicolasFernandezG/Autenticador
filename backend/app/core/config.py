import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "Autenticador Central - Torre de Control"
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "autenticador_db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    SERVICE_API_KEY: str = os.getenv("SERVICE_API_KEY", "")
    FRONTEND_URL: str = os.getenv(
        "FRONTEND_URL", "https://autenticacion.asistodo.com.ar"
    ).rstrip("/")
    MAYORES_FRONTEND_URL: str = os.getenv(
        "MAYORES_FRONTEND_URL", "https://mayoresactualizaciones.asistodo.com.ar"
    ).rstrip("/")
    CONMIJUEGOS_FRONTEND_URL: str = os.getenv(
        "CONMIJUEGOS_FRONTEND_URL", "https://cognijuegos.asistodo.com.ar"
    ).rstrip("/")
    CORS_ORIGINS: List[str] = [
        o.strip()
        for o in os.getenv(
            "CORS_ORIGINS",
            "https://autenticacion.asistodo.com.ar,https://mayoresactualizaciones.asistodo.com.ar,https://cognijuegos.asistodo.com.ar,http://localhost:5173,http://localhost:3000,http://localhost:5174",
        ).split(",")
        if o.strip()
    ]


settings = Settings()
