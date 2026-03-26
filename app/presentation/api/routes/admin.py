from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.application.services.analytics_application_service import AnalyticsApplicationService
from app.application.services.ticket_application_service import TicketApplicationService
from app.core.deps import (
    get_analytics_application_service,
    get_current_admin,
    get_session,
    get_ticket_application_service,
)
from app.bootstrap.credentials import DEFAULT_ANALYST_PASSWORD
from app.core.security import hash_password
from app.domain.entities.admin import Admin
from app.domain.entities.analyst import Analyst
from app.domain.entities.enums import AnalystLevel
from app.infrastructure.repositories.analyst_repository_impl import AnalystRepositoryImpl
from app.presentation.schemas.admin_schemas import (
    AdminAnalystCreate,
    AdminAnalystOut,
    AdminAnalystPatch,
    AdminSetPasswordBody,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/kpis")
def admin_kpis(
    backlog_days: int = Query(30, ge=7, le=365),
    svc: AnalyticsApplicationService = Depends(get_analytics_application_service),
) -> dict:
    """Indicadores de eficiencia operativa (KPIs) para el panel de administración."""
    return svc.efficiency_kpis(backlog_days=backlog_days)


@router.get("/analysts", response_model=list[AdminAnalystOut])
def list_analysts_admin(session: Session = Depends(get_session)) -> list[AdminAnalystOut]:
    rows = AnalystRepositoryImpl(session).list_all(active_only=False)
    return [
        AdminAnalystOut(id=a.id or 0, name=a.name, email=a.email, level=a.level.value, is_active=a.is_active)
        for a in rows
        if a.id is not None
    ]


@router.post("/analysts", response_model=AdminAnalystOut, status_code=status.HTTP_201_CREATED)
def create_analyst(
    body: AdminAnalystCreate,
    _: Admin = Depends(get_current_admin),
    session: Session = Depends(get_session),
) -> AdminAnalystOut:
    repo = AnalystRepositoryImpl(session)
    email_norm = str(body.email).strip().lower()
    if repo.get_by_email(email_norm):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un analista con ese correo")

    pwd = body.password if body.password else DEFAULT_ANALYST_PASSWORD
    analyst = Analyst(
        id=None,
        name=body.name.strip(),
        email=email_norm,
        level=AnalystLevel(body.level.value),
        password_hash=hash_password(pwd),
        is_active=True,
    )
    saved = repo.create(analyst)
    if saved.id is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "No se pudo crear el analista")
    return AdminAnalystOut(
        id=saved.id, name=saved.name, email=saved.email, level=saved.level.value, is_active=saved.is_active
    )


@router.patch("/analysts/{analyst_id}", response_model=AdminAnalystOut)
def patch_analyst(
    analyst_id: int,
    body: AdminAnalystPatch,
    _: Admin = Depends(get_current_admin),
    session: Session = Depends(get_session),
) -> AdminAnalystOut:
    repo = AnalystRepositoryImpl(session)
    cur = repo.get_by_id(analyst_id)
    if not cur:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analista no encontrado")
    name = body.name if body.name is not None else cur.name
    email = str(body.email).strip().lower() if body.email is not None else cur.email
    level = AnalystLevel(body.level.value) if body.level is not None else cur.level
    is_active = body.is_active if body.is_active is not None else cur.is_active
    if email != cur.email:
        other = repo.get_by_email(email)
        if other and other.id != analyst_id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe otro analista con ese correo")
    updated = Analyst(
        id=cur.id,
        name=name,
        email=email,
        level=level,
        password_hash=None,
        is_active=is_active,
    )
    saved = repo.update(updated)
    return AdminAnalystOut(
        id=saved.id or analyst_id,
        name=saved.name,
        email=saved.email,
        level=saved.level.value,
        is_active=saved.is_active,
    )


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_ticket(
    ticket_id: int,
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> None:
    """Eliminación física del caso (solo administración)."""
    if not svc.delete_ticket(ticket_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket no encontrado")


@router.post("/analysts/{analyst_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def set_analyst_password(
    analyst_id: int,
    body: AdminSetPasswordBody,
    _: Admin = Depends(get_current_admin),
    session: Session = Depends(get_session),
) -> None:
    repo = AnalystRepositoryImpl(session)
    if not repo.get_by_id(analyst_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analista no encontrado")
    repo.update_password_hash(analyst_id, hash_password(body.password))
