from pydantic import BaseModel

class BaseSchema(BaseModel):
    """
    ������� ����� ��� ���� Pydantic �������.
    ��������� ����� ��������� � ������.
    """
    class Config:
        anystr_strip_whitespace = True
        json_encoders = {
            bytes: lambda v: v.decode("utf-8", errors="replace") if v else None
        }

    def dict(self, **kwargs):
        """��������������� ������ dict ��� ���������� ��������� bytes"""
        kwargs.setdefault("exclude_unset", True)
        return super().dict(**kwargs)
