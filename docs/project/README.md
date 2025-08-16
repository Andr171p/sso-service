# Документация для внесения изменения в проект

## Структура проекта 📁
```
docs - Документаия проекта
migration - Миграции alembic
sso_service - Код проекта
 - api - Слой презентации
 -- routers - API ендпоинты
 -- __init__.py
 -- app.py - Кинфигурация API приложения
 -- schemas.py - JSON схемы, query прааметры ...
 - core - Слой доменной логики
 -- __init__.py
 -- base.py - Интерфейсы, базовые и абстрактные классы
 -- constants.py - Константы
 -- domain.py - Доменные сущности
 -- enums.py - Перечисления
 -- exceptions.py - Ошибки на уровне приложения
 -- utils.py - Вспомогательные фугкции и утилиты
 - database - Работа с базой данных
 - providers - Identity провайдеры (Google, VK, ...) 
 - __init__.py
 - dependencies.py - Контейнер зависимостей
 - security.py - JWT, хэшированние и.т.д
 - services.py - Сервисный слой (бизнес логика)
 - settings.py - Настройки, переменные окружения
 - storage.py - Кэшевые хранилища данных (Redis)
alembic.ini
docker-compose.yml
main.py - Точка входа приложения
pyproject.toml
uv.lock
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