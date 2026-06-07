# Учебная платформа — production cleanup

## Запуск локально

```bash
python main_admin.py
```

## Что исправлено

- `config.json` удалён: настройки читаются из `.env` через `configs/config.py`.
- `.gitignore` содержит `*.db`, `.env`, `logs/`, `__pycache__/`.
- `main_admin.py` сокращён: запуск, admin, routers и frontend разделены.
- Frontend API вынесен в `routers/frontend_api.py`.
- Healthcheck доступен по `/health`.
- Dashboard берёт пользователя из JWT, а не из query-параметров.
- Открытый `/frontend-api/seed` отсутствует.
- Добавлен базовый in-memory rate limit.
- Добавлен request-id и rotating log file `logs/app.log`.
- Материалы сохраняются с короткими latin filenames.

## База данных

Локально можно использовать SQLite:

```env
DATABASE_URL=sqlite:///./learning_platform.db
```

Для production рекомендуется PostgreSQL:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/learning_platform
```

## Структура

```text
main_admin.py          # app factory / entrypoint
configs/config.py      # настройки из .env
core/                  # security, logging, rate limit, materials
routers/               # frontend-api, health, files
pkg/controllers/       # основные API контроллеры проекта
pkg/services/          # бизнес-логика
pkg/repositories/      # работа с БД
seed_database.py       # начальные данные, без открытого HTTP endpoint
```

## Для защиты

Основной запуск:

```bash
python main_admin.py
```

Основные демо-пользователи задаются через `.env`:

```env
INITIAL_ADMIN_PASSWORD=admin123
INITIAL_MENTOR_PASSWORD=mentor123
INITIAL_STUDENT_PASSWORD=student123
```

На защите можно сказать:

> Система использует единый источник данных, JWT-авторизацию, ролевой доступ, healthcheck, базовый rate limiting и логирование запросов. Для production база данных может быть переключена на PostgreSQL через `DATABASE_URL`.
