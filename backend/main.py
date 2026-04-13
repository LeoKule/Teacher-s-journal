from fastapi import FastAPI
import models
from database import engine
from fastapi.middleware.cors import CORSMiddleware

# Импортируем роутеры
from routers import auth, journal, curriculum

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

# Инициализируем приложение
app = FastAPI(
    title="Teacher Journal API",
    description="API для управления журналом преподавателя",
    version="1.0.0"
)

# ========== MIDDLEWARE ==========

# Настройка CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== РОУТЕРЫ ==========

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(journal.router)
app.include_router(curriculum.router)

# ========== HEALTH CHECK ==========

@app.get("/health")
def health_check():
    """Проверка здоровья сервера"""
    return {"status": "ok"}
from fastapi import FastAPI
import models
from database import engine
from fastapi.middleware.cors import CORSMiddleware

# Импортируем роутеры
from routers import auth, journal, curriculum

# Создаем таблицы в БД
models.Base.metadata.create_all(bind=engine)

# Инициализируем приложение
app = FastAPI(
    title="Teacher Journal API",
    description="API для управления журналом преподавателя",
    version="1.0.0"
)

# ========== MIDDLEWARE ==========

# Настройка CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== РОУТЕРЫ ==========

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(journal.router)
app.include_router(curriculum.router)

# ========== HEALTH CHECK ==========

@app.get("/health")
def health_check():
    """Проверка здоровья сервера"""
    return {"status": "ok"}