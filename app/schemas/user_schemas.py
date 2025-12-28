from .employee_schemas import EmployeeResponse
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List

# Schema Base (campos comuns)
class UserBase(BaseModel):
    username: str
    employee_id: int

# Schema para Criação (o que vem do formulário)
class UserCreate(UserBase):
    password: str

# Schema para Resposta (o que sai do banco para o template/API)
class UserResponse(UserBase):
    id: int
    is_active: bool
    employee: EmployeeResponse

    class Config:
        from_attributes = True # Permite converter do modelo SQLAlchemy automaticamente