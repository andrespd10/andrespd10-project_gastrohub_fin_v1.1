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
    OTP = "otp"  # Añadido para la funcionalidad de código temporal

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
    user_id: Optional[int] = None,
) -> str:
    """Crea un token JWT firmado."""
    if expires_delta is None:
        if token_type == TokenType.RESET:
            expires_delta = timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
        elif token_type == TokenType.OTP:
            expires_delta = timedelta(minutes=5) # El OTP suele durar menos
        else:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": token_type,
    }

    if role:
        payload["role"] = role

    if user_id is not None:
        payload["user_id"] = user_id


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

        # Validamos que el propósito del token sea el correcto (access vs reset vs otp)
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El propósito de este token es inválido para esta operación."
            )

        return payload

    except JWTError:
        # Simplificado para no exponer detalles técnicos del error en la respuesta API
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )