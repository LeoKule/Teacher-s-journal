"""initial schema

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'teachers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(150), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='teacher'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_teachers_id', 'teachers', ['id'])

    op.create_table(
        'student_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_name', sa.String(50), nullable=False),
        sa.Column('course_year', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_name'),
        sa.CheckConstraint('course_year >= 1 AND course_year <= 6', name='ck_student_group_course_year'),
    )
    op.create_index('ix_student_groups_id', 'student_groups', ['id'])

    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(150), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['group_id'], ['student_groups.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_students_id', 'students', ['id'])
    op.create_index('ix_students_group_id', 'students', ['group_id'])
    op.create_index('ix_students_is_deleted', 'students', ['is_deleted'])

    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_subjects_id', 'subjects', ['id'])
    op.create_index('ix_subjects_teacher_id', 'subjects', ['teacher_id'])

    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('lesson_date', sa.Date(), nullable=False),
        sa.Column('lesson_topic', sa.String(255), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['group_id'], ['student_groups.id']),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lessons_id', 'lessons', ['id'])
    op.create_index('ix_lessons_teacher_id', 'lessons', ['teacher_id'])
    op.create_index('ix_lessons_subject_id', 'lessons', ['subject_id'])
    op.create_index('ix_lessons_group_id', 'lessons', ['group_id'])

    op.create_table(
        'grade_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('grade_value', sa.String(10), nullable=True),
        sa.Column('attendance_status', sa.String(20), nullable=False, server_default='present'),
        sa.Column('comment', sa.String(255), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='0'),
        sa.CheckConstraint(
            "grade_value IS NULL OR grade_value IN ('2', '3', '4', '5', 'Н')",
            name='ck_grade_record_grade_value',
        ),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lesson_id', 'student_id', name='uq_grade_record_lesson_student'),
    )
    op.create_index('ix_grade_records_id', 'grade_records', ['id'])
    op.create_index('ix_grade_records_lesson_id', 'grade_records', ['lesson_id'])
    op.create_index('ix_grade_records_student_id', 'grade_records', ['student_id'])

    op.create_table(
        'academic_periods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('academic_year', sa.String(20), nullable=False),
        sa.Column('semester_number', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.CheckConstraint('semester_number >= 1 AND semester_number <= 2', name='ck_academic_period_semester'),
        sa.CheckConstraint('start_date < end_date', name='ck_academic_period_dates'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('academic_year', 'semester_number', name='uq_academic_period_year_semester'),
    )
    op.create_index('ix_academic_periods_id', 'academic_periods', ['id'])

    op.create_table(
        'teaching_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('academic_period_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['academic_period_id'], ['academic_periods.id']),
        sa.ForeignKeyConstraint(['group_id'], ['student_groups.id']),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'teacher_id', 'subject_id', 'group_id', 'academic_period_id',
            name='uq_teaching_assignment_scope',
        ),
    )
    op.create_index('ix_teaching_assignments_id', 'teaching_assignments', ['id'])

    op.create_table(
        'schedule_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teaching_assignment_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('lesson_number', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('classroom', sa.String(50), nullable=True),
        sa.CheckConstraint('day_of_week >= 1 AND day_of_week <= 7', name='ck_schedule_template_day_of_week'),
        sa.CheckConstraint('lesson_number >= 1 AND lesson_number <= 8', name='ck_schedule_template_lesson_number'),
        sa.CheckConstraint('start_time < end_time', name='ck_schedule_template_times'),
        sa.ForeignKeyConstraint(['teaching_assignment_id'], ['teaching_assignments.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'teaching_assignment_id', 'day_of_week', 'lesson_number',
            name='uq_schedule_template_slot',
        ),
    )
    op.create_index('ix_schedule_templates_id', 'schedule_templates', ['id'])

    op.create_table(
        'schedule_occurrences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_template_id', sa.Integer(), nullable=False),
        sa.Column('lesson_date', sa.Date(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id']),
        sa.ForeignKeyConstraint(['schedule_template_id'], ['schedule_templates.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('schedule_template_id', 'lesson_date', name='uq_schedule_occurrence_template_date'),
        sa.UniqueConstraint('lesson_id', name='uq_schedule_occurrence_lesson'),
    )
    op.create_index('ix_schedule_occurrences_id', 'schedule_occurrences', ['id'])

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['teachers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_id', 'audit_logs', ['id'])

    op.create_table(
        'token_blacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(500), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )
    op.create_index('ix_token_blacklist_id', 'token_blacklist', ['id'])
    op.create_index('ix_token_blacklist_token', 'token_blacklist', ['token'])


def downgrade() -> None:
    op.drop_table('token_blacklist')
    op.drop_table('audit_logs')
    op.drop_table('schedule_occurrences')
    op.drop_table('schedule_templates')
    op.drop_table('teaching_assignments')
    op.drop_table('academic_periods')
    op.drop_table('grade_records')
    op.drop_table('lessons')
    op.drop_table('subjects')
    op.drop_table('students')
    op.drop_table('student_groups')
    op.drop_table('teachers')
