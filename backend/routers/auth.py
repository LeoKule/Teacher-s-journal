from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import jwt
import secrets
import models
import schemas
import crud
import auth
import logging
from routers.dependencies import get_db, get_current_teacher, get_token_from_request, get_client_ip
from collections import defaultdict
from config import get_settings

# Настройка логирования
logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["auth"])

# ========== ПРОСТОЙ RATE LIMITER ==========
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW = 60  # окно в секундах


def check_rate_limit(request: Request) -> bool:
    """Проверяет rate limit для входа (5 попыток в минуту с IP)"""
    client_ip = get_client_ip(request)
    now = datetime.now(timezone.utc).timestamp()

    login_attempts[client_ip] = [
        ts for ts in login_attempts[client_ip]
        if now - ts < LOGIN_ATTEMPT_WINDOW
    ]

    if len(login_attempts[client_ip]) >= MAX_LOGIN_ATTEMPTS:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return False

    login_attempts[client_ip].append(now)
    return True


def _set_access_cookie(response: Response, access_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def _set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=auth.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def _set_csrf_cookie(response: Response, csrf_token: str):
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # читается JS
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=auth.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


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
    """Логин: ставит httpOnly cookies (access, refresh) и JS-readable csrf_token."""

    client_ip = get_client_ip(request)

    if not check_rate_limit(request):
        raise HTTPException(
            status_code=429,
            detail="Слишком много попыток входа. Попробуйте позже."
        )

    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for email: {form_data.username} from {client_ip}")
        try:
            crud.create_audit_log(
                db=db,
                admin_id=None,
                action="failed_login",
                entity_type="auth",
                description=f"Неудачная попытка входа: {form_data.username}",
                ip_address=client_ip,
            )
        except Exception as log_err:
            logger.error(f"Failed to write failed_login audit: {log_err}")
            db.rollback()
        raise HTTPException(status_code=400, detail="Неверный логин или пароль")

    access_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=auth.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    _set_access_cookie(response, access_token)
    _set_refresh_cookie(response, refresh_token)
    _set_csrf_cookie(response, secrets.token_urlsafe(32))

    logger.info(f"Successful login for email: {user.email}")

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "user_role": user.role,
    }


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Обновляет access_token cookie через refresh_token cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        if auth.is_token_blacklisted(db, refresh_token):
            raise HTTPException(status_code=401, detail="Refresh token revoked")

        payload = jwt.decode(refresh_token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = db.query(models.Teacher).filter(models.Teacher.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        new_access_token = auth.create_access_token(data={"sub": user.email})
        _set_access_cookie(response, new_access_token)
        # Обновляем CSRF чтобы не истекал раньше refresh
        _set_csrf_cookie(response, secrets.token_urlsafe(32))
        return {"detail": "ok"}

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/profile", response_model=schemas.TeacherResponse)
def get_profile(current_teacher: models.Teacher = Depends(get_current_teacher)):
    """Получить данные своего профиля"""
    return schemas.TeacherResponse(
        id=current_teacher.id,
        email=current_teacher.email,
        full_name=current_teacher.full_name,
        role=current_teacher.role,
        is_active=current_teacher.is_active,
        last_login=current_teacher.last_login.isoformat() if current_teacher.last_login else None,
        created_at=current_teacher.created_at.isoformat(),
        updated_at=current_teacher.updated_at.isoformat()
    )


@router.patch("/profile", response_model=schemas.TeacherResponse)
def update_profile(
    data: schemas.ProfileUpdate,
    current_teacher: models.Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """Обновить собственный профиль (ФИО, email, пароль)"""
    if data.new_password and not data.current_password:
        raise HTTPException(status_code=400, detail="Для смены пароля укажите текущий пароль")
    teacher = crud.update_teacher_profile(db, current_teacher, data)
    if teacher is None:
        raise HTTPException(status_code=400, detail="Неверный текущий пароль или email уже занят")
    logger.info(f"Profile updated for teacher: {teacher.email}")
    return schemas.TeacherResponse(
        id=teacher.id,
        email=teacher.email,
        full_name=teacher.full_name,
        role=teacher.role,
        is_active=teacher.is_active,
        last_login=teacher.last_login.isoformat() if teacher.last_login else None,
        created_at=teacher.created_at.isoformat(),
        updated_at=teacher.updated_at.isoformat()
    )


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher),
):
    """Выход из системы — добавляет access_token в blacklist и очищает cookies."""
    token = get_token_from_request(request)

    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        expires_at_timestamp = payload.get("exp")

        if expires_at_timestamp:
            expires_at = datetime.fromtimestamp(expires_at_timestamp, tz=timezone.utc)
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)

        auth.add_token_to_blacklist(
            db=db,
            token=token,
            teacher_id=current_teacher.id,
            expires_at=expires_at
        )

        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        response.delete_cookie(key="csrf_token", path="/")

        logger.info(f"Logout successful for teacher: {current_teacher.email}")
        return {"detail": "Успешно завершили сеанс"}

    except jwt.PyJWTError as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
