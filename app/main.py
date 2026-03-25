from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap.credentials import ensure_analyst_passwords, ensure_demo_admin, ensure_demo_user
from app.bootstrap.schema_patch import apply_schema_patches
from app.bootstrap.seed import seed_if_empty
from app.core.config import settings
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import SessionLocal, engine
from app.presentation.api.router import api_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    apply_schema_patches()
    with SessionLocal() as db:
        ensure_demo_user(db)
        ensure_demo_admin(db)
        seed_if_empty(db)
        ensure_analyst_passwords(db)
        db.commit()
    print(
        "[mesa-servicios] API lista. Login: POST /api/auth/login body {email,password,profile}",
        flush=True,
    )
    yield


app = FastAPI(title="Mesa de Servicios API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
