FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-openbsd \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Конвертируем в Unix формат и делаем исполняемым
RUN dos2unix entrypoint.sh && \
    chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]