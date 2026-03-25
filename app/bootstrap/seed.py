from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.bootstrap.credentials import DEMO_USER_EMAIL
from app.domain.services.sla_service import compute_sla_due_at
from app.infrastructure.database.models import (
    AnalystModel,
    SLAPolicyModel,
    ServiceCategoryModel,
    TicketModel,
    UserModel,
)


def seed_if_empty(session: Session) -> None:
    n = session.scalar(select(func.count()).select_from(SLAPolicyModel))
    if n and n > 0:
        return

    policies = [
        SLAPolicyModel(priority="P1", resolution_hours=2),
        SLAPolicyModel(priority="P2", resolution_hours=8),
        SLAPolicyModel(priority="P3", resolution_hours=24),
        SLAPolicyModel(priority="P4", resolution_hours=48),
    ]
    session.add_all(policies)

    analysts = [
        AnalystModel(name="Ana López", email="ana.l1@example.com", level="L1"),
        AnalystModel(name="Bruno Ruiz", email="bruno.l2@example.com", level="L2"),
        AnalystModel(name="Carla Méndez", email="carla.l3@example.com", level="L3"),
    ]
    session.add_all(analysts)
    session.flush()

    cats = [
        ServiceCategoryModel(name="Red y conectividad", description="VPN, Wi‑Fi, accesos"),
        ServiceCategoryModel(name="Aplicaciones", description="ERP, correo, SSO"),
        ServiceCategoryModel(name="Hardware", description="Equipos y periféricos"),
    ]
    session.add_all(cats)
    session.flush()

    demo_user = session.scalars(select(UserModel).where(UserModel.email == DEMO_USER_EMAIL)).first()
    demo_uid = demo_user.id if demo_user else None

    policy_map = {"P1": 2, "P2": 8, "P3": 24, "P4": 48}
    now = datetime.now(timezone.utc)

    def add_ticket(
        *,
        title: str,
        description: str,
        ticket_type: str,
        status: str,
        priority: str,
        analyst_level: str,
        analyst_id: int | None,
        category_id: int,
        created_at: datetime,
        resolved_at: datetime | None = None,
        closed_at: datetime | None = None,
        reopened: int = 0,
    ) -> None:
        from app.domain.entities.enums import Priority as P

        due = compute_sla_due_at(created_at, P(priority), {P(k): v for k, v in policy_map.items()})
        session.add(
            TicketModel(
                title=title,
                description=description,
                ticket_type=ticket_type,
                status=status,
                priority=priority,
                analyst_level=analyst_level,
                analyst_id=analyst_id,
                category_id=category_id,
                created_by_user_id=demo_uid,
                sla_due_at=due,
                reopened_count=reopened,
                created_at=created_at,
                resolved_at=resolved_at,
                closed_at=closed_at,
            )
        )

    a1, a2, a3 = analysts[0].id, analysts[1].id, analysts[2].id
    c1, c2, c3 = cats[0].id, cats[1].id, cats[2].id

    add_ticket(
        title="Caída de VPN corporativa",
        description="Usuarios remotos no pueden conectar",
        ticket_type="incident",
        status="closed",
        priority="P1",
        analyst_level="L3",
        analyst_id=a3,
        category_id=c1,
        created_at=now - timedelta(days=40),
        resolved_at=now - timedelta(days=39, hours=1),
        closed_at=now - timedelta(days=38),
    )
    add_ticket(
        title="Solicitud de acceso a carpeta compartida",
        description="Nuevo ingreso en Finanzas",
        ticket_type="request",
        status="closed",
        priority="P3",
        analyst_level="L1",
        analyst_id=a1,
        category_id=c2,
        created_at=now - timedelta(days=25),
        resolved_at=now - timedelta(days=23),
        closed_at=now - timedelta(days=22),
        reopened=1,
    )
    add_ticket(
        title="Reemplazo de monitor",
        description="Pixel quemado en puesto 12",
        ticket_type="request",
        status="resolved",
        priority="P4",
        analyst_level="L1",
        analyst_id=a1,
        category_id=c3,
        created_at=now - timedelta(days=8),
        resolved_at=now - timedelta(days=6),
    )
    add_ticket(
        title="Lentitud en ERP",
        description="Timeouts intermitentes mañana",
        ticket_type="incident",
        status="in_progress",
        priority="P2",
        analyst_level="L2",
        analyst_id=a2,
        category_id=c2,
        created_at=now - timedelta(days=3),
    )
    add_ticket(
        title="Incidente para probar SLA vencido",
        description="Ticket antiguo aún abierto",
        ticket_type="incident",
        status="open",
        priority="P4",
        analyst_level="L1",
        analyst_id=a1,
        category_id=c1,
        created_at=now - timedelta(hours=100),
    )
    add_ticket(
        title="Alta de usuario en SSO",
        ticket_type="request",
        description="Onboarding semanal",
        status="open",
        priority="P3",
        analyst_level="L1",
        analyst_id=a1,
        category_id=c2,
        created_at=now - timedelta(hours=5),
    )
