# FASTAPI Imports
from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.deps import get_current_user, templates
from app.routers import auth, employees, patients, specialties, users, appointments, medical_records

# Initialize FASTAPI

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(auth.router)
app.include_router(patients.router, dependencies=[Depends(get_current_user)])
app.include_router(specialties.router, dependencies=[Depends(get_current_user)])
app.include_router(users.router, dependencies=[Depends(get_current_user)])
app.include_router(employees.router, dependencies=[Depends(get_current_user)])
app.include_router(appointments.router, dependencies=[Depends(get_current_user)])
app.include_router(medical_records.router, dependencies=[Depends(get_current_user)])


@app.exception_handler(302)
@app.exception_handler(401)  # Caso prefira usar 401 para "Não autorizado"
async def auth_exception_handler(request: Request, exc: Exception):
    login_url = "/auth/login"

    # Se for uma requisição HTMX, o redirecionamento comum não funciona bem (ele tentaria carregar o login dentro de uma div)
    # Por isso, usamos o cabeçalho HX-Redirect
    if request.headers.get("HX-Request"):
        return Response(headers={"HX-Redirect": login_url})

    # Para requisições normais (acesso direto via barra de endereço)
    return RedirectResponse(url=login_url)


@app.get("/", response_class=HTMLResponse, dependencies=[Depends(get_current_user)])
async def index(request: Request):
    template_name = (
        "/home/dashboard.html" if request.headers.get("HX-request")
        else "index.html"
    )
    return templates.TemplateResponse(template_name, {"request": request})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="localhost", port=80, reload=True)
