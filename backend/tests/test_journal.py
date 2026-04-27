"""Тесты журнала оценок: создание, обновление, bulk upsert, soft delete."""
import pytest
from datetime import date
import models


@pytest.fixture
def setup_lesson(client, teacher_headers, db, registered_teacher):
    """Создаёт группу, студента, предмет, занятие для тестов оценок."""
    import auth as auth_module

    # Получаем ID преподавателя
    token_resp = client.post("/token", data={
        "username": registered_teacher["email"],
        "password": registered_teacher["password"]
    })
    teacher_id = token_resp.json()["user_id"]

    # Создаём объекты напрямую через БД
    group = models.StudentGroup(group_name="ТГ-41", course_year=4)
    db.add(group)
    db.commit()

    student = models.Student(full_name="Студент Один", group_id=group.id)
    db.add(student)
    db.commit()

    subject = models.Subject(name="Информатика", teacher_id=teacher_id)
    db.add(subject)
    db.commit()

    lesson = models.Lesson(
        teacher_id=teacher_id,
        subject_id=subject.id,
        group_id=group.id,
        lesson_date=date(2024, 10, 1),
    )
    db.add(lesson)
    db.commit()

    return {
        "group": group,
        "student": student,
        "subject": subject,
        "lesson": lesson,
        "teacher_id": teacher_id
    }


class TestGradeRecords:
    def test_create_grade_record(self, client, teacher_headers, setup_lesson):
        ctx = setup_lesson
        resp = client.post("/grade-records/", json={
            "lesson_id": ctx["lesson"].id,
            "student_id": ctx["student"].id,
            "grade_value": 5
        }, headers=teacher_headers)
        assert resp.status_code == 200
        assert str(resp.json()["grade_value"]) == "5"

    def test_create_grade_absence(self, client, teacher_headers, setup_lesson):
        ctx = setup_lesson
        resp = client.post("/grade-records/", json={
            "lesson_id": ctx["lesson"].id,
            "student_id": ctx["student"].id,
            "grade_value": "Н"
        }, headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["grade_value"] == "Н"

    def test_invalid_grade_rejected(self, client, teacher_headers, setup_lesson):
        ctx = setup_lesson
        resp = client.post("/grade-records/", json={
            "lesson_id": ctx["lesson"].id,
            "student_id": ctx["student"].id,
            "grade_value": 6
        }, headers=teacher_headers)
        assert resp.status_code == 422

    def test_upsert_grade(self, client, teacher_headers, setup_lesson):
        ctx = setup_lesson
        payload = {
            "lesson_id": ctx["lesson"].id,
            "student_id": ctx["student"].id,
            "grade_value": 4
        }
        # Создаём
        r1 = client.put("/grade-records/upsert/", json=payload, headers=teacher_headers)
        assert r1.status_code == 200
        # Обновляем
        payload["grade_value"] = 5
        r2 = client.put("/grade-records/upsert/", json=payload, headers=teacher_headers)
        assert r2.status_code == 200
        assert str(r2.json()["grade_value"]) == "5"

    def test_bulk_upsert(self, client, teacher_headers, setup_lesson, db):
        ctx = setup_lesson
        student2 = models.Student(full_name="Студент Два", group_id=ctx["group"].id)
        db.add(student2)
        db.commit()

        resp = client.put("/grade-records/bulk-upsert/", json={
            "lesson_id": ctx["lesson"].id,
            "rows": [
                {"student_id": ctx["student"].id, "grade_value": "3", "attendance_status": "present"},
                {"student_id": student2.id, "grade_value": "Н", "attendance_status": "absent"},
            ]
        }, headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["saved_count"] == 2

    def test_delete_grade_record(self, client, teacher_headers, setup_lesson):
        ctx = setup_lesson
        create = client.post("/grade-records/", json={
            "lesson_id": ctx["lesson"].id,
            "student_id": ctx["student"].id,
            "grade_value": 3
        }, headers=teacher_headers)
        record_id = create.json()["id"]
        resp = client.delete(f"/grade-records/{record_id}", headers=teacher_headers)
        assert resp.status_code == 200

    def test_get_grade_records(self, client, teacher_headers, setup_lesson):
        ctx = setup_lesson
        client.post("/grade-records/", json={
            "lesson_id": ctx["lesson"].id,
            "student_id": ctx["student"].id,
            "grade_value": 4
        }, headers=teacher_headers)
        resp = client.get(f"/grade-records/?lesson_id={ctx['lesson'].id}", headers=teacher_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_grade_requires_auth(self, client):
        resp = client.get("/grade-records/")
        assert resp.status_code == 401


class TestSchedule:
    def test_get_schedule(self, client, teacher_headers, setup_lesson):
        resp = client.get("/schedule/?date_from=2024-10-01&date_to=2024-10-31", headers=teacher_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_update_lesson_topic(self, client, teacher_headers, setup_lesson):
        ctx = setup_lesson
        resp = client.patch(f"/lessons/{ctx['lesson'].id}", json={
            "lesson_topic": "Введение в Python"
        }, headers=teacher_headers)
        assert resp.status_code == 200
        assert resp.json()["lesson_topic"] == "Введение в Python"
