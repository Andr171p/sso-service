__all__ = ("auth_router",)

from fastapi import APIRouter

from .realms import realms_router

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

auth_router.include_router(realms_router)
