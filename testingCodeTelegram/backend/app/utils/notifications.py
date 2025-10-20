# File: backend/app/utils/notifications.py
# Purpose: Telegram notifications (text + photos) with safe fallbacks
from __future__ import annotations
import os
import requests
from typing import Iterable, Optional

TELEGRAM_ENABLED = os.getenv("NOTIFY_TELEGRAM_ENABLED", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def _bot_api(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"

def can_send() -> bool:
    return TELEGRAM_ENABLED and bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_CHAT_ID)

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
    # Use 'sendMediaGroup' to send multiple images with a single caption
    # If only one image, we can use sendPhoto; but media group gives better UX for many.
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
            # If file missing, skip it gracefully
            pass
    if not media:
        return send_telegram_message(caption)
    try:
        data = {"chat_id": TELEGRAM_CHAT_ID, "media": str(media).replace("'", '"')}
        # Telegram allows caption only on first media
        if caption:
            # put caption into first element
            media[0]["caption"] = caption
            data["media"] = str(media).replace("'", '"')
        resp = requests.post(_bot_api("sendMediaGroup"), data=data, files=form, timeout=20)
        # close files
        for f in form.values():
            try:
                f.close()
            except Exception:
                pass
        return resp.json()
    except Exception as e:
        for f in form.values():
            try:
                f.close()
            except Exception:
                pass
        return {"ok": False, "error": str(e)}
