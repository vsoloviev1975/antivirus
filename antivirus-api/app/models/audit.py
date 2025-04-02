from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import Base
import uuid
from datetime import datetime

class SystemEvent(Base):
    """
    Модель системных событий для мониторинга и отладки.
    """
    __tablename__ = 'system_events'
    __table_args__ = {'comment': 'Системные события и ошибки'}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    event_type = Column(
        String(50),
        nullable=False,
        comment='Тип события'
    )
    severity = Column(
        String(20),
        nullable=False,
        comment='Уровень важности'
    )
    message = Column(
        Text,
        nullable=False,
        comment='Текст сообщения'
    )
    details = Column(
        JSONB,
        nullable=True,
        comment='Детали события'
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    stack_trace = Column(
        Text,
        nullable=True,
        comment='Трассировка стека для ошибок'
    )

    def __repr__(self):
        return f'<SystemEvent {self.event_type} {self.severity}>'
