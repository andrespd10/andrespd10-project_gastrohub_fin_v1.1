from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLE_ADMIN = "ADMIN"
ROLE_MESERO = "MESERO"
ROLE_COCINA = "COCINA"


class TokenType:
    ACCESS = "access"
    RESET = "reset"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_token(
    subject: str,
    role: Optional[str] = None,
    token_type: str = TokenType.ACCESS,
    expires_delta: Optional[timedelta] = None,
) -> str:

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

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def decode_token(token: str, token_type: str = TokenType.ACCESS) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")

        return payload

    except JWTError as e:
        raise Exception(f"Token inválido: {str(e)}")