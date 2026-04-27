"""
Фикстуры для тестов: тестовая БД SQLite in-memory, тестовый клиент FastAPI.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from main import app
from routers.dependencies import get_db

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Создаём таблицы перед каждым тестом, удаляем после."""
    Base.metadata.create_all(bind=engine)
    # Сбрасываем in-memory rate limiter перед каждым тестом
    from routers.auth import login_attempts
    login_attempts.clear()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФИКСТУРЫ ==========

@pytest.fixture
def teacher_data():
    return {
        "email": "teacher@test.com",
        "password": "Password1!",
        "full_name": "Иван Иванов"
    }


@pytest.fixture
def admin_data():
    return {
        "email": "admin@test.com",
        "password": "Admin123!",
        "full_name": "Администратор"
    }


@pytest.fixture
def registered_teacher(client, teacher_data):
    """Создаёт и возвращает зарегистрированного преподавателя."""
    client.post("/register/", json=teacher_data)
    return teacher_data


@pytest.fixture
def teacher_token(client, registered_teacher):
    """Возвращает access_token для преподавателя."""
    resp = client.post(
        "/token",
        data={"username": registered_teacher["email"], "password": registered_teacher["password"]},
    )
    return resp.json()["access_token"]


@pytest.fixture
def teacher_headers(teacher_token):
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def registered_admin(client, db, admin_data):
    """Создаёт преподавателя с ролью admin напрямую через БД."""
    import models
    import auth as auth_module
    admin = models.Teacher(
        full_name=admin_data["full_name"],
        email=admin_data["email"],
        password_hash=auth_module.get_password_hash(admin_data["password"]),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    return admin_data


@pytest.fixture
def admin_token(client, registered_admin):
    resp = client.post(
        "/token",
        data={"username": registered_admin["email"], "password": registered_admin["password"]},
    )
    return resp.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
