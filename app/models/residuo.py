from sqlalchemy import Column, Integer, String, Float, Date
from app.database.conexion import Base

class ResiduoDB(Base):
    __tablename__ = "residuos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    tipo_material = Column(String(100), nullable=False, index=True)
    peso_kg = Column(Float, nullable=False)
    fecha_recoleccion = Column(Date, nullable=False)
    lugar = Column(String(150), nullable=False)
    responsable = Column(String(150), nullable=False)