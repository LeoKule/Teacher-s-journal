# Журнал преподавателя

Веб-приложение для автоматизации учёта успеваемости студентов и управления учебным процессом. Преподаватели выставляют оценки и отслеживают посещаемость через интерактивный журнал; администраторы управляют пользователями, группами и просматривают аналитику.

## Основные функции

**Журнал преподавателя**
- Интерактивная таблица оценок с выбором курса, группы и предмета
- Выставление оценок (2–5) и отметок об отсутствии («Н») с комментарием
- Экспорт текущего журнала в `.xlsx` прямо из браузера

**Панель администратора**
- Управление преподавателями: создание, редактирование, блокировка, сброс пароля
- Управление группами: перевод на следующий курс
- Импорт студентов из CSV с предпросмотром и dry-run режимом
- Восстановление удалённых студентов (soft delete)
- Аналитика по группам: средний балл, посещаемость, распределение оценок, графики (Chart.js)
- Рассылка уведомлений преподавателям
- Логи аудита всех административных действий

**Общее**
- Авторизация на JWT с refresh-токенами и функцией «Запомнить меня»
- Поддержка светлой и тёмной тем оформления
- Ролевая модель: `teacher` / `admin`

## Технологический стек

| Слой | Технологии |
|---|---|
| Frontend | Vue 3 (Composition API), Vuetify 3, Vue Router, Axios, vue-chartjs, SheetJS |
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, python-jose, passlib/bcrypt |
| База данных | MySQL |

## Установка и запуск

### Требования
- Python 3.9+
- Node.js 18+
- MySQL Server

### Backend

```bash
cd backend

# Создать и активировать виртуальное окружение
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt

# Настроить переменные окружения
copy .env.example .env       # Windows
# cp .env.example .env       # Linux / macOS
# Отредактировать .env — заполнить данные MySQL и SECRET_KEY

# Применить миграции БД
alembic upgrade head

# Запустить сервер разработки
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## Переменные окружения (backend/.env)

```env
DATABASE_USER=teacher_app
DATABASE_PASSWORD=your_password
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_NAME=teacher_journal

SECRET_KEY=           # openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Структура проекта

```
Teacher-s-journal/
├── backend/
│   ├── routers/
│   │   ├── auth.py          # /token, /refresh, /logout
│   │   ├── journal.py       # Оценки и уроки
│   │   ├── curriculum.py    # Предметы, расписание
│   │   ├── admin.py         # Управление преподавателями, группами, студентами
│   │   └── dependencies.py  # get_db, get_current_user
│   ├── alembic/             # Миграции БД
│   ├── models.py            # ORM-модели (12 таблиц)
│   ├── schemas.py           # Pydantic схемы
│   ├── crud.py              # Все запросы к БД
│   ├── auth.py              # JWT и bcrypt
│   ├── main.py              # Инициализация приложения, CORS
│   ├── config.py            # Настройки через pydantic-settings
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/src/
    ├── views/
    │   ├── LoginView.vue
    │   ├── JournalView.vue   # Журнал преподавателя
    │   └── AdminView.vue     # Панель администратора
    ├── components/admin/     # AdminTeachers, AdminGroups, AdminAnalytics,
    │                         # AdminAuditLogs, AdminNotifications,
    │                         # AdminStudentImport, AdminStudentRecovery,
    │                         # AdminStatistics
    ├── router/index.js       # Навигационные гарды (role-based)
    └── api/
        ├── axios.js          # Axios + авто-обновление токена при 401
        └── authStorage.js    # Работа с localStorage / sessionStorage
```

## Основные API маршруты

| Метод | Путь | Описание |
|---|---|---|
| POST | `/token` | Вход, получение токенов |
| POST | `/refresh` | Обновление access-токена |
| POST | `/logout` | Инвалидация токена |
| GET | `/profile` | Профиль текущего пользователя |
| PATCH | `/profile` | Обновление профиля и пароля |
| GET | `/groups/by-course/{year}` | Группы по курсу |
| GET | `/subjects/by-group/{id}` | Предметы группы |
| GET | `/lessons/` | Уроки (фильтр по группе/предмету) |
| PUT | `/grade-records/upsert/` | Создать или обновить оценку |
| GET | `/admin/teachers/` | Список преподавателей |
| POST | `/admin/teachers/` | Создать преподавателя |
| POST | `/admin/teachers/{id}/reset-password` | Сброс пароля |
| POST | `/admin/groups/promote-year/` | Перевод групп на следующий курс |
| POST | `/admin/students/bulk-import` | Импорт студентов из CSV |
| GET | `/admin/students/deleted` | Удалённые студенты |
| POST | `/admin/students/{id}/restore` | Восстановить студента |
| POST | `/admin/notifications/send` | Отправить уведомление |
| GET | `/admin/audit-logs/` | Логи аудита |
| GET | `/admin/statistics/` | Общая статистика |
| GET | `/analytics/group/{id}` | Аналитика по группе |
