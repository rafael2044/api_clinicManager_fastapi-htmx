from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Employee
from app.deps import templates, get_current_user
from app.auth import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_class=HTMLResponse)
async def list_users(request: Request, db: Session = Depends(get_db)):
    # Apenas administradores gerenciam usuários
    if request.state.user.employee.role != "admin":
        raise HTTPException(status_code=403)
        
    users = db.query(User).all()
    # Funcionários que ainda não possuem uma conta de usuário
    available_employees = db.query(Employee).filter(~Employee.user_account.has()).all()
    
    return templates.TemplateResponse("users/list_fragment.html", {
        "request": request,
        "users": users,
        "employees": available_employees
    })

@router.post("/save", response_class=HTMLResponse)
async def save_user(
    request: Request,
    employee_id: int = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    new_user = User(
        username=username,
        hashed_password=get_password_hash(password),
        employee_id=employee_id,
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