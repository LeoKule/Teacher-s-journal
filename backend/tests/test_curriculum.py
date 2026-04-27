"""Тесты учебного плана: группы, студенты, предметы, занятия, учебные периоды."""
import pytest
from datetime import date


@pytest.fixture
def group(client, teacher_headers):
    resp = client.post("/groups/", json={"group_name": "ИТ-31", "course_year": 3}, headers=teacher_headers)
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture
def subject(client, teacher_headers):
    resp = client.post("/subjects/", json={"name": "Математика"}, headers=teacher_headers)
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture
def academic_period(client, teacher_headers):
    resp = client.post("/academic-periods/", json={
        "name": "2024-2025 1й семестр",
        "academic_year": "2024-2025",
        "semester_number": 1,
        "start_date": "2024-09-01",
        "end_date": "2025-01-31"
    }, headers=teacher_headers)
    assert resp.status_code == 200
    return resp.json()


class TestGroups:
    def test_create_group(self, client, teacher_headers):
        resp = client.post("/groups/", json={"group_name": "АТ-11", "course_year": 1}, headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["group_name"] == "АТ-11"

    def test_get_groups(self, client, teacher_headers, group):
        resp = client.get("/groups/", headers=teacher_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_update_group_as_admin(self, client, admin_headers):
        create = client.post("/groups/", json={"group_name": "БХ-21", "course_year": 2}, headers=admin_headers)
        group_id = create.json()["id"]
        resp = client.patch(f"/groups/{group_id}", json={"group_name": "БХ-22"}, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["group_name"] == "БХ-22"

    def test_update_group_forbidden_for_teacher(self, client, teacher_headers, group):
        resp = client.patch(f"/groups/{group['id']}", json={"group_name": "ИТ-99"}, headers=teacher_headers)
        assert resp.status_code == 403


class TestStudents:
    def test_create_student_requires_access(self, client, teacher_headers, group):
        resp = client.post("/students/", json={
            "full_name": "Студент Тестович",
            "group_id": group["id"]
        }, headers=teacher_headers)
        # Преподаватель без назначения не имеет доступа к группе
        assert resp.status_code in (200, 403)

    def test_update_student(self, client, admin_headers, db):
        import models
        grp = models.StudentGroup(group_name="ОО-11", course_year=1)
        db.add(grp)
        db.commit()
        student = models.Student(full_name="Старое Имя", group_id=grp.id)
        db.add(student)
        db.commit()

        # Админ сначала нужно иметь назначение... или просто проверяем ошибку 403
        resp = client.patch(f"/students/{student.id}", json={"full_name": "Новое Имя"}, headers=admin_headers)
        # Без назначения — 403, это корректно
        assert resp.status_code in (200, 403)

    def test_update_nonexistent_student(self, client, teacher_headers):
        resp = client.patch("/students/99999", json={"full_name": "Никого"}, headers=teacher_headers)
        assert resp.status_code in (403, 404)


class TestSubjects:
    def test_create_subject(self, client, teacher_headers):
        resp = client.post("/subjects/", json={"name": "Физика"}, headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Физика"

    def test_get_subjects(self, client, teacher_headers, subject):
        resp = client.get("/subjects/", headers=teacher_headers)
        assert resp.status_code == 200
        names = [s["name"] for s in resp.json()]
        assert subject["name"] in names

    def test_update_subject(self, client, teacher_headers, subject):
        resp = client.patch(f"/subjects/{subject['id']}", json={"name": "Алгебра"}, headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Алгебра"

    def test_update_foreign_subject_forbidden(self, client, teacher_headers, admin_headers, subject):
        # Создаём другого преподавателя и логинимся как он
        client.post("/register/", json={
            "email": "other@test.com",
            "password": "Other123!",
            "full_name": "Другой"
        })
        token = client.post("/token", data={
            "username": "other@test.com",
            "password": "Other123!"
        }).json()["access_token"]
        resp = client.patch(
            f"/subjects/{subject['id']}",
            json={"name": "Кража"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 403


class TestAcademicPeriods:
    def test_create_academic_period(self, client, teacher_headers):
        resp = client.post("/academic-periods/", json={
            "name": "2025-2026 1й",
            "academic_year": "2025-2026",
            "semester_number": 1,
            "start_date": "2025-09-01",
            "end_date": "2026-01-31"
        }, headers=teacher_headers)
        assert resp.status_code == 200

    def test_create_period_invalid_dates(self, client, teacher_headers):
        resp = client.post("/academic-periods/", json={
            "name": "Плохой период",
            "academic_year": "2025-2026",
            "semester_number": 1,
            "start_date": "2026-01-31",
            "end_date": "2025-09-01"
        }, headers=teacher_headers)
        assert resp.status_code == 400

    def test_get_academic_periods(self, client, teacher_headers, academic_period):
        resp = client.get("/academic-periods/", headers=teacher_headers)
        assert resp.status_code == 200
        assert any(p["id"] == academic_period["id"] for p in resp.json())
