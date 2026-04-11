from datetime import date, time
from typing import List, Optional

from pydantic import BaseModel, Field

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


class GradeRecordCreate(GradeRecordBase):
    pass


class GradeRecordUpdate(BaseModel):
    grade_value: Optional[str] = None
    attendance_status: Optional[str] = None
    comment: Optional[str] = None


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

# Схема для ответа с токеном
class Token(BaseModel):
    access_token: str
    token_type: str


TeachingAssignment.model_rebuild()
