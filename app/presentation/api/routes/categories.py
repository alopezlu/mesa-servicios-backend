from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_session
from app.presentation.schemas.common_schemas import CategoryOut
from app.infrastructure.repositories.category_repository_impl import CategoryRepositoryImpl

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(session: Session = Depends(get_session)) -> list[CategoryOut]:
    rows = CategoryRepositoryImpl(session).list_all()
    return [CategoryOut(id=c.id, name=c.name, description=c.description) for c in rows]
