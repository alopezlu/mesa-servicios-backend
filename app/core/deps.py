from typing import Literal, NamedTuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.services.analytics_application_service import AnalyticsApplicationService
from app.application.services.sla_notification_application_service import SLANotificationApplicationService
from app.application.services.ticket_application_service import TicketApplicationService
from app.core.security import safe_decode_token
from app.domain.entities.admin import Admin
from app.domain.entities.analyst import Analyst
from app.domain.entities.user import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.admin_repository_impl import AdminRepositoryImpl
from app.infrastructure.repositories.analyst_repository_impl import AnalystRepositoryImpl
from app.infrastructure.repositories.category_repository_impl import CategoryRepositoryImpl
from app.infrastructure.repositories.notification_repository_impl import NotificationRepositoryImpl
from app.infrastructure.repositories.satisfaction_repository_impl import SatisfactionRepositoryImpl
from app.infrastructure.repositories.sla_policy_repository_impl import SLAPolicyRepositoryImpl
from app.infrastructure.repositories.ticket_repository_impl import TicketRepositoryImpl
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl


class AuthPrincipal(NamedTuple):
    kind: Literal["user", "analyst"]
    user: User | None
    analyst: Analyst | None


security = HTTPBearer()


def get_session(db: Session = Depends(get_db)) -> Session:
    return db


def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = safe_decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido o expirado")
    return payload


def get_current_principal(
    session: Session = Depends(get_session),
    payload: dict = Depends(get_token_payload),
) -> AuthPrincipal:
    role = payload.get("role")
    try:
        sub = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token mal formado") from e
    if role == "user":
        u = UserRepositoryImpl(session).get_by_id(sub)
        if not u or not u.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no válido")
        return AuthPrincipal("user", u, None)
    if role == "analyst":
        a = AnalystRepositoryImpl(session).get_by_id(sub)
        if not a or not a.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Analista no válido o inactivo")
        return AuthPrincipal("analyst", None, a)
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Rol no reconocido")


def get_current_end_user(principal: AuthPrincipal = Depends(get_current_principal)) -> User:
    if principal.kind != "user" or principal.user is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere perfil de usuario final")
    if principal.user.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión inválida")
    return principal.user


def get_current_analyst(principal: AuthPrincipal = Depends(get_current_principal)) -> Analyst:
    if principal.kind != "analyst" or principal.analyst is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere perfil de analista")
    if principal.analyst.id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sesión inválida")
    if not principal.analyst.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Analista inactivo")
    return principal.analyst


def get_current_admin(
    session: Session = Depends(get_session),
    payload: dict = Depends(get_token_payload),
) -> Admin:
    if payload.get("role") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere perfil de administrador")
    try:
        sub = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token mal formado") from e
    adm = AdminRepositoryImpl(session).get_by_id(sub)
    if not adm or not adm.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Administrador no válido o inactivo")
    return adm


def get_ticket_application_service(session: Session = Depends(get_session)) -> TicketApplicationService:
    return TicketApplicationService(
        TicketRepositoryImpl(session),
        AnalystRepositoryImpl(session),
        CategoryRepositoryImpl(session),
        SLAPolicyRepositoryImpl(session),
        UserRepositoryImpl(session),
        SatisfactionRepositoryImpl(session),
    )


def get_analytics_application_service(session: Session = Depends(get_session)) -> AnalyticsApplicationService:
    return AnalyticsApplicationService(
        TicketRepositoryImpl(session),
        SatisfactionRepositoryImpl(session),
    )


def get_sla_notification_application_service(
    session: Session = Depends(get_session),
) -> SLANotificationApplicationService:
    return SLANotificationApplicationService(
        TicketRepositoryImpl(session),
        NotificationRepositoryImpl(session),
    )
