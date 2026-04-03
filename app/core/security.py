from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings

# Configuración para el hasheo de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Constantes de Roles para usar en toda la App
ROLE_ADMIN = "ADMIN"
ROLE_MESERO = "MESERO"
ROLE_COCINA = "COCINA"

class TokenType:
    ACCESS = "access"
    RESET = "reset"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash seguro a partir de una contraseña."""
    return pwd_context.hash(password)

def create_token(
    subject: str,
    role: Optional[str] = None,
    token_type: str = TokenType.ACCESS,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Crea un token JWT firmado."""
    if expires_delta is None:
        if token_type == TokenType.RESET:
            expires_delta = timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
        else:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
        "type": token_type,
    }

    if role:
        payload["role"] = role

    # Firmamos el token con nuestra SECRET_KEY y el Algoritmo definido en settings
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def decode_token(token: str, token_type: str = TokenType.ACCESS) -> dict:
    """
    Decodifica y valida un token JWT. 
    Si es inválido o expiró, lanza una excepción HTTP 401.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )

        # Validamos que el propósito del token sea el correcto (access vs reset)
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El propósito de este token es inválido para esta operación."
            )

        return payload

    except JWTError as e:
        # Esto captura tokens expirados, firmas falsas o manipuladas
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )