from datetime import date, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from models import Appointment, Employee, Patient
from sqlalchemy.orm import Session

from app.deps import get_db

router = APIRouter(prefix="/appointments", tags=["Appointments"])


# --- LISTAR (Com filtros opcionais) ---
@router.get("/", response_class=HTMLResponse)
def read_appointments(
    skip: int = 0,
    limit: int = 100,
    doctor_id: Optional[int] = None,  # Filtro opcional
    date: Optional[str] = None,  # Filtro por dia (YYYY-MM-DD)
    db: Session = Depends(get_db),
):
    query = db.query(Appointment)

    # Aplica filtros se foram passados na URL
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if date:
        # Filtra strings que começam com a data (ex: '2025-12-14')
        query = query.filter(Appointment.date.like(f"{date}%"))

    appointments = (
        query.order_by(Appointment.date.asc()).offset(skip).limit(limit).all()
    )
    return appointments


@router.get("/count")
def count_appointments_today(db: Session = Depends(get_db)):
    date_start = date.today().strftime("%Y-%m-%dT00:00:00")
    date_last = (date.today() + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")
    count = (
        db.query(Appointment)
        .filter(Appointment.date >= date_start)
        .filter(Appointment.date <= date_last)
        .count()
    )
    return count


# --- CRIAR ---
@router.post("/", response_class=HTMLResponse)
def create_appointment(
    appointment: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    # 1. Validar Paciente
    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    # 2. Validar Médico
    doctor = db.query(Employee).filter(Employee.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Médico não encontrado")

    # 2.1 Regra de Negócio: Verificar se é mesmo um médico
    if doctor.role != "doctor":
        raise HTTPException(
            status_code=400, detail="O funcionário selecionado não é um médico"
        )

    # 3. Criar
    # Convertemos o datetime do Pydantic para string ISO para o SQLite
    db_appointment = Appointment(
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        date=appointment.date.isoformat(),
        status=appointment.status,
        notes=appointment.notes,
        cost=appointment.cost,
    )

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment


# --- ATUALIZAR STATUS (Ex: Cancelar ou Finalizar) ---
@router.post("/{appointment_id}/status", response_class=HTMLResponse)
def update_appointment_status(
    appointment_id: int,
    status_update: str,  # Recebe string direta query param ou body simples? Vamos fazer query param para simplificar
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    valid_statuses = ["scheduled", "waiting", "in_progress", "completed", "canceled"]
    if status_update not in valid_statuses:
        raise HTTPException(status_code=400, detail="Status inválido")

    appointment.status = status_update
    db.commit()
    db.refresh(appointment)
    return appointment


# --- DELETAR ---
@router.delete("/{appointment_id}", response_class=HTMLResponse)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    db.delete(appointment)
    db.commit()
    return None
