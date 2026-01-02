from datetime import datetime
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.deps import templates, get_db, RoleChecker
from app.models import Appointment, MedicalRecord, Patient
# Supondo que você tenha esses schemas para validação
# from app.schemas import MedicalRecordCreate 

router = APIRouter(prefix="/consultations", tags=["Consultations"])

# Apenas médicos podem acessar esta rota
allow_doctor = RoleChecker(["doctor", "admin"])

@router.get("", response_class=HTMLResponse, dependencies=[Depends(allow_doctor)])
async def list_consultations(
    request: Request, 
    db: Session = Depends(get_db),
    success: str = ''
):
    # Obtém o ID do funcionário/médico logado através do estado do request (setado no auth)
    doctor_id = request.state.user.employee_id
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Filtra pacientes agendados para HOJE que estão esperando ou em atendimento
    appointments = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date.contains(today),
        Appointment.status.in_(["scheduled", "waiting", "in_progress"])
    ).order_by(Appointment.date.asc()).all()
    
    template_name = ("consultations/list_consultations_fragment.html" if request.headers.get("HX-request")
                     else "consultations/list_consultations_full.html")
    
    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "appointments": appointments,
            "success": success,
            "now": datetime.now()
        }
    )

@router.get("/history", response_class=HTMLResponse)
async def list_medical_history(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    size: int = 10,
    search: str = ""
):
    offset = (page - 1) * size
    
    # Query base unindo prontuário com agendamento e paciente
    query = db.query(MedicalRecord).join(Appointment).join(Patient)
    
    if search:
        query = query.filter(Patient.name.contains(search) | Patient.cpf.contains(search))
    
    total_count = query.count()
    records = query.order_by(MedicalRecord.created_at.desc()).offset(offset).limit(size).all()
    total_pages = (total_count + size - 1) // size
    
    template_name = ("consultations/history_fragment.html" if request.headers.get("HX-request")
                     else "consultations/history_full.html")
    
    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            "records": records,
            "current_page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "search": search
        }
    )

@router.get("/view/{record_id}", response_class=HTMLResponse)
async def view_medical_record(request: Request, record_id: int, db: Session = Depends(get_db)):
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    
    if not record:
        return templates.TemplateResponse("components/not_found_error.html", {"request": request})
        
    return templates.TemplateResponse(
        "consultations/partials/view_modal.html",
        {
            "request": request,
            "record": record
        }
    )

@router.get("/start/{appointment_id}", response_class=HTMLResponse, dependencies=[Depends(allow_doctor)])
async def start_consultation(
    request: Request, 
    appointment_id: int, 
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        return templates.TemplateResponse("components/not_found_error.html", {"request": request})

    # Se o paciente estava apenas agendado ou esperando, muda para 'em progresso'
    if appointment.status in ["scheduled", "waiting"]:
        appointment.status = "in_progress"
        db.commit()

    return templates.TemplateResponse(
        "consultations/partials/consultation_form.html",
        {
            "request": request,
            "appointment": appointment,
            "now": datetime.now()
        }
    )

@router.post("/save/{appointment_id}", response_class=HTMLResponse, dependencies=[Depends(allow_doctor)])
async def save_medical_record(
    request: Request,
    appointment_id: int,
    chief_complaint: str = Form(...),
    physical_exam: str = Form(...),
    diagnosis: str = Form(...),
    prescription: str = Form(...),
    cid_code: str = Form(None),
    medical_certificate: str = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # 1. Cria o registro médico (Prontuário)
        new_record = MedicalRecord(
            appointment_id=appointment_id,
            chief_complaint=chief_complaint,
            physical_exam=physical_exam,
            diagnosis=diagnosis,
            prescription={"text": prescription}, # Estrutura JSON
            cid_code=cid_code,
            medical_certificate=medical_certificate
        )
        
        # 2. Atualiza o status do agendamento para concluído
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appointment:
            appointment.status = "completed"
        
        db.add(new_record)
        db.commit()

        # Retorna para a lista de consultas com push url
        response = await list_consultations(
            request, 
            db, 
            success=f"Atendimento de {appointment.patient.name} finalizado com sucesso."
        )
        response.headers['HX-Push-Url'] = '/consultations'
        return response

    except Exception as e:
        db.rollback()
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        return templates.TemplateResponse(
            "consultations/consultation_form.html",
            {
                "request": request,
                "appointment": appointment,
                "now": datetime.now(),
                "erro": f"Erro ao salvar prontuário: {str(e)}"
            }
        )