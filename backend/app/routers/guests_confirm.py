# File: backend/app/routers/guests_confirm.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
import os

from .. import models, schemas
from ..deps import get_db
from ..auth import require_roles, get_current_user
# Cập nhật import: chỉ dùng hàm chạy nền mới
from ..utils.notifications import run_pending_list_notification
from ..models import get_local_time

router = APIRouter(prefix="/guests", tags=["guests-confirm"])

@router.post("/{guest_id}/confirm-in", dependencies=[Depends(require_roles("admin","manager","guard","staff"))])
def confirm_in(guest_id: int, bg: BackgroundTasks, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    guest = db.query(models.Guest).options(joinedload(models.Guest.registered_by)).get(guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    if guest.status != "checked_in":
        guest.status = "checked_in"
        guest.check_in_time = get_local_time()
        db.commit()
        db.refresh(guest)
    
    # Kích hoạt gửi lại danh sách tổng hợp sau khi xác nhận
    bg.add_task(run_pending_list_notification)
    
    return schemas.GuestRead.model_validate(guest)

