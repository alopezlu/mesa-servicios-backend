from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.repositories.satisfaction_repository import ISatisfactionRepository
from app.infrastructure.database.models import TicketSatisfactionModel


class SatisfactionRepositoryImpl(ISatisfactionRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def ticket_ids_with_survey(self, ticket_ids: Iterable[int]) -> set[int]:
        ids = {int(i) for i in ticket_ids}
        if not ids:
            return set()
        stmt = select(TicketSatisfactionModel.ticket_id).where(TicketSatisfactionModel.ticket_id.in_(ids))
        return {int(r[0]) for r in self._session.execute(stmt).all()}

    def create(self, *, ticket_id: int, user_id: int, rating: int, comment: str | None) -> None:
        row = TicketSatisfactionModel(
            ticket_id=ticket_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )
        self._session.add(row)
        self._session.flush()

    def aggregate_stats(self) -> dict:
        total = self._session.scalar(select(func.count()).select_from(TicketSatisfactionModel))
        n = int(total or 0)
        if n == 0:
            return {
                "responses_count": 0,
                "avg_rating": None,
                "by_rating": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            }
        avg = self._session.scalar(select(func.avg(TicketSatisfactionModel.rating)))
        by_star: dict[str, int] = {str(i): 0 for i in range(1, 6)}
        stmt = select(TicketSatisfactionModel.rating, func.count()).group_by(TicketSatisfactionModel.rating)
        for star, cnt in self._session.execute(stmt).all():
            by_star[str(int(star))] = int(cnt)
        return {
            "responses_count": n,
            "avg_rating": round(float(avg), 2) if avg is not None else None,
            "by_rating": by_star,
        }
