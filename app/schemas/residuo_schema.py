from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date

class ResiduoBase(BaseModel):
    tipo_material: str = Field(..., example="Plástico")
    peso_kg: float = Field(..., gt=0, example=12.5)
    fecha_recoleccion: date = Field(..., example="2026-11-24")
    lugar: str = Field(..., example="Centro de Acopio Robledo")
    responsable: str = Field(..., example="Samuel Mora Vélez")

class ResiduoCreate(ResiduoBase):
    id: int = Field(..., gt=0, example=1)

class ResiduoUpdate(BaseModel):
    tipo_material: Optional[str] = None
    peso_kg: Optional[float] = Field(None, gt=0)
    fecha_recoleccion: Optional[date] = None
    lugar: Optional[str] = None
    responsable: Optional[str] = None

class ResiduoResponse(ResiduoCreate):
    model_config = ConfigDict(from_attributes=True)