from enum import Enum


class TicketType(str, Enum):
    INCIDENT = "incident"
    REQUEST = "request"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class AnalystLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
