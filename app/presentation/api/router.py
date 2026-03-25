from fastapi import APIRouter

from app.presentation.api.routes import (
    admin,
    analytics,
    analysts,
    auth,
    categories,
    notifications,
    tickets,
    user_tickets,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(user_tickets.router)
api_router.include_router(tickets.router)
api_router.include_router(analysts.router)
api_router.include_router(categories.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
