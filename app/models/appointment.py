from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(
        String
    )  # Armazenaremos como ISO String 'YYYY-MM-DDTHH:MM:SS' para simplificar SQLite
    status = Column(
        String, default="scheduled"
    )  # scheduled, waiting, in_progress, completed, canceled
    notes = Column(Text, nullable=True)
    cost = Column(Float, default=0.0)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Employee", back_populates="appointments")
    medical_record = relationship(
        "MedicalRecord", back_populates="appointment", uselist=False
    )
