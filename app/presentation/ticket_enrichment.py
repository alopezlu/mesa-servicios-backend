from sqlalchemy.orm import Session

from app.domain.entities.ticket import Ticket
from app.infrastructure.repositories.analyst_repository_impl import AnalystRepositoryImpl
from app.infrastructure.repositories.satisfaction_repository_impl import SatisfactionRepositoryImpl
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.presentation.schemas.ticket_schemas import TicketOut, ticket_to_out


def tickets_with_sla_to_out(session: Session, rows: list[tuple[Ticket, dict]]) -> list[TicketOut]:
    tickets = [t for t, _ in rows]
    uids = {t.created_by_user_id for t in tickets if t.created_by_user_id is not None}
    aids = {t.analyst_id for t in tickets if t.analyst_id is not None}
    tids = {t.id for t in tickets if t.id is not None}
    user_map = UserRepositoryImpl(session).get_full_names_by_ids(uids)
    analyst_map = AnalystRepositoryImpl(session).get_names_by_ids(aids)
    sat_repo = SatisfactionRepositoryImpl(session)
    with_survey = sat_repo.ticket_ids_with_survey(tids)
    return [
        ticket_to_out(
            t,
            s,
            analyst_name=analyst_map.get(t.analyst_id) if t.analyst_id is not None else None,
            created_by_name=user_map.get(t.created_by_user_id)
            if t.created_by_user_id is not None
            else None,
            satisfaction_submitted=(t.id in with_survey) if t.id is not None else False,
        )
        for t, s in rows
    ]


def one_ticket_to_out(session: Session, ticket: Ticket, sla: dict) -> TicketOut:
    return tickets_with_sla_to_out(session, [(ticket, sla)])[0]
