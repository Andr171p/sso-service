FROM python:3.13-slim as builder

WORKDIR /sso_service

RUN pip install --no-cache-dir uv && \
    uv venv -p python3.13 /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml requirements.txt ./

RUN uv pip install --no-cache -r requirements.txt

FROM python:3.13-slim

WORKDIR /sso_service

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

COPY . .

CMD alembic upgrade head && ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]