from sqlalchemy import Column, Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


#   Модель Преподавателя
class Teacher(Base):
    __tablename__ = "teachers"  # Точное имя таблицы в MySQL

    # Описываем колонки, шаг за шагом проецируя типы данных SQL в типы SQLAlchemy
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    lessons = relationship("Lesson", back_populates="teacher")
    subjects = relationship("Subject", back_populates="teacher")
    teaching_assignments = relationship("TeachingAssignment", back_populates="teacher")


#   Модель Учебной группы
class StudentGroup(Base):
    __tablename__ = "student_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(50), unique=True, nullable=False)
    course_year = Column(Integer, nullable=False)

    # Устанавливаем двунаправленную связь на уровне Python.
    # Это позволит нам обращаться к студентам группы как к списку: group.students
    students = relationship("Student", back_populates="group")
    lessons = relationship("Lesson", back_populates="group")
    teaching_assignments = relationship("TeachingAssignment", back_populates="group")


#   Модель Студента
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)

    # Внешний ключ: ссылается на id из таблицы student_groups
    group_id = Column(Integer, ForeignKey("student_groups.id"), nullable=False)

    # Обратная связь для SQLAlchemy: позволяет у объекта студента
    # сразу получить объект его группы (student.group.group_name)
    group = relationship("StudentGroup", back_populates="students")
    grade_records = relationship("GradeRecord", back_populates="student")

#   Предмет, который будет в занятии
class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

    teacher = relationship("Teacher", back_populates="subjects")
    lessons = relationship("Lesson", back_populates="subject")
    teaching_assignments = relationship("TeachingAssignment", back_populates="subject")

#   Занятия
class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("student_groups.id"), nullable=False)
    lesson_date = Column(Date, nullable=False)
    lesson_topic = Column(String(255), nullable=True)

    subject = relationship("Subject", back_populates="lessons")
    teacher = relationship("Teacher", back_populates="lessons")
    group = relationship("StudentGroup", back_populates="lessons")
    grade_records = relationship("GradeRecord", back_populates="lesson")
    schedule_occurrences = relationship("ScheduleOccurrence", back_populates="lesson")

#   Оценки
class GradeRecord(Base):
    __tablename__ = "grade_records"
    __table_args__ = (
        UniqueConstraint("lesson_id", "student_id", name="uq_grade_record_lesson_student"),
    )

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    grade_value = Column(String(10), nullable=True)
    attendance_status = Column(String(20), nullable=False, default="present")
    comment = Column(String(255), nullable=True)

    lesson = relationship("Lesson", back_populates="grade_records")
    student = relationship("Student", back_populates="grade_records")


class AcademicPeriod(Base):
    __tablename__ = "academic_periods"
    __table_args__ = (
        UniqueConstraint("academic_year", "semester_number", name="uq_academic_period_year_semester"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    academic_year = Column(String(20), nullable=False)
    semester_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    teaching_assignments = relationship("TeachingAssignment", back_populates="academic_period")


class TeachingAssignment(Base):
    __tablename__ = "teaching_assignments"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "subject_id",
            "group_id",
            "academic_period_id",
            name="uq_teaching_assignment_scope",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("student_groups.id"), nullable=False)
    academic_period_id = Column(Integer, ForeignKey("academic_periods.id"), nullable=False)

    teacher = relationship("Teacher", back_populates="teaching_assignments")
    subject = relationship("Subject", back_populates="teaching_assignments")
    group = relationship("StudentGroup", back_populates="teaching_assignments")
    academic_period = relationship("AcademicPeriod", back_populates="teaching_assignments")
    schedule_templates = relationship("ScheduleTemplate", back_populates="teaching_assignment")


class ScheduleTemplate(Base):
    __tablename__ = "schedule_templates"
    __table_args__ = (
        UniqueConstraint(
            "teaching_assignment_id",
            "day_of_week",
            "lesson_number",
            name="uq_schedule_template_slot",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    teaching_assignment_id = Column(Integer, ForeignKey("teaching_assignments.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    classroom = Column(String(50), nullable=True)

    teaching_assignment = relationship("TeachingAssignment", back_populates="schedule_templates")
    schedule_occurrences = relationship("ScheduleOccurrence", back_populates="schedule_template")


class ScheduleOccurrence(Base):
    __tablename__ = "schedule_occurrences"
    __table_args__ = (
        UniqueConstraint(
            "schedule_template_id",
            "lesson_date",
            name="uq_schedule_occurrence_template_date",
        ),
        UniqueConstraint("lesson_id", name="uq_schedule_occurrence_lesson"),
    )

    id = Column(Integer, primary_key=True, index=True)
    schedule_template_id = Column(Integer, ForeignKey("schedule_templates.id"), nullable=False)
    lesson_date = Column(Date, nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)

    schedule_template = relationship("ScheduleTemplate", back_populates="schedule_occurrences")
    lesson = relationship("Lesson", back_populates="schedule_occurrences")
