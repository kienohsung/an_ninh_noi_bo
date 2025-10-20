# File: backend/app/utils/notifications.py
from __future__ import annotations
import os
import requests
from typing import Iterable, Optional
import pytz

TELEGRAM_ENABLED = os.getenv("NOTIFY_TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def _bot_api(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"

def can_send() -> bool:
    return TELEGRAM_ENABLED and bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_CHAT_ID)

def format_guest_for_telegram(guest, registered_by_name: str | None = None) -> str:
    """Formats guest details into a caption for Telegram, with Vietnamese status."""
    status_map = {
        "pending": "⏳ ĐANG CHỜ",
        "checked_in": "✅ ĐÃ VÀO",
        "checked_out": "🚪 ĐÃ RA"
    }
    status_vietnamese = status_map.get(guest.status, guest.status)

    title = "👤 Khách Mới Đăng Ký" if guest.status == 'pending' else "➡️ Xác Nhận Khách Vào"

    lines = [
        title,
        "--------------------------",
        f"Tên: {guest.full_name}",
        f"CCCD: {guest.id_card_number or 'N/A'}",
        f"NCC: {guest.supplier_name or 'N/A'}",
        f"Biển số: {guest.license_plate or 'N/A'}",
        f"Lý do: {guest.reason or 'N/A'}",
        f"Trạng thái: {status_vietnamese}",
    ]
    if registered_by_name:
        lines.append(f"Đăng ký bởi: {registered_by_name}")

    tz = pytz.timezone(os.getenv("TZ", "Asia/Bangkok"))
    
    if guest.created_at:
        created_local = guest.created_at.astimezone(tz)
        lines.append(f"Tạo lúc: {created_local.strftime('%H:%M %d/%m/%Y')}")

    if guest.check_in_time:
        check_in_local = guest.check_in_time.astimezone(tz)
        lines.append(f"Vào lúc: {check_in_local.strftime('%H:%M %d/%m/%Y')}")
        
    return "\n".join(lines)


def send_telegram_message(text: str) -> dict:
    """Send a plain text message. Returns response JSON or a stub if disabled."""
    if not can_send():
        return {"ok": False, "skipped": True, "reason": "TELEGRAM_DISABLED_OR_MISSING_ENV"}
    try:
        resp = requests.post(_bot_api("sendMessage"), json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text
        }, timeout=10)
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_telegram_photos(caption: str, file_paths: Iterable[str]) -> dict:
    """Send multiple photos (up to Telegram limits). If no files provided, fallback to text."""
    files = list(file_paths or [])
    if not files:
        return send_telegram_message(caption)
    if not can_send():
        return {"ok": False, "skipped": True, "reason": "TELEGRAM_DISABLED_OR_MISSING_ENV"}
    
    media = []
    form = {}
    for idx, fp in enumerate(files):
        field = f"photo{idx}"
        media.append({
            "type": "photo",
            "media": f"attach://{field}"
        })
        try:
            form[field] = open(fp, "rb")
        except Exception:
            pass # If file missing, skip it gracefully
    
    if not media:
        return send_telegram_message(caption)
        
    try:
        data = {"chat_id": TELEGRAM_CHAT_ID}
        
        # Telegram allows caption only on first media item in a group
        media[0]["caption"] = caption
        data["media"] = str(media).replace("'", '"')
        
        resp = requests.post(_bot_api("sendMediaGroup"), data=data, files=form, timeout=20)
        
        return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        # Ensure all file handles are closed
        for f in form.values():
            try:
                f.close()
            except Exception:
                pass

