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
    patients = db.query(Patient).all()
    result = [
        PatientResponse(
            id=p.id,
            name=p.name,
            cpf=p.cpf,
            contact=p.contact,
            birth_date=p.birth_date,
            address=p.address,
        )
        for p in patients
    ]
    is_htmx = request.headers.get("HX-request")

    if is_htmx:
        return templates.TemplateResponse(
            name="patients/list_fragment.html",
            request=request,
            context={"patients": result},
        )

    return templates.TemplateResponse(
        name="patients/list_full.html",
        request=request,
        context={"patients": result},
    )


@router.get("/new", response_class=HTMLResponse, dependencies=[Depends(allow_patient_manage)])
def form_patient(request: Request):
    if request.headers.get("HX-request"):
        return templates.TemplateResponse(
            "patients/form_fragment.html", {"request": request}
        )
    return templates.TemplateResponse("patients/form_full.html", {"request": request})


@router.get("/edit/{patient_id}", response_class=HTMLResponse, dependencies=[Depends(allow_patient_manage)])
async def form_edit_patient(
    request: Request, patient_id: int, db: Session = Depends(get_db)
):
    is_htmx = request.headers.get("HX-request")

    db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if db_patient:
        patient = PatientResponse(
            id=db_patient.id,
            name=db_patient.name,
            cpf=db_patient.cpf,
            birth_date=db_patient.birth_date,
            contact=db_patient.contact,
            address=db_patient.address,
        )
        if is_htmx:
            return templates.TemplateResponse(
                name="patients/form_fragment.html",
                request=request,
                context={"patient": patient},
            )
        return templates.TemplateResponse(
            name="patients/form_full.html",
            request=request,
            context={"patient": patient},
        )
    patients = db.query(Patient).all()
    result = [
        PatientResponse(
            id=p.id,
            name=p.name,
            cpf=p.cpf,
            contact=p.contact,
            birth_date=p.birth_date,
            address=p.address,
        )
        for p in patients
    ]
    if is_htmx:
        return templates.TemplateResponse(
            name="components/not_found_error.html",
            request=request,
            context={
                "request": request,
                "return_point": "/patients",
                "return_page": "a Lista de Pacientes",
                "message": f"Paciente com id {patient_id} não existe.",
            },
        )
    return templates.TemplateResponse(
        "components/notfound_error_page.html",
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
    date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
    try:
        exists = db.query(Patient).filter(Patient.cpf == cpf).first()

        if exists:
            return templates.TemplateResponse(
                "patients/form_fragment.html",
                {
                    "request": request,
                    "patient": Patient(
                        name=name,
                        cpf=cpf,
                        birth_date=date_obj,
                        contact=contact,
                        address=address,
                    ),  # Para não perder o que o usuário digitou
                    "erro": "CPF utilizado por outro paciente",
                },
            )
        novo_paciente = Patient(
            name=name, cpf=cpf, birth_date=date_obj, contact=contact, address=address
        )

        db.add(novo_paciente)
        db.commit()

        # Após salvar, redirecionamos para a lista de pacientes usando HTMX
        patients = db.query(Patient).all()
        return templates.TemplateResponse(
            "patients/list_fragment.html",
            {
                "request": request,
                "patients": patients,
                "success": "Paciente cadastrado com sucesso!",
            },
        )
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "patients/form_fragment.html",
            {
                "request": request,
                "patient": Patient(
                    name=name,
                    cpf=cpf,
                    birth_date=date_obj,
                    contact=contact,
                    address=address,
                ),
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
    date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    try:
        if patient:
            exists = db.query(Patient).filter(Patient.cpf == cpf).first()

            if (patient.cpf != cpf and exists):
                return templates.TemplateResponse(
                    "patients/form_fragment.html",
                    {
                        "request": request,
                        "patient": Patient(
                            name=name,
                            cpf=cpf,
                            birth_date=date_obj,
                            contact=contact,
                            address=address,
                        ),  # Para não perder o que o usuário digitou
                        "erro": "CPF utilizado por outro paciente",
                    },
                )

            patient.name = name
            patient.cpf = cpf
            patient.birth_date = date_obj
            patient.contact = contact
            patient.address = address

            db.commit()

            patients = db.query(Patient).all()
            return templates.TemplateResponse(
                "patients/list_fragment.html",
                {
                    "request": request,
                    "patients": patients,
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
                "patient": Patient(
                    name=name,
                    cpf=cpf,
                    birth_date=date_obj,
                    contact=contact,
                    address=address,
                ),  # Para não perder o que o usuário digitou
                "erro": f"Erro interno ao tentar salvar dados: {e}",
            },
        )


@router.delete("/{patient_id}", dependencies=[Depends(allow_patient_manage)])
async def delete_patient(
    request: Request, patient_id: int, db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient:
        db.delete(patient)
        db.commit()
        patients = db.query(Patient).all()

        return templates.TemplateResponse(
            "patients/list_fragment.html",
            {
                "request": request,
                "patients": patients,
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


# --- BUSCAR POR ID ---
# @router.get("/{patient_id}", response_class=HTMLResponse)
# def read_patient(
#     patient_id: int,
#     db: Session = Depends(get_db),
# ):
#     patient = db.query(Patient).filter(Patient.id == patient_id).first()
#     if patient is None:
#         raise HTTPException(status_code=404, detail="Paciente não encontrado")
#     return patient


# # --- CRIAR ---
# @router.post("/", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
# def create_patient(
#     patient: Annotated[str, Form()],
#     db: Session = Depends(get_db),
# ):
#     # Validar CPF duplicado
#     if db.query(Patient).filter(Patient.cpf == patient.cpf).first():
#         raise HTTPException(
#             status_code=400, detail="CPF já cadastrado para outro paciente"
#         )

#     new_patient = Patient(**patient.model_dump())

#     db.add(new_patient)
#     db.commit()
#     db.refresh(new_patient)
#     return new_patient


# # --- ATUALIZAR ---
# @router.put("/{patient_id}", response_class=HTMLResponse)
# def update_patient(
#     patient_id: int,
#     patient_update: schemas.PatientCreate,
#     db: Session = Depends(get_db),
# ):
#     db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
#     if not db_patient:
#         raise HTTPException(status_code=404, detail="Paciente não encontrado")

#     for key, value in patient_update.model_dump().items():
#         setattr(db_patient, key, value)

#     db.commit()
#     db.refresh(db_patient)
#     return db_patient


# # --- DELETAR ---
# @router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_patient(
#     patient_id: int,
#     db: Session = Depends(get_db),
# ):
#     db_patient = db.query(Patient).filter(Patient.id == patient_id).first()
#     if not db_patient:
#         raise HTTPException(status_code=404, detail="Paciente não encontrado")

#     # Nota de Pleno: Futuramente, verificar se existem consultas (appointments) vinculadas
#     # antes de deletar, para manter a integridade do histórico médico.

#     db.delete(db_patient)
#     db.commit()
#     return None
