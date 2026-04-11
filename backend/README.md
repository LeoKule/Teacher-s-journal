# Backend веб-приложения «Журнал преподавателя»

Backend-часть веб-приложения для ведения журнала преподавателя.

## Стек технологий

- Python
- FastAPI
- SQLAlchemy
- MySQL
- JWT-аутентификация

## Что уже реализовано

- Регистрация и авторизация преподавателя
- Защита эндпоинтов через JWT
- Работа с учебными группами
- Работа со студентами
- Работа с предметами
- Работа с занятиями
- Журнал оценок и посещаемости
- Журнал по выбранной дате
- Обновление, массовое сохранение и удаление записей журнала
- Учебные периоды
- Назначения преподавателя:
  преподаватель -> предмет -> группа -> учебный период
- Шаблоны расписания
- Генерация занятий по шаблонам расписания
- Предпросмотр и удаление сгенерированных занятий
- `.gitignore` для проекта

## Структура проекта

- `main.py` — маршруты FastAPI
- `models.py` — модели SQLAlchemy
- `schemas.py` — Pydantic-схемы
- `crud.py` — работа с базой данных
- `auth.py` — хэширование паролей и JWT
- `database.py` — подключение к базе данных

## Основные возможности API

### Авторизация

- `POST /register/`
- `POST /token`

### Основные сущности

- `GET/POST /groups/`
- `GET/POST /students/`
- `GET/POST /subjects/`
- `GET/POST /lessons/`

### Журнал

- `GET /journal/daily/`
- `GET /grade-records/`
- `POST /grade-records/`
- `PUT /grade-records/upsert/`
- `PUT /grade-records/bulk-upsert/`
- `PATCH /grade-records/{grade_record_id}`
- `DELETE /grade-records/{grade_record_id}`

### Учебная структура

- `GET/POST /academic-periods/`
- `GET/POST /teaching-assignments/`
- `GET/POST /schedule-templates/`

### Расписание и генерация занятий

- `GET /schedule/`
- `POST /lessons/generate/`
- `POST /lessons/generate/preview/`
- `POST /lessons/generated/delete/`

## Как запустить проект

1. Создать базу данных MySQL.
2. Указать параметры подключения в `database.py`.
3. Установить зависимости.
4. Запустить сервер:

```bash
uvicorn main:app --reload
```

## Что можно улучшить дальше

- Вынести настройки базы данных и секретные ключи в `.env`
- Добавить миграции через Alembic
- Добавить строгую валидацию оценок и статусов посещаемости
- Реализовать отчёты и аналитику
- Написать автоматические тесты
- Разработать frontend
