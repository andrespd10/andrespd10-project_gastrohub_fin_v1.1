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
    RATE_LIMIT_LOGIN: int = Field(25, env="RATE_LIMIT_LOGIN")
    RATE_LIMIT_STORAGE_URL: str = Field("memory://", env="RATE_LIMIT_STORAGE_URL")

    RECAPTCHA_SECRET_KEY: str = Field(..., env="RECAPTCHA_SECRET_KEY")
    RECAPTCHA_VERIFY_URL: str = Field("https://www.google.com/recaptcha/api/siteverify", env="RECAPTCHA_VERIFY_URL")

    # --- Modo Desarrollo ---
    DEBUG: bool = Field(True, env="DEBUG")

    # --- Configuración de Correo (GMAIL) ---
    MAIL_USERNAME: str = Field(..., env="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(..., env="MAIL_PASSWORD")
    MAIL_FROM: str = Field(..., env="MAIL_FROM")
    MAIL_PORT: int = Field(587, env="MAIL_PORT")
    MAIL_SERVER: str = Field("smtp.gmail.com", env="MAIL_SERVER")
    MAIL_STARTTLS: bool = Field(True, env="MAIL_STARTTLS")
    MAIL_SSL_TLS: bool = Field(False, env="MAIL_SSL_TLS")
    MAIL_ENABLED: bool = Field(True, env="MAIL_ENABLED")
    
    # --- Frontend ---
    FRONTEND_URL: str = Field("http://localhost:4200", env="FRONTEND_URL")

    # --- Seguridad de Red ---
    ALLOWED_HOSTS: str = Field("http://localhost:4200", env="ALLOWED_HOSTS")

    def get_allowed_hosts(self) -> List[str]:
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    # --- CONFIGURACIÓN DE PYDANTIC V2 ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instancia única para todo el proyecto
settings = Settings()
