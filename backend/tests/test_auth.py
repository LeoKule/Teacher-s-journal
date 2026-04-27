"""Тесты аутентификации: регистрация, логин, рефреш, логаут."""
import pytest


class TestRegister:
    def test_register_success(self, client, teacher_data):
        resp = client.post("/register/", json=teacher_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == teacher_data["email"]
        assert data["full_name"] == teacher_data["full_name"]

    def test_register_duplicate_email(self, client, teacher_data):
        client.post("/register/", json=teacher_data)
        resp = client.post("/register/", json=teacher_data)
        assert resp.status_code == 400
        assert "Email" in resp.json()["detail"] or "email" in resp.json()["detail"].lower()

    def test_register_weak_password(self, client):
        resp = client.post("/register/", json={
            "email": "test@test.com",
            "password": "weakpass",
            "full_name": "Тест Тест"
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client):
        resp = client.post("/register/", json={
            "email": "not-an-email",
            "password": "Password1!",
            "full_name": "Тест Тест"
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_teacher):
        resp = client.post(
            "/token",
            data={"username": registered_teacher["email"], "password": registered_teacher["password"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["email"] == registered_teacher["email"]

    def test_login_wrong_password(self, client, registered_teacher):
        resp = client.post(
            "/token",
            data={"username": registered_teacher["email"], "password": "WrongPass1!"},
        )
        assert resp.status_code == 400

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/token",
            data={"username": "nobody@test.com", "password": "Password1!"},
        )
        assert resp.status_code == 400

    def test_login_returns_role(self, client, registered_teacher):
        resp = client.post(
            "/token",
            data={"username": registered_teacher["email"], "password": registered_teacher["password"]},
        )
        assert resp.json()["user_role"] == "teacher"


class TestProfile:
    def test_get_profile(self, client, teacher_headers, registered_teacher):
        resp = client.get("/profile", headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == registered_teacher["email"]

    def test_get_profile_unauthorized(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 401

    def test_update_profile_name(self, client, teacher_headers):
        resp = client.patch("/profile", json={"full_name": "Новое Имя"}, headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Новое Имя"

    def test_change_password_wrong_current(self, client, teacher_headers):
        resp = client.patch(
            "/profile",
            json={"current_password": "WrongOld1!", "new_password": "NewPass1!"},
            headers=teacher_headers
        )
        assert resp.status_code == 400

    def test_change_password_success(self, client, teacher_headers, registered_teacher):
        resp = client.patch(
            "/profile",
            json={"current_password": registered_teacher["password"], "new_password": "NewPass123!"},
            headers=teacher_headers
        )
        assert resp.status_code == 200
        # Логинимся с новым паролем
        login = client.post(
            "/token",
            data={"username": registered_teacher["email"], "password": "NewPass123!"},
        )
        assert login.status_code == 200


class TestLogout:
    def test_logout_success(self, client, teacher_headers):
        resp = client.post("/logout", headers=teacher_headers)
        assert resp.status_code == 200

    def test_token_blacklisted_after_logout(self, client, teacher_headers):
        client.post("/logout", headers=teacher_headers)
        resp = client.get("/profile", headers=teacher_headers)
        assert resp.status_code == 401


class TestRateLimit:
    def test_rate_limit_login(self, client, registered_teacher):
        for _ in range(5):
            client.post(
                "/token",
                data={"username": registered_teacher["email"], "password": "WrongPass1!"},
            )
        resp = client.post(
            "/token",
            data={"username": registered_teacher["email"], "password": registered_teacher["password"]},
        )
        assert resp.status_code == 429
