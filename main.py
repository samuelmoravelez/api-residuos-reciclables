"""
Evidencia: API REST de Gestión de Residuos Reciclables y Usuarios (Arquitectura por Capas)
Aprendiz: SAMUEL MORA VELEZ
Programa: Análisis y Desarrollo de Software (ADSO) - Ficha 3504434
"""

from fastapi import FastAPI
from app.database.conexion import engine, Base
from app.models import residuo, usuario  # noqa: F401 - Registra ambas tablas en SQLAlchemy
from app.routes.residuos import router as residuos_router
from app.routes.usuarios import router as usuarios_router

# Crea las tablas 'residuos' y 'usuarios' en Neon si aún no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Residuos Reciclables y Usuarios",
    description="API con arquitectura por capas conectada a PostgreSQL (Neon) - Aprendiz: Samuel Mora Vélez",
    version="3.0.0"
)

# Registrar capas de rutas
app.include_router(usuarios_router)
app.include_router(residuos_router)

@app.get("/", tags=["Inicio"])
def inicio():
    return {
        "mensaje": "API de Residuos y Usuarios activa en Neon. Abre /docs para probar."
    }