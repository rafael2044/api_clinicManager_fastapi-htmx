from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from app.deps import get_db, templates
from app.models import Employee, Specialty
from app.schemas import EmployeeCreate, EmployeeResponse, SpecialtyResponse

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_class=HTMLResponse)
async def list_employees(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    size:int = 5,
    success: str = None,
    error: str = None
):
    offset = (page - 1) * size
    total_count = db.query(Employee).count()
    employees = db.query(Employee).options(joinedload(Employee.specialty_data)).offset(offset).limit(size).all()
    total_pages = (total_count + size - 1) // size
    template = (
        "employees/list_fragment.html"
        if request.headers.get("HX-Request")
        else "employees/list_full.html"
    )
    result = [EmployeeResponse.model_validate(p) for p in employees]
    return templates.TemplateResponse(
        template, {
            "request": request,
            "employees": result,
            "current_page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "success": success,
            "error": error
        }
    )


@router.get("/new", response_class=HTMLResponse)
async def form_employee(request: Request, db: Session = Depends(get_db)):
    is_htmx = request.headers.get("HX-request")
    specialties = db.query(Specialty).all()
    result_specialties = [SpecialtyResponse.model_validate(s) for s in specialties]
    template_name = (
        "employees/form_fragment.html" if request.headers.get("HX-request")
        else "employees/form_full.html")
    return templates.TemplateResponse(
       template_name, {"request": request, "specialties": result_specialties}
    )


@router.get("/edit/{emp_id}", response_class=HTMLResponse)
async def edit_employee(emp_id: int, request: Request, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        template_name = (
            "components/notfound_error.html" if request.headers.get("HX-request")
            else "components/notfound_error_page.html"
        )
        
        return templates.TemplateResponse(
            template_name,
            {
                "request": request,
                "message": f"Não existe nenhum funcionário com o ID {emp_id}.",
                "return_point": "/employees",
                "return_page": "a Lista de Funcionários",
            },
        )

    specialties = (
        db.query(Specialty).all() if employee.role == "doctor" else []
    )
    result_specialties = [SpecialtyResponse.model_validate(s) for s in specialties] if specialties else []
    template_name = (
        "employees/form_fragment.html" if request.headers.get("HX-request")
        else "employees/form_full.html"
    )
    return templates.TemplateResponse(
        template_name,
        {"request": request, "employee": employee, "specialties": result_specialties},
    )


# 3. RENDERIZAÇÃO DINÂMICA DE CAMPOS (O "PULO DO GATO" DO HTMX)
@router.get("/render-fields")
async def render_fields(request: Request, role: str, db: Session = Depends(get_db)):
    if role == "doctor":
        specialties = db.query(Specialty).all()
        result_specialties = [SpecialtyResponse.model_validate(s) for s in specialties]

        return templates.TemplateResponse(
            "employees/partials/fields_medical.html",
            {"request": request, "specialties": result_specialties},
        )
    else:
        return templates.TemplateResponse(
            "employees/partials/fields_admin.html", {"request": request}
        )
    return ""


# 4. SALVAR / ATUALIZAR
@router.post("/save")
async def save_employee(
    request: Request,
    employee_id: int = None,
    name: str = Form(...),
    cpf: str = Form(...),
    birth_date: str = Form(...),
    role: str = Form(...),
    crm: Optional[str] = Form(None),
    specialty_id: Optional[int] = Form(None),
    department: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    employee_request = EmployeeCreate(
        name=name,
        cpf=cpf,
        birth_date=datetime.strptime(birth_date, "%Y-%m-%d").date(),
        role=role,
        crm=crm,
        specialty_id=specialty_id,
        department=department
    )

    if not employee_id:
        new_employee = Employee(
            name=employee_request.name,
            cpf=employee_request.cpf,
            birth_date=employee_request.birth_date,
            role=employee_request.role,
            crm=crm if employee_request.role in ["doctor", "nutritionist"] else None,
            specialty_id=specialty_id if employee_request.role in ["doctor", "nutritionist"] else None,
            department=department if employee_request.role in ["receptionist", "admin"] else None,
        )
        
        exists_cpf = db.query(Employee).filter(Employee.cpf == cpf).first()
        if exists_cpf:
            return templates.TemplateResponse(
                "employees/form_fragment.html", {
                    "request": request,
                    "employee": employee_request,
                    "erro": f"CPF já está em uso."
                }
            )

        try:
            db.add(new_employee)
            db.commit()
            return await list_employees(request, db, success="Funcionário cadastrado com sucesso.")  # Retorna a lista atualizada
        except Exception as e:
            db.rollback()
            return templates.TemplateResponse(
                "employees/form_fragment.html",
                {
                    "request": request,
                    "employee": employee_request,
                    "erro": "Erro interno ao tentar gravar dados.",
                },
            )
    try:
        db_employee = db.query(Employee).filter(Employee.id == int(employee_id)).first()
        if db_employee:
            exists_cpf = db.query(Employee).filter(Employee.cpf == cpf).first()
            if (cpf != db_employee.cpf and not exists_cpf) or (cpf == db_employee.cpf and exists_cpf):
                db_employee.name = employee_request.name
                db_employee.cpf = employee_request.cpf
                db_employee.birth_date=employee_request.birth_date
                db_employee.role = employee_request.role
                db_employee.crm = crm if employee_request.role == "doctor" else None
                db_employee.specialty_id = specialty_id if employee_request.role == "doctor" else None
                db_employee.department = department if employee_request.role != "doctor" else None
                db.commit()
                return await list_employees(request, db, success="Funcionário atualizado com sucesso.")
            template_name = (
                "employees/form_fragment.html" if request.headers.get("HX-request") else
                "employees/form_full.html"
            )
            return templates.TemplateResponse(
                template_name,
                {
                    "request": request,
                    "error": "CPF em uso.",
                    "employee": EmployeeResponse(id=employee_id, **employee_request.model_dump())
                }
            )
    except Exception as e:
        db.rollback()
        template_name = (
            "components/notfound_error.html" if request.headers.get("HX-request")
            else "components/notfound_error_page.html"
        )
        return templates.TemplateResponse(
                template_name,
                {
                    "request": request,
                    "message": f"Erro ao salvar: {e} ",
                },
            )
                    
        


@router.delete("/delete/{emp_id}")
async def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if emp:
        db.delete(emp)
        db.commit()
    return Response(status_code=200)
