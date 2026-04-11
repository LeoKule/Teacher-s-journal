from datetime import datetime, timedelta, timezone
import jwt
import bcrypt  # Используем чистый bcrypt вместо passlib

SECRET_KEY = "super_secret_key_for_my_diploma_project"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365 * 10


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


def create_access_token(data: dict):
    """Генерирует JWT токен"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt