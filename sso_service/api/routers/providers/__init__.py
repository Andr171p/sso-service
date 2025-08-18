__all__ = ("provider_router",)

from fastapi import APIRouter

from .vk import vk_router
from .yandex import yandex_router

provider_router = APIRouter()

provider_router.include_router(vk_router)
provider_router.include_router(yandex_router)
