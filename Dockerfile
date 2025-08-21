FROM python:3.13-slim as builder

WORKDIR /sso_service

RUN pip install --no-cache-dir uv && \
    uv venv -p python3.13 /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml ./

RUN uv pip install --no-cache --system . alembic

FROM python:3.13-slim

WORKDIR /sso_service

COPY --from=builder /opt/venv /opt/venv
COPY alembic.ini ./
COPY alembic ./alembic/

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

RUN alembic upgrade head

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]