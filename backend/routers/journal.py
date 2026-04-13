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
    validate_grade_record_access,
    validate_bulk_grade_record_access,
)

router = APIRouter(tags=["journals"])


@router.get("/grade-records/", response_model=List[schemas.GradeRecord])
def read_grade_records(
    lesson_id: int | None = Query(default=None),
    student_id: int | None = Query(default=None),
    group_id: int | None = Query(default=None),
    subject_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить оценки с фильтрацией"""
    if group_id is not None and subject_id is not None:
        lessons = crud.get_lessons(
            db=db,
            teacher_id=current_teacher.id,
            group_id=group_id,
            subject_id=subject_id,
        )
        lesson_ids = [lesson.id for lesson in lessons]
        query = db.query(models.GradeRecord).filter(models.GradeRecord.lesson_id.in_(lesson_ids))
        if student_id is not None:
            query = query.filter(models.GradeRecord.student_id == student_id)
        return query.order_by(models.GradeRecord.id.desc()).all()
    
    return crud.get_grade_records(
        db=db,
        teacher_id=current_teacher.id,
        lesson_id=lesson_id,
        student_id=student_id,
    )


@router.post("/grade-records/", response_model=schemas.GradeRecord)
def create_grade_record(
    grade_record: schemas.GradeRecordCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать новую оценку"""
    validate_grade_record_access(
        db=db,
        current_teacher=current_teacher,
        lesson_id=grade_record.lesson_id,
        student_id=grade_record.student_id,
    )

    existing_record = crud.get_grade_record_by_lesson_and_student(
        db,
        lesson_id=grade_record.lesson_id,
        student_id=grade_record.student_id,
    )
    if existing_record:
        raise HTTPException(status_code=400, detail="Запись журнала для этого студента уже существует")

    return crud.create_grade_record(db=db, grade_record=grade_record)


@router.put("/grade-records/upsert/", response_model=schemas.GradeRecord)
def upsert_grade_record(
    grade_record: schemas.GradeRecordCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать или обновить оценку"""
    validate_grade_record_access(
        db=db,
        current_teacher=current_teacher,
        lesson_id=grade_record.lesson_id,
        student_id=grade_record.student_id,
    )
    return crud.upsert_grade_record(db=db, grade_record=grade_record)


@router.put("/grade-records/bulk-upsert/", response_model=schemas.BulkGradeRecordUpsertResponse)
def bulk_upsert_grade_records(
    payload: schemas.BulkGradeRecordUpsertRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Создать или обновить несколько оценок за раз"""
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


@router.patch("/grade-records/{grade_record_id}", response_model=schemas.GradeRecord)
def update_grade_record(
    grade_record_id: int,
    grade_record: schemas.GradeRecordUpdate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Обновить оценку"""
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


@router.delete("/grade-records/{grade_record_id}", response_model=schemas.MessageResponse)
def delete_grade_record(
    grade_record_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Удалить оценку"""
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


# ========== РАСПИСАНИЕ И ЕЖЕДНЕВНЫЙ ЖУРНАЛ ==========

@router.get("/schedule/", response_model=List[schemas.ScheduleLesson])
def read_schedule(
    target_date: date | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить расписание на период"""
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


@router.get("/journal/daily/", response_model=schemas.DailyJournal)
def read_daily_journal(
    target_date: date = Query(...),
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """Получить ежедневный журнал на дату"""
    return crud.get_daily_journal(
        db=db,
        teacher_id=current_teacher.id,
        target_date=target_date,
    )
