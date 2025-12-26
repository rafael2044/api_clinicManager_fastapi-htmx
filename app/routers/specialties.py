from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.deps import get_db, templates
from app.models import Specialty

router = APIRouter(prefix="/specialties", tags=["Specialties"])


@router.get("/manage", response_class=HTMLResponse)
async def manage_specialties(request: Request, db: Session = Depends(get_db)):
    specialties = db.query(Specialty).order_by(Specialty.name).all()
    # Rota híbrida: se for HTMX retorna fragmento, se for URL retorna página completa
    template = (
        "specialties/manage_fragment.html"
        if request.headers.get("HX-Request")
        else "specialties/manage_full.html"
    )
    return templates.TemplateResponse(
        template, {"request": request, "specialties": specialties}
    )


@router.post("/", response_class=HTMLResponse)
async def save_specialty(
    request: Request, name: str = Form(...), db: Session = Depends(get_db)
):
    new_spec = Specialty(name=name.upper())
    db.add(new_spec)
    db.commit()

    specialties = db.query(Specialty).order_by(Specialty.name).all()
    return templates.TemplateResponse(
        "specialties/list_partial.html",
        {"request": request, "specialties": specialties},
    )


@router.delete("/delete/{spec_id}")
async def delete_specialty(request: Request, spec_id: int, db: Session = Depends(get_db)):
    spec = db.query(Specialty).filter(Specialty.id == spec_id).first()
    if spec:
        db.delete(spec)
        db.commit()
    specialties = db.query(Specialty).all()
    return templates.TemplateResponse('specialties/list_partial.html', {"request": request, "specialties": specialties})

