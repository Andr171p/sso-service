import logging

from src.auth_service.api.app import create_fastapi_app

logging.basicConfig(level=logging.INFO)

app = create_fastapi_app()
