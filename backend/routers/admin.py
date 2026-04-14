"""
Роутер для администраторских функций.
Только пользователи с ролью 'admin' имеют доступ к этим эндпоинтам.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
import crud
from routers.dependencies import get_db, get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


# ========== УПРАВЛЕНИЕ ПРЕПОДАВАТЕЛЯМИ ==========

@router.post("/teachers/", response_model=dict)
def create_teacher(
    teacher_data: schemas.TeacherCreateByAdmin,
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
        new_values=f"role={teacher.role}, is_active={teacher.is_active}"
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
        new_values=str(teacher_data.model_dump(exclude_unset=True))
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
        description=f"Сброс пароля преподавателя {teacher.full_name}"
    )
    
    return {"message": f"Пароль преподавателя {teacher.full_name} успешно сброшен"}


@router.post("/teachers/{teacher_id}/toggle-status")
def toggle_teacher_status(
    teacher_id: int,
    request: schemas.BlockTeacherRequest,
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
        description=f"Преподаватель {teacher.full_name} {status_text}"
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
    print(f"DEBUG: get_statistics called by admin: {current_admin.email}")
    stats = crud.get_school_statistics(db)
    print(f"DEBUG: stats = {stats}")
    return schemas.SchoolStatistics(**stats)


# ========== УПРАВЛЕНИЕ КУРСАМИ И ГРУППАМИ ==========

@router.post("/groups/promote-year/", response_model=schemas.GroupPromotionResponse)
def promote_groups(
    request: schemas.GroupPromotionRequest,
    db: Session = Depends(get_db),
    current_admin: models.Teacher = Depends(get_current_admin)
):
    """Перевести группы на следующий курс (для начала новый учебный год)"""
    if not request.group_ids:
        raise HTTPException(status_code=400, detail="Список групп пуст")
    
    promoted, failed = crud.promote_groups_to_next_year(db, request.group_ids)
    
    # Логируем действие
    for i in range(len(request.group_ids)):
        crud.create_audit_log(
            db=db,
            admin_id=current_admin.id,
            action="promote_group",
            entity_type="group",
            entity_id=request.group_ids[i],
            description=f"Группа переведена на следующий курс"
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
            "Перевод групп на следующий курс"
        ],
        "documentation": "https://api.example.com/docs"
    }
