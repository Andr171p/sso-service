__all__ = ("router",)

from fastapi import APIRouter

from .admin import admin_router
from .auth import auth_router
from .oauth import oauth_router
from .registration import registration_router

router = APIRouter(prefix="/api/v1")

router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(oauth_router)
router.include_router(registration_router)
