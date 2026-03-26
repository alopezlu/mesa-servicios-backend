"""ALTER puntuales para bases ya creadas antes de users / created_by / password_hash / cierre ITSM."""

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database.session import engine


def apply_schema_patches() -> None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())

    if "users" not in tables:
        return

    t_cols = {c["name"] for c in insp.get_columns("tickets")}
    a_cols = {c["name"] for c in insp.get_columns("analysts")}

    with engine.begin() as conn:
        if "created_by_user_id" not in t_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN created_by_user_id INT NULL"))
            try:
                conn.execute(
                    text(
                        "ALTER TABLE tickets ADD CONSTRAINT fk_tickets_created_by_user "
                        "FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL"
                    )
                )
            except SQLAlchemyError:
                pass

        if "password_hash" not in a_cols:
            conn.execute(text("ALTER TABLE analysts ADD COLUMN password_hash VARCHAR(255) NULL"))

        if "is_active" not in a_cols:
            conn.execute(text("ALTER TABLE analysts ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1"))

    insp = inspect(engine)
    t_cols = {c["name"] for c in insp.get_columns("tickets")}
    resolution_ddl = [
        ("root_cause_description", "TEXT NULL"),
        ("corrective_actions", "TEXT NULL"),
        ("user_closure_confirmation", "TEXT NULL"),
        ("metric_detected_at", "DATETIME(6) NULL"),
        ("metric_first_response_at", "DATETIME(6) NULL"),
        ("metric_resolution_at", "DATETIME(6) NULL"),
    ]
    with engine.begin() as conn:
        for name, ddl in resolution_ddl:
            if name not in t_cols:
                conn.execute(text(f"ALTER TABLE tickets ADD COLUMN {name} {ddl}"))

    insp = inspect(engine)
    t_cols = {c["name"] for c in insp.get_columns("tickets")}
    extra_ticket_cols = [
        ("handover_notes", "TEXT NULL"),
        ("user_agreement_to_close", "TEXT NULL"),
    ]
    with engine.begin() as conn:
        for name, ddl in extra_ticket_cols:
            if name not in t_cols:
                conn.execute(text(f"ALTER TABLE tickets ADD COLUMN {name} {ddl}"))

    insp = inspect(engine)
    tables = set(insp.get_table_names())
    if "ticket_satisfaction_surveys" not in tables:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE ticket_satisfaction_surveys (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        ticket_id INT NOT NULL,
                        user_id INT NOT NULL,
                        rating INT NOT NULL,
                        comment TEXT NULL,
                        created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                        UNIQUE KEY uq_ticket_satisfaction_ticket (ticket_id),
                        CONSTRAINT fk_sat_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
                        CONSTRAINT fk_sat_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                    """
                )
            )
