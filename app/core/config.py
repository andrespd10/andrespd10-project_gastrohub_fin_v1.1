from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # --- Configuración de Base de Datos ---
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # --- Seguridad y JWT ---
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    RESET_TOKEN_EXPIRE_MINUTES: int = Field(15, env="RESET_TOKEN_EXPIRE_MINUTES")

    # --- Limitación de Tasa (Rate Limiting) ---
    RATE_LIMIT_PER_MINUTE: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_LOGIN: int = Field(3, env="RATE_LIMIT_LOGIN")

    # --- Almacenamiento de Rate Limit ---
    # Por defecto usa la memoria (memory://)
    # En producción (con Redis) cambiarías el .env a redis://localhost:6379/0
    RATE_LIMIT_STORAGE_URL: str = Field("memory://", env="RATE_LIMIT_STORAGE_URL")

    # --- Modo Desarrollo ---
    DEBUG: bool = Field(True, env="DEBUG")

    # --- Configuración de Correo ---
    MAIL_FROM: str = Field("test@gastrohub.com", env="MAIL_FROM")
    MAIL_ENABLED: bool = Field(False, env="MAIL_ENABLED")

    # --- Seguridad de Red (cors / hosts)---
    ALLOWED_HOSTS: str = Field("*", env="ALLOWED_HOSTS")

    def get_allowed_hosts(self) -> List[str]:
        # Si es "*", devolvemos una lista con el comodín
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        # Si hay URLs específicas, las separamos por coma
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    # --- CONFIGURACIÓN DE PYDANTIC V2 ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignora variables extra en el .env que no estén aquí
    )

# Instancia global para usar en todo el proyecto
settings = Settings()