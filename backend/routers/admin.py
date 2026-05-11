"""
Роутер для администраторских функций.
Только пользователи с ролью 'admin' имеют доступ к этим эндпоинтам.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from typing import List, Optional
import models
import schemas
import crud
import logging
import json
from routers.dependencies import get_db, get_current_admin, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ========== УПРАВЛЕНИЕ ПРЕПОДАВАТЕЛЯМИ ==========

@router.post("/teachers/", response_model=dict)
def create_teacher(
    teacher_data: schemas.TeacherCreateByAdmin,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """
    Создает новый аккаунт преподавателя.
    Возвращает данные учителя и ВРЕМЕННЫЙ пароль.
    """
    result = crud.create_teacher_by_admin(db, teacher_data)
    if result is None:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    teacher, temp_password = result

    # Логируем действие
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="create",
        entity_type="teacher",
        entity_id=teacher.id,
        description=f"Создан аккаунт преподавателя {teacher.full_name} ({teacher.email})",
        new_values=f"role={teacher.role}, is_active={teacher.is_active}",
        ip_address=get_client_ip(req),
    )
    
    return {
        "message": f"Преподаватель {teacher.full_name} создан",
        "teacher_id": teacher.id,
        "email": teacher.email,
        "temporary_password": temp_password,
        "note": "⚠️ Сообщите преподавателю временный пароль. Он должен его изменить при первом входе."
    }


@router.get("/teachers/", response_model=List[schemas.TeacherResponse])
def get_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Получить список всех преподавателей"""
    teachers = crud.get_all_teachers(db, skip=skip, limit=limit)
    
    return [
        schemas.TeacherResponse(
            id=t.id,
            email=t.email,
            full_name=t.full_name,
            role=t.role,
            is_active=t.is_active,
            last_login=t.last_login.isoformat() if t.last_login else None,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat()
        )
        for t in teachers
    ]


@router.get("/teachers/{teacher_id}", response_model=schemas.TeacherResponse)
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Получить информацию о конкретном преподавателе"""
    teacher = crud.get_teacher_by_id(db, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    
    return schemas.TeacherResponse(
        id=teacher.id,
        email=teacher.email,
        full_name=teacher.full_name,
        role=teacher.role,
        is_active=teacher.is_active,
        last_login=teacher.last_login.isoformat() if teacher.last_login else None,
        created_at=teacher.created_at.isoformat(),
        updated_at=teacher.updated_at.isoformat()
    )


@router.put("/teachers/{teacher_id}", response_model=schemas.TeacherResponse)
def update_teacher(
    teacher_id: int,
    teacher_data: schemas.TeacherUpdate,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Обновить информацию преподавателя"""
    teacher = crud.update_teacher_by_admin(db, teacher_id, teacher_data)
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден или email занят")

    # Логируем действие
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="update",
        entity_type="teacher",
        entity_id=teacher_id,
        description=f"Обновлены данные преподавателя",
        new_values=str(teacher_data.model_dump(exclude_unset=True)),
        ip_address=get_client_ip(req),
    )
    
    return schemas.TeacherResponse(
        id=teacher.id,
        email=teacher.email,
        full_name=teacher.full_name,
        role=teacher.role,
        is_active=teacher.is_active,
        last_login=teacher.last_login.isoformat() if teacher.last_login else None,
        created_at=teacher.created_at.isoformat(),
        updated_at=teacher.updated_at.isoformat()
    )


@router.post("/teachers/{teacher_id}/reset-password")
def reset_password(
    teacher_id: int,
    request: schemas.ResetPasswordRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Сброс пароля преподавателя"""
    if request.teacher_id != teacher_id:
        raise HTTPException(status_code=400, detail="ID преподавателя не совпадает")

    teacher = crud.reset_teacher_password(db, teacher_id, request.new_password)
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    # Логируем действие
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="reset_password",
        entity_type="teacher",
        entity_id=teacher_id,
        description=f"Сброс пароля преподавателя {teacher.full_name}",
        ip_address=get_client_ip(req),
    )
    
    return {"message": f"Пароль преподавателя {teacher.full_name} успешно сброшен"}


@router.post("/teachers/{teacher_id}/toggle-status")
def toggle_teacher_status(
    teacher_id: int,
    request: schemas.BlockTeacherRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Блокировать/разблокировать преподавателя"""
    if request.teacher_id != teacher_id:
        raise HTTPException(status_code=400, detail="ID преподавателя не совпадает")

    teacher = crud.block_teacher(db, teacher_id, request.is_active)
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    status_text = "разблокирован" if request.is_active else "заблокирован"

    # Логируем действие
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="block_teacher" if not request.is_active else "unblock_teacher",
        entity_type="teacher",
        entity_id=teacher_id,
        description=f"Преподаватель {teacher.full_name} {status_text}",
        ip_address=get_client_ip(req),
    )
    
    return {
        "message": f"Преподаватель {teacher.full_name} {status_text}",
        "teacher_id": teacher.id,
        "is_active": teacher.is_active
    }


# ========== ЛОГИ АУДИТА ==========

@router.get("/audit-logs/", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    entity_type: Optional[str] = Query(None),
    admin_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Получить логи аудита с фильтрацией"""
    logs = crud.get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
        entity_type=entity_type,
        admin_id=admin_id,
        action=action
    )
    
    return [
        schemas.AuditLogResponse(
            id=log.id,
            admin_id=log.admin_id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            description=log.description,
            old_values=log.old_values,
            new_values=log.new_values,
            ip_address=log.ip_address,
            created_at=log.created_at.isoformat()
        )
        for log in logs
    ]


# ========== СТАТИСТИКА ==========

@router.get("/statistics/", response_model=schemas.SchoolStatistics)
def get_statistics(
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Получить статистику по всей школе"""
    stats = crud.get_school_statistics(db)
    return schemas.SchoolStatistics(**stats)


# ========== УПРАВЛЕНИЕ КУРСАМИ И ГРУППАМИ ==========

@router.post("/groups/promote-year/", response_model=schemas.GroupPromotionResponse)
def promote_groups(
    request: schemas.GroupPromotionRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Перевести группы на следующий курс (для начала новый учебный год)"""
    if not request.group_ids:
        raise HTTPException(status_code=400, detail="Список групп пуст")

    promoted, failed = crud.promote_groups_to_next_year(db, request.group_ids)

    client_ip = get_client_ip(req)
    # Логируем действие
    for i in range(len(request.group_ids)):
        crud.create_audit_log(
            db=db,
            admin_id=current_admin.id,
            action="promote_group",
            entity_type="group",
            entity_id=request.group_ids[i],
            description=f"Группа переведена на следующий курс",
            ip_address=client_ip,
        )
    
    return schemas.GroupPromotionResponse(
        promoted_count=len(promoted),
        failed_count=len(failed),
        details=promoted + failed
    )


# ========== ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ==========

@router.get("/info/")
def admin_info(
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Информация об администраторе и доступных действиях"""
    return {
        "admin_name": current_admin.full_name,
        "admin_email": current_admin.email,
        "admin_id": current_admin.id,
        "available_actions": [
            "Создание аккаунтов преподавателей",
            "Сброс пароля преподавателей",
            "Блокировка/разблокировка преподавателей",
            "Просмотр логов аудита",
            "Просмотр статистики по школе",
            "Перевод групп на следующий курс",
            "Bulk import студентов",
            "Восстановление удаленных студентов"
        ],
        "documentation": "https://api.example.com/docs"
    }


# ========== УПРАВЛЕНИЕ СТУДЕНТАМИ ==========

@router.post("/students/bulk-import", response_model=schemas.StudentBulkImportResult)
def bulk_import_students(
    request: schemas.StudentBulkImportRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """
    Bulk импорт студентов из CSV
    
    Формат: last_name, first_name, group_name, student_id (опционально)
    
    Параметры:
    - dry_run: если true, только проверяет валидность без сохранения
    
    Возвращает:
    - imported_count: количество успешно импортированных
    - error_count: количество ошибок
    - errors: список ошибок с указанием строк
    """
    logger.info(f"Начало bulk import студентов. Админ: {current_admin.email}, Строк: {len(request.rows)}")
    errors: list[schemas.StudentBulkImportError] = []
    imported_students = []
    
    # Валидация и сбор студентов
    for row_num, row in enumerate(request.rows, start=1):
        try:
            # Проверяем существование группы
            group = db.query(models.StudentGroup).filter(
                models.StudentGroup.group_name == row.group_name
            ).first()
            
            if group is None:
                errors.append(schemas.StudentBulkImportError(
                    row_number=row_num,
                    last_name=row.last_name,
                    first_name=row.first_name,
                    group_name=row.group_name,
                    error=f"Группа '{row.group_name}' не найдена"
                ))
                logger.warning(f"Строка {row_num}: Группа '{row.group_name}' не найдена")
                continue
            
            # Проверяем дублирование (студент с таким именем и группой)
            existing = db.query(models.Student).filter(
                models.Student.full_name == f"{row.first_name} {row.last_name}",
                models.Student.group_id == group.id,
                models.Student.is_deleted == False
            ).first()
            
            if existing is not None:
                errors.append(schemas.StudentBulkImportError(
                    row_number=row_num,
                    last_name=row.last_name,
                    first_name=row.first_name,
                    group_name=row.group_name,
                    error=f"Студент '{row.first_name} {row.last_name}' уже существует в группе '{row.group_name}'"
                ))
                logger.warning(f"Строка {row_num}: Дублирование студента '{row.first_name} {row.last_name}'")
                continue
            
            # Если валидация прошла, добавляем в список для импорта
            imported_students.append({
                "full_name": f"{row.first_name} {row.last_name}",
                "group_id": group.id,
                "row_num": row_num
            })
        
        except Exception as e:
            errors.append(schemas.StudentBulkImportError(
                row_number=row_num,
                last_name=row.last_name,
                first_name=row.first_name,
                group_name=row.group_name,
                error=f"Неожиданная ошибка: {str(e)}"
            ))
            logger.error(f"Строка {row_num}: Неожиданная ошибка: {str(e)}")
    
    # Если есть ошибки и не dry_run - откатываем всё
    if errors and not request.dry_run:
        logger.warning(f"Импорт отменён из-за {len(errors)} ошибок")
        return schemas.StudentBulkImportResult(
            success=False,
            imported_count=0,
            error_count=len(errors),
            errors=errors,
            message=f"Импорт отменён из-за {len(errors)} ошибок. Исправьте ошибки и попробуйте снова."
        )
    
    # Если dry_run=true, только возвращаем результаты без сохранения
    if request.dry_run:
        logger.info(f"[DRY RUN] Готово к импорту: {len(imported_students)} студентов, {len(errors)} ошибок")
        return schemas.StudentBulkImportResult(
            success=True,
            imported_count=len(imported_students),
            error_count=len(errors),
            errors=errors,
            message=f"[DRY RUN] Готово к импорту: {len(imported_students)} студентов, {len(errors)} ошибок"
        )
    
    # Сохраняем студентов в БД (в одной транзакции)
    try:
        for student_data in imported_students:
            new_student = models.Student(
                full_name=student_data["full_name"],
                group_id=student_data["group_id"],
                is_deleted=False
            )
            db.add(new_student)
        
        db.commit()
        
        # Логируем действие админа
        crud.create_audit_log(
            db=db,
            admin_id=current_admin.id,
            action="bulk_import",
            entity_type="student",
            entity_id=None,
            description=f"Bulk импорт студентов",
            new_values=f"imported={len(imported_students)}, errors={len(errors)}",
            ip_address=get_client_ip(req),
        )
        
        logger.info(f" Успешно импортировано {len(imported_students)} студентов")
        
        return schemas.StudentBulkImportResult(
            success=True,
            imported_count=len(imported_students),
            error_count=len(errors),
            errors=errors,
            message=f" Успешно импортировано {len(imported_students)} студентов"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f" Ошибка при сохранении в БД: {str(e)}")
        return schemas.StudentBulkImportResult(
            success=False,
            imported_count=0,
            error_count=len(errors) + 1,
            errors=errors,
            message=f" Ошибка при сохранении в БД: {str(e)}"
        )


@router.get("/students/deleted", response_model=List[schemas.DeletedStudent])
def get_deleted_students(
    group_id: int = Query(None),
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Получить список удаленных студентов для восстановления"""
    deleted_students = crud.get_deleted_students(db, group_id=group_id)
    
    result = []
    for student in deleted_students:
        result.append(schemas.DeletedStudent(
            id=student.id,
            full_name=student.full_name,
            group_id=student.group_id,
            group_name=student.group.group_name
        ))
    
    return result


@router.post("/students/{student_id}/restore", response_model=schemas.StudentRestoreResponse)
def restore_student(
    student_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Восстановить удаленного студента из soft-delete"""
    logger.info(f"Попытка восстановить студента ID={student_id}")

    student = crud.restore_student(db, student_id)

    if student is None:
        logger.warning(f"Студент ID={student_id} не найден")
        raise HTTPException(status_code=404, detail="Студент не найден")

    # Логируем действие
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="restore",
        entity_type="student",
        entity_id=student_id,
        description=f"Студент {student.full_name} восстановлен",
        new_values=f"is_deleted=False",
        ip_address=get_client_ip(req),
    )
    
    logger.info(f" Студент '{student.full_name}' (ID={student_id}) успешно восстановлен")
    
    return schemas.StudentRestoreResponse(
        success=True,
        student_id=student.id,
        full_name=student.full_name,
        message=f" Студент '{student.full_name}' успешно восстановлен"
    )


@router.get("/students/{student_id}/delete-impact")
def hard_delete_impact(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin),
):
    """Подсчитать что именно будет удалено вместе со студентом (для confirm-диалога)."""
    student = db.query(models.Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    grades_count = db.query(models.GradeRecord).filter_by(student_id=student_id).count()
    return {
        "student_name": student.full_name,
        "grades_count": grades_count,
    }


@router.delete("/students/{student_id}")
def hard_delete_student(
    student_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Окончательно удалить студента из базы данных (необратимо)"""
    student = db.query(models.Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    name = f"{student.full_name}"
    grades_deleted = db.query(models.GradeRecord).filter_by(student_id=student_id).delete()
    db.delete(student)
    db.commit()
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="delete",
        entity_type="student",
        entity_id=student_id,
        description=f"Жёсткое удаление студента {name} (оценок удалено: {grades_deleted})",
        ip_address=get_client_ip(req),
    )
    return {"ok": True, "grades_deleted": grades_deleted}


@router.post("/students/", response_model=schemas.Student)
def create_single_student(
    data: schemas.StudentCreate,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin),
):
    """Создать одного студента в группе (быстрое добавление, в обход CSV-импорта)."""
    full_name = data.full_name.strip()
    if not full_name:
        raise HTTPException(status_code=400, detail="ФИО не может быть пустым")

    group = db.query(models.StudentGroup).filter_by(id=data.group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")

    existing = db.query(models.Student).filter(
        models.Student.full_name == full_name,
        models.Student.group_id == data.group_id,
        models.Student.is_deleted == False,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Студент «{full_name}» уже есть в этой группе")

    student = models.Student(full_name=full_name, group_id=data.group_id, is_deleted=False)
    db.add(student)
    db.commit()
    db.refresh(student)

    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="create",
        entity_type="student",
        entity_id=student.id,
        description=f"Добавлен студент {full_name} в группу {group.group_name}",
        ip_address=get_client_ip(req),
    )
    return student


@router.post("/students/{student_id}/soft-delete")
def soft_delete_student(
    student_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Перемещает студента в корзину (is_deleted=True), оценки сохраняются."""
    student = db.query(models.Student).filter_by(id=student_id, is_deleted=False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден или уже удалён")
    student.is_deleted = True
    db.commit()
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="soft_delete",
        entity_type="student",
        entity_id=student_id,
        description=f"Студент {student.full_name} перемещён в корзину",
        ip_address=get_client_ip(req),
    )
    return {"ok": True, "message": f"{student.full_name} перемещён в корзину"}


# ========== УПРАВЛЕНИЕ НАЗНАЧЕНИЯМИ ==========

@router.get("/assignments/", response_model=List[schemas.TeachingAssignmentWithTeacher])
def get_assignments(
    teacher_id: Optional[int] = Query(None),
    group_id: Optional[int] = Query(None),
    academic_period_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Получить все назначения преподавателей"""
    assignments = crud.get_all_teaching_assignments(
        db, teacher_id=teacher_id, group_id=group_id, academic_period_id=academic_period_id
    )
    return [
        schemas.TeachingAssignmentWithTeacher(
            id=a.id,
            teacher_id=a.teacher_id,
            teacher_name=a.teacher.full_name,
            subject=schemas.SubjectShort(id=a.subject.id, name=a.subject.name),
            group=schemas.GroupShort(id=a.group.id, group_name=a.group.group_name, course_year=a.group.course_year),
            academic_period=schemas.AcademicPeriodShort(
                id=a.academic_period.id,
                name=a.academic_period.name,
                academic_year=a.academic_period.academic_year,
                semester_number=a.academic_period.semester_number,
            ),
        )
        for a in assignments
    ]


@router.post("/assignments/", response_model=schemas.TeachingAssignmentWithTeacher)
def create_assignment(
    data: schemas.TeachingAssignmentAdminCreate,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Создать назначение: преподаватель → предмет → группа → период"""
    teacher = crud.get_teacher_by_id(db, data.teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    group = crud.get_group_by_id(db, data.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    period = crud.get_academic_period_by_id(db, data.academic_period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Учебный период не найден")

    subject = crud.find_or_create_subject(db, data.teacher_id, data.subject_name.strip())

    existing = crud.get_teaching_assignment_by_scope(
        db,
        teacher_id=data.teacher_id,
        subject_id=subject.id,
        group_id=data.group_id,
        academic_period_id=data.academic_period_id,
    )
    if existing:
        raise HTTPException(status_code=400, detail="Такое назначение уже существует")

    assignment = crud.create_teaching_assignment(
        db,
        teacher_id=data.teacher_id,
        teaching_assignment=schemas.TeachingAssignmentCreate(
            subject_id=subject.id,
            group_id=data.group_id,
            academic_period_id=data.academic_period_id,
        ),
    )

    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="create",
        entity_type="teaching_assignment",
        entity_id=assignment.id,
        description=f"Назначен {teacher.full_name} → {subject.name} → {group.group_name}",
        ip_address=get_client_ip(req),
    )

    return schemas.TeachingAssignmentWithTeacher(
        id=assignment.id,
        teacher_id=assignment.teacher_id,
        teacher_name=teacher.full_name,
        subject=schemas.SubjectShort(id=subject.id, name=subject.name),
        group=schemas.GroupShort(id=group.id, group_name=group.group_name, course_year=group.course_year),
        academic_period=schemas.AcademicPeriodShort(
            id=period.id,
            name=period.name,
            academic_year=period.academic_year,
            semester_number=period.semester_number,
        ),
    )


@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Удалить назначение"""
    assignment = (
        db.query(models.TeachingAssignment)
        .options(
            joinedload(models.TeachingAssignment.teacher),
            joinedload(models.TeachingAssignment.subject),
            joinedload(models.TeachingAssignment.group),
        )
        .filter_by(id=assignment_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Назначение не найдено")

    desc = f"Удалено назначение: {assignment.teacher.full_name} → {assignment.subject.name} → {assignment.group.group_name}"

    try:
        # Raw SQL — обходим ORM relationship handling (он пытается SET NULL на NOT NULL колонках)
        db.execute(
            text("""
                DELETE so FROM schedule_occurrences so
                INNER JOIN schedule_templates st ON so.schedule_template_id = st.id
                WHERE st.teaching_assignment_id = :aid
            """),
            {"aid": assignment_id}
        )
        db.execute(
            text("DELETE FROM schedule_templates WHERE teaching_assignment_id = :aid"),
            {"aid": assignment_id}
        )
        db.execute(
            text("DELETE FROM teaching_assignments WHERE id = :aid"),
            {"aid": assignment_id}
        )
        db.commit()
    except IntegrityError as e:
        db.rollback()
        logger.error("Ошибка удаления назначения %s: %s", assignment_id, e)
        raise HTTPException(status_code=409, detail="Невозможно удалить назначение: есть связанные данные")

    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="delete",
        entity_type="teaching_assignment",
        entity_id=assignment_id,
        description=desc,
        ip_address=get_client_ip(req),
    )
    return {"ok": True}


# ========== УПРАВЛЕНИЕ РАСПИСАНИЕМ ==========

@router.get("/schedule-templates/", response_model=List[schemas.ScheduleTemplate])
def get_schedule_templates(
    teaching_assignment_id: int = Query(...),
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Получить шаблоны расписания для назначения"""
    return (
        db.query(models.ScheduleTemplate)
        .filter(models.ScheduleTemplate.teaching_assignment_id == teaching_assignment_id)
        .order_by(models.ScheduleTemplate.day_of_week, models.ScheduleTemplate.lesson_number)
        .all()
    )


@router.post("/schedule-templates/", response_model=schemas.ScheduleTemplate)
def create_schedule_template(
    data: schemas.ScheduleTemplateCreate,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Создать шаблон расписания для любого назначения"""
    assignment = db.query(models.TeachingAssignment).filter_by(id=data.teaching_assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    existing = crud.get_schedule_template_by_slot(
        db,
        teaching_assignment_id=data.teaching_assignment_id,
        day_of_week=data.day_of_week,
        lesson_number=data.lesson_number,
    )
    if existing:
        raise HTTPException(status_code=400, detail="Шаблон для этого слота уже существует")
    template = crud.create_schedule_template(db, data)
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="create",
        entity_type="schedule_template",
        entity_id=template.id,
        description=f"Создан шаблон расписания: день {data.day_of_week}, урок {data.lesson_number}",
        ip_address=get_client_ip(req),
    )
    return template


@router.delete("/schedule-templates/{template_id}")
def delete_schedule_template(
    template_id: int,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Удалить шаблон расписания"""
    template = db.query(models.ScheduleTemplate).filter_by(id=template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    db.delete(template)
    db.commit()
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="delete",
        entity_type="schedule_template",
        entity_id=template_id,
        description="Удалён шаблон расписания",
        ip_address=get_client_ip(req),
    )
    return {"ok": True}


@router.post("/lessons/generate/preview/", response_model=schemas.LessonGenerationPreviewResponse)
def admin_preview_lessons(
    payload: schemas.LessonGenerationRequest,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Предпросмотр генерируемых уроков (администратор)"""
    if payload.teaching_assignment_id is None:
        raise HTTPException(status_code=400, detail="Укажите teaching_assignment_id")
    assignment = db.query(models.TeachingAssignment).filter_by(id=payload.teaching_assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    templates = crud.get_schedule_templates_for_generation(
        db=db,
        teacher_id=assignment.teacher_id,
        academic_period_id=payload.academic_period_id,
        teaching_assignment_id=payload.teaching_assignment_id,
    )
    if not templates:
        raise HTTPException(status_code=400, detail="Нет шаблонов расписания для предпросмотра")
    return crud.preview_lessons_from_templates(
        db=db,
        templates=templates,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )


@router.post("/lessons/generate/", response_model=schemas.LessonGenerationResponse)
def admin_generate_lessons(
    payload: schemas.LessonGenerationRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Сгенерировать уроки из шаблонов расписания (администратор)"""
    if payload.teaching_assignment_id is None:
        raise HTTPException(status_code=400, detail="Укажите teaching_assignment_id")
    assignment = db.query(models.TeachingAssignment).filter_by(id=payload.teaching_assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    templates = crud.get_schedule_templates_for_generation(
        db=db,
        teacher_id=assignment.teacher_id,
        academic_period_id=payload.academic_period_id,
        teaching_assignment_id=payload.teaching_assignment_id,
    )
    if not templates:
        raise HTTPException(status_code=400, detail="Нет шаблонов расписания для генерации")
    result = crud.generate_lessons_from_templates(
        db=db,
        templates=templates,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="generate_lessons",
        entity_type="lesson",
        entity_id=None,
        description=f"Сгенерировано {result['generated_count']} уроков для назначения #{payload.teaching_assignment_id}",
        ip_address=get_client_ip(req),
    )
    return result


# ========== УПРАВЛЕНИЕ УВЕДОМЛЕНИЯМИ ==========

@router.post("/notifications/send", response_model=schemas.NotificationSendResponse)
def send_notification(
    notification_request: schemas.NotificationSendRequest,
    req: Request,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """
    Отправляет уведомление преподавателям.
    
    Поддерживаемые типы уведомлений:
    - announcement: Важное объявление
    - reminder: Напоминание о дедлайне
    - completion: Завершение задачи
    - technical: Техническое уведомление
    - other: Прочее
    """
    logger.info(f"Попытка отправить уведомление '{notification_request.title}' на {len(notification_request.recipient_teacher_ids)} адресов")
    
    # Проверяем, что выбраны получатели
    if not notification_request.recipient_teacher_ids:
        logger.warning("Попытка отправить уведомление без получателей")
        raise HTTPException(status_code=400, detail="Не выбраны получатели уведомления")
    
    # Проверяем, что все указанные преподаватели существуют
    recipients = db.query(models.Teacher).filter(
        models.Teacher.id.in_(notification_request.recipient_teacher_ids)
    ).all()
    
    if len(recipients) != len(notification_request.recipient_teacher_ids):
        logger.warning(f"Некоторые преподаватели не найдены. Ожидалось {len(notification_request.recipient_teacher_ids)}, найдено {len(recipients)}")
        raise HTTPException(status_code=400, detail="Некоторые преподаватели не найдены")
    
    # Логируем отправку уведомления
    recipients_emails = [r.email for r in recipients]
    logger.info(
        f"Уведомление '{notification_request.title}' отправлено на адреса: {', '.join(recipients_emails)}"
    )
    
    # Сохраняем уведомление в истории
    notification = models.Notification(
        admin_id=current_admin.id,
        notification_type=notification_request.notification_type,
        title=notification_request.title,
        message=notification_request.message,
        recipient_ids=json.dumps(notification_request.recipient_teacher_ids),
        recipients_count=len(recipients),
    )
    db.add(notification)
    db.commit()

    # Создаем запись в логе аудита
    crud.create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="send_notification",
        entity_type="notification",
        entity_id=notification.id,
        description=f"Отправлено уведомление '{notification_request.title}' типа {notification_request.notification_type}",
        new_values=f"type={notification_request.notification_type}, recipients={len(recipients)}",
        ip_address=get_client_ip(req),
    )

    return schemas.NotificationSendResponse(
        success=True,
        message=f"Уведомление успешно отправлено {len(recipients)} преподавателям",
        recipients_count=len(recipients)
    )


@router.get("/notifications/", response_model=List[schemas.NotificationRecord])
def get_notification_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Получить историю отправленных уведомлений"""
    notifications = (
        db.query(models.Notification)
        .order_by(models.Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        schemas.NotificationRecord(
            id=n.id,
            admin_id=n.admin_id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            recipients_count=n.recipients_count,
            created_at=n.created_at.isoformat(),
        )
        for n in notifications
    ]
