from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.schemas.residuo_schema import ResiduoCreate, ResiduoUpdate
from app.repositories import residuo_repository

def registrar_residuo(db: Session, residuo: ResiduoCreate):
    existe = residuo_repository.obtener_por_id(db, residuo.id)
    if existe:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un residuo registrado con el ID {residuo.id}"
        )
    return residuo_repository.crear(db, residuo.model_dump())

def listar_residuos(db: Session, tipo_material: Optional[str] = None):
    if tipo_material:
        material_limpio = tipo_material.strip()
        resultados = residuo_repository.obtener_por_tipo(db, material_limpio)
        return {
            "total": len(resultados),
            "filtro_aplicado": material_limpio,
            "residuos": resultados
        }
    
    resultados = residuo_repository.obtener_todos(db)
    return {"total": len(resultados), "residuos": resultados}

def buscar_residuo_por_id(db: Session, residuo_id: int):
    residuo = residuo_repository.obtener_por_id(db, residuo_id)
    if not residuo:
        raise HTTPException(
            status_code=404,
            detail=f"Residuo con ID {residuo_id} no encontrado"
        )
    return residuo

def modificar_residuo(db: Session, residuo_id: int, datos: ResiduoUpdate):
    residuo = buscar_residuo_por_id(db, residuo_id)
    cambios = datos.model_dump(exclude_unset=True)
    return residuo_repository.actualizar(db, residuo, cambios)

def borrar_residuo(db: Session, residuo_id: int):
    residuo = buscar_residuo_por_id(db, residuo_id)
    residuo_repository.eliminar(db, residuo)
    return {"mensaje": f"Residuo con ID {residuo_id} eliminado de la base de datos"}