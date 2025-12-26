from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

# Schema Base (campos comuns)
class SpecialtyBase(BaseModel):
    name: str

# Schema para Criação (o que vem do formulário)
class SpecialtyCreate(SpecialtyBase):
    pass

# Schema para Resposta (o que sai do banco para o template/API)
class SpecialtyResponse(SpecialtyBase):
    id: int

    class Config:
        from_attributes = True # Permite converter do modelo SQLAlchemy automaticamente