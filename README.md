# Журнал преподавателя (Teacher's Journal)

Веб-приложение для автоматизации учета успеваемости студентов и управления учебным процессом. Позволяет преподавателям выставлять оценки, отслеживать посещаемость и экспортировать данные в формат Excel.

## Основные функции

* **Управление оценками:** Интерактивная таблица для выставления баллов и отметок о посещаемости ("Н").
* **Фильтрация:** Быстрый поиск по курсам (1-4) и академическим группам.
* **Экспорт в Excel:** Мгновенная выгрузка текущего журнала в таблицу `.xlsx` прямо из браузера.
* **Темы оформления:** Поддержка светлого и темного режимов для комфортной работы в любое время суток.
* **Безопасность:** Система авторизации на базе JWT-токенов с функцией "Запомнить меня".

##  Технологический стек

### Frontend:
* **Vue.js 3** (Composition API) — основная логика интерфейса.
* **Vuetify 3** — библиотека UI-компонентов и систем тем оформления.
* **Axios** — взаимодействие с API бэкенда.
* **XLSX (SheetJS)** — генерация Excel-файлов на стороне клиента.

### Backend:
* **FastAPI** (Python) — высокопроизводительный серверный фреймворк.
* **SQLAlchemy** — ORM для работы с базой данных.
* **MySQL** — реляционная база данных для хранения данных студентов и оценок.

---

##  Установка и запуск

### 1. Предварительные требования
Убедитесь, что у вас установлены:
* Python 3.9+
* Node.js 16+
* MySQL Server

### 2. Настройка Бэкенда (Python)

```bash
cd backend

# Создание и активация виртуального окружения
python -m venv venv
# Для Windows:
venv\Scripts\activate
# Для Linux/Mac:
source venv/bin/activate

# Установка зависимостей
pip install fastapi uvicorn sqlalchemy mysql-connector-python pydantic python-jose passlib
```

### 3. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните реальные значения:

```bash
cd backend
cp .env.example .env  # Для Windows используйте: copy .env.example .env
```

Отредактируйте `.env` файл с вашими данными БД и секретным ключом:
```env
DATABASE_USER=teacher_app
DATABASE_PASSWORD=your_password
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_NAME=teacher_journal
SECRET_KEY=your_super_secret_key_change_me_in_production
```

### 4. Запуск приложения

**Запуск Бэкенда:**
```bash
cd backend
# Убедитесь, что виртуальное окружение активировано
python -m uvicorn main:app --reload
# Сервер будет доступен на http://localhost:8000
```

**Запуск Фронтенда** (в отдельном терминале):
```bash
cd frontend
npm install
npm run dev
# Приложение откроется на http://localhost:5173
```

---

## 📁 Структура проекта

```
Teacher-s-journal/
├── backend/              # FastAPI приложение
│   ├── routers/         # API маршруты (авторизация, журнал, управление)
│   ├── models.py        # SQLAlchemy модели БД
│   ├── schemas.py       # Pydantic схемы валидации
│   ├── database.py      # Конфигурация подключения к БД
│   ├── crud.py          # CRUD операции
│   ├── main.py          # Главный файл приложения
│   ├── config.py        # Конфигурация приложения
│   └── .env.example     # Шаблон переменных окружения
│
├── frontend/            # Vue.js + Vite приложение
│   ├── src/
│   │   ├── components/  # Vue компоненты (табличное представление, фильтры)
│   │   ├── views/       # Страницы (Журнал, Администрирование, Логин)
│   │   ├── router/      # Маршрутизация
│   │   ├── api/         # Axios клиент и хранилище авторизации
│   │   └── App.vue      # Корневой компонент
│   ├── index.html       # HTML точка входа
│   ├── vite.config.js   # Конфигурация Vite
│   └── package.json     # Зависимости Node.js
│
└── README.md            # Этот файл
```

## 🔌 API маршруты

### Аутентификация
- `POST /api/auth/login` — Вход в систему
- `POST /api/auth/refresh` — Обновление JWT токена
- `POST /api/auth/logout` — Выход из системы

### Журнал (данные студентов и оценок)
- `GET /api/journal/groups` — Получить список групп
- `GET /api/journal/students/{group_id}` — Получить студентов группы
- `GET /api/journal/marks` — Получить оценки
- `POST /api/journal/marks` — Добавить/обновить оценку

### Администрирование (только для админов)
- `GET /api/admin/teachers` — Список преподавателей
- `GET /api/admin/audit-logs` — Логи действий

## 💥 Требуемые зависимости (Backend)

Установка всех необходимых пакетов:
```bash
pip install fastapi uvicorn sqlalchemy mysql-connector-python pydantic python-jose[cryptography] passlib[bcrypt]
```

## 🛠️ Доступные npm команды (Frontend)

```bash
npm run dev      # Запустить сервер разработки
npm run build    # Собрать приложение для продакшена
npm run preview  # Превью собранного приложения
```

## ⚙️ Переменные окружения (Backend)

Смотрите файл `.env.example` для полного списка с описокнаниями:
- `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME` — Подключение к MySQL
- `SECRET_KEY` — Секретный ключ для подписи JWT (генерируйте безопасный в продакшене!)
- `ALGORITHM` — Алгоритм JWT кодирования
- `ACCESS_TOKEN_EXPIRE_MINUTES` — Время жизни access токена
- `REFRESH_TOKEN_EXPIRE_DAYS` — Время жизни refresh токена
- `DEBUG` — Режим отладки

## 📝 FAQ

**Q: Как сгенерировать безопасный SECRET_KEY?**
```bash
openssl rand -hex 32
```
Или в Python:
```python
import secrets
print(secrets.token_hex(32))
```

**Q: Приложение не подключается к БД**
- Убедитесь, что MySQL сервер запущен
- Проверьте учетные данные в `.env` файле
- Убедитесь, что БД `teacher_journal` создана (или запустите `seed_data.py`)

---
