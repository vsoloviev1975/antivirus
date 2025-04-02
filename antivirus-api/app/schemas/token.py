from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .base import BaseSchema

class Token(BaseSchema):
    """
    Схема для возврата JWT токена.
    """
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field("bearer", example="bearer")

class TokenPayload(BaseSchema):
    """
    Схема с данными, хранящимися в JWT токене.
    """
    sub: Optional[str] = Field(None, example="550e8400-e29b-41d4-a716-446655440000")
    is_admin: bool = Field(False, example=False)
    exp: Optional[datetime] = Field(None, example="2023-01-01T00:00:00")
