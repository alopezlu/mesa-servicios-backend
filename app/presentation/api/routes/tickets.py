from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.application.services.ticket_application_service import TicketApplicationService
from app.core.deps import get_current_analyst, get_session, get_ticket_application_service
from app.domain.entities.analyst import Analyst
from app.domain.entities.enums import AnalystLevel, Priority, TicketStatus, TicketType
from app.presentation.schemas.ticket_schemas import (
    ConvertTypeBody,
    EscalateHandoverBody,
    RecategorizeBody,
    TicketAdjustSLABody,
    TicketCloseBody,
    TicketOut,
    TicketUpdate,
    TransferBody,
)
from app.presentation.ticket_enrichment import one_ticket_to_out, tickets_with_sla_to_out

router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
    dependencies=[Depends(get_current_analyst)],
)


@router.get("", response_model=list[TicketOut])
def list_tickets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    assigned_to_me: bool = Query(
        False,
        description="Si es true, solo tickets asignados al analista autenticado (evita colisión de rutas con /{ticket_id}).",
    ),
    historicos: bool = Query(
        False,
        description="Si es true, solo tickets resueltos o cerrados (no aplica junto con assigned_to_me).",
    ),
    analyst: Analyst = Depends(get_current_analyst),
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> list[TicketOut]:
    if assigned_to_me:
        if analyst.id is None:
            raise HTTPException(401, "Sesión inválida")
        rows = svc.list_tickets_assigned_to_analyst(
            analyst.id, analyst.level, skip=skip, limit=limit
        )
    elif historicos:
        rows = svc.list_tickets_historical(skip=skip, limit=limit)
    else:
        rows = svc.list_tickets(skip=skip, limit=limit)
    return tickets_with_sla_to_out(session, rows)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    row = svc.get_ticket(ticket_id)
    if not row:
        raise HTTPException(404, "Ticket no encontrado")
    t, sla = row
    return one_ticket_to_out(session, t, sla)


@router.patch("/{ticket_id}", response_model=TicketOut)
def patch_ticket(
    ticket_id: int,
    body: TicketUpdate,
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    try:
        t, sla = svc.update_ticket_core(
            ticket_id,
            title=body.title,
            description=body.description,
            status=TicketStatus(body.status.value) if body.status else None,
            priority=Priority(body.priority.value) if body.priority else None,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return one_ticket_to_out(session, t, sla)


@router.post("/{ticket_id}/close", response_model=TicketOut)
def close_ticket(
    ticket_id: int,
    body: TicketCloseBody,
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    try:
        t, sla = svc.close_ticket(
            ticket_id,
            root_cause_description=body.root_cause_description,
            corrective_actions=body.corrective_actions,
            user_closure_confirmation=body.user_closure_confirmation,
            metric_detected_at=body.metric_detected_at,
            metric_first_response_at=body.metric_first_response_at,
            metric_resolution_at=body.metric_resolution_at,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    return one_ticket_to_out(session, t, sla)


@router.post("/{ticket_id}/convert-type", response_model=TicketOut)
def convert_type(
    ticket_id: int,
    body: ConvertTypeBody,
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    try:
        t, sla = svc.convert_ticket_type(ticket_id, TicketType(body.ticket_type.value))
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return one_ticket_to_out(session, t, sla)


@router.post("/{ticket_id}/escalate", response_model=TicketOut)
def escalate(
    ticket_id: int,
    body: EscalateHandoverBody,
    session: Session = Depends(get_session),
    analyst: Analyst = Depends(get_current_analyst),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    if analyst.id is None:
        raise HTTPException(401, "Sesión inválida")
    try:
        t, sla = svc.escalate_with_handover(
            ticket_id,
            actor_analyst_id=analyst.id,
            target_level=AnalystLevel(body.target_level.value),
            assignee_analyst_id=body.assignee_analyst_id,
            handover_notes=body.handover_notes,
            new_status=TicketStatus(body.status.value),
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return one_ticket_to_out(session, t, sla)


@router.post("/{ticket_id}/transfer", response_model=TicketOut)
def transfer(
    ticket_id: int,
    body: TransferBody,
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    try:
        t, sla = svc.transfer_analyst(ticket_id, body.analyst_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return one_ticket_to_out(session, t, sla)


@router.post("/{ticket_id}/recategorize", response_model=TicketOut)
def recategorize(
    ticket_id: int,
    body: RecategorizeBody,
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    try:
        t, sla = svc.recategorize(ticket_id, body.category_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return one_ticket_to_out(session, t, sla)


@router.post("/{ticket_id}/adjust-sla", response_model=TicketOut)
def adjust_sla(
    ticket_id: int,
    body: TicketAdjustSLABody,
    analyst: Analyst = Depends(get_current_analyst),
    session: Session = Depends(get_session),
    svc: TicketApplicationService = Depends(get_ticket_application_service),
) -> TicketOut:
    """El analista asignado redefine la fecha límite del SLA (p. ej. acuerdo de extensión)."""
    if analyst.id is None:
        raise HTTPException(401, "Sesión inválida")
    try:
        t, sla = svc.adjust_sla_due_at_by_assignee(
            ticket_id,
            analyst.id,
            sla_due_at=body.sla_due_at,
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return one_ticket_to_out(session, t, sla)
