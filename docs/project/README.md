# Документация для внесения изменения в проект

## 🌳 Структура проекта

```bash
.
├── 📂 docs/                  # Документация проекта
├── 📂 migration/             # Миграции Alembic
├── 📂 sso_service/           # Основной код проекта
│   ├── 📂 api/               # Слой презентации (API)
│   │   ├── 📂 routers/       # API эндпоинты
│   │   ├── </> __init__.py 
│   │   ├── </> app.py         # Логика создания FastAPI приложения
│   │   ├── </> schemas.py     # Pydantic схемы и параметры запросов
│   ├── 📂 core/               # Доменная логика
│   │   ├── 🏛️ domain.py       # Доменные модели
│   │   ├── </> enums.py
│   │   └── ...               # Другие core-файлы
│   ├── 📂 providers/         # Identity провайдеры (Google, VK)
│   ├── 🔒 security.py        # JWT, хеширование ...
│   ├── ⚙️ services.py        # Бизнес-логика
│   └── ⚙️ settings.py        # Конфигурация приложения
├── </> main.py               # Точка входа
├── 🐳 docker-compose.yml
└── 📜 pyproject.toml         # Зависимости проекта и конфигурация проекта
```

## Стек технологий 🛠️

- **Язык программирования**:</br>
  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

 - **Web-framework**:</br>
  ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
  
- **Базы данных**:</br>
  ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
  ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-1C1C1C?style=for-the-badge&logo=sqlalchemy)
  ![Alembic](https://img.shields.io/badge/Alembic-1C1C1C?style=for-the-badge&logo=alembic)
  ![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
  
- **Аутентификация и безопасность**:</br>
  ![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=JSON%20web%20tokens)
  
- **HTTP клиент**:</br>
  ![aiohttp](https://img.shields.io/badge/aiohttp-2C5BB4?style=for-the-badge&logo=aiohttp&logoColor=white)
  
- **Инъекция зависимостей**:</br>
  ![Dishka](https://img.shields.io/badge/Dishka-1C1C1C?style=for-the-badge)