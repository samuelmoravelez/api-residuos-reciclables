from sqlalchemy import Column, Integer, String
from app.database.conexion import Base

class UsuarioDB(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    nombre = Column(String(150), nullable=False)
    correo = Column(String(150), unique=True, nullable=False, index=True)
    contrasena = Column(String(255), nullable=False)