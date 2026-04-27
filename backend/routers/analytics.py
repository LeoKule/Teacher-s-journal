from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from routers.dependencies import get_db, get_current_teacher
import models

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/group/{group_id}", response_model=schemas.GroupAnalytics)
def get_group_analytics(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: models.Teacher = Depends(get_current_teacher),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ только для администратора")
    result = crud.get_group_analytics(db, group_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Группа не найдена")
    return result


@router.get("/groups", response_model=list[schemas.GroupShort])
def list_groups_for_analytics(
    db: Session = Depends(get_db),
    current_user: models.Teacher = Depends(get_current_teacher),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ только для администратора")
    return crud.get_groups(db)
