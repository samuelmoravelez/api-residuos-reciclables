from sqlalchemy.orm import Session
from app.models.residuo import ResiduoDB

def obtener_todos(db: Session):
    return db.query(ResiduoDB).all()

def obtener_por_tipo(db: Session, tipo_material: str):
    return db.query(ResiduoDB).filter(
        ResiduoDB.tipo_material.ilike(tipo_material)
    ).all()

def obtener_por_id(db: Session, residuo_id: int):
    return db.query(ResiduoDB).filter(ResiduoDB.id == residuo_id).first()

def crear(db: Session, datos_residuo: dict):
    nuevo_residuo = ResiduoDB(**datos_residuo)
    db.add(nuevo_residuo)
    db.commit()
    db.refresh(nuevo_residuo)
    return nuevo_residuo

def actualizar(db: Session, residuo: ResiduoDB, cambios: dict):
    for clave, valor in cambios.items():
        setattr(residuo, clave, valor)
    db.commit()
    db.refresh(residuo)
    return residuo

def eliminar(db: Session, residuo: ResiduoDB):
    db.delete(residuo)
    db.commit()