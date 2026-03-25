from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.service_category import ServiceCategory
from app.domain.repositories.category_repository import ICategoryRepository
from app.infrastructure.database.models import ServiceCategoryModel


class CategoryRepositoryImpl(ICategoryRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, category_id: int) -> ServiceCategory | None:
        row = self._session.get(ServiceCategoryModel, category_id)
        if not row:
            return None
        return ServiceCategory(id=row.id, name=row.name, description=row.description)

    def list_all(self) -> list[ServiceCategory]:
        rows = self._session.scalars(select(ServiceCategoryModel).order_by(ServiceCategoryModel.name)).all()
        return [ServiceCategory(id=r.id, name=r.name, description=r.description) for r in rows]
