from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session


from app.database import get_db
from app.models import User, Employee
from app.schemas import EmployeeResponse, UserCreate, UserResponse
from app.deps import templates, get_current_user, RoleChecker
from app.auth import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

allow_patient_manage = RoleChecker(["admin"])


@router.get("", response_class=HTMLResponse, dependencies=[Depends(allow_patient_manage)])
async def list_users(request: Request, db: Session = Depends(get_db)):

    users = db.query(User).all()
    result_users = [UserResponse.model_validate(u) for u in users ]
    
    available_employees = db.query(Employee).filter(~Employee.user_account.has()).all()
    result_available_employees = [EmployeeResponse.model_validate(e) for e in available_employees]
    return templates.TemplateResponse("users/list_fragment.html", {
        "request": request,
        "users": result_users,
        "employees": result_available_employees
    })

@router.post("/save", response_class=HTMLResponse)
async def save_user(
    request: Request,
    employee_id: int = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user_request = UserCreate(
        username=username,
        password=password,
        employee_id=employee_id
    )
    
    new_user = User(
        username=user_request.username,
        hashed_password=get_password_hash(user_request.password),
        employee_id=user_request.employee_id,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    # Retorna para a lista atualizada
    return await list_users(request, db)

@router.post("/toggle-status/{user_id}", response_class=HTMLResponse)
async def toggle_user_status(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = not user.is_active
        db.commit()
        
        # Retornamos o fragmento do botão atualizado
        status_text = "Ativo" if user.is_active else "Inativo"
        bg_color = "bg-green-100 text-green-800" if user.is_active else "bg-red-100 text-red-800"
        
        return templates.TemplateResponse("users/partials/status_badge.html", {
            "request": request,
            "user": user,
            "bg_color": bg_color,
            "status_text": status_text
        })