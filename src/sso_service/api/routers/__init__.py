__all__ = ("router",)

from fastapi import APIRouter

from .admin import admin_router
from .clients import clients_router

router = APIRouter(prefix="/api/v1")

router.include_router(admin_router)
router.include_router(clients_router)
