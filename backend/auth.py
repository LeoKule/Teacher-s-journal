from datetime import datetime, timedelta, timezone
import jwt
import bcrypt  # Используем чистый bcrypt вместо passlib
from sqlalchemy.orm import Session
import models
from typing import Optional

SECRET_KEY = "super_secret_key_for_my_diploma_project"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнивает введенный пароль с хэшем из БД"""
    # bcrypt требует данные в формате байтов (utf-8), поэтому кодируем строки
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Превращает обычный пароль в хэш"""
    # Генерируем уникальную "соль" и хэшируем пароль
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Возвращаем в виде обычной строки, чтобы сохранить в БД
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Генерирует JWT токен"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Если время не передано, берем стандартные 15 минут
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str):
    # Ищем пользователя по email
    user = db.query(models.Teacher).filter(models.Teacher.email == email).first()
    if not user:
        return False
    # Проверяем пароль (используем уже существующую у тебя функцию verify_password)
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(models.Teacher).filter(models.Teacher.email == email).first()