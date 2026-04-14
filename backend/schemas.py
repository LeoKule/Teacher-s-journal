from datetime import date, time
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, EmailStr, field_validator


# Строгая схема для создания/обновления пользователя
class UserCreate(BaseModel):
    # EmailStr автоматически проверит, что строка имеет формат почты (name@domain.com)
    email: EmailStr
    password: str = Field(min_length=8, description="Пароль должен быть не менее 8 символов")
    full_name: str = Field(min_length=2, max_length=50)

# Схемы для Групп
class GroupBase(BaseModel):
    group_name: str
    course_year: int

class GroupCreate(GroupBase):
    pass # При создании группы нам нужно только имя и курс

class Group(GroupBase):
    id: int
    class Config:
        from_attributes = True # Позволяет Pydantic читать данные из моделей SQLAlchemy

# Схемы для Студентов
class StudentBase(BaseModel):
    full_name: str
    group_id: int

class StudentCreate(StudentBase):
    pass

class Student(StudentBase):
    id: int
    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    name: str


class SubjectCreate(SubjectBase):
    pass


class Subject(SubjectBase):
    id: int
    teacher_id: int
    class Config:
        from_attributes = True


class LessonBase(BaseModel):
    subject_id: int
    group_id: int
    lesson_date: date
    lesson_topic: Optional[str] = None


class LessonCreate(LessonBase):
    pass


class Lesson(LessonBase):
    id: int
    class Config:
        from_attributes = True


class GradeRecordBase(BaseModel):
    lesson_id: int
    student_id: int
    grade_value: Optional[str] = None
    attendance_status: str = "present"
    comment: Optional[str] = None


# Строгая схема для оценки
class GradeRecordCreate(BaseModel):
    student_id: int
    lesson_id: int
    # Оценка может быть либо числом от 2 до 5, либо строкой "Н" (отсутствие)
    grade_value: Optional[Union[int, str]] = Field(None, description="Оценка 2-5 или 'Н'")
    comment: Optional[str] = None

    @field_validator('grade_value', mode='before')
    def validate_grade(cls, v):
        # Пропускаем если не отправлено, пусто или None
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return None
        
        # Если это число - проверяем диапазон
        if isinstance(v, int):
            if v < 2 or v > 5:
                raise ValueError('Оценка должна быть от 2 до 5')
            return v
        
        # Если это строка
        if isinstance(v, str):
            # Пытаемся конвертировать в число
            try:
                grade_int = int(v.strip())
                if grade_int < 2 or grade_int > 5:
                    raise ValueError('Оценка должна быть от 2 до 5')
                return grade_int
            except ValueError:
                # Если не число, проверяем букву "Н"
                if v.upper() == 'Н':
                    return 'Н'
                raise ValueError('Допустима только буква "Н" для отметки отсутствия или оценка 2-5')
        
        return v


class GradeRecordUpdate(BaseModel):
    grade_value: Optional[Union[int, str]] = None
    attendance_status: Optional[str] = None
    comment: Optional[str] = None

    @field_validator('grade_value', mode='before')
    def validate_grade(cls, v):
        # Пропускаем если не отправлено, пусто или None
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return None
        # Проверяем числовые оценки
        if isinstance(v, int):
            if v < 2 or v > 5:
                raise ValueError('Оценка должна быть от 2 до 5')
            return v
        # Проверяем букву "Н"
        if isinstance(v, str):
            if v.upper() != 'Н':
                raise ValueError('Допустима только буква "Н" для отметки отсутствия')
            return v.upper()
        return v


class GradeRecord(GradeRecordBase):
    id: int
    class Config:
        from_attributes = True


class BulkGradeRecordUpsertItem(BaseModel):
    student_id: int
    grade_value: Optional[str] = None
    attendance_status: str = "present"
    comment: Optional[str] = None


class BulkGradeRecordUpsertRequest(BaseModel):
    lesson_id: int
    rows: List[BulkGradeRecordUpsertItem]


class BulkGradeRecordUpsertResponse(BaseModel):
    lesson_id: int
    saved_count: int
    records: List[GradeRecord]


class MessageResponse(BaseModel):
    detail: str


class AcademicPeriodBase(BaseModel):
    name: str
    academic_year: str
    semester_number: int = Field(ge=1, le=2)
    start_date: date
    end_date: date


class AcademicPeriodCreate(AcademicPeriodBase):
    pass


class AcademicPeriod(AcademicPeriodBase):
    id: int

    class Config:
        from_attributes = True


class AcademicPeriodShort(BaseModel):
    id: int
    name: str
    academic_year: str
    semester_number: int

    class Config:
        from_attributes = True


class TeachingAssignmentBase(BaseModel):
    subject_id: int
    group_id: int
    academic_period_id: int


class TeachingAssignmentCreate(TeachingAssignmentBase):
    pass


class TeachingAssignment(BaseModel):
    id: int
    teacher_id: int
    subject: "SubjectShort"
    group: "GroupShort"
    academic_period: AcademicPeriodShort

    class Config:
        from_attributes = True


class ScheduleTemplateBase(BaseModel):
    teaching_assignment_id: int
    day_of_week: int = Field(ge=1, le=7)
    lesson_number: int = Field(ge=1)
    start_time: time
    end_time: time
    classroom: Optional[str] = None


class ScheduleTemplateCreate(ScheduleTemplateBase):
    pass


class ScheduleTemplate(ScheduleTemplateBase):
    id: int

    class Config:
        from_attributes = True


class LessonGenerationRequest(BaseModel):
    academic_period_id: int
    date_from: date
    date_to: date
    teaching_assignment_id: Optional[int] = None


class GeneratedLessonInfo(BaseModel):
    lesson_id: Optional[int] = None
    lesson_date: date
    subject_name: str
    group_name: str
    teaching_assignment_id: int
    schedule_template_id: int


class LessonGenerationResponse(BaseModel):
    generated_count: int
    skipped_count: int
    lessons: List[GeneratedLessonInfo]


class LessonGenerationPreviewResponse(BaseModel):
    would_generate_count: int
    skipped_count: int
    lessons: List[GeneratedLessonInfo]


class GeneratedLessonDeleteResponse(BaseModel):
    deleted_count: int
    protected_count: int
    lessons: List[GeneratedLessonInfo]


class SubjectShort(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class GroupShort(BaseModel):
    id: int
    group_name: str
    course_year: int

    class Config:
        from_attributes = True


class ScheduleLesson(BaseModel):
    id: int
    lesson_date: date
    topic: Optional[str] = None
    subject: SubjectShort
    group: GroupShort


class JournalStudentRow(BaseModel):
    student_id: int
    student_full_name: str
    grade_record_id: Optional[int] = None
    grade_value: Optional[str] = None
    attendance_status: Optional[str] = None
    comment: Optional[str] = None


class JournalLesson(BaseModel):
    lesson_id: int
    lesson_date: date
    topic: Optional[str] = None
    subject: SubjectShort
    group: GroupShort
    students: List[JournalStudentRow]


class DailyJournal(BaseModel):
    target_date: date
    lessons: List[JournalLesson]
# Схемы для преподавателя
class TeacherBase(BaseModel):
    email: str # По-хорошему здесь используют EmailStr из pydantic[email], но пока оставим str
    full_name: str

class TeacherCreate(TeacherBase):
    password: str # При регистрации мы получаем чистый пароль от пользователя

class Teacher(TeacherBase):
    id: int
    class Config:
        from_attributes = True

# ========== SCHEMAS ДЛЯ АДМИНИСТРАТОРА ==========

class TeacherCreateByAdmin(BaseModel):
    """Создание учителя администратором (без пароля в явном виде)"""
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    role: str = Field(default="teacher", description="teacher или admin")


class TeacherUpdate(BaseModel):
    """Обновление учителя администратором"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherResponse(BaseModel):
    """Информация об учителе для администратора"""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Запись в логе аудита"""
    id: int
    admin_id: Optional[int] = None
    action: str  # create, update, delete, block_teacher, reset_password
    entity_type: str  # teacher, subject, group, lesson, grade_record
    entity_id: Optional[int] = None
    description: Optional[str] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ResetPasswordRequest(BaseModel):
    """Сброс пароля"""
    teacher_id: int
    new_password: str = Field(min_length=8)


class BlockTeacherRequest(BaseModel):
    """Блокировка/разблокировка учителя"""
    teacher_id: int
    is_active: bool


class SchoolStatistics(BaseModel):
    """Статистика по всей школе"""
    total_teachers: int
    total_students: int
    total_groups: int
    total_subjects: int
    active_teachers: int
    total_grades_recorded: int
    average_grade: Optional[float] = None


class GroupPromotionRequest(BaseModel):
    """Запрос на перевод группы на следующий курс"""
    group_ids: List[int] = Field(..., description="ID групп для перевода")


class GroupPromotionResponse(BaseModel):
    """Результат перевода групп"""
    promoted_count: int
    failed_count: int
    details: List[str] = []


# Схема для ответа с токеном
class Token(BaseModel):
    access_token: str
    token_type: str


TeachingAssignment.model_rebuild()
