from dataclasses import dataclass

from app.domain.entities.enums import AnalystLevel


@dataclass(slots=True)
class Analyst:
    id: int | None
    name: str
    email: str
    level: AnalystLevel
    password_hash: str | None = None
    is_active: bool = True
