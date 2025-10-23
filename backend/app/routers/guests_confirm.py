# File: backend/app/routers/guests_confirm.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
import os
import logging # Thêm logging

from .. import models, schemas
from ..deps import get_db
from ..auth import require_roles, get_current_user
# Cập nhật import: Thêm hàm gửi sự kiện lưu trữ
from ..utils.notifications import run_pending_list_notification, send_event_to_archive_background
from ..models import get_local_time

router = APIRouter(prefix="/guests", tags=["guests-confirm"])
logger = logging.getLogger(__name__) # Khởi tạo logger

@router.post("/{guest_id}/confirm-in", dependencies=[Depends(require_roles("admin","manager","guard","staff"))])
def confirm_in(guest_id: int, bg: BackgroundTasks, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Load cả thông tin người đăng ký gốc để dùng cho thông báo lưu trữ
    guest = db.query(models.Guest).options(joinedload(models.Guest.registered_by)).get(guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    guest_updated = False
    if guest.status != "checked_in":
        guest.status = "checked_in"
        guest.check_in_time = get_local_time()
        db.commit()
        db.refresh(guest)
        guest_updated = True
        logger.info(f"User {user.username} confirmed check-in for guest ID {guest_id} ({guest.full_name}).")
    else:
        logger.info(f"Guest ID {guest_id} ({guest.full_name}) already checked in. No status change.")

    # Chỉ gửi thông báo nếu trạng thái thực sự thay đổi
    if guest_updated:
        # --- THÊM MỚI: Gửi sự kiện xác nhận vào cổng đến kênh lưu trữ ---
        bg.add_task(send_event_to_archive_background, guest.id, "Xác nhận vào cổng", user.id)
        # --- KẾT THÚC THÊM MỚI ---

        # Kích hoạt cập nhật danh sách chờ trên kênh chính
        bg.add_task(run_pending_list_notification)

    # Vẫn trả về thông tin khách dù trạng thái có thay đổi hay không
    return schemas.GuestRead.model_validate(guest)
