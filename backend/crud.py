from datetime import date, timedelta

from sqlalchemy.orm import Session, joinedload
import models, schemas, auth

# Получить список всех групп
def get_groups(db: Session):
    return db.query(models.StudentGroup).all()


def get_groups_for_teacher(db: Session, teacher_id: int):
    """Получить только группы, где преподаватель ведет занятия"""
    return (
        db.query(models.StudentGroup)
        .distinct()
        .join(models.TeachingAssignment, models.TeachingAssignment.group_id == models.StudentGroup.id)
        .filter(models.TeachingAssignment.teacher_id == teacher_id)
        .order_by(models.StudentGroup.course_year, models.StudentGroup.group_name)
        .all()
    )


def get_groups_by_course_for_teacher(db: Session, teacher_id: int, course_year: int):
    """Получить группы определенного курса, где преподаватель ведет занятия"""
    return (
        db.query(models.StudentGroup)
        .distinct()
        .join(models.TeachingAssignment, models.TeachingAssignment.group_id == models.StudentGroup.id)
        .filter(
            models.TeachingAssignment.teacher_id == teacher_id,
            models.StudentGroup.course_year == course_year
        )
        .order_by(models.StudentGroup.group_name)
        .all()
    )


def get_group_by_id(db: Session, group_id: int):
    return db.query(models.StudentGroup).filter(models.StudentGroup.id == group_id).first()

# Создать новую группу
def create_group(db: Session, group: schemas.GroupCreate):
    db_group = models.StudentGroup(
        group_name=group.group_name,
        course_year=group.course_year
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

# Создать студента
def create_student(db: Session, student: schemas.StudentCreate):
    db_student = models.Student(
        full_name=student.full_name,
        group_id=student.group_id
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def get_students(db: Session, group_id: int | None = None):
    query = db.query(models.Student).filter(models.Student.is_deleted == False)
    if group_id is not None:
        query = query.filter(models.Student.group_id == group_id)
    return query.order_by(models.Student.full_name).all()


def get_students_for_teacher(db: Session, teacher_id: int, group_id: int | None = None):
    """Получить студентов только из групп, где преподаватель ведет занятия"""
    query = (
        db.query(models.Student)
        .distinct()
        .join(models.StudentGroup, models.StudentGroup.id == models.Student.group_id)
        .join(models.TeachingAssignment, models.TeachingAssignment.group_id == models.StudentGroup.id)
        .filter(
            models.TeachingAssignment.teacher_id == teacher_id,
            models.Student.is_deleted == False
        )
    )
    
    if group_id is not None:
        query = query.filter(models.Student.group_id == group_id)
    
    return query.order_by(models.Student.full_name).all()


def get_student_by_id(db: Session, student_id: int):
    return db.query(models.Student).filter(
        models.Student.id == student_id,
        models.Student.is_deleted == False
    ).first()


def get_teacher_by_email(db: Session, email: str):
    """Ищет преподавателя в базе по email"""
    return db.query(models.Teacher).filter(models.Teacher.email == email).first()


def create_teacher(db: Session, teacher: schemas.TeacherCreate):
    """Регистрирует нового преподавателя"""
    # 1. Берем чистый пароль и хэшируем его
    hashed_password = auth.get_password_hash(teacher.password)

    # 2. Создаем объект модели для записи в БД (чистый пароль забываем навсегда)
    db_teacher = models.Teacher(
        full_name=teacher.full_name,
        email=teacher.email,
        password_hash=hashed_password
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher


def get_academic_periods(db: Session):
    return (
        db.query(models.AcademicPeriod)
        .order_by(models.AcademicPeriod.start_date.desc(), models.AcademicPeriod.id.desc())
        .all()
    )


def get_academic_period_by_id(db: Session, academic_period_id: int):
    return (
        db.query(models.AcademicPeriod)
        .filter(models.AcademicPeriod.id == academic_period_id)
        .first()
    )


def get_academic_period_by_year_and_semester(
    db: Session,
    academic_year: str,
    semester_number: int,
):
    return (
        db.query(models.AcademicPeriod)
        .filter(
            models.AcademicPeriod.academic_year == academic_year,
            models.AcademicPeriod.semester_number == semester_number,
        )
        .first()
    )


def create_academic_period(db: Session, academic_period: schemas.AcademicPeriodCreate):
    db_academic_period = models.AcademicPeriod(
        name=academic_period.name,
        academic_year=academic_period.academic_year,
        semester_number=academic_period.semester_number,
        start_date=academic_period.start_date,
        end_date=academic_period.end_date,
    )
    db.add(db_academic_period)
    db.commit()
    db.refresh(db_academic_period)
    return db_academic_period


def get_teaching_assignment_by_id(db: Session, teaching_assignment_id: int):
    return (
        db.query(models.TeachingAssignment)
        .options(
            joinedload(models.TeachingAssignment.subject),
            joinedload(models.TeachingAssignment.group),
            joinedload(models.TeachingAssignment.academic_period),
        )
        .filter(models.TeachingAssignment.id == teaching_assignment_id)
        .first()
    )


def get_teaching_assignment_by_scope(
    db: Session,
    teacher_id: int,
    subject_id: int,
    group_id: int,
    academic_period_id: int,
):
    return (
        db.query(models.TeachingAssignment)
        .filter(
            models.TeachingAssignment.teacher_id == teacher_id,
            models.TeachingAssignment.subject_id == subject_id,
            models.TeachingAssignment.group_id == group_id,
            models.TeachingAssignment.academic_period_id == academic_period_id,
        )
        .first()
    )


def get_teaching_assignments(
    db: Session,
    teacher_id: int,
    academic_period_id: int | None = None,
    group_id: int | None = None,
    subject_id: int | None = None,
):
    query = (
        db.query(models.TeachingAssignment)
        .options(
            joinedload(models.TeachingAssignment.subject),
            joinedload(models.TeachingAssignment.group),
            joinedload(models.TeachingAssignment.academic_period),
        )
        .filter(models.TeachingAssignment.teacher_id == teacher_id)
    )
    if academic_period_id is not None:
        query = query.filter(models.TeachingAssignment.academic_period_id == academic_period_id)
    if group_id is not None:
        query = query.filter(models.TeachingAssignment.group_id == group_id)
    if subject_id is not None:
        query = query.filter(models.TeachingAssignment.subject_id == subject_id)
    return query.order_by(models.TeachingAssignment.id.desc()).all()


def create_teaching_assignment(
    db: Session,
    teacher_id: int,
    teaching_assignment: schemas.TeachingAssignmentCreate,
):
    db_teaching_assignment = models.TeachingAssignment(
        teacher_id=teacher_id,
        subject_id=teaching_assignment.subject_id,
        group_id=teaching_assignment.group_id,
        academic_period_id=teaching_assignment.academic_period_id,
    )
    db.add(db_teaching_assignment)
    db.commit()
    db.refresh(db_teaching_assignment)
    return get_teaching_assignment_by_id(db, db_teaching_assignment.id)


def get_schedule_templates(
    db: Session,
    teacher_id: int,
    teaching_assignment_id: int | None = None,
):
    query = (
        db.query(models.ScheduleTemplate)
        .join(
            models.TeachingAssignment,
            models.TeachingAssignment.id == models.ScheduleTemplate.teaching_assignment_id,
        )
        .filter(models.TeachingAssignment.teacher_id == teacher_id)
    )
    if teaching_assignment_id is not None:
        query = query.filter(models.ScheduleTemplate.teaching_assignment_id == teaching_assignment_id)
    return query.order_by(
        models.ScheduleTemplate.day_of_week,
        models.ScheduleTemplate.lesson_number,
        models.ScheduleTemplate.id,
    ).all()


def get_schedule_template_by_slot(
    db: Session,
    teaching_assignment_id: int,
    day_of_week: int,
    lesson_number: int,
):
    return (
        db.query(models.ScheduleTemplate)
        .filter(
            models.ScheduleTemplate.teaching_assignment_id == teaching_assignment_id,
            models.ScheduleTemplate.day_of_week == day_of_week,
            models.ScheduleTemplate.lesson_number == lesson_number,
        )
        .first()
    )


def get_schedule_templates_for_generation(
    db: Session,
    teacher_id: int,
    academic_period_id: int,
    teaching_assignment_id: int | None = None,
):
    query = (
        db.query(models.ScheduleTemplate)
        .options(
            joinedload(models.ScheduleTemplate.teaching_assignment).joinedload(
                models.TeachingAssignment.subject
            ),
            joinedload(models.ScheduleTemplate.teaching_assignment).joinedload(
                models.TeachingAssignment.group
            ),
            joinedload(models.ScheduleTemplate.teaching_assignment).joinedload(
                models.TeachingAssignment.academic_period
            ),
        )
        .join(
            models.TeachingAssignment,
            models.TeachingAssignment.id == models.ScheduleTemplate.teaching_assignment_id,
        )
        .filter(
            models.TeachingAssignment.teacher_id == teacher_id,
            models.TeachingAssignment.academic_period_id == academic_period_id,
        )
    )
    if teaching_assignment_id is not None:
        query = query.filter(models.ScheduleTemplate.teaching_assignment_id == teaching_assignment_id)
    return query.order_by(
        models.ScheduleTemplate.day_of_week,
        models.ScheduleTemplate.lesson_number,
        models.ScheduleTemplate.id,
    ).all()


def get_schedule_occurrence_by_template_and_date(
    db: Session,
    schedule_template_id: int,
    lesson_date: date,
):
    return (
        db.query(models.ScheduleOccurrence)
        .filter(
            models.ScheduleOccurrence.schedule_template_id == schedule_template_id,
            models.ScheduleOccurrence.lesson_date == lesson_date,
        )
        .first()
    )


def create_schedule_template(db: Session, schedule_template: schemas.ScheduleTemplateCreate):
    db_schedule_template = models.ScheduleTemplate(
        teaching_assignment_id=schedule_template.teaching_assignment_id,
        day_of_week=schedule_template.day_of_week,
        lesson_number=schedule_template.lesson_number,
        start_time=schedule_template.start_time,
        end_time=schedule_template.end_time,
        classroom=schedule_template.classroom,
    )
    db.add(db_schedule_template)
    db.commit()
    db.refresh(db_schedule_template)
    return db_schedule_template


def generate_lessons_from_templates(
    db: Session,
    templates: list[models.ScheduleTemplate],
    date_from: date,
    date_to: date,
):
    generated_lessons = []
    skipped_count = 0

    for template in templates:
        period = template.teaching_assignment.academic_period
        effective_start = max(date_from, period.start_date)
        effective_end = min(date_to, period.end_date)
        if effective_start > effective_end:
            continue

        current_date = effective_start
        while current_date <= effective_end:
            if current_date.isoweekday() == template.day_of_week:
                existing_occurrence = get_schedule_occurrence_by_template_and_date(
                    db,
                    schedule_template_id=template.id,
                    lesson_date=current_date,
                )
                if existing_occurrence is not None:
                    skipped_count += 1
                else:
                    lesson = models.Lesson(
                        subject_id=template.teaching_assignment.subject_id,
                        group_id=template.teaching_assignment.group_id,
                        teacher_id=template.teaching_assignment.teacher_id,
                        lesson_date=current_date,
                        lesson_topic=None,
                    )
                    db.add(lesson)
                    db.flush()

                    occurrence = models.ScheduleOccurrence(
                        schedule_template_id=template.id,
                        lesson_date=current_date,
                        lesson_id=lesson.id,
                    )
                    db.add(occurrence)
                    generated_lessons.append(
                        {
                            "lesson_id": lesson.id,
                            "lesson_date": current_date,
                            "subject_name": template.teaching_assignment.subject.name,
                            "group_name": template.teaching_assignment.group.group_name,
                            "teaching_assignment_id": template.teaching_assignment.id,
                            "schedule_template_id": template.id,
                        }
                    )
            current_date += timedelta(days=1)

    db.commit()
    return {
        "generated_count": len(generated_lessons),
        "skipped_count": skipped_count,
        "lessons": generated_lessons,
    }


def preview_lessons_from_templates(
    db: Session,
    templates: list[models.ScheduleTemplate],
    date_from: date,
    date_to: date,
):
    preview_lessons = []
    skipped_count = 0

    for template in templates:
        period = template.teaching_assignment.academic_period
        effective_start = max(date_from, period.start_date)
        effective_end = min(date_to, period.end_date)
        if effective_start > effective_end:
            continue

        current_date = effective_start
        while current_date <= effective_end:
            if current_date.isoweekday() == template.day_of_week:
                existing_occurrence = get_schedule_occurrence_by_template_and_date(
                    db,
                    schedule_template_id=template.id,
                    lesson_date=current_date,
                )
                if existing_occurrence is not None:
                    skipped_count += 1
                else:
                    preview_lessons.append(
                        {
                            "lesson_id": None,
                            "lesson_date": current_date,
                            "subject_name": template.teaching_assignment.subject.name,
                            "group_name": template.teaching_assignment.group.group_name,
                            "teaching_assignment_id": template.teaching_assignment.id,
                            "schedule_template_id": template.id,
                        }
                    )
            current_date += timedelta(days=1)

    return {
        "would_generate_count": len(preview_lessons),
        "skipped_count": skipped_count,
        "lessons": preview_lessons,
    }


def get_schedule_occurrences_for_range(
    db: Session,
    teacher_id: int,
    academic_period_id: int,
    date_from: date,
    date_to: date,
    teaching_assignment_id: int | None = None,
):
    query = (
        db.query(models.ScheduleOccurrence)
        .options(
            joinedload(models.ScheduleOccurrence.lesson).joinedload(models.Lesson.grade_records),
            joinedload(models.ScheduleOccurrence.schedule_template)
            .joinedload(models.ScheduleTemplate.teaching_assignment)
            .joinedload(models.TeachingAssignment.subject),
            joinedload(models.ScheduleOccurrence.schedule_template)
            .joinedload(models.ScheduleTemplate.teaching_assignment)
            .joinedload(models.TeachingAssignment.group),
        )
        .join(
            models.ScheduleTemplate,
            models.ScheduleTemplate.id == models.ScheduleOccurrence.schedule_template_id,
        )
        .join(
            models.TeachingAssignment,
            models.TeachingAssignment.id == models.ScheduleTemplate.teaching_assignment_id,
        )
        .filter(
            models.TeachingAssignment.teacher_id == teacher_id,
            models.TeachingAssignment.academic_period_id == academic_period_id,
            models.ScheduleOccurrence.lesson_date >= date_from,
            models.ScheduleOccurrence.lesson_date <= date_to,
        )
    )
    if teaching_assignment_id is not None:
        query = query.filter(models.TeachingAssignment.id == teaching_assignment_id)
    return query.order_by(models.ScheduleOccurrence.lesson_date, models.ScheduleOccurrence.id).all()


def delete_generated_lessons(
    db: Session,
    occurrences: list[models.ScheduleOccurrence],
):
    deleted_lessons = []
    protected_count = 0

    for occurrence in occurrences:
        lesson = occurrence.lesson
        if lesson.grade_records:
            protected_count += 1
            continue

        deleted_lessons.append(
            {
                "lesson_id": lesson.id,
                "lesson_date": occurrence.lesson_date,
                "subject_name": occurrence.schedule_template.teaching_assignment.subject.name,
                "group_name": occurrence.schedule_template.teaching_assignment.group.group_name,
                "teaching_assignment_id": occurrence.schedule_template.teaching_assignment.id,
                "schedule_template_id": occurrence.schedule_template.id,
            }
        )
        db.delete(occurrence)
        db.delete(lesson)

    db.commit()
    return {
        "deleted_count": len(deleted_lessons),
        "protected_count": protected_count,
        "lessons": deleted_lessons,
    }


def get_subjects(db: Session, teacher_id: int):
    return (
        db.query(models.Subject)
        .filter(
            models.Subject.teacher_id == teacher_id,
            models.Subject.is_deleted == False
        )
        .order_by(models.Subject.name)
        .all()
    )


def get_subject_by_id(db: Session, subject_id: int):
    return db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.is_deleted == False
    ).first()


def create_subject(db: Session, subject: schemas.SubjectCreate, teacher_id: int):
    db_subject = models.Subject(name=subject.name, teacher_id=teacher_id)
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


def get_lessons(
    db: Session,
    teacher_id: int,
    group_id: int | None = None,
    subject_id: int | None = None,
):
    query = (
        db.query(models.Lesson)
        .options(
            joinedload(models.Lesson.subject),
            joinedload(models.Lesson.group),
        )
        .join(models.Subject, models.Subject.id == models.Lesson.subject_id)
        .filter(
            models.Subject.teacher_id == teacher_id,
            models.Lesson.is_deleted == False,
            models.Subject.is_deleted == False
        )
    )
    if group_id is not None:
        query = query.filter(models.Lesson.group_id == group_id)
    if subject_id is not None:
        query = query.filter(models.Lesson.subject_id == subject_id)
    return query.order_by(models.Lesson.lesson_date.desc(), models.Lesson.id.desc()).all()


def get_lesson_by_id(db: Session, lesson_id: int):
    return (
        db.query(models.Lesson)
        .options(
            joinedload(models.Lesson.subject),
            joinedload(models.Lesson.group),
        )
        .filter(
            models.Lesson.id == lesson_id,
            models.Lesson.is_deleted == False
        )
        .first()
    )


# Измени заголовок функции, добавив teacher_id: int
def create_teacher_lesson(db: Session, lesson: schemas.LessonCreate, teacher_id: int):
    db_lesson = models.Lesson(
        teacher_id=teacher_id,  # Используем ID, пришедший из аргумента
        subject_id=lesson.subject_id,
        group_id=lesson.group_id,
        lesson_date=lesson.lesson_date,
        lesson_topic=lesson.lesson_topic,
    )
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


def get_grade_records(
    db: Session,
    teacher_id: int,
    lesson_id: int | None = None,
    student_id: int | None = None,
):
    query = (
        db.query(models.GradeRecord)
        .options(
            joinedload(models.GradeRecord.student),
            joinedload(models.GradeRecord.lesson).joinedload(models.Lesson.subject),
        )
        .join(models.Lesson, models.Lesson.id == models.GradeRecord.lesson_id)
        .join(models.Subject, models.Subject.id == models.Lesson.subject_id)
        .filter(
            models.Subject.teacher_id == teacher_id,
            models.GradeRecord.is_deleted == False,
            models.Lesson.is_deleted == False
        )
    )
    if lesson_id is not None:
        query = query.filter(models.GradeRecord.lesson_id == lesson_id)
    if student_id is not None:
        query = query.filter(models.GradeRecord.student_id == student_id)
    return query.order_by(models.GradeRecord.id.desc()).all()


def get_grade_record_by_lesson_and_student(db: Session, lesson_id: int, student_id: int):
    return (
        db.query(models.GradeRecord)
        .filter(
            models.GradeRecord.lesson_id == lesson_id,
            models.GradeRecord.student_id == student_id,
            models.GradeRecord.is_deleted == False
        )
        .first()
    )


def get_grade_record_by_id(db: Session, grade_record_id: int):
    return db.query(models.GradeRecord).filter(
        models.GradeRecord.id == grade_record_id,
        models.GradeRecord.is_deleted == False
    ).first()


def create_grade_record(db: Session, grade_record: schemas.GradeRecordCreate):
    db_grade_record = models.GradeRecord(
        lesson_id=grade_record.lesson_id,
        student_id=grade_record.student_id,
        grade_value=grade_record.grade_value,
        comment=grade_record.comment,
    )
    db.add(db_grade_record)
    db.commit()
    db.refresh(db_grade_record)
    return db_grade_record


def update_grade_record(
    db: Session,
    db_grade_record: models.GradeRecord,
    grade_record: schemas.GradeRecordUpdate,
):
    update_data = grade_record.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        setattr(db_grade_record, field_name, value)

    db.commit()
    db.refresh(db_grade_record)
    return db_grade_record


def delete_grade_record(db: Session, db_grade_record: models.GradeRecord):
    # Soft Delete: помечаем как удаленную вместо физического удаления
    db_grade_record.is_deleted = True
    db.commit()


def upsert_grade_record(db: Session, grade_record: schemas.GradeRecordCreate):
    existing_record = get_grade_record_by_lesson_and_student(
        db,
        lesson_id=grade_record.lesson_id,
        student_id=grade_record.student_id,
    )

    if existing_record is None:
        return create_grade_record(db=db, grade_record=grade_record)

    existing_record.grade_value = grade_record.grade_value
    existing_record.comment = grade_record.comment
    db.commit()
    db.refresh(existing_record)
    return existing_record


def bulk_upsert_grade_records(
    db: Session,
    lesson_id: int,
    rows: list[schemas.BulkGradeRecordUpsertItem],
):
    student_ids = [row.student_id for row in rows]
    existing_records = (
        db.query(models.GradeRecord)
        .filter(
            models.GradeRecord.lesson_id == lesson_id,
            models.GradeRecord.student_id.in_(student_ids),
        )
        .all()
    )
    existing_records_by_student_id = {
        record.student_id: record for record in existing_records
    }

    saved_records = []
    for row in rows:
        record = existing_records_by_student_id.get(row.student_id)
        if record is None:
            record = models.GradeRecord(
                lesson_id=lesson_id,
                student_id=row.student_id,
                grade_value=row.grade_value,
                attendance_status=row.attendance_status,
                comment=row.comment,
            )
            db.add(record)
        else:
            record.grade_value = row.grade_value
            record.attendance_status = row.attendance_status
            record.comment = row.comment
        saved_records.append(record)

    db.commit()
    for record in saved_records:
        db.refresh(record)
    return saved_records


def get_schedule_lessons(
    db: Session,
    teacher_id: int,
    target_date: date | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    query = (
        db.query(models.Lesson)
        .options(
            joinedload(models.Lesson.subject),
            joinedload(models.Lesson.group),
        )
        .join(models.Subject, models.Subject.id == models.Lesson.subject_id)
        .filter(
            models.Subject.teacher_id == teacher_id,
            models.Lesson.is_deleted == False,
            models.Subject.is_deleted == False
        )
    )

    if target_date is not None:
        query = query.filter(models.Lesson.lesson_date == target_date)
    if date_from is not None:
        query = query.filter(models.Lesson.lesson_date >= date_from)
    if date_to is not None:
        query = query.filter(models.Lesson.lesson_date <= date_to)

    return query.order_by(models.Lesson.lesson_date, models.Lesson.id).all()


def get_daily_journal(db: Session, teacher_id: int, target_date: date):
    #  ОПТИМИЗИРОВАНО: Загружаем все уроки с их relations одним запросом
    lessons = (
        db.query(models.Lesson)
        .options(
            joinedload(models.Lesson.subject),
            joinedload(models.Lesson.group),
            joinedload(models.Lesson.grade_records).joinedload(models.GradeRecord.student),
        )
        .join(models.Subject, models.Subject.id == models.Lesson.subject_id)
        .filter(
            models.Subject.teacher_id == teacher_id,
            models.Lesson.lesson_date == target_date,
            models.Lesson.is_deleted == False,
            models.Subject.is_deleted == False
        )
        .order_by(models.Lesson.id)
        .all()
    )

    #  Получаем все уникальные группы из уроков
    group_ids = list(set(lesson.group_id for lesson in lessons))
    
    #  ОПТИМИЗИРОВАНО: Загружаем всех студентов для этих групп одним запросом
    all_students = (
        db.query(models.Student)
        .filter(
            models.Student.group_id.in_(group_ids),
            models.Student.is_deleted == False
        )
        .order_by(models.Student.full_name)
        .all()
    )
    
    #  Кэшируем студентов по group_id для быстрого поиска (O(1) вместо O(n))
    students_by_group_id = {}
    for student in all_students:
        if student.group_id not in students_by_group_id:
            students_by_group_id[student.group_id] = []
        students_by_group_id[student.group_id].append(student)

    lesson_payload = []
    for lesson in lessons:
        #  Берем студентов из кэша вместо отдельного запроса
        students = students_by_group_id.get(lesson.group_id, [])
        
        records_by_student_id = {
            record.student_id: record for record in lesson.grade_records
            if not record.is_deleted  # Не показываем удаленные оценки
        }

        student_rows = []
        for student in students:
            record = records_by_student_id.get(student.id)
            student_rows.append(
                {
                    "student_id": student.id,
                    "student_full_name": student.full_name,
                    "grade_record_id": record.id if record else None,
                    "grade_value": record.grade_value if record else None,
                    "attendance_status": record.attendance_status if record else None,
                    "comment": record.comment if record else None,
                }
            )

        lesson_payload.append(
            {
                "lesson_id": lesson.id,
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
                "students": student_rows,
            }
        )

    return {
        "target_date": target_date,
        "lessons": lesson_payload,
    }


# ========== SOFT DELETE ФУНКЦИИ ==========
# Мягкое удаление и восстановление данных

def soft_delete_student(db: Session, student_id: int):
    """Мягко удаляет студента (помечает как удаленного)"""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if student is None:
        return None
    student.is_deleted = True
    db.commit()
    return student


def restore_student(db: Session, student_id: int):
    """Восстанавливает удаленного студента"""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if student is None:
        return None
    student.is_deleted = False
    db.commit()
    db.refresh(student)
    return student


def soft_delete_subject(db: Session, subject_id: int):
    """Мягко удаляет предмет (помечает как удаленный)"""
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if subject is None:
        return None
    subject.is_deleted = True
    db.commit()
    return subject


def restore_subject(db: Session, subject_id: int):
    """Восстанавливает удаленный предмет"""
    subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
    if subject is None:
        return None
    subject.is_deleted = False
    db.commit()
    db.refresh(subject)
    return subject


def soft_delete_lesson(db: Session, lesson_id: int):
    """Мягко удаляет урок (помечает как удаленный)"""
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if lesson is None:
        return None
    lesson.is_deleted = True
    db.commit()
    return lesson


def restore_lesson(db: Session, lesson_id: int):
    """Восстанавливает удаленный урок"""
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if lesson is None:
        return None
    lesson.is_deleted = False
    db.commit()
    db.refresh(lesson)
    return lesson


def restore_grade_record(db: Session, grade_record_id: int):
    """Восстанавливает удаленную оценку"""
    record = db.query(models.GradeRecord).filter(models.GradeRecord.id == grade_record_id).first()
    if record is None:
        return None
    record.is_deleted = False
    db.commit()
    db.refresh(record)
    return record
