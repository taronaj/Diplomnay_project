# Учебная платформа

LMS/CRM для управления образовательным процессом: пользователи, роли, курсы, уроки, материалы, домашние задания, посещаемость, комментарии, лента событий и аналитика успеваемости.

## Стек

- Python, FastAPI, SQLAlchemy
- PostgreSQL для production, SQLite для локальной проверки
- JWT-авторизация
- SQLAdmin для админ-панели
- Alembic для миграций
- Pytest для базовых проверок

## Запуск

Создайте `.env`:

```env
DATABASE_URL=sqlite:///./learning_platform.db
SECRET_KEY=change-me
APP_HOST=127.0.0.1
APP_PORT=8080
```

Запуск приложения:

```bash
python3 main_admin.py
```

Основные страницы:

- `GET /` - frontend
- `GET /admin` - админ-панель
- `GET /docs` - Swagger
- `GET /health` - healthcheck

## Архитектура

`main_admin.py` оставлен как точка входа и app factory. Основная сборка разнесена по модулям:

- `core/startup.py` - логирование, создание таблиц для локального запуска, seed-данные, директория материалов
- `core/frontend.py` - frontend и совместимый `/sign-in`
- `core/admin_panel.py` - SQLAdmin и список admin views
- `core/router_registry.py` - подключение API routers
- `routers/` - frontend API, файлы, healthcheck
- `pkg/controllers/`, `pkg/services/`, `pkg/repositories/` - основные CRUD-слои

## База данных и миграции

Alembic уже подключен. Начальная миграция находится в `alembic/versions/20260518_0001_initial_schema.py`.

Для локальной дипломной демонстрации приложение всё ещё может создать таблицы через `Base.metadata.create_all()` при старте. Для production-подхода используйте миграции:

```bash
alembic upgrade head
```

Создание новой миграции после изменения моделей:

```bash
alembic revision --autogenerate -m "describe change"
```

## Безопасность

- Настройки и секреты читаются из `.env`.
- `configs/config.json` не используется.
- Пароли не выводятся в логи.
- Dashboard API требует JWT в `Authorization: Bearer <token>`.
- Открытый `/frontend-api/seed` отсутствует.
- Во frontend нет hardcoded demo-паролей.

## Тесты

Для проверки на SQLite:

```bash
DATABASE_URL=sqlite:///./test_learning_platform.db SECRET_KEY=test-secret python3 -m pytest
```

Если используется PostgreSQL, убедитесь, что сервер доступен по `DATABASE_URL`.
