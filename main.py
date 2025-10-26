import logging

from sso_service.api.app import create_fastapi_app, setup_errors_handlers, setup_middleware

logging.basicConfig(level=logging.INFO)

app = create_fastapi_app()
setup_middleware(app)
setup_errors_handlers(app)
