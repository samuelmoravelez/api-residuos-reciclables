import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate
from app.repositories import usuario_repository

def generar_hash_contrasena(contrasena_plana: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(contrasena_plana.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def registrar_usuario(db: Session, usuario: UsuarioCreate):
    if usuario_repository.obtener_por_id(db, usuario.id):
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un usuario registrado con el ID {usuario.id}"
        )

    if usuario_repository.obtener_por_correo(db, usuario.correo):
        raise HTTPException(
            status_code=400,
            detail=f"El correo {usuario.correo} ya está registrado"
        )

    datos = usuario.model_dump()
    datos["contrasena"] = generar_hash_contrasena(datos["contrasena"])
    return usuario_repository.crear(db, datos)

def listar_usuarios(db: Session):
    return usuario_repository.obtener_todos(db)

def buscar_usuario_por_id(db: Session, usuario_id: int):
    usuario = usuario_repository.obtener_por_id(db, usuario_id)
    if not usuario:
        raise HTTPException(
            status_code=404,
            detail=f"Usuario con ID {usuario_id} no encontrado"
        )
    return usuario

def modificar_usuario(db: Session, usuario_id: int, datos: UsuarioUpdate):
    usuario = buscar_usuario_por_id(db, usuario_id)
    cambios = datos.model_dump(exclude_unset=True)

    if "correo" in cambios:
        usuario_con_correo = usuario_repository.obtener_por_correo(db, cambios["correo"])
        if usuario_con_correo and usuario_con_correo.id != usuario_id:
            raise HTTPException(
                status_code=400,
                detail=f"El correo {cambios['correo']} ya pertenece a otro usuario"
            )

    if "contrasena" in cambios:
        cambios["contrasena"] = generar_hash_contrasena(cambios["contrasena"])

    return usuario_repository.actualizar(db, usuario, cambios)

def borrar_usuario(db: Session, usuario_id: int):
    usuario = buscar_usuario_por_id(db, usuario_id)
    usuario_repository.eliminar(db, usuario)
    return {"mensaje": f"Usuario con ID {usuario_id} eliminado correctamente"}