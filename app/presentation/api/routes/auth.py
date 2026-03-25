from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_session, get_token_payload
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.entities.user import User
from app.infrastructure.repositories.admin_repository_impl import AdminRepositoryImpl
from app.infrastructure.repositories.analyst_repository_impl import AnalystRepositoryImpl
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.presentation.schemas.auth_schemas import (
    AdminMeOut,
    AnalystMeOut,
    LoginBody,
    LoginCredentials,
    TokenResponse,
    UserMeOut,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _perform_login(session: Session, email: str, password: str, profile: str) -> TokenResponse:
    profile = (profile or "").strip().lower()
    if profile == "user":
        repo = UserRepositoryImpl(session)
        u = repo.get_by_email(email)
        if not u or not verify_password(password, u.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales incorrectas")
        if not u.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuario inactivo")
        token = create_access_token(subject=str(u.id), role="user")
        return TokenResponse(access_token=token, role="user")

    if profile == "admin":
        repo_adm = AdminRepositoryImpl(session)
        adm = repo_adm.get_by_email(email)
        if not adm or not verify_password(password, adm.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales incorrectas")
        if not adm.is_active or adm.id is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrador inactivo")
        token = create_access_token(subject=str(adm.id), role="admin")
        return TokenResponse(access_token=token, role="admin")

    if profile == "analyst":
        repo_a = AnalystRepositoryImpl(session)
        a = repo_a.get_by_email(email)
        if not a or not a.password_hash or not verify_password(password, a.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales incorrectas")
        if not a.is_active or a.id is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Analista inactivo")
        token = create_access_token(subject=str(a.id), role="analyst")
        return TokenResponse(access_token=token, role="analyst")

    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Perfil no válido")


@router.post("/register", response_model=UserMeOut, status_code=status.HTTP_201_CREATED)
def register_user(body: UserRegister, session: Session = Depends(get_session)) -> UserMeOut:
    repo = UserRepositoryImpl(session)
    if repo.get_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya está registrado")
    user = User(
        id=None,
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        is_active=True,
    )
    saved = repo.create(user)
    if saved.id is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "No se pudo crear el usuario")
    return UserMeOut(id=saved.id, email=saved.email, full_name=saved.full_name, profile="user")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginBody, session: Session = Depends(get_session)) -> TokenResponse:
    """Perfil en el JSON (`user` | `analyst` | `admin`)."""
    return _perform_login(session, str(body.email), body.password, body.profile)


@router.post("/login/{login_profile}", response_model=TokenResponse)
def login_with_profile_in_path(
    login_profile: Literal["user", "analyst", "admin"],
    body: LoginCredentials,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """Opcional: mismo login con el perfil en la URL (útil para Swagger o clientes sin campo `profile`)."""
    return _perform_login(session, str(body.email), body.password, login_profile)


@router.get("/me", response_model=UserMeOut | AnalystMeOut | AdminMeOut)
def me(
    payload: dict = Depends(get_token_payload),
    session: Session = Depends(get_session),
) -> UserMeOut | AnalystMeOut | AdminMeOut:
    role = payload.get("role")
    try:
        sub = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token mal formado") from e

    if role == "user":
        u = UserRepositoryImpl(session).get_by_id(sub)
        if not u or not u.is_active or u.id is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no válido")
        return UserMeOut(id=u.id, email=u.email, full_name=u.full_name, profile="user")

    if role == "analyst":
        a = AnalystRepositoryImpl(session).get_by_id(sub)
        if not a or not a.is_active or a.id is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Analista no válido")
        return AnalystMeOut(
            id=a.id,
            email=a.email,
            name=a.name,
            level=a.level.value,
            profile="analyst",
        )

    if role == "admin":
        adm = AdminRepositoryImpl(session).get_by_id(sub)
        if not adm or not adm.is_active or adm.id is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Administrador no válido")
        return AdminMeOut(
            id=adm.id,
            email=adm.email,
            full_name=adm.full_name,
            profile="admin",
        )

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Rol no reconocido")
