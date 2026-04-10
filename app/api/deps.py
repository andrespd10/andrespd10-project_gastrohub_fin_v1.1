from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.services.usuario import UsuarioService
from app.core.security import decode_token, TokenType
from app.models.enums import UserRole
from app.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> Usuario:

    payload = decode_token(token, token_type=TokenType.ACCESS)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    usuario = UsuarioService().get_by_email(db, email)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    return usuario


def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:

    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )

    return current_user


def require_role(roles: List[UserRole]):
    def role_dependency(
        current_user: Usuario = Depends(get_current_active_user)
    ):

        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos suficientes"
            )

        return current_user

    return role_dependency