from fastapi import FastAPI
import logging
import models
from database import engine
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

# Загружаем конфигурацию
settings = get_settings()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импортируем роутеры
from routers import auth, journal, curriculum, admin

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

# Инициализируем приложение
app = FastAPI(
    title="Teacher Journal API",
    description="API для управления журналом преподавателя",
    version="1.0.0"
)

# ========== MIDDLEWARE ==========

# Настройка CORS из конфигурации
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS настроена для origins: {settings.ALLOWED_ORIGINS}")

# ========== РОУТЕРЫ ==========

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(journal.router)
app.include_router(curriculum.router)
app.include_router(admin.router)

# ========== HEALTH CHECK ==========

@app.get("/health")
def health_check():
    """Проверка здоровья сервера"""
    logger.info("Health check запрос")
    return {"status": "ok"}
