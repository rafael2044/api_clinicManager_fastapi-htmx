from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.deps import get_db, templates
from app.models import Employee, Specialty

router = APIRouter(prefix="/employees", tags=["Employees"])


# --- LISTAR TODOS (GET) ---
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
    employees = db.query(Employee).offset(offset).limit(size).all()
    total_pages = (total_count + size - 1) // size
    template = (
        "employees/list_fragment.html"
        if request.headers.get("HX-Request")
        else "employees/list_full.html"
    )
    return templates.TemplateResponse(
        template, {
            "request": request,
            "employees": employees,
            "current_page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "success": success,
            "error": error
        }
    )


# 2. FORMULÁRIO (NOVO/EDITAR)
@router.get("/new", response_class=HTMLResponse)
async def form_employee(request: Request, db: Session = Depends(get_db)):
    is_htmx = request.headers.get("HX-request")
    specialties = db.query(Specialty).all()
    template_name = (
        "employees/form_fragment.html" if request.headers.get("HX-request")
        else "employees/form_full.html")
    return templates.TemplateResponse(
       template_name, {"request": request, "employee": None, "specialties": specialties}
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
                "return_point": "/employees/",
                "return_page": "a Lista de Funcionários",
            },
        )

    specialties = (
        db.query(Specialty).all() if employee.role == "doctor" else []
    )
    template_name = (
        "employees/form_fragment.html" if request.headers.get("HX-request")
        else "employees/form_full.html"
    )
    return templates.TemplateResponse(
        template_name,
        {"request": request, "employee": employee, "specialties": specialties},
    )


# 3. RENDERIZAÇÃO DINÂMICA DE CAMPOS (O "PULO DO GATO" DO HTMX)
@router.get("/render-fields")
async def render_fields(request: Request, role: str, db: Session = Depends(get_db)):
    if role == "doctor":
        specialties = db.query(Specialty).all()
        return templates.TemplateResponse(
            "employees/partials/fields_medical.html",
            {"request": request, "specialties": specialties},
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
    date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()

    if not employee_id:
        new_emp = Employee(
            name=name,
            cpf=cpf,
            birth_date=date_obj,
            role=role,
            crm=crm if role in ["doctor", "nutritionist"] else None,
            specialty_id=specialty_id if role in ["doctor", "nutritionist"] else None,
            department=department if role in ["receptionist", "admin"] else None,
        )
        
        exists_cpf = db.query(Employee).filter(Employee.cpf == cpf).first()
        if exists_cpf:
            return templates.TemplateResponse(
                "employees/form_fragment.html", {
                    "request": request,
                    "employee": new_emp,
                    "erro": f"CPF já está em uso."
                }
            )

        try:
            db.add(new_emp)
            db.commit()
            return await list_employees(request, db, success="Funcionário cadastrado com sucesso.")  # Retorna a lista atualizada
        except Exception as e:
            db.rollback()
            return templates.TemplateResponse(
                "employees/form_fragment.html",
                {
                    "request": request,
                    "employee": new_emp,
                    "erro": "Erro interno ao tentar gravar dados.",
                },
            )
    try:
        db_employee = db.query(Employee).filter(Employee.id == int(employee_id)).first()
        if db_employee:
            exists_cpf = db.query(Employee).filter(Employee.cpf == cpf).first()
            if (cpf != db_employee.cpf and not exists_cpf) or (cpf == db_employee.cpf and exists_cpf):
                db_employee.name = name
                db_employee.cpf = cpf
                db_employee.birth_date=date_obj
                db_employee.role = role
                db_employee.crm = crm if role == "doctor" else None
                db_employee.specialty_id = specialty_id if role == "doctor" else None
                db_employee.department = department if role != "doctor" else None
                db.commit()
                return await list_employees(request, db, success="Funcionário atualizado com sucesso.")
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
                    "erro": "Erro ao salvar: CPF já cadastrado ou dados inválidos.",
                },
            )
                    
        


@router.delete("/delete/{emp_id}")
async def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if emp:
        db.delete(emp)
        db.commit()
    return Response(status_code=200)
