from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from .base import Base, TimestampMixin, SoftDeleteMixin
import uuid

class Signature(Base, TimestampMixin, SoftDeleteMixin):
    """
    Модель антивирусной сигнатуры.
    Содержит все данные для обнаружения угроз в файлах.
    """
    __tablename__ = 'signatures'
    __table_args__ = {'comment': 'Антивирусные сигнатуры'}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment='Уникальный идентификатор'
    )
    threat_name = Column(
        String(255),
        nullable=False,
        comment='Название угрозы'
    )
    first_bytes = Column(
        BYTEA,
        nullable=False,
        comment='Первые 8 байт сигнатуры'
    )
    remainder_hash = Column(
        String(64),
        nullable=False,
        comment='Хэш оставшейся части сигнатуры'
    )
    remainder_length = Column(
        Integer,
        nullable=False,
        comment='Длина оставшейся части сигнатуры'
    )
    file_type = Column(
        String(50),
        nullable=False,
        comment='Тип файла для сигнатуры'
    )
    offset_start = Column(
        Integer,
        nullable=True,
        comment='Смещение начала сигнатуры в файле'
    )
    offset_end = Column(
        Integer,
        nullable=True,
        comment='Смещение конца сигнатуры в файле'
    )
    digital_signature = Column(
        BYTEA,
        nullable=False,
        comment='Электронная подпись сигнатуры'
    )
    status = Column(
        String(20),
        default='ACTUAL',
        nullable=False,
        comment='Статус сигнатуры (ACTUAL/DELETED/CORRUPTED)'
    )
    creator_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        comment='Создатель сигнатуры'
    )

    def __repr__(self):
        return f'<Signature {self.threat_name}>'

class SignatureHistory(Base):
    """
    Модель истории изменений сигнатур.
    Сохраняет все предыдущие версии сигнатур.
    """
    __tablename__ = 'signatures_history'
    __table_args__ = {'comment': 'История изменений сигнатур'}

    history_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    # Все поля из Signature, кроме id
    signature_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment='ID оригинальной сигнатуры'
    )
    version_created_at = Column(
        DateTime,
        nullable=False,
        comment='Дата создания версии'
    )
    # Остальные поля аналогичны Signature
