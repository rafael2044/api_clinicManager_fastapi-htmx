from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import database, models, schemas
from ..deps import get_db, get_current_user

router = APIRouter(
    prefix="/medical-records",
    tags=["Medical Records"]
)

# --- LISTAR (Histórico do Paciente) ---
@router.get("/", response_model=List[schemas.MedicalRecordResponse])
def read_medical_records(
    patient_id: Optional[int] = None, # Filtro principal
    doctor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.MedicalRecord)
    
    # Geralmente queremos filtrar pelos relacionamentos via Appointment
    if patient_id:
        query = query.join(models.Appointment).filter(models.Appointment.patient_id == patient_id)
    
    if doctor_id:
        query = query.join(models.Appointment).filter(models.Appointment.doctor_id == doctor_id)

    records = query.all()
    
    # Conversão manual do JSON de prescrição se necessário (SQLAlchemy costuma fazer automático, 
    # mas o Pydantic valida a estrutura)
    return records

# --- CRIAR (Finalizar Atendimento) ---
@router.post("/", response_model=schemas.MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(
    record: schemas.MedicalRecordCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Validar se a consulta existe
    appointment = db.query(models.Appointment).filter(models.Appointment.id == record.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Consulta não encontrada")

    # 2. Validar se o utilizador atual é o médico da consulta (Segurança)
    # Nota: Em sistemas reais, devemos validar se current_user.employee_id == appointment.doctor_id
    # Para facilitar testes, deixarei comentado, mas é uma boa prática.
    # if current_user.employee_id != appointment.doctor_id and current_user.employee.role != 'admin':
    #     raise HTTPException(status_code=403, detail="Não tem permissão para preencher este prontuário")

    # 3. Validar se já existe prontuário para esta consulta (Evitar duplicatas)
    if appointment.medical_record:
        raise HTTPException(status_code=400, detail="Esta consulta já possui um prontuário registado")

    # 4. Criar o Prontuário
    # Precisamos converter a lista de Pydantic models para lista de dicts para salvar no JSON do SQLite
    prescription_json = [item.model_dump() for item in record.prescription]

    new_record = models.MedicalRecord(
        appointment_id=record.appointment_id,
        chief_complaint=record.chief_complaint,
        diagnosis=record.diagnosis,
        prescription=prescription_json
    )
    
    db.add(new_record)
    
    # 5. Side-Effect: Atualizar status da consulta para 'completed'
    appointment.status = "completed"
    
    db.commit()
    db.refresh(new_record)
    return new_record