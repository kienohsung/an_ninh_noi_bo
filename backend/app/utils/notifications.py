# File: backend/app/utils/notifications.py
# Purpose: Telegram notifications (text + photos) with safe fallbacks
from __future__ import annotations
import os
import requests
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

# SỬA LỖI: Thay đổi đường dẫn import từ "." thành ".." để trỏ ra thư mục app
from ..database import SessionLocal
from .. import models
from ..models import get_local_time
from ..config import settings

# Dữ liệu đã được nạp từ .env vào settings trong main.py
TELEGRAM_ENABLED = settings.NOTIFY_TELEGRAM_ENABLED
TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID = settings.TELEGRAM_CHAT_ID

# --- CẢI TIẾN: Lưu trữ ID tin nhắn cuối cùng ---
# Lưu file ID trong thư mục backend, bên ngoài thư mục app
LAST_MESSAGE_ID_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "telegram_last_message_id.txt"))
logger = logging.getLogger(__name__)

def _bot_api(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"

def can_send() -> bool:
    return TELEGRAM_ENABLED and bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_CHAT_ID)

# --- CẢI TIẾN: Các hàm quản lý ID tin nhắn ---
def _save_last_message_id(message_id: int):
    """Lưu ID của tin nhắn đã gửi vào file."""
    try:
        with open(LAST_MESSAGE_ID_FILE, "w") as f:
            f.write(str(message_id))
    except Exception as e:
        logger.error(f"Không thể lưu ID tin nhắn Telegram cuối cùng: {e}")

def _read_last_message_id() -> Optional[int]:
    """Đọc ID của tin nhắn cuối cùng từ file."""
    if not os.path.exists(LAST_MESSAGE_ID_FILE):
        return None
    try:
        with open(LAST_MESSAGE_ID_FILE, "r") as f:
            content = f.read().strip()
            return int(content) if content.isdigit() else None
    except Exception as e:
        logger.error(f"Không thể đọc ID tin nhắn Telegram cuối cùng: {e}")
        return None

def delete_telegram_message(message_id: int):
    """Gửi yêu cầu xóa một tin nhắn cụ thể."""
    if not can_send() or not message_id:
        return
    try:
        logger.info(f"Đang yêu cầu Telegram xóa tin nhắn ID: {message_id}")
        resp = requests.post(_bot_api("deleteMessage"), json={
            "chat_id": TELEGRAM_CHAT_ID,
            "message_id": message_id
        }, timeout=10)
        
        # Ghi log chi tiết phản hồi từ Telegram
        response_json = resp.json()
        if not response_json.get("ok"):
             logger.warning(f"Không thể xóa tin nhắn Telegram {message_id}. Phản hồi từ Telegram: {resp.text}")
        else:
             logger.info(f"Đã xóa thành công tin nhắn ID: {message_id}")
    except Exception as e:
        logger.error(f"Ngoại lệ khi xóa tin nhắn Telegram {message_id}: {e}")

# --- Hàm send_telegram_message giữ nguyên ---
def send_telegram_message(text: str) -> dict:
    """Gửi một tin nhắn văn bản. Trả về JSON phản hồi hoặc một stub nếu bị vô hiệu hóa."""
    if not can_send():
        return {"ok": False, "skipped": True, "reason": "TELEGRAM_DISABLED_OR_MISSING_ENV"}
    try:
        resp = requests.post(_bot_api("sendMessage"), json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

# --- Hàm format_pending_list_for_telegram giữ nguyên ---
def format_pending_list_for_telegram(pending_guests: List[models.Guest]) -> str:
    """Định dạng danh sách khách đang chờ thành một tin nhắn Telegram duy nhất."""
    now = get_local_time().strftime('%H:%M %d/%m/%Y')
    
    if not pending_guests:
        return f"✅ <b>Tất cả khách đã được xác nhận vào.</b>\n<i>(Cập nhật lúc {now})</i>"

    header = f"📢 <b>DANH SÁCH KHÁCH CHỜ VÀO ({len(pending_guests)} người)</b>\n<i>(Cập nhật lúc {now})</i>"
    
    lines = [header]
    for i, guest in enumerate(pending_guests, 1):
        full_name = guest.full_name.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        id_card = (guest.id_card_number or 'N/A').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        supplier_name = (guest.supplier_name or 'N/A').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
        license_plate = (guest.license_plate or 'N/A').replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')

        lines.append("--------------------")
        lines.append(f"{i} - <b>{full_name}</b> - {id_card}")
        lines.append(f"BKS: {license_plate} - {supplier_name}")
    
    lines.append("--------------------")
        
    message = "\n".join(lines)
    
    if len(message) > 4096:
        message = message[:4090] + "\n..."
        
    return message

# --- CẢI TIẾN: Bổ sung logging chi tiết vào toàn bộ quy trình ---
def run_pending_list_notification():
    """
    Hàm chạy nền: Xóa tin nhắn cũ, lấy danh sách khách đang chờ và gửi một thông báo tổng hợp mới.
    """
    logger.info("Bắt đầu tác vụ gửi thông báo danh sách chờ...")
    
    # 1. Đọc và xóa tin nhắn cũ
    last_message_id = _read_last_message_id()
    if last_message_id:
        logger.info(f"Đã tìm thấy ID tin nhắn cũ: {last_message_id}. Đang tiến hành xóa...")
        delete_telegram_message(last_message_id)
    else:
        logger.info("Không tìm thấy ID tin nhắn cũ, sẽ gửi tin nhắn mới.")

    # 2. Lấy danh sách mới và tạo nội dung
    db: Session = SessionLocal()
    try:
        pending_guests = db.query(models.Guest).filter(models.Guest.status == 'pending').order_by(models.Guest.created_at.asc()).all()
        logger.info(f"Tìm thấy {len(pending_guests)} khách đang chờ.")
        message_text = format_pending_list_for_telegram(pending_guests)
        
        # 3. Gửi tin nhắn mới
        logger.info("Đang gửi tin nhắn mới...")
        response_data = send_telegram_message(message_text)
        
        # 4. Lưu ID của tin nhắn mới nếu gửi thành công
        if response_data.get("ok"):
            new_message_id = response_data.get("result", {}).get("message_id")
            if new_message_id:
                logger.info(f"Gửi tin nhắn mới thành công. ID mới: {new_message_id}. Đang lưu lại...")
                _save_last_message_id(new_message_id)
            else:
                logger.warning("Gửi tin nhắn thành công nhưng không nhận được ID tin nhắn mới.")
        else:
            logger.error(f"Gửi tin nhắn mới thất bại. Phản hồi từ Telegram: {response_data}")

    finally:
        db.close()
    logger.info("Hoàn tất tác vụ gửi thông báo.")

