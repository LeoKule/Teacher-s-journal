from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import jwt
import models
import schemas
import crud
import auth
from database import SessionLocal
from fastapi.security import OAuth2PasswordBearer

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    """Создает сессию БД на каждый запрос"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_teacher(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Проверяет токен и возвращает текущего пользователя"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Срок действия токена истек")
    except jwt.InvalidTokenError:
        raise credentials_exception

    teacher = crud.get_teacher_by_email(db, email=email)
    if teacher is None:
        raise credentials_exception
    
    # Проверяем, активен ли учитель
    if not teacher.is_active:
        raise HTTPException(status_code=403, detail="Ваш аккаунт заблокирован")

    return teacher


def get_current_admin(current_teacher: models.Teacher = Depends(get_current_teacher)):
    """Проверяет, что текущий пользователь администратор"""
    if current_teacher.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется роль администратора"
        )
    return current_teacher


def validate_grade_record_access(
    db: Session,
    current_teacher: models.Teacher,
    lesson_id: int,
    student_id: int,
):
    """Проверяет доступ преподавателя к оценке студента"""
    lesson = crud.get_lesson_by_id(db, lesson_id=lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Занятие не найдено")

    subject = crud.get_subject_by_id(db, subject_id=lesson.subject_id)
    if subject is None or subject.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому занятию")

    student = crud.get_student_by_id(db, student_id=student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    if student.group_id != lesson.group_id:
        raise HTTPException(status_code=400, detail="Студент не состоит в группе этого занятия")

    return lesson, student


def validate_bulk_grade_record_access(
    db: Session,
    current_teacher: models.Teacher,
    lesson_id: int,
    rows: List[schemas.BulkGradeRecordUpsertItem],
):
    """Проверяет доступ к пакету оценок"""
    lesson = crud.get_lesson_by_id(db, lesson_id=lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Занятие не найдено")

    subject = crud.get_subject_by_id(db, subject_id=lesson.subject_id)
    if subject is None or subject.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому занятию")

    students = crud.get_students(db=db, group_id=lesson.group_id)
    students_by_id = {student.id: student for student in students}

    seen_student_ids = set()
    for row in rows:
        if row.student_id in seen_student_ids:
            raise HTTPException(status_code=400, detail="В пакете есть дублирующиеся студенты")
        seen_student_ids.add(row.student_id)

        student = students_by_id.get(row.student_id)
        if student is None:
            raise HTTPException(
                status_code=400,
                detail=f"Студент {row.student_id} не состоит в группе этого занятия",
            )

    return lesson


def validate_teaching_assignment_create(
    db: Session,
    current_teacher: models.Teacher,
    teaching_assignment: schemas.TeachingAssignmentCreate,
):
    """Проверяет возможность создания назначения"""
    subject = crud.get_subject_by_id(db, subject_id=teaching_assignment.subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    if subject.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Нельзя создавать назначение для чужого предмета")

    group = crud.get_group_by_id(db, group_id=teaching_assignment.group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    academic_period = crud.get_academic_period_by_id(
        db,
        academic_period_id=teaching_assignment.academic_period_id,
    )
    if academic_period is None:
        raise HTTPException(status_code=404, detail="Учебный период не найден")

    return subject, group, academic_period


def validate_schedule_template_create(
    db: Session,
    current_teacher: models.Teacher,
    schedule_template: schemas.ScheduleTemplateCreate,
):
    """Проверяет возможность создания шаблона расписания"""
    teaching_assignment = crud.get_teaching_assignment_by_id(
        db,
        teaching_assignment_id=schedule_template.teaching_assignment_id,
    )
    if teaching_assignment is None:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    if teaching_assignment.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому назначению")
    if schedule_template.start_time >= schedule_template.end_time:
        raise HTTPException(status_code=400, detail="Время начала должно быть раньше времени окончания")

    return teaching_assignment


def validate_lesson_generation_request(
    db: Session,
    current_teacher: models.Teacher,
    payload: schemas.LessonGenerationRequest,
):
    """Проверяет возможность генерации уроков"""
    if payload.date_from > payload.date_to:
        raise HTTPException(status_code=400, detail="Начальная дата диапазона позже конечной")

    academic_period = crud.get_academic_period_by_id(
        db,
        academic_period_id=payload.academic_period_id,
    )
    if academic_period is None:
        raise HTTPException(status_code=404, detail="Учебный период не найден")

    if payload.teaching_assignment_id is not None:
        teaching_assignment = crud.get_teaching_assignment_by_id(
            db,
            teaching_assignment_id=payload.teaching_assignment_id,
        )
        if teaching_assignment is None:
            raise HTTPException(status_code=404, detail="Назначение не найдено")
        if teaching_assignment.teacher_id != current_teacher.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому назначению")
        if teaching_assignment.academic_period_id != payload.academic_period_id:
            raise HTTPException(status_code=400, detail="Назначение не относится к выбранному периоду")

    return academic_period
