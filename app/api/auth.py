from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import random

from app.db.session import get_db
from app.services.usuario import UsuarioService
from app.services.exceptions import ForbiddenError, BadRequestError
from app.schemas.schemas import (
    LoginRequest,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    UsuarioCreate,
    UsuarioResponse
)
from app.core.security import (
    verify_password,
    create_token,
    decode_token,
    TokenType,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

# Almacenamiento temporal de OTP (solo simulación)
_otp_storage: dict[str, tuple[str, datetime]] = {}


# ------------------------
# 🟢 REGISTRAR (NUEVO 🔥)
# ------------------------
@router.post("/register", response_model=UsuarioResponse)
def register(payload: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Registro público.

    SOLO permite crear ADMIN
    """
    try:
        return UsuarioService().create(
            db,
            payload.model_dump(),
            actor_role=None  # 🔥 clave para diferenciar registro público
        )
    except ForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))



def _verify_otp(email: str, code: str) -> bool:
    if email not in _otp_storage:
        return False

    saved_code, expires_at = _otp_storage[email]

    if datetime.now(timezone.utc) > expires_at:
        del _otp_storage[email]
        return False

    if saved_code != code:
        return False

    del _otp_storage[email]
    return True


# ------------------------
# INICIAR SESIÓN
# ------------------------

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = UsuarioService().get_by_email(db, payload.email)

    if not user or not user.activo or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    token = create_token(
        subject=user.email,
        token_type=TokenType.ACCESS
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ------------------------
# RECUPERACIÓN DE CONTRASEÑA
# ------------------------

@router.post("/request-password-reset")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = UsuarioService().get_by_email(db, payload.email)

    token = create_token(
        subject=payload.email,
        token_type=TokenType.RESET,
        expires_delta=timedelta(minutes=15)
    )

    if user and user.activo:
        print(f"[RECUPERACIÓN] {payload.email} -> token: {token}")

    return {
        "message": "Si el email es correcto, se ha enviado un link de recuperación"
    }


@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    decoded = decode_token(payload.token, token_type=TokenType.RESET)

    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )

    email = decoded.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )

    user = UsuarioService().get_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )

    UsuarioService().update(db, user.id, {
        "password": payload.new_password
    })

    return {
        "message": "Contraseña actualizada correctamente"
    }

# ------------------------
# UTILIDADES OTP-One Time Password (SIMULADO)
# ------------------------

def _generate_otp() -> str:
    return f"{random.randint(10000000, 99999999)}"


# ------------------------
# OTP (SIMULADO) - time
# ------------------------

@router.post("/request-otp")
def request_otp(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = UsuarioService().get_by_email(db, payload.email)

    if user and user.activo:
        code = _generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        _otp_storage[payload.email] = (code, expires_at)

        print(f"[OTP] {payload.email} -> {code}")

    return {
        "message": "Si el email existe, se ha enviado un código OTP"
    }


@router.post("/verify-otp", response_model=Token)
def verify_otp(payload: LoginRequest, db: Session = Depends(get_db)):
    if not _verify_otp(payload.email, payload.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP inválido"
        )

    user = UsuarioService().get_by_email(db, payload.email)

    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no activo"
        )

    token = create_token(
        subject=user.email,
        token_type=TokenType.ACCESS
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }