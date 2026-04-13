from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import jwt
import models
import schemas
import crud
import auth
from routers.dependencies import get_db, get_current_teacher

router = APIRouter(tags=["auth"])


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
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Эндпоинт авторизации (логин)"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
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

    return {"access_token": access_token, "token_type": "bearer"}


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
