from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database.conexion import get_db
from app.schemas.residuo_schema import ResiduoCreate, ResiduoUpdate, ResiduoResponse
from app.services import residuo_service

router = APIRouter(prefix="/residuos", tags=["Residuos"])

@router.post("/", response_model=ResiduoResponse, status_code=201)
def crear_residuo(residuo: ResiduoCreate, db: Session = Depends(get_db)):
    return residuo_service.registrar_residuo(db, residuo)

@router.get("/")
def consultar_residuos(
    tipo_material: Optional[str] = Query(None, description="Filtrar por tipo de material"),
    db: Session = Depends(get_db)
):
    return residuo_service.listar_residuos(db, tipo_material)

@router.get("/{residuo_id}", response_model=ResiduoResponse)
def consultar_residuo_por_id(residuo_id: int, db: Session = Depends(get_db)):
    return residuo_service.buscar_residuo_por_id(db, residuo_id)

@router.put("/{residuo_id}", response_model=ResiduoResponse)
def actualizar_residuo(residuo_id: int, datos: ResiduoUpdate, db: Session = Depends(get_db)):
    return residuo_service.modificar_residuo(db, residuo_id, datos)

@router.delete("/{residuo_id}")
def eliminar_residuo(residuo_id: int, db: Session = Depends(get_db)):
    return residuo_service.borrar_residuo(db, residuo_id)