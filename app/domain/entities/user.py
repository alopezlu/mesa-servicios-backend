from dataclasses import dataclass


@dataclass(slots=True)
class User:
    id: int | None
    email: str
    full_name: str
    password_hash: str
    is_active: bool
