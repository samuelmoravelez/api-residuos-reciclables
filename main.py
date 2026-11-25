"""
Evidencia: API REST para gestión de residuos reciclables (Arquitectura por Capas)
Aprendiz: SAMUEL MORA VELEZ
Programa: Análisis y Desarrollo de Software (ADSO) - Ficha 3504434
"""

from fastapi import FastAPI
from app.database.conexion import engine, Base
from app.models import residuo  # noqa: F401 - Registra el modelo antes de crear tablas
from app.routes.residuos import router as residuos_router

# Crea las tablas en Neon si aún no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Gestión de Residuos Reciclables",
    description="API con arquitectura por capas conectada a PostgreSQL (Neon) - Aprendiz: Samuel Mora Vélez",
    version="3.0.0"
)

# Registrar capa de rutas
app.include_router(residuos_router)

@app.get("/", tags=["Inicio"])
def inicio():
    return {
        "mensaje": "API de Residuos con arquitectura por capas conectada a Neon. Abre /docs para probar."
    }