import logging
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, status

from sso_service.core.domain import Client
from sso_service.core.exceptions import (
    CreationError,
    DeletionError,
    ReadingError,
    UpdateError,
)
from sso_service.database.repository import ClientRepository

from ...schemas import ClientCreate, ClientUpdate, CreatedClient

logger = logging.getLogger(__name__)

clients_router = APIRouter(prefix="/clients", tags=["Clients"], route_class=DishkaRoute)


@clients_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    response_model=CreatedClient,
    summary="Создаёт клиента в заданной области",
)
async def create_client(
        client_create: ClientCreate, repository: Depends[ClientRepository]
) -> CreatedClient:
    try:
        client = Client.model_validate(client_create)
        client_secret = client.client_secret
        client = client.hash_client_secret()
        created_client = await repository.create(client)
        return CreatedClient(
            **created_client.model_dump(exclude={"client_secret"}),
            client_secret=client_secret
        )
    except CreationError:
        logger.exception("Error while creating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while creating client",
        ) from None


@clients_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=CreatedClient,
    response_model_exclude={"client_secret"},
    summary="Получает клиента из заданной области"
)
async def get_client(
        id: UUID, repository: Depends[ClientRepository]
) -> CreatedClient:
    try:
        client = await repository.read(id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            ) from None
        return CreatedClient.model_validate(client)
    except ReadingError:
        logger.exception("Error while retrieving client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while retrieving client"
        ) from None


@clients_router.patch(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=CreatedClient,
    summary="Обновляет данные клиента"
)
async def update_client(
        id: UUID, client_update: ClientUpdate, repository: Depends[ClientRepository]
) -> CreatedClient:
    try:
        updated_client = await repository.update(
            id, **client_update.model_dump(exclude_none=True)
        )
        if not updated_client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )
        return CreatedClient.model_validate(updated_client)
    except UpdateError:
        logger.exception("Error while updating client: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while updating client"
        ) from None


@clients_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаляет клиента по его уникальному id"
)
async def delete_client(id: UUID, repository: Depends[ClientRepository]) -> None:
    try:
        is_deleted = await repository.delete(id)
        if not is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )
    except DeletionError:
        logger.exception("Error while deleting client: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error while deleting client"
        ) from None
    else:
        return
