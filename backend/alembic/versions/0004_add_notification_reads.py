"""add notification_reads table

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notification_reads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), sa.ForeignKey('notifications.id'), nullable=False),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('teachers.id'), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notification_id', 'teacher_id', name='uq_notification_read'),
    )
    op.create_index('ix_notification_reads_id', 'notification_reads', ['id'])
    op.create_index('ix_notification_reads_notification_id', 'notification_reads', ['notification_id'])
    op.create_index('ix_notification_reads_teacher_id', 'notification_reads', ['teacher_id'])


def downgrade() -> None:
    op.drop_index('ix_notification_reads_teacher_id', table_name='notification_reads')
    op.drop_index('ix_notification_reads_notification_id', table_name='notification_reads')
    op.drop_index('ix_notification_reads_id', table_name='notification_reads')
    op.drop_table('notification_reads')
