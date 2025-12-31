from fastapi import APIRouter, Request, Depends, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Appointment, Patient, Employee
from app.deps import templates, get_current_user

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.get("")
async def list_appointments(request: Request, db: Session = Depends(get_db)):
    template_name = (
        "appointments/list_fragment.html" if request.headers.get('HX-request')
        else "appointments/list_full.html"
    )
    appointments = db.query(Appointment).order_by(Appointment.date.asc()).all()
    
    # Tratamento simples para exibição amigável da data no template
    for app in appointments:
        app.display_date = app.date.replace("T", " ")
        
    return templates.TemplateResponse(template_name, {
        "request": request,
        "appointments": appointments
    })

@router.get("/new")
async def new_appointment(request: Request, db: Session = Depends(get_db)):
    template_name = (
        "appointments/form_fragment.html" if request.headers.get('HX-request')
        else "appointments/form_full.html"
    )
    patients = db.query(Patient).all()
    doctors = db.query(Employee).filter(Employee.role == "doctor").all()
    return templates.TemplateResponse(template_name, {
        "request": request,
        "patients": patients,
        "doctors": doctors
    })

@router.post("/save")
async def save_appointment(
    request: Request,
    patient_id: int = Form(...),
    doctor_id: int = Form(...),
    date: str = Form(...), # Recebe 'YYYY-MM-DDTHH:MM' do input
    cost: float = Form(0.0),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    # O SQLite armazenará a string exatamente como vem do input datetime-local
    new_app = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        date=date,
        cost=cost,
        notes=notes,
        status="scheduled"
    )
    db.add(new_app)
    db.commit()
    
    return await list_appointments(request, db)

@router.post("/update-status/{app_id}")
async def update_status(app_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    app = db.query(Appointment).filter(Appointment.id == app_id).first()
    if app:
        app.status = status
        db.commit()
    return Response(headers={"HX-Refresh": "true"}) # Recarrega a lista para aplicar cores