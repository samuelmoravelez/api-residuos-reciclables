from sqlalchemy.orm import Session
from app.models.usuario import UsuarioDB

def obtener_todos(db: Session):
    return db.query(UsuarioDB).all()

def obtener_por_id(db: Session, usuario_id: int):
    return db.query(UsuarioDB).filter(UsuarioDB.id == usuario_id).first()

def obtener_por_correo(db: Session, correo: str):
    return db.query(UsuarioDB).filter(UsuarioDB.correo == correo).first()

def crear(db: Session, datos_usuario: dict):
    nuevo_usuario = UsuarioDB(**datos_usuario)
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

def actualizar(db: Session, usuario: UsuarioDB, cambios: dict):
    for clave, valor in cambios.items():
        setattr(usuario, clave, valor)
    db.commit()
    db.refresh(usuario)
    return usuario

def eliminar(db: Session, usuario: UsuarioDB):
    db.delete(usuario)
    db.commit()