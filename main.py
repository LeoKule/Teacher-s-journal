from datetime import date
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
import models, schemas, crud
from database import SessionLocal, engine
from fastapi.security import OAuth2PasswordRequestForm
import auth
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
import jwt  # Для расшифровки токена

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Teacher Journal API")

# Разрешаем фронтенду делать запросы к нашему API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # Адреса твоего Vue-сервера
    allow_credentials=True,
    allow_methods=["*"], # Разрешаем любые методы (GET, POST, PUT, DELETE)
    allow_headers=["*"], # Разрешаем любые заголовки (включая Authorization для токена)
)

# Эта переменная указывает FastAPI, где именно клиент получает токен.
# Мы назвали наш эндпоинт "/token", поэтому пишем "token".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Функция-зависимость для создания сессии БД на каждый запрос
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_teacher(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Создаем стандартную ошибку для проблем с авторизацией
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Пытаемся расшифровать токен нашим секретным ключом
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        # В функции create_access_token мы сохраняли email в поле "sub"
        email: str = payload.get("sub")

        if email is None:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Срок действия токена истек")
    except jwt.InvalidTokenError:
        raise credentials_exception

    # Ищем преподавателя в БД
    teacher = crud.get_teacher_by_email(db, email=email)
    if teacher is None:
        raise credentials_exception

    return teacher


def validate_grade_record_access(
    db: Session,
    current_teacher: models.Teacher,
    lesson_id: int,
    student_id: int,
):
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


@app.get("/groups/", response_model=List[schemas.Group])
def read_groups(db: Session = Depends(get_db)):
    return crud.get_groups(db)

@app.post("/groups/", response_model=schemas.Group)
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher) # <--- Замок
):
    return crud.create_group(db=db, group=group)

@app.post("/students/", response_model=schemas.Student)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher) # <--- Замок
):
    group = crud.get_group_by_id(db, group_id=student.group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return crud.create_student(db=db, student=student)

@app.get("/students/", response_model=List[schemas.Student])
def read_students(
    group_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.get_students(db=db, group_id=group_id)


@app.get("/academic-periods/", response_model=List[schemas.AcademicPeriod])
def read_academic_periods(
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    return crud.get_academic_periods(db=db)


@app.post("/academic-periods/", response_model=schemas.AcademicPeriod)
def create_academic_period(
    academic_period: schemas.AcademicPeriodCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    if academic_period.start_date >= academic_period.end_date:
        raise HTTPException(status_code=400, detail="Дата начала должна быть раньше даты окончания")
    existing_academic_period = crud.get_academic_period_by_year_and_semester(
        db,
        academic_year=academic_period.academic_year,
        semester_number=academic_period.semester_number,
    )
    if existing_academic_period is not None:
        raise HTTPException(status_code=400, detail="Такой учебный период уже существует")
    return crud.create_academic_period(db=db, academic_period=academic_period)


@app.get("/teaching-assignments/", response_model=List[schemas.TeachingAssignment])
def read_teaching_assignments(
    academic_period_id: int | None = Query(default=None),
    group_id: int | None = Query(default=None),
    subject_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    return crud.get_teaching_assignments(
        db=db,
        teacher_id=current_teacher.id,
        academic_period_id=academic_period_id,
        group_id=group_id,
        subject_id=subject_id,
    )


@app.post("/teaching-assignments/", response_model=schemas.TeachingAssignment)
def create_teaching_assignment(
    teaching_assignment: schemas.TeachingAssignmentCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    validate_teaching_assignment_create(
        db=db,
        current_teacher=current_teacher,
        teaching_assignment=teaching_assignment,
    )
    existing_teaching_assignment = crud.get_teaching_assignment_by_scope(
        db,
        teacher_id=current_teacher.id,
        subject_id=teaching_assignment.subject_id,
        group_id=teaching_assignment.group_id,
        academic_period_id=teaching_assignment.academic_period_id,
    )
    if existing_teaching_assignment is not None:
        raise HTTPException(status_code=400, detail="Такое назначение уже существует")
    return crud.create_teaching_assignment(
        db=db,
        teacher_id=current_teacher.id,
        teaching_assignment=teaching_assignment,
    )


@app.get("/schedule-templates/", response_model=List[schemas.ScheduleTemplate])
def read_schedule_templates(
    teaching_assignment_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    return crud.get_schedule_templates(
        db=db,
        teacher_id=current_teacher.id,
        teaching_assignment_id=teaching_assignment_id,
    )


@app.post("/schedule-templates/", response_model=schemas.ScheduleTemplate)
def create_schedule_template(
    schedule_template: schemas.ScheduleTemplateCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    validate_schedule_template_create(
        db=db,
        current_teacher=current_teacher,
        schedule_template=schedule_template,
    )
    existing_schedule_template = crud.get_schedule_template_by_slot(
        db,
        teaching_assignment_id=schedule_template.teaching_assignment_id,
        day_of_week=schedule_template.day_of_week,
        lesson_number=schedule_template.lesson_number,
    )
    if existing_schedule_template is not None:
        raise HTTPException(status_code=400, detail="Шаблон для этого слота уже существует")
    return crud.create_schedule_template(db=db, schedule_template=schedule_template)


@app.post("/lessons/generate/", response_model=schemas.LessonGenerationResponse)
def generate_lessons(
    payload: schemas.LessonGenerationRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    validate_lesson_generation_request(
        db=db,
        current_teacher=current_teacher,
        payload=payload,
    )

    templates = crud.get_schedule_templates_for_generation(
        db=db,
        teacher_id=current_teacher.id,
        academic_period_id=payload.academic_period_id,
        teaching_assignment_id=payload.teaching_assignment_id,
    )
    if not templates:
        raise HTTPException(status_code=400, detail="Нет шаблонов расписания для генерации")

    return crud.generate_lessons_from_templates(
        db=db,
        templates=templates,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )


@app.post("/lessons/generate/preview/", response_model=schemas.LessonGenerationPreviewResponse)
def preview_generated_lessons(
    payload: schemas.LessonGenerationRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    validate_lesson_generation_request(
        db=db,
        current_teacher=current_teacher,
        payload=payload,
    )

    templates = crud.get_schedule_templates_for_generation(
        db=db,
        teacher_id=current_teacher.id,
        academic_period_id=payload.academic_period_id,
        teaching_assignment_id=payload.teaching_assignment_id,
    )
    if not templates:
        raise HTTPException(status_code=400, detail="Нет шаблонов расписания для предпросмотра")

    return crud.preview_lessons_from_templates(
        db=db,
        templates=templates,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )


@app.post("/lessons/generated/delete/", response_model=schemas.GeneratedLessonDeleteResponse)
def delete_generated_lessons(
    payload: schemas.LessonGenerationRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    validate_lesson_generation_request(
        db=db,
        current_teacher=current_teacher,
        payload=payload,
    )

    occurrences = crud.get_schedule_occurrences_for_range(
        db=db,
        teacher_id=current_teacher.id,
        academic_period_id=payload.academic_period_id,
        date_from=payload.date_from,
        date_to=payload.date_to,
        teaching_assignment_id=payload.teaching_assignment_id,
    )
    return crud.delete_generated_lessons(db=db, occurrences=occurrences)


@app.get("/subjects/", response_model=List[schemas.Subject])
def read_subjects(
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    return crud.get_subjects(db=db, teacher_id=current_teacher.id)


@app.post("/subjects/", response_model=schemas.Subject)
def create_subject(
    subject: schemas.SubjectCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    return crud.create_subject(db=db, subject=subject, teacher_id=current_teacher.id)


@app.get("/lessons/", response_model=List[schemas.Lesson])
def read_lessons(
    group_id: int | None = Query(default=None),
    subject_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    return crud.get_lessons(
        db=db,
        teacher_id=current_teacher.id,
        group_id=group_id,
        subject_id=subject_id,
    )


@app.post("/lessons/", response_model=schemas.Lesson)
def create_lesson(
    lesson: schemas.LessonCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    subject = crud.get_subject_by_id(db, subject_id=lesson.subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    if subject.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Нельзя создавать занятия для чужого предмета")

    group = crud.get_group_by_id(db, group_id=lesson.group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    return crud.create_teacher_lesson(db=db, lesson=lesson, teacher_id=current_teacher.id)


@app.get("/grade-records/", response_model=List[schemas.GradeRecord])
def read_grade_records(
    lesson_id: int | None = Query(default=None),
    student_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    return crud.get_grade_records(
        db=db,
        teacher_id=current_teacher.id,
        lesson_id=lesson_id,
        student_id=student_id,
    )


@app.get("/schedule/", response_model=List[schemas.ScheduleLesson])
def read_schedule(
    target_date: date | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    lessons = crud.get_schedule_lessons(
        db=db,
        teacher_id=current_teacher.id,
        target_date=target_date,
        date_from=date_from,
        date_to=date_to,
    )

    return [
        {
            "id": lesson.id,
            "lesson_date": lesson.lesson_date,
            "topic": lesson.lesson_topic,
            "subject": {
                "id": lesson.subject.id,
                "name": lesson.subject.name,
            },
            "group": {
                "id": lesson.group.id,
                "group_name": lesson.group.group_name,
                "course_year": lesson.group.course_year,
            },
        }
        for lesson in lessons
    ]


@app.get("/journal/daily/", response_model=schemas.DailyJournal)
def read_daily_journal(
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    return crud.get_daily_journal(
        db=db,
        teacher_id=current_teacher.id,
        target_date=target_date,
    )


@app.put("/grade-records/bulk-upsert/", response_model=schemas.BulkGradeRecordUpsertResponse)
def bulk_upsert_grade_records(
    payload: schemas.BulkGradeRecordUpsertRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    if not payload.rows:
        raise HTTPException(status_code=400, detail="Список строк журнала пуст")

    validate_bulk_grade_record_access(
        db=db,
        current_teacher=current_teacher,
        lesson_id=payload.lesson_id,
        rows=payload.rows,
    )

    records = crud.bulk_upsert_grade_records(
        db=db,
        lesson_id=payload.lesson_id,
        rows=payload.rows,
    )
    return {
        "lesson_id": payload.lesson_id,
        "saved_count": len(records),
        "records": records,
    }


@app.put("/grade-records/upsert/", response_model=schemas.GradeRecord)
def upsert_grade_record(
    grade_record: schemas.GradeRecordCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    validate_grade_record_access(
        db=db,
        current_teacher=current_teacher,
        lesson_id=grade_record.lesson_id,
        student_id=grade_record.student_id,
    )
    return crud.upsert_grade_record(db=db, grade_record=grade_record)


@app.post("/grade-records/", response_model=schemas.GradeRecord)
def create_grade_record(
    grade_record: schemas.GradeRecordCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    lesson = crud.get_lesson_by_id(db, lesson_id=grade_record.lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Занятие не найдено")

    subject = crud.get_subject_by_id(db, subject_id=lesson.subject_id)
    if subject is None or subject.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому занятию")

    student = crud.get_student_by_id(db, student_id=grade_record.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Студент не найден")
    if student.group_id != lesson.group_id:
        raise HTTPException(status_code=400, detail="Студент не состоит в группе этого занятия")

    existing_record = crud.get_grade_record_by_lesson_and_student(
        db,
        lesson_id=grade_record.lesson_id,
        student_id=grade_record.student_id,
    )
    if existing_record:
        raise HTTPException(status_code=400, detail="Запись журнала для этого студента уже существует")

    return crud.create_grade_record(db=db, grade_record=grade_record)


@app.patch("/grade-records/{grade_record_id}", response_model=schemas.GradeRecord)
def update_grade_record(
    grade_record_id: int,
    grade_record: schemas.GradeRecordUpdate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    db_grade_record = crud.get_grade_record_by_id(db, grade_record_id=grade_record_id)
    if db_grade_record is None:
        raise HTTPException(status_code=404, detail="Запись журнала не найдена")

    validate_grade_record_access(
        db=db,
        current_teacher=current_teacher,
        lesson_id=db_grade_record.lesson_id,
        student_id=db_grade_record.student_id,
    )

    if not grade_record.model_dump(exclude_unset=True):
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    return crud.update_grade_record(
        db=db,
        db_grade_record=db_grade_record,
        grade_record=grade_record,
    )


@app.delete("/grade-records/{grade_record_id}", response_model=schemas.MessageResponse)
def delete_grade_record(
    grade_record_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    db_grade_record = crud.get_grade_record_by_id(db, grade_record_id=grade_record_id)
    if db_grade_record is None:
        raise HTTPException(status_code=404, detail="Запись журнала не найдена")

    validate_grade_record_access(
        db=db,
        current_teacher=current_teacher,
        lesson_id=db_grade_record.lesson_id,
        student_id=db_grade_record.student_id,
    )

    crud.delete_grade_record(db=db, db_grade_record=db_grade_record)
    return {"detail": "Запись журнала удалена"}


# Эндпоинт регистрации
@app.post("/register/", response_model=schemas.Teacher)
def register_teacher(teacher: schemas.TeacherCreate, db: Session = Depends(get_db)):
    # Сначала проверяем, нет ли уже такого email в базе
    db_teacher = crud.get_teacher_by_email(db, email=teacher.email)
    if db_teacher:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    return crud.create_teacher(db=db, teacher=teacher)


# Эндпоинт авторизации (логин)
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Ищем пользователя по логину (FastAPI OAuth2 форма по умолчанию использует поле username,
    # мы будем передавать туда email)
    teacher = crud.get_teacher_by_email(db, email=form_data.username)

    # 2. Если пользователя нет или пароль (который мы пропускаем через верификацию) не совпал с хэшем:
    if not teacher or not auth.verify_password(form_data.password, teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Если всё ок, генерируем токен, зашифровав в него email преподавателя
    access_token = auth.create_access_token(
        data={"sub": teacher.email}
    )

    # 4. Отдаем токен клиенту
    return {"access_token": access_token, "token_type": "bearer"}
