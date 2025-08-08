__all__ = ("admin_router",)

from fastapi import APIRouter

from .clients import clients_router
from .groups import groups_router
from .realms import realms_router

admin_router = APIRouter(prefix="/admin", tags=["Admin"])

admin_router.include_router(realms_router)
admin_router.include_router(clients_router)
admin_router.include_router(groups_router)
