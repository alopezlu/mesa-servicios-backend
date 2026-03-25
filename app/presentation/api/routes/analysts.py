from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_analyst, get_session
from app.infrastructure.repositories.analyst_repository_impl import AnalystRepositoryImpl
from app.presentation.schemas.common_schemas import AnalystOut

router = APIRouter(
    prefix="/analysts",
    tags=["analysts"],
    dependencies=[Depends(get_current_analyst)],
)


@router.get("", response_model=list[AnalystOut])
def list_analysts(session: Session = Depends(get_session)) -> list[AnalystOut]:
    rows = AnalystRepositoryImpl(session).list_all(active_only=True)
    return [
        AnalystOut(id=a.id, name=a.name, email=a.email, level=a.level.value, is_active=a.is_active)
        for a in rows
        if a.id is not None
    ]
