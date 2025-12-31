from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import create_access_token, verify_password
from app.deps import get_db, templates
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    # Se o usuário já estiver logado (opcional), você poderia redirecionar para a home
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return templates.TemplateResponse(
                "auth/login.html", {"request": request, "error": "Usuário Não existe."}
            )
        if user and not verify_password(password, user.hashed_password):
            return templates.TemplateResponse(
                "auth/login.html", {"request": request, "error": "Senha inválida."}
            )
        if user and verify_password(password, user.hashed_password) and not user.is_active:
            return templates.TemplateResponse(
                "auth/login.html", {"request": request, "error": "Usuário desativado."}
            )

        token = create_access_token({"sub": user.username})

        # Criamos a resposta e setamos o Cookie
        response = Response(headers={"HX-Redirect": "/"})  # Redireciona para home via HTMX
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,  # Impede acesso via JavaScript (Segurança)
            max_age=28800,
            samesite="lax",
        )
        return response
    except Exception as e:
        print(e)
        return templates.TemplateResponse(
                "auth/login.html", {"request": request, "error": "Erro interno no servidor."}
            )


@router.get("/logout")
async def logout(response: Response):
    response = Response(headers={"HX-Redirect": "/auth/login"})
    response.delete_cookie("access_token")
    return response
