from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import jwt
import models
import schemas
import crud
import auth
import logging
from routers.dependencies import get_db, get_current_teacher
from collections import defaultdict

# Настройка логирования
logger = logging.getLogger(__name__)

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(tags=["auth"])

# ========== ПРОСТОЙ RATE LIMITER ==========
# Словарь для отслеживания попыток входа: {ip: [(timestamp, count), ...]}
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = 60  # окно в секундах


def check_rate_limit(request: Request) -> bool:
    """Проверяет rate limit для входа (5 попыток в минуту с IP)"""
    client_ip = request.client.host
    now = datetime.now(timezone.utc).timestamp()
    
    # Удаляем старые попытки (старше окна)
    login_attempts[client_ip] = [
        ts for ts in login_attempts[client_ip]
        if now - ts < LOGIN_ATTEMPT_WINDOW
    ]
    
    # Если превышено количество попыток - возвращаем False
    if len(login_attempts[client_ip]) >= MAX_LOGIN_ATTEMPTS:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return False
    
    # Добавляем текущую попытку
    login_attempts[client_ip].append(now)
    return True


@router.post("/register/", response_model=schemas.Teacher)
def register_teacher(teacher: schemas.TeacherCreate, db: Session = Depends(get_db)):
    """Регистрирует нового преподавателя"""
    db_teacher = crud.get_teacher_by_email(db, email=teacher.email)
    if db_teacher:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    return crud.create_teacher(db=db, teacher=teacher)


@router.post("/token")
async def login_for_access_token(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Эндпоинт авторизации (логин)"""
    """Эндпоинт авторизации (логин) с rate limiting"""
    
    # =================== RATE LIMITING ===================
    if not check_rate_limit(request):
        logger.warning(f"Login rate limit exceeded for IP: {request.client.host}")
        raise HTTPException(
            status_code=429,
            detail="Слишком много попыток входа. Попробуйте позже."
        )
    
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {form_data.username}")
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    # Создаем Access Token
    access_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Создаем Refresh Token
    refresh_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    # Кладем Refresh в куки
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=auth.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )

    logger.info(f"Successful login for email: {user.email}")
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "user_role": user.role
    }


@router.post("/refresh")
async def refresh_access_token(request: Request, db: Session = Depends(get_db)):
    """Рефреш access токена через refresh токен из куки"""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(models.Teacher).filter(models.Teacher.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        new_access_token = auth.create_access_token(data={"sub": user.email})
        return {"access_token": new_access_token, "token_type": "bearer"}

    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token")
