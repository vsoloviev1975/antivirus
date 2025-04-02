"""Initial tables

Revision ID: 0001
Revises: 
Create Date: 2023-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Идентификаторы ревизии
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Создание таблицы пользователей
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )

    # Создание таблицы сигнатур
    op.create_table('signatures',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('threat_name', sa.String(length=255), nullable=False),
        sa.Column('first_bytes', sa.LargeBinary(length=8), nullable=False),
        sa.Column('remainder_hash', sa.String(length=64), nullable=False),
        sa.Column('remainder_length', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('offset_start', sa.Integer(), nullable=True),
        sa.Column('offset_end', sa.Integer(), nullable=True),
        sa.Column('digital_signature', sa.LargeBinary(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='ACTUAL', nullable=False),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание таблицы файлов
    op.create_table('files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('hash_sha256', sa.String(length=64), nullable=False),
        sa.Column('scan_result', postgresql.JSONB(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Создание таблицы истории сигнатур
    op.create_table('signatures_history',
        sa.Column('history_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('signature_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        # Все остальные поля как в signatures
        sa.PrimaryKeyConstraint('history_id')
    )

def downgrade():
    # Откат миграции - удаление всех таблиц в обратном порядке
    op.drop_table('signatures_history')
    op.drop_table('files')
    op.drop_table('signatures')
    op.drop_table('users')
