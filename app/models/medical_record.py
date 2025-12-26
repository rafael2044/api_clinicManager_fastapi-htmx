import datetime

from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), unique=True)

    chief_complaint = Column(Text)  # Queixa principal
    diagnosis = Column(Text)

    # SQLite não tem tipo JSON nativo robusto em versões antigas, mas SQLAlchemy lida bem.
    # Armazenará a lista de medicamentos.
    prescription = Column(JSON)
    physical_exam = Column(Text)  # Exame físico
    medical_certificate = Column(Text, nullable=True)  # Texto do atestado se houver
    icd_code = Column(String(10))  # CID-10

    created_at = Column(String, default=datetime.datetime.utcnow().isoformat)

    appointment = relationship("Appointment", back_populates="medical_record")

    def generate_full_report(self):
        return f"Paciente: {self.appointment.patient.name}..."
