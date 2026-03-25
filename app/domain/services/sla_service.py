from datetime import datetime, timedelta, timezone
from typing import Mapping

from app.domain.entities.enums import Priority


DEFAULT_SLA_HOURS: Mapping[Priority, int] = {
    Priority.P1: 2,
    Priority.P2: 8,
    Priority.P3: 24,
    Priority.P4: 48,
}


def resolution_hours_for_priority(
    priority: Priority,
    policy_hours: dict[Priority, int] | None = None,
) -> int:
    if policy_hours and priority in policy_hours:
        return policy_hours[priority]
    return DEFAULT_SLA_HOURS[priority]


def compute_sla_due_at(
    start: datetime,
    priority: Priority,
    policy_hours: dict[Priority, int] | None = None,
) -> datetime:
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    hours = resolution_hours_for_priority(priority, policy_hours)
    return start + timedelta(hours=hours)


def sla_state(
    *,
    now: datetime,
    sla_due_at: datetime | None,
    is_terminal: bool,
) -> str:
    """
    Retorna 'n/a' si no aplica, 'on_time' si aún hay margen o ya cerró a tiempo,
    'overdue' si pasó el vencimiento y el ticket no está en estado terminal.
    """
    if sla_due_at is None:
        return "n/a"
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if sla_due_at.tzinfo is None:
        sla_due_at = sla_due_at.replace(tzinfo=timezone.utc)
    if is_terminal:
        return "on_time" if now <= sla_due_at else "resolved_late"
    return "overdue" if now > sla_due_at else "on_time"


def is_breached(now: datetime, sla_due_at: datetime | None, is_terminal: bool) -> bool:
    if sla_due_at is None or is_terminal:
        return False
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if sla_due_at.tzinfo is None:
        sla_due_at = sla_due_at.replace(tzinfo=timezone.utc)
    return now > sla_due_at
