from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    cpf = Column(String, unique=True, index=True)
    birth_date = Column(Date)
    contact = Column(String)
    address = Column(String)

    appointments = relationship("Appointment", back_populates="patient")


from . import Appointment
