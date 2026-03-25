from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.infrastructure.database.models import AdminModel, AnalystModel, UserModel

DEMO_USER_EMAIL = "usuario@example.com"
DEMO_USER_PASSWORD = "Demo123!"
DEFAULT_ANALYST_PASSWORD = "Analista123!"
DEMO_ADMIN_EMAIL = "admin@example.com"
DEMO_ADMIN_PASSWORD = "Admin123!"
DEMO_ADMIN_NAME = "Administrador demo"


def ensure_demo_user(session: Session) -> None:
    if session.scalars(select(UserModel).where(UserModel.email == DEMO_USER_EMAIL)).first():
        return
    session.add(
        UserModel(
            email=DEMO_USER_EMAIL,
            full_name="Usuario demo",
            password_hash=hash_password(DEMO_USER_PASSWORD),
            is_active=True,
        )
    )


def ensure_demo_admin(session: Session) -> None:
    if session.scalars(select(AdminModel).where(AdminModel.email == DEMO_ADMIN_EMAIL)).first():
        return
    session.add(
        AdminModel(
            email=DEMO_ADMIN_EMAIL,
            full_name=DEMO_ADMIN_NAME,
            password_hash=hash_password(DEMO_ADMIN_PASSWORD),
            is_active=True,
        )
    )


def ensure_analyst_passwords(session: Session) -> None:
    analyst_hash = hash_password(DEFAULT_ANALYST_PASSWORD)
    for row in session.scalars(select(AnalystModel)).all():
        if not row.password_hash:
            row.password_hash = analyst_hash


def ensure_auth_defaults(session: Session) -> None:
    """Compat: usuario demo + contraseñas de analistas (usar funciones separadas desde main)."""
    ensure_demo_user(session)
    ensure_analyst_passwords(session)
