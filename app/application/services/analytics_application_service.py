from datetime import date, timedelta

from app.domain.repositories.satisfaction_repository import ISatisfactionRepository
from app.domain.repositories.ticket_repository import ITicketRepository


def _seconds_to_hours(sec: float | None) -> float | None:
    if sec is None:
        return None
    return round(sec / 3600.0, 2)


class AnalyticsApplicationService:
    def __init__(
        self,
        tickets: ITicketRepository,
        satisfaction: ISatisfactionRepository,
    ) -> None:
        self._tickets = tickets
        self._satisfaction = satisfaction

    def resolved_ranking(self) -> list[dict]:
        rows = self._tickets.resolved_by_analyst()
        return [{"analyst": name, "resolved": count} for name, count in rows]

    def reopen_rate(self) -> dict:
        reopened, total_resolved = self._tickets.reopened_stats()
        rate = (reopened / total_resolved) if total_resolved else 0.0
        return {
            "reopened_tickets": reopened,
            "resolved_or_closed_total": total_resolved,
            "reopen_rate": round(rate, 4),
            "reopen_rate_percent": round(rate * 100, 2),
        }

    def open_vs_closed(self) -> dict:
        open_cnt, closed_cnt = self._tickets.open_vs_closed_counts()
        return {"open": open_cnt, "closed": closed_cnt}

    def backlog_history(self, days: int = 30) -> list[dict]:
        today = date.today()
        out: list[dict] = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            out.append(
                {
                    "date": d.isoformat(),
                    "backlog": self._tickets.count_open_on_date(d),
                    "created": self._tickets.count_created_on_date(d),
                    "closed": self._tickets.count_closed_on_date(d),
                }
            )
        return out

    def efficiency_kpis(self, *, backlog_days: int = 30) -> dict:
        """Paquete de KPIs para panel de administración (eficiencia operativa)."""
        reopen = self.reopen_rate()
        ov = self.open_vs_closed()
        ranking = self.resolved_ranking()
        backlog_hist = self.backlog_history(days=backlog_days)
        by_status = [
            {"status": s, "count": n, "label_es": _status_label_es(s)}
            for s, n in self._tickets.counts_by_status()
        ]
        satisfaction = self._satisfaction.aggregate_stats()
        open_by_analyst = [
            {"analyst": name, "open": count} for name, count in self._tickets.open_tickets_by_analyst()
        ]
        return {
            "resolved_ranking": ranking,
            "reopen_rate": reopen,
            "open_vs_closed": ov,
            "backlog_history": backlog_hist,
            "open_tickets_by_analyst": open_by_analyst,
            "current_backlog_open": self._tickets.count_open_not_closed(),
            "avg_resolution_hours": self._tickets.avg_resolution_hours(),
            "avg_hours_detection_to_first_response": _seconds_to_hours(
                self._tickets.avg_seconds_metric_detection_to_first_response()
            ),
            "avg_hours_first_response_to_resolution_metric": _seconds_to_hours(
                self._tickets.avg_seconds_metric_first_response_to_resolution()
            ),
            "tickets_by_current_status": by_status,
            "satisfaction": satisfaction,
        }


def _status_label_es(status: str) -> str:
    return {
        "open": "Abierto",
        "in_progress": "En curso",
        "resolved": "Resuelto",
        "closed": "Cerrado",
        "reopened": "Reabierto",
    }.get(status, status)
