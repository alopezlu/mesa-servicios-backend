from fastapi import APIRouter, Depends, Query

from app.application.services.analytics_application_service import AnalyticsApplicationService
from app.core.deps import get_analytics_application_service, get_current_analyst

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(get_current_analyst)],
)


@router.get("/resolved-ranking")
def resolved_ranking(svc: AnalyticsApplicationService = Depends(get_analytics_application_service)):
    return svc.resolved_ranking()


@router.get("/reopen-rate")
def reopen_rate(svc: AnalyticsApplicationService = Depends(get_analytics_application_service)):
    return svc.reopen_rate()


@router.get("/open-vs-closed")
def open_vs_closed(svc: AnalyticsApplicationService = Depends(get_analytics_application_service)):
    return svc.open_vs_closed()


@router.get("/backlog-history")
def backlog_history(
    days: int = Query(30, ge=7, le=365),
    svc: AnalyticsApplicationService = Depends(get_analytics_application_service),
):
    return svc.backlog_history(days=days)
