"""
Pydantic Settings - конфигурация приложения из переменных окружения (.env файла)
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """
    Конфигурация приложения из переменных окружения.
    Переменные читаются из .env файла в корне backend/.
    """
    
    # ============= Базы данных =============
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str
    
    # ============= Аутентификация =============
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ============= Приложение =============
    DEBUG: bool = False
    
    # ============= CORS =============
    # Для разработки: localhost:5173, 8080, 3000
    # Для production: укажите официальные домены
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    class Config:
        """Конфигурация Pydantic Settings"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True  # Переменные окружения чувствительны к регистру
    
    @property
    def DATABASE_URL(self) -> str:
        """Генерирует строку подключения к БД из отдельных параметров"""
        return (
            f"mysql+pymysql://"
            f"{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@"
            f"{self.DATABASE_HOST}:{self.DATABASE_PORT}/"
            f"{self.DATABASE_NAME}"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Загружает настройки один раз и кэширует их.
    Используется во всем приложении через Depends(get_settings).
    """
    return Settings()
