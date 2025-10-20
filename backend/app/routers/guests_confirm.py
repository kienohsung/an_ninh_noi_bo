# File: backend/app/routers/guests_confirm.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from .. import models, schemas
from ..deps import get_db
from ..auth import get_current_user, require_roles
from ..utils.notifications import send_telegram_message, send_telegram_photos

router = APIRouter(prefix="/guests", tags=["guests-confirm"])

def _format_guest_caption(guest: models.Guest, registered_by_name: str | None = None) -> str:
    lines = [
        f"Khách: {guest.full_name}",
        f"CCCD: {guest.id_card_number or ''}",
        f"Nhà cung cấp: {guest.supplier_name or ''}",
        f"Biển số: {guest.license_plate or ''}",
        f"Trạng thái: {guest.status}",
    ]
    if registered_by_name:
        lines.append(f"Đăng ký bởi: {registered_by_name}")
    if guest.check_in_time:
        lines.append(f"Vào lúc: {guest.check_in_time.isoformat()}")
    if guest.check_out_time:
        lines.append(f"Ra lúc: {guest.check_out_time.isoformat()}")
    lines.append(f"Tạo lúc: {guest.created_at.isoformat()}")
    return "\n".join(lines)

@router.post("/{guest_id}/confirm-in", dependencies=[Depends(require_roles("admin","manager","guard","staff"))])
def confirm_in(guest_id: int, bg: BackgroundTasks, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    guest = db.query(models.Guest).options(joinedload(models.Guest.images), joinedload(models.Guest.registered_by)).get(guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    # keep idempotent
    if guest.status != "checked_in":
        guest.status = "checked_in"
        guest.check_in_time = datetime.utcnow()
        db.commit(); db.refresh(guest)
    # notify Telegram (with all photos)
    caption = _format_guest_caption(guest, guest.registered_by.full_name if guest.registered_by else None)
    image_paths = []
    for img in (guest.images or []):
        # ensure absolute path
        image_paths.append(img.image_path if img.image_path.startswith("/") else None)
    # filter Nones
    image_paths = [p for p in image_paths if p]
    bg.add_task(send_telegram_photos, caption, image_paths)
    return schemas.GuestRead.model_validate(guest)
