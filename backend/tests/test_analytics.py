"""Тесты аналитики: доступ только для admin, структура ответа, 404."""
import pytest
import models
import auth as auth_module
from datetime import date


@pytest.fixture
def group_in_db(db):
    """Создаёт группу напрямую в БД."""
    group = models.StudentGroup(group_name="ИТ-41", course_year=4)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@pytest.fixture
def group_with_data(db, group_in_db):
    """Создаёт группу со студентами, предметом, занятием и оценкой."""
    teacher = models.Teacher(
        full_name="Тест Преподаватель",
        email="analytics_teacher@test.com",
        password_hash=auth_module.get_password_hash("Password1!"),
        role="teacher",
        is_active=True,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    student = models.Student(full_name="Петров Пётр", group_id=group_in_db.id)
    db.add(student)
    db.commit()
    db.refresh(student)

    subject = models.Subject(name="Физика", teacher_id=teacher.id)
    db.add(subject)
    db.commit()
    db.refresh(subject)

    lesson = models.Lesson(
        group_id=group_in_db.id,
        subject_id=subject.id,
        teacher_id=teacher.id,
        lesson_date=date(2024, 10, 1),
        lesson_topic="Механика",
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    grade = models.GradeRecord(
        student_id=student.id,
        lesson_id=lesson.id,
        grade_value="4",
        attendance_status="present",
    )
    db.add(grade)
    db.commit()

    return group_in_db


class TestAnalyticsAccess:
    def test_requires_auth(self, client, group_in_db):
        resp = client.get(f"/analytics/group/{group_in_db.id}")
        assert resp.status_code == 401

    def test_requires_admin_role(self, client, teacher_headers, group_in_db):
        resp = client.get(f"/analytics/group/{group_in_db.id}", headers=teacher_headers)
        assert resp.status_code == 403

    def test_groups_list_requires_admin(self, client, teacher_headers):
        resp = client.get("/analytics/groups", headers=teacher_headers)
        assert resp.status_code == 403

    def test_groups_list_requires_auth(self, client):
        resp = client.get("/analytics/groups")
        assert resp.status_code == 401


class TestAnalyticsGroupNotFound:
    def test_nonexistent_group_returns_404(self, client, admin_headers):
        resp = client.get("/analytics/group/99999", headers=admin_headers)
        assert resp.status_code == 404


class TestAnalyticsGroupData:
    def test_empty_group_structure(self, client, admin_headers, group_in_db):
        """Пустая группа возвращает корректную структуру с нулями."""
        resp = client.get(f"/analytics/group/{group_in_db.id}", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["group_id"] == group_in_db.id
        assert data["group_name"] == "ИТ-41"
        assert data["course_year"] == 4
        assert data["total_students"] == 0
        assert data["total_lessons"] == 0
        assert data["overall_avg_grade"] is None
        assert data["overall_attendance_rate"] == 0.0
        assert data["subjects"] == []
        assert data["students"] == []

    def test_group_with_grades_structure(self, client, admin_headers, group_with_data):
        """Группа с данными возвращает корректные поля и считает статистику."""
        resp = client.get(f"/analytics/group/{group_with_data.id}", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_students"] == 1
        assert data["total_lessons"] == 1
        assert data["overall_avg_grade"] == pytest.approx(4.0, abs=0.01)
        assert len(data["subjects"]) == 1
        assert len(data["students"]) == 1

        subject = data["subjects"][0]
        assert subject["subject_name"] == "Физика"
        assert subject["lesson_count"] == 1
        assert subject["avg_grade"] == pytest.approx(4.0, abs=0.01)
        assert "grade_distribution" in subject

        student = data["students"][0]
        assert student["student_name"] == "Петров Пётр"
        assert student["avg_grade"] == pytest.approx(4.0, abs=0.01)
        assert "grade_distribution" in student


class TestAnalyticsGroupsList:
    def test_empty_list(self, client, admin_headers):
        resp = client.get("/analytics/groups", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_created_groups(self, client, admin_headers, group_in_db):
        resp = client.get("/analytics/groups", headers=admin_headers)
        assert resp.status_code == 200
        ids = [g["id"] for g in resp.json()]
        assert group_in_db.id in ids
