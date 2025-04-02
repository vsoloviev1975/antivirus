from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base
import uuid
from datetime import datetime

class OperationType:
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    CORRUPT = 'CORRUPT'

class AuditLog(Base):
    """
    Модель аудит-лога для отслеживания всех изменений в системе.
    """
    __tablename__ = 'audit_logs'
    __table_args__ = {'comment': 'Лог изменений системы'}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment='Уникальный идентификатор'
    )
    entity_type = Column(
        String(50),
        nullable=False,
        comment='Тип изменяемой сущности'
    )
    entity_id = Column(
        String(36),
        nullable=False,
        comment='ID изменяемой сущности'
    )
    operation_type = Column(
        String(20),
        nullable=False,
        comment='Тип операции (CREATE/UPDATE/DELETE)'
    )
    operation_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment='Время операции'
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=True,
        comment='Пользователь, совершивший операцию'
    )
    old_values = Column(
        JSONB,
        nullable=True,
        comment='Значения до изменения'
    )
    new_values = Column(
        JSONB,
        nullable=True,
        comment='Значения после изменения'
    )
    ip_address = Column(
        String(45),
        nullable=True,
        comment='IP адрес инициатора'
    )
    user_agent = Column(
        Text,
        nullable=True,
        comment='User-Agent инициатора'
    )

    def __repr__(self):
        return f'<AuditLog {self.entity_type}.{self.entity_id} {self.operation_type}>'
