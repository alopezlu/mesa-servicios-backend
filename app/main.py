import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap.credentials import ensure_analyst_passwords, ensure_demo_admin, ensure_demo_user
from app.bootstrap.schema_patch import apply_schema_patches
from app.bootstrap.seed import seed_if_empty
from app.core.config import settings
from app.application.services.ticket_application_service import TicketApplicationService
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import SessionLocal, engine
from app.infrastructure.repositories.analyst_repository_impl import AnalystRepositoryImpl
from app.infrastructure.repositories.category_repository_impl import CategoryRepositoryImpl
from app.infrastructure.repositories.satisfaction_repository_impl import SatisfactionRepositoryImpl
from app.infrastructure.repositories.sla_policy_repository_impl import SLAPolicyRepositoryImpl
from app.infrastructure.repositories.ticket_repository_impl import TicketRepositoryImpl
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from app.presentation.api.router import api_router


def _auto_close_stale_resolved_sync() -> None:
    with SessionLocal() as session:
        try:
            svc = TicketApplicationService(
                TicketRepositoryImpl(session),
                AnalystRepositoryImpl(session),
                CategoryRepositoryImpl(session),
                SLAPolicyRepositoryImpl(session),
                UserRepositoryImpl(session),
                SatisfactionRepositoryImpl(session),
            )
            n = svc.auto_close_stale_resolved()
            session.commit()
            if n:
                print(f"[mesa-servicios] Cierre automatico: {n} ticket(s) resueltos -> cerrado", flush=True)
        except Exception as exc:  # noqa: BLE001
            session.rollback()
            print(f"[mesa-servicios] auto_close (sync): {exc}", flush=True)


async def _auto_close_loop() -> None:
    await asyncio.sleep(15)
    while True:
        await asyncio.to_thread(_auto_close_stale_resolved_sync)
        await asyncio.sleep(60)


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
    _auto_close_stale_resolved_sync()
    print(
        "[mesa-servicios] API lista. Login: POST /api/auth/login body {email,password,profile}",
        flush=True,
    )
    task = asyncio.create_task(_auto_close_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


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
