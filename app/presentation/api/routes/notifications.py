from fastapi import APIRouter, Depends, Query

from app.application.services.sla_notification_application_service import SLANotificationApplicationService
from app.core.deps import get_current_analyst, get_sla_notification_application_service

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Depends(get_current_analyst)],
)


@router.post("/simulate-sla-expiry")
def simulate_sla_expiry(
    svc: SLANotificationApplicationService = Depends(get_sla_notification_application_service),
):
    """
    Genera registros de notificación para tickets activos con SLA vencido (simulación).
    No duplica si ya existe notificación para el mismo ticket.
    """
    created = svc.process_due_notifications()
    return {"generated": len(created), "items": created}


@router.get("/sla")
def list_sla_notifications(
    limit: int = Query(50, ge=1, le=200),
    svc: SLANotificationApplicationService = Depends(get_sla_notification_application_service),
):
    return svc.list_notifications(limit=limit)
