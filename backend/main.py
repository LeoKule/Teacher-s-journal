from fastapi import FastAPI
import asyncio
import logging
from datetime import datetime, timezone
import models

from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from database import SessionLocal
from middleware.csrf import CSRFMiddleware

# Загружаем конфигурацию
settings = get_settings()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импортируем роутеры
from routers import auth, journal, curriculum, admin, analytics

# Инициализируем приложение
app = FastAPI(
    title="Teacher Journal API",
    description="API для управления журналом преподавателя",
    version="1.0.0"
)

# ========== MIDDLEWARE ==========

# CSRF middleware (выполняется ПОСЛЕ CORS — Starlette стек применяет последний добавленный первым)
app.add_middleware(CSRFMiddleware)

# Настройка CORS из конфигурации
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)

logger.info(f"CORS настроена для origins: {settings.ALLOWED_ORIGINS}")

# ========== РОУТЕРЫ ==========

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(journal.router)
app.include_router(curriculum.router)
app.include_router(admin.router)
app.include_router(analytics.router)

# ========== HEALTH CHECK ==========

@app.get("/health")
def health_check():
    """Проверка здоровья сервера"""
    logger.info("Health check запрос")
    return {"status": "ok"}


async def _cleanup_token_blacklist():
    """Фоновая задача: удаляет просроченные токены раз в час."""
    while True:
        await asyncio.sleep(3600)
        db = SessionLocal()
        try:
            deleted = db.query(models.TokenBlacklist).filter(
                models.TokenBlacklist.expires_at < datetime.now(timezone.utc)
            ).delete()
            db.commit()
            if deleted:
                logger.info(f"TokenBlacklist: удалено {deleted} просроченных токенов")
        except Exception as e:
            logger.error(f"Ошибка очистки TokenBlacklist: {e}")
            db.rollback()
        finally:
            db.close()


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(_cleanup_token_blacklist())
