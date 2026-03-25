from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=160)


ALLOWED_LOGIN_PROFILES = frozenset({"user", "analyst", "admin"})


class LoginCredentials(BaseModel):
    """Solo correo y contraseña (el perfil va en la URL: POST /auth/login/admin)."""

    email: EmailStr
    password: str


class LoginBody(BaseModel):
    """POST /auth/login — `profile` debe ser user, analyst o admin."""

    email: EmailStr
    password: str
    profile: str = Field(
        ...,
        description="user (solicitante), analyst (mesa L1–L3), admin (KPIs y gestión de analistas).",
        examples=["user", "analyst", "admin"],
    )

    @field_validator("profile")
    @classmethod
    def profile_ok(cls, v: str) -> str:
        s = (v or "").strip().lower()
        if s not in ALLOWED_LOGIN_PROFILES:
            raise ValueError("profile debe ser uno de: user, analyst, admin")
        return s


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Literal["user", "analyst", "admin"]


class UserMeOut(BaseModel):
    id: int
    email: str
    full_name: str
    profile: Literal["user"]


class AnalystMeOut(BaseModel):
    id: int
    email: str
    name: str
    level: str
    profile: Literal["analyst"]


class AdminMeOut(BaseModel):
    id: int
    email: str
    full_name: str
    profile: Literal["admin"]
