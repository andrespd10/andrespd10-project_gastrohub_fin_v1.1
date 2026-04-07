from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.usuario import UsuarioService
from app.services.exceptions import ForbiddenError, BadRequestError, NotFoundError
from app.schemas.schemas import (
    LoginRequest,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    UsuarioCreate,
    UsuarioResponse
)

router = APIRouter(prefix="/auth", tags=["Autenticación - Login y Recuperación"])

# ------------------------
# INICIAR SESIÓN
# ------------------------
@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        return UsuarioService().login(db, payload.email, payload.password)
    except (NotFoundError, BadRequestError) as exc:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

# ------------------------
# RECUPERACIÓN DE CONTRASEÑA
# ------------------------
@router.post("/request-password-reset")
async def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    # El Router solo ordena al servicio que envíe el correo
    return await UsuarioService().send_password_reset_email(db, payload.email)

@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    try:
        # El Router solo pasa los datos, el Service valida el token y cambia la clave
        return UsuarioService().reset_password_with_token(
            db, 
            payload.token, 
            payload.new_password
        )
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

# ------------------------
# OTP (One Time Password)
# ------------------------
@router.post("/request-otp")
async def request_otp(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    return await UsuarioService().send_otp_email(db, payload.email)

@router.post("/verify-otp", response_model=Token)
def verify_otp(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        return UsuarioService().verify_otp_and_login(db, payload.email, payload.password)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))