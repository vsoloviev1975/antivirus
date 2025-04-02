from pydantic import BaseModel

class BaseSchema(BaseModel):
    """
    Базовая схема для всех Pydantic моделей.
    Добавляет общие настройки и методы.
    """
    class Config:
        anystr_strip_whitespace = True
        json_encoders = {
            bytes: lambda v: v.decode("utf-8", errors="replace") if v else None
        }

    def dict(self, **kwargs):
        """Переопределение метода dict для корректной обработки bytes"""
        kwargs.setdefault("exclude_unset", True)
        return super().dict(**kwargs)
