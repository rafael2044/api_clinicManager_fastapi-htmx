
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

# Schema Base (campos comuns)
class EmployeeBase(BaseModel):
    name: str
    cpf: str = Field(..., pattern=r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$")
    birth_date: date
    role: str
    crm: Optional[str] = None
    specialty_id: Optional[int] = None
    department: Optional[str] = None

# Schema para Criação (o que vem do formulário)
class EmployeeCreate(EmployeeBase):
    pass

# Schema para Resposta (o que sai do banco para o template/API)
class EmployeeResponse(EmployeeBase):
    id: int

    class Config:
        from_attributes = True # Permite converter do modelo SQLAlchemy automaticamente