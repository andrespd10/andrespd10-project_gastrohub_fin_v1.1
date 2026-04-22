from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
import httpx

from app.db.session import get_db
from app.services.usuario import UsuarioService
from app.services.exceptions import ForbiddenError, BadRequestError, NotFoundError
from app.schemas.schemas import (
    LoginRequest,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    UsuarioResponse,
)
from app.core.config import settings
from app.api.deps import get_current_user
from app.models import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticación - Login y Recuperación"])

# ------------------------
# INICIAR SESIÓN
# ------------------------
def verify_recaptcha(token: str) -> bool:
    try:
        response = httpx.post(
            settings.RECAPTCHA_VERIFY_URL,
            data={"secret": settings.RECAPTCHA_SECRET_KEY, "response": token},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("success", False)
    except Exception:
        return False


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    if not verify_recaptcha(payload.recaptcha_token):
        raise HTTPException(status_code=400, detail="ReCaptcha no válido")

    try:
        token_data = UsuarioService().login(db, payload.email, payload.password)
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except (NotFoundError, BadRequestError):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Establecer el token como cookie HttpOnly para persistir la sesión
    response.set_cookie(
        key="access_token",
        value=token_data["access_token"],
        httponly=True,
        secure=not settings.DEBUG,  # True en producción (HTTPS)
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return token_data


# ------------------------
# VERIFICAR SESIÓN ACTUAL
# ------------------------
@router.get("/me", response_model=UsuarioResponse)
def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user


# ------------------------
# CERRAR SESIÓN
# ------------------------
@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
    )
    return {"message": "Sesión cerrada correctamente"}

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


