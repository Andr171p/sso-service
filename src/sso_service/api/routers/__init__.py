__all__ = ("router",)

from fastapi import APIRouter

from .admin import admin_router
from .auth import auth_router

router = APIRouter(prefix="/v1")

router.include_router(admin_router)
router.include_router(auth_router)
