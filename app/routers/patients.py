from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.deps import templates
from app.models import Patient
from app.schemas.patient_schemas import PatientResponse, PatientCreate

from app.deps import get_db, RoleChecker

router = APIRouter(prefix="/patients", tags=["Patients"])

allow_patient_manage = RoleChecker(["admin", "receptionist"])

@router.get("", response_class=HTMLResponse, dependencies=[Depends(allow_patient_manage)])
async def list_complete_patients(request: Request, db: Session = Depends(get_db)):
    templote_name = ("patients/list_fragment.html" if request.headers.get("HX-request")
                     else "patients/list_full.html")
    
    patients = db.query(Patient).all()
    result = [
        PatientResponse.model_validate(p)
        for p in patients
    ]
    
    return templates.TemplateResponse(
        templote_name,
        {
            "request": request,
            "patients": result
        }
    )


@router.get("/new", response_class=HTMLResponse, dependencies=[Depends(allow_patient_manage)])
def form_patient(request: Request):
    templote_name = ("patients/form_fragment.html" if request.headers.get("HX-request")
                     else "patients/form_full.html")
    
    return templates.TemplateResponse(templote_name, {"request": request})


@router.get("/edit/{patient_id}", response_class=HTMLResponse, dependencies=[Depends(allow_patient_manage)])
async def form_edit_patient(
    request: Request, patient_id: int, db: Session = Depends(get_db)
):
    
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if db_patient:
        templote_name = ("patients/form_fragment.html" if request.headers.get("HX-request")
                     else "patients/form_full.html")
        patient = PatientResponse(
            id=db_patient.id,
            name=db_patient.name,
            cpf=db_patient.cpf,
            birth_date=db_patient.birth_date,
            contact=db_patient.contact,
            address=db_patient.address,
        )
        return templates.TemplateResponse(
            templote_name,
            {
                "request": request,
                "patient": patient
            }
        )

    templote_name = ("components/not_found_error.html" if request.headers.get("HX-request")
                     else "components/notfound_error_page.html")
   
    return templates.TemplateResponse(
        templote_name,
        {
            "request": request,
            "return_point": "/patients",
            "return_page": "a Lista de Pacientes",
            "message": f"Paciente com id {patient_id} não existe.",
        },
    )


@router.post("/save", response_class=HTMLResponse, dependencies=[Depends(allow_patient_manage)])
async def salvar_paciente(
    request: Request,
    name: str = Form(...),
    cpf: str = Form(...),
    birth_date: str = Form(...),
    contact: str = Form(...),
    address: str = Form(None),
    db: Session = Depends(get_db),
):
    patient_request = PatientCreate(
        name=name,
        cpf=cpf,
        birth_date=datetime.strptime(birth_date, "%Y-%m-%d").date(),
        contact=contact,
        address=address
    )
    try:
        exists = db.query(Patient).filter(Patient.cpf == cpf).first()

        if exists:
            return templates.TemplateResponse(
                "patients/form_fragment.html",
                {
                    "request": request,
                    "patient": patient_request,
                    "erro": "CPF utilizado por outro paciente",
                },
            )
        patient = Patient(
            **patient_request.model_dump()
        )

        db.add(patient)
        db.commit()

        # Após salvar, redirecionamos para a lista de pacientes usando HTMX
        patients = db.query(Patient).all()
        result = [PatientResponse.model_validate(p) for p in patients]
        return templates.TemplateResponse(
            "patients/list_fragment.html",
            {
                "request": request,
                "patients": result,
                "success": "Paciente cadastrado com sucesso!",
            },
        )
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "patients/form_fragment.html",
            {
                "request": request,
                "patient": patient_request,
                "erro": "Erro interno ao salvar os dados.",
            },
            status_code=500,
        )


@router.post("/edit/{patient_id}", response_class=HTMLResponse, dependencies=[Depends(allow_patient_manage)])
async def edit_patient(
    request: Request,
    patient_id: int,
    name: str = Form(...),
    cpf: str = Form(...),
    birth_date: str = Form(...),
    contact: str = Form(...),
    address: str = Form(None),
    db: Session = Depends(get_db),
):
    patient_update = PatientCreate(
        name=name,
        cpf=cpf,
        birth_date=datetime.strptime(birth_date, "%Y-%m-%d").date(),
        contact=contact,
        address=address
    )
    
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    try:
        if db_patient:
            exists = db.query(Patient).filter(Patient.cpf == cpf).first()

            if (db_patient.cpf != patient_update.cpf and exists):
                return templates.TemplateResponse(
                    "patients/form_fragment.html",
                    {
                        "request": request,
                        "patient": patient_update,  # Para não perder o que o usuário digitou
                        "erro": "CPF utilizado por outro paciente",
                    },
                )

            db_patient.name = patient_update.name
            db_patient.cpf = patient_update.cpf
            db_patient.birth_date = patient_update.birth_date
            db_patient.contact = patient_update.contact
            db_patient.address = patient_update.address

            db.commit()

            patients = db.query(Patient).all()
            result = [PatientResponse.model_validate(p) for p in patients]
            return templates.TemplateResponse(
                "patients/list_fragment.html",
                {
                    "request": request,
                    "patients": result,
                    "success": "Paciente Atualizado com sucesso!",
                },
            )
        return templates.TemplateResponse(
            "patients/notfound_error.html",
            {
                "request": request,
                "return_point": "/patients",
                "return_page": "a Lista de Pacientes",
                "message": f"Não existe paciente com o ID {patient_id}",
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "patients/form_fragment.html",
            {
                "request": request,
                "patient": patient_update,
                "erro": f"Erro interno ao tentar salvar dados: {e}",
            },
        )


@router.delete("/{patient_id}", dependencies=[Depends(allow_patient_manage)])
async def delete_patient(
    request: Request, patient_id: int, db: Session = Depends(get_db)
):
    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if db_patient:
        db.delete(db_patient)
        db.commit()
        patients = db.query(Patient).all()
        result = [PatientResponse.model_validate(p) for p in patients]

        return templates.TemplateResponse(
            "patients/list_fragment.html",
            {
                "request": request,
                "patients": result,
                "success": "Paciente Excluido com sucesso!",
            },
        )
    return templates.TemplateResponse(
        "components/notfound_error.html",
        {
            "request": request,
            "return_point": "/patients",
            "return_page": "a Lista de Paciente",
            "message": f"Não existe paciente com o ID {patient_id}",
        },
    )


@router.get("/count")
def amount_patients(db: Session = Depends(get_db)):
    count = db.query(Patient).count()
    return count
