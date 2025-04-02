from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, BYTEA
from .base import Base, TimestampMixin
import uuid

class File(Base, TimestampMixin):
    """
    Модель загруженного файла.
    Содержит как метаданные, так и само содержимое файла.
    """
    __tablename__ = 'files'
    __table_args__ = {'comment': 'Загруженные файлы'}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment='Уникальный идентификатор'
    )
    name = Column(
        String(255),
        nullable=False,
        comment='Оригинальное имя файла'
    )
    content = Column(
        BYTEA,
        nullable=False,
        comment='Содержимое файла'
    )
    content_type = Column(
        String(100),
        nullable=False,
        comment='MIME-тип файла'
    )
    size = Column(
        Integer,
        nullable=False,
        comment='Размер файла в байтах'
    )
    hash_sha256 = Column(
        String(64),
        nullable=False,
        comment='SHA256 хэш содержимого'
    )
    scan_result = Column(
        JSON,
        nullable=True,
        comment='Результаты сканирования'
    )
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id'),
        nullable=False,
        comment='Владелец файла'
    )

    def __repr__(self):
        return f'<File {self.name}>'
