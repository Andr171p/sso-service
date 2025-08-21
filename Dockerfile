FROM python:3.13-slim as builder

WORKDIR /app

RUN pip install uv
COPY pyproject.toml .
RUN uv lock && uv sync --frozen --no-cache
COPY . .

FROM python:3.13-slim as runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app /app

RUN echo '#!/bin/sh\n\
set -e\n\
\n\
echo "Running migrations..."\n\
alembic upgrade head\n\
\n\
echo "Starting application..."\n\
exec uvicorn main:app --host 0.0.0.0 --port 8000\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/entrypoint.sh"]