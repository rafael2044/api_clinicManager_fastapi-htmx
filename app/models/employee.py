from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)  # Usaremos UUID string
    name = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    birth_date = Column(Date)
    role = Column(String)  # 'doctor', 'receptionist', 'admin'

    # Campos específicos de Médico
    crm = Column(String, nullable=True)
    specialty_id = Column(Integer, ForeignKey("specialties.id"), nullable=True)
    # Campos específicos de Staff
    department = Column(String, nullable=True)

    # Relacionamentos
    user_account = relationship("User", back_populates="employee", uselist=False)
    appointments = relationship("Appointment", back_populates="doctor")
    specialty_data = relationship("Specialty", back_populates="doctors")
