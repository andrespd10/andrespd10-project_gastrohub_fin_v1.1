from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    RESET_TOKEN_EXPIRE_MINUTES: int = Field(15, env="RESET_TOKEN_EXPIRE_MINUTES")

    RATE_LIMIT_PER_MINUTE: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_LOGIN: int = Field(5, env="RATE_LIMIT_LOGIN")

    DEBUG: bool = Field(True, env="DEBUG")

    MAIL_FROM: str = Field("test@gastrohub.com", env="MAIL_FROM")
    MAIL_ENABLED: bool = Field(False, env="MAIL_ENABLED")

    # ⚠️ Procesar lista manualmente
    ALLOWED_HOSTS: str = Field("*", env="ALLOWED_HOSTS")

    def get_allowed_hosts(self) -> List[str]:
        return self.ALLOWED_HOSTS.split(",")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()