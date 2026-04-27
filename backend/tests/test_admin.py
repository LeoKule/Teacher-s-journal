"""Тесты администраторских функций: управление преподавателями, студентами, статистика."""
import pytest


class TestAdminAccess:
    def test_admin_endpoint_requires_admin_role(self, client, teacher_headers):
        resp = client.get("/admin/teachers/", headers=teacher_headers)
        assert resp.status_code == 403

    def test_admin_endpoint_requires_auth(self, client):
        resp = client.get("/admin/teachers/")
        assert resp.status_code == 401


class TestTeacherManagement:
    def test_create_teacher_by_admin(self, client, admin_headers):
        resp = client.post("/admin/teachers/", json={
            "email": "new@test.com",
            "full_name": "Новый Преподаватель",
            "role": "teacher"
        }, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "temporary_password" in data
        assert data["email"] == "new@test.com"

    def test_create_teacher_duplicate_email(self, client, admin_headers):
        payload = {"email": "dup@test.com", "full_name": "Дублирует", "role": "teacher"}
        client.post("/admin/teachers/", json=payload, headers=admin_headers)
        resp = client.post("/admin/teachers/", json=payload, headers=admin_headers)
        assert resp.status_code == 400

    def test_get_all_teachers(self, client, admin_headers, registered_teacher):
        resp = client.get("/admin/teachers/", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_get_teacher_by_id(self, client, admin_headers):
        create = client.post("/admin/teachers/", json={
            "email": "byid@test.com",
            "full_name": "По ID",
            "role": "teacher"
        }, headers=admin_headers)
        teacher_id = create.json()["teacher_id"]
        resp = client.get(f"/admin/teachers/{teacher_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == teacher_id

    def test_update_teacher(self, client, admin_headers):
        create = client.post("/admin/teachers/", json={
            "email": "upd@test.com",
            "full_name": "Старое Имя",
            "role": "teacher"
        }, headers=admin_headers)
        teacher_id = create.json()["teacher_id"]
        resp = client.put(f"/admin/teachers/{teacher_id}", json={
            "full_name": "Новое Имя"
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Новое Имя"

    def test_toggle_teacher_status(self, client, admin_headers):
        create = client.post("/admin/teachers/", json={
            "email": "block@test.com",
            "full_name": "Блокируемый",
            "role": "teacher"
        }, headers=admin_headers)
        teacher_id = create.json()["teacher_id"]
        # Блокируем
        resp = client.post(f"/admin/teachers/{teacher_id}/toggle-status", json={
            "teacher_id": teacher_id,
            "is_active": False
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_reset_password(self, client, admin_headers):
        create = client.post("/admin/teachers/", json={
            "email": "reset@test.com",
            "full_name": "Сброс Пароля",
            "role": "teacher"
        }, headers=admin_headers)
        teacher_id = create.json()["teacher_id"]
        resp = client.post(f"/admin/teachers/{teacher_id}/reset-password", json={
            "teacher_id": teacher_id,
            "new_password": "NewPass123!"
        }, headers=admin_headers)
        assert resp.status_code == 200


class TestStatistics:
    def test_get_statistics(self, client, admin_headers):
        resp = client.get("/admin/statistics/", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_teachers" in data
        assert "total_students" in data
        assert "active_teachers" in data


class TestBulkImport:
    def _make_group(self, client, admin_headers, group_name="ИС-21", course_year=2):
        resp = client.post("/groups/", json={"group_name": group_name, "course_year": course_year},
                           headers=admin_headers)
        return resp

    def test_bulk_import_dry_run(self, client, admin_headers):
        self._make_group(client, admin_headers)
        resp = client.post("/admin/students/bulk-import", json={
            "rows": [{"last_name": "Иванов", "first_name": "Иван", "group_name": "ИС-21"}],
            "dry_run": True
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["imported_count"] == 1
        assert resp.json()["error_count"] == 0

    def test_bulk_import_unknown_group(self, client, admin_headers):
        resp = client.post("/admin/students/bulk-import", json={
            "rows": [{"last_name": "Иванов", "first_name": "Иван", "group_name": "НЕСУЩЕСТВУЮЩАЯ"}],
            "dry_run": True
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["error_count"] == 1

    def test_bulk_import_saves(self, client, admin_headers):
        self._make_group(client, admin_headers, "ИС-22")
        resp = client.post("/admin/students/bulk-import", json={
            "rows": [{"last_name": "Петров", "first_name": "Пётр", "group_name": "ИС-22"}],
            "dry_run": False
        }, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["imported_count"] == 1


class TestStudentRecovery:
    def test_restore_student(self, client, admin_headers, db):
        import models
        group = models.StudentGroup(group_name="Тест-1", course_year=1)
        db.add(group)
        db.commit()
        student = models.Student(full_name="Удалённый Студент", group_id=group.id, is_deleted=True)
        db.add(student)
        db.commit()

        resp = client.post(f"/admin/students/{student.id}/restore", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_get_deleted_students(self, client, admin_headers, db):
        import models
        group = models.StudentGroup(group_name="Тест-2", course_year=1)
        db.add(group)
        db.commit()
        student = models.Student(full_name="Удалённый 2", group_id=group.id, is_deleted=True)
        db.add(student)
        db.commit()

        resp = client.get("/admin/students/deleted", headers=admin_headers)
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert student.id in ids
