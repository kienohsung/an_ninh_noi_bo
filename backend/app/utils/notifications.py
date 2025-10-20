# File: backend/app/utils/notifications.py
# Purpose: Telegram notifications (text + photos) with safe fallbacks
from __future__ import annotations
import os
import requests
from typing import List
from sqlalchemy.orm import Session

# SỬA LỖI: Thay đổi đường dẫn import từ "." thành ".." để trỏ ra thư mục app
from ..database import SessionLocal
from .. import models
from ..models import get_local_time

TELEGRAM_ENABLED = os.getenv("NOTIFY_TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def _bot_api(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"

def can_send() -> bool:
    return TELEGRAM_ENABLED and bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_CHAT_ID)

def send_telegram_message(text: str) -> dict:
    """Gửi một tin nhắn văn bản. Trả về JSON phản hồi hoặc một stub nếu bị vô hiệu hóa."""
    if not can_send():
        return {"ok": False, "skipped": True, "reason": "TELEGRAM_DISABLED_OR_MISSING_ENV"}
    try:
        resp = requests.post(_bot_api("sendMessage"), json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML" # Cho phép dùng thẻ HTML cơ bản
        }, timeout=10)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def format_pending_list_for_telegram(pending_guests: List[models.Guest]) -> str:
    """Định dạng danh sách khách đang chờ thành một tin nhắn Telegram duy nhất."""
    now = get_local_time().strftime('%H:%M %d/%m/%Y')
    
    if not pending_guests:
        return f"✅ <b>Tất cả khách đã được xác nhận vào.</b>\n<i>(Cập nhật lúc {now})</i>"

    header = f"📢 <b>DANH SÁCH KHÁCH CHỜ VÀO ({len(pending_guests)} người)</b>\n<i>(Cập nhật lúc {now})</i>"
    
    lines = [header]
    for i, guest in enumerate(pending_guests, 1):
        # Escape các ký tự HTML đặc biệt trong tên và thông tin để tránh lỗi parse_mode
        full_name = guest.full_name.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        id_card = (guest.id_card_number or 'N/A').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        supplier_name = (guest.supplier_name or 'N/A').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        license_plate = (guest.license_plate or 'N/A').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')

        lines.append("--------------------")
        lines.append(f"{i} - <b>{full_name}</b> - {id_card}")
        lines.append(f"BKS: {license_plate} - {supplier_name}")
    
    lines.append("--------------------")
        
    message = "\n".join(lines)
    
    # Giới hạn ký tự của Telegram là 4096. Cắt bớt nếu cần thiết.
    if len(message) > 4096:
        message = message[:4090] + "\n..."
        
    return message

def run_pending_list_notification():
    """
    Hàm chạy nền: Lấy toàn bộ khách đang chờ và gửi một thông báo tổng hợp.
    Hàm này tự tạo DB session riêng để đảm bảo an toàn trong môi trường đa luồng.
    """
    db: Session = SessionLocal()
    try:
        pending_guests = db.query(models.Guest).filter(models.Guest.status == 'pending').order_by(models.Guest.created_at.asc()).all()
        message = format_pending_list_for_telegram(pending_guests)
        send_telegram_message(message)
    finally:
        db.close()

