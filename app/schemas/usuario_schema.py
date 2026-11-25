from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional

class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, example="Samuel Mora Vélez")
    correo: EmailStr = Field(..., example="samuel.mora@ejemplo.com")

class UsuarioCreate(UsuarioBase):
    id: int = Field(..., gt=0, example=1)
    contrasena: str = Field(..., min_length=6, example="ClaveSegura123")

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2)
    correo: Optional[EmailStr] = None
    contrasena: Optional[str] = Field(None, min_length=6)

class UsuarioResponse(UsuarioBase):
    id: int
    model_config = ConfigDict(from_attributes=True)  