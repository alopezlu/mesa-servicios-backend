from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "mysql+pymysql://root:12345678@localhost:3306/mesaservicios"
    api_prefix: str = "/api"

    @field_validator("api_prefix", mode="before")
    @classmethod
    def _normalize_api_prefix(cls, v: object) -> str:
        """Si .env deja API_PREFIX vacío, el front llama /api/... y FastAPI monta en '' → 404."""
        if v is None:
            return "/api"
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return "/api"
            return s if s.startswith("/") else f"/{s}"
        return "/api"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    secret_key: str = "cambiar-en-produccion-usa-SECRET_KEY-larga-y-aleatoria"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24


settings = Settings()
