from pydantic import BaseModel


class AnalystOut(BaseModel):
    id: int
    name: str
    email: str
    level: str
    is_active: bool = True


class CategoryOut(BaseModel):
    id: int
    name: str
    description: str | None
