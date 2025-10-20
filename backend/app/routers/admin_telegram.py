# File: backend/app/routers/admin_telegram.py
from fastapi import APIRouter, Depends, HTTPException
from ..auth import require_roles
from ..utils.notifications import send_telegram_message
router = APIRouter(prefix="/admin/telegram", tags=["admin-telegram"])

@router.get("/test", dependencies=[Depends(require_roles("admin"))])
def test_message():
    res = send_telegram_message("🔔 Test: hệ thống đã kết nối Telegram thành công.")
    if not res.get("ok"):
        return {"ok": False, "detail": res}
    return {"ok": True, "detail": res}
