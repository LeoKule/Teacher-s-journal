from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
import crud
from routers.dependencies import (
    get_db,
    get_current_teacher,
    validate_teaching_assignment_create,
    validate_schedule_template_create,
    validate_lesson_generation_request,
)

router = APIRouter(tags=["curriculum"])


# ========== ГРУППЫ ==========

@router.get("/groups/", response_model=List[schemas.Group])
def read_groups(db: Session = Depends(get_db)):
    """Получить все группы"""
    return crud.get_groups(db)


@router.get("/groups/by-course/{course}", response_model=List[schemas.Group])
def get_groups_by_course(course: int, db: Session = Depends(get_db)):
    """Получить группы по курсу"""
    return db.query(models.StudentGroup).filter(models.StudentGroup.course_year == course).all()


@router.post("/groups/", response_model=schemas.Group)
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать новую группу"""
    return crud.create_group(db=db, group=group)


# ========== СТУДЕНТЫ ==========

@router.get("/students/", response_model=List[schemas.Student])
def read_students(
    group_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Получить список студентов"""
    return crud.get_students(db=db, group_id=group_id)


@router.post("/students/", response_model=schemas.Student)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать нового студента"""
    group = crud.get_group_by_id(db, group_id=student.group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return crud.create_student(db=db, student=student)


# ========== ПРЕДМЕТЫ ==========

@router.get("/subjects/", response_model=List[schemas.Subject])
def read_subjects(
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить предметы преподавателя"""
    return crud.get_subjects(db=db, teacher_id=current_teacher.id)


@router.get("/subjects/by-group/{group_id}", response_model=List[schemas.SubjectShort])
def get_subjects_by_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить предметы, которые преподаватель ведет в группе"""
    assignments = db.query(models.TeachingAssignment).filter(
        models.TeachingAssignment.group_id == group_id,
        models.TeachingAssignment.teacher_id == current_teacher.id
    ).all()

    return [assignment.subject for assignment in assignments]


@router.post("/subjects/", response_model=schemas.Subject)
def create_subject(
    subject: schemas.SubjectCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать новый предмет"""
    return crud.create_subject(db=db, subject=subject, teacher_id=current_teacher.id)


# ========== УРОКИ ==========

@router.get("/lessons/", response_model=List[schemas.Lesson])
def read_lessons(
    group_id: int | None = Query(default=None),
    subject_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить уроки преподавателя"""
    return crud.get_lessons(
        db=db,
        teacher_id=current_teacher.id,
        group_id=group_id,
        subject_id=subject_id,
    )


@router.post("/lessons/", response_model=schemas.Lesson)
def create_lesson(
    lesson: schemas.LessonCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать новый урок"""
    subject = crud.get_subject_by_id(db, subject_id=lesson.subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Предмет не найден")
    if subject.teacher_id != current_teacher.id:
        raise HTTPException(status_code=403, detail="Нельзя создавать занятия для чужого предмета")

    group = crud.get_group_by_id(db, group_id=lesson.group_id)
    if group is None:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    return crud.create_teacher_lesson(db=db, lesson=lesson, teacher_id=current_teacher.id)


# ========== УЧЕБНЫЕ ПЕРИОДЫ ==========

@router.get("/academic-periods/", response_model=List[schemas.AcademicPeriod])
def read_academic_periods(
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить учебные периоды"""
    return crud.get_academic_periods(db=db)


@router.post("/academic-periods/", response_model=schemas.AcademicPeriod)
def create_academic_period(
    academic_period: schemas.AcademicPeriodCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать новый учебный период"""
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


# ========== НАЗНАЧЕНИЯ ПРЕПОДАВАТЕЛЕЙ ==========

@router.get("/teaching-assignments/", response_model=List[schemas.TeachingAssignment])
def read_teaching_assignments(
    academic_period_id: int | None = Query(default=None),
    group_id: int | None = Query(default=None),
    subject_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить назначения преподавателя"""
    return crud.get_teaching_assignments(
        db=db,
        teacher_id=current_teacher.id,
        academic_period_id=academic_period_id,
        group_id=group_id,
        subject_id=subject_id,
    )


@router.post("/teaching-assignments/", response_model=schemas.TeachingAssignment)
def create_teaching_assignment(
    teaching_assignment: schemas.TeachingAssignmentCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать новое назначение"""
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


# ========== ШАБЛОНЫ РАСПИСАНИЯ ==========

@router.get("/schedule-templates/", response_model=List[schemas.ScheduleTemplate])
def read_schedule_templates(
    teaching_assignment_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить шаблоны расписания преподавателя"""
    return crud.get_schedule_templates(
        db=db,
        teacher_id=current_teacher.id,
        teaching_assignment_id=teaching_assignment_id,
    )


@router.post("/schedule-templates/", response_model=schemas.ScheduleTemplate)
def create_schedule_template(
    schedule_template: schemas.ScheduleTemplateCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать новый шаблон расписания"""
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


# ========== ГЕНЕРАЦИЯ И УПРАВЛЕНИЕ УРОКАМИ ==========

@router.post("/lessons/generate/", response_model=schemas.LessonGenerationResponse)
def generate_lessons(
    payload: schemas.LessonGenerationRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Сгенерировать уроки из шаблонов расписания"""
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


@router.post("/lessons/generate/preview/", response_model=schemas.LessonGenerationPreviewResponse)
def preview_generated_lessons(
    payload: schemas.LessonGenerationRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Предпросмотр генерируемых уроков"""
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


@router.post("/lessons/generated/delete/", response_model=schemas.GeneratedLessonDeleteResponse)
def delete_generated_lessons(
    payload: schemas.LessonGenerationRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Удалить сгенерированные уроки"""
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
