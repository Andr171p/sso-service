from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka as Depends
from fastapi import APIRouter, HTTPException, status

from sso_service.core.domain import Client
from sso_service.database.repository import ClientRepository

from ...schemas import ClientCreate, ClientUpdate, CreatedClient

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
    client = Client.model_validate(client_create)
    client_secret = client.client_secret
    client.hash_client_secret()
    created_client = await repository.create(client)
    return CreatedClient(
        **created_client.model_dump(exclude={"client_secret"}),
        client_secret=client_secret.get_secret_value()
    )


@clients_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=CreatedClient,
    response_model_exclude={"client_secret"},
    summary="Получает клиента из заданной области"
)
async def get_client(
        id: UUID, repository: Depends[ClientRepository]  # noqa: A002
) -> CreatedClient:
    client = await repository.read(id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return CreatedClient.model_validate(client)


@clients_router.patch(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    response_model=CreatedClient,
    summary="Обновляет данные клиента"
)
async def update_client(
        id: UUID, client_update: ClientUpdate, repository: Depends[ClientRepository]  # noqa: A002
) -> CreatedClient:
    updated_client = await repository.update(
        id, **client_update.model_dump(exclude_none=True)
    )
    if not updated_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
    return CreatedClient.model_validate(updated_client)


@clients_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаляет клиента по его уникальному id"
)
async def delete_client(id: UUID, repository: Depends[ClientRepository]) -> None:  # noqa: A002
    is_deleted = await repository.delete(id)
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )
