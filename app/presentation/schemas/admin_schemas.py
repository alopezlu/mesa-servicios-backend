from pydantic import BaseModel, EmailStr, Field

from app.presentation.schemas.ticket_schemas import AnalystLevelStr


class AdminAnalystOut(BaseModel):
    id: int
    name: str
    email: str
    level: str
    is_active: bool


class AdminAnalystCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    level: AnalystLevelStr
    password: str | None = Field(None, min_length=6, max_length=128)


class AdminAnalystPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    email: EmailStr | None = None
    level: AnalystLevelStr | None = None
    is_active: bool | None = None


class AdminSetPasswordBody(BaseModel):
    password: str = Field(min_length=6, max_length=128)
