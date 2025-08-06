__all__ = ("auth_router",)

from fastapi import APIRouter

from .clients import clients_router
from .users import users_router

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

auth_router.include_router(clients_router)
auth_router.include_router(users_router)
