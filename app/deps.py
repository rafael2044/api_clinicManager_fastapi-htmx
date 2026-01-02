from fastapi import Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from typing import List
# from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session

# from app.models import User
from app.models import User
from app import database
from app.auth import ALGORITHM, SECRET_KEY

# # Define que a URL para pegar o token é /auth/token
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Configuring templates directory for Jinja2
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        # Se não houver token, redirecionamos para o login
        raise HTTPException(status_code=302, detail="Not authenticated")

    try:
        # Lógica para decodificar JWT e buscar usuário no banco...
        payload = jwt.decode(
            token.replace("Bearer ", ""), SECRET_KEY, algorithms=[ALGORITHM]
        )
        username = payload.get("sub")
        db_user = db.query(User).filter(User.username == username).first()
        
        if not db_user:
            raise HTTPException(status_code=302, detail="Usuário não encontrado")
        
        request.state.user = db_user
        return db_user
    
    except:
        raise HTTPException(status_code=302, detail="Token invalid")

class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, request: Request):
        # Assumindo que você já colocou o usuário no request.state 
        # dentro do seu middleware de autenticação
        user = getattr(request.state, "user", None)
        
        if not user:
            raise HTTPException(status_code=302, detail="Não autenticado")
            
        # Admin tem "passe livre" em tudo
        if user.employee.role == "admin":
            return True
            
        if user.employee.role not in self.allowed_roles:
            # Se for HTMX, podemos redirecionar para uma página de "Acesso Negado"
            if request.headers.get("HX-Request"):
                raise HTTPException(status_code=403, headers={"HX-Retarget": "#main-content"})
            
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        return True

# async def get_current_user(
#     token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
# ):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Credenciais inválidas ou token expirado",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     try:
#         # Decodifica o token usando a chave secreta
#         payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = schemas.TokenData(username=username)
#     except JWTError:
#         raise credentials_exception

#     # Busca o usuário no banco
#     user = db.query(User).filter(User.username == token_data.username).first()
#     if user is None:
#         raise credentials_exception

#     return user
