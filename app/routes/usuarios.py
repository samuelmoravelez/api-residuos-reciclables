from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database.conexion import get_db
from app.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", response_model=UsuarioResponse, status_code=201)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return usuario_service.registrar_usuario(db, usuario)

@router.get("/", response_model=List[UsuarioResponse])
def consultar_usuarios(db: Session = Depends(get_db)):
    return usuario_service.listar_usuarios(db)

@router.get("/{id}", response_model=UsuarioResponse)
def consultar_usuario_por_id(id: int, db: Session = Depends(get_db)):
    return usuario_service.buscar_usuario_por_id(db, id)

@router.put("/{id}", response_model=UsuarioResponse)
def actualizar_usuario(id: int, datos: UsuarioUpdate, db: Session = Depends(get_db)):
    return usuario_service.modificar_usuario(db, id, datos)

@router.delete("/{id}")
def eliminar_usuario(id: int, db: Session = Depends(get_db)):
    return usuario_service.borrar_usuario(db, id)