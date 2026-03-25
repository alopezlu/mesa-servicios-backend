from dataclasses import dataclass


@dataclass(slots=True)
class ServiceCategory:
    id: int | None
    name: str
    description: str | None
