# File: backend/app/utils/notifications.py
# Purpose: Telegram notifications with event logging to archive channel
from __future__ import annotations
import os
import requests
import logging
import pytz # --- THÊM MỚI: Cần cho múi giờ ---
from datetime import timedelta # --- THÊM MỚI (V3): Cần để "ép" trừ giờ ---
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload # Thêm joinedload

# SỬA LỖI: Thay đổi đường dẫn import từ "." thành ".." để trỏ ra thư mục app
from ..database import SessionLocal
from .. import models
from ..models import get_local_time
from ..config import settings

# Dữ liệu đã được nạp từ .env vào settings trong main.py
TELEGRAM_ENABLED = settings.NOTIFY_TELEGRAM_ENABLED
TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID = settings.TELEGRAM_CHAT_ID
TELEGRAM_ARCHIVE_CHAT_ID = settings.TELEGRAM_ARCHIVE_CHAT_ID # Nạp ID kênh lưu trữ

# Lưu file ID trong thư mục backend, bên ngoài thư mục app
LAST_MESSAGE_ID_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "telegram_last_message_id.txt"))
logger = logging.getLogger(__name__)

def _bot_api(method: str) -> str:
    """Tạo URL API cho Telegram bot."""
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"

def can_send_main() -> bool:
    """Kiểm tra cấu hình kênh chính có hợp lệ không."""
    return TELEGRAM_ENABLED and bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_CHAT_ID)

# --- THÊM MỚI: Kiểm tra cấu hình kênh lưu trữ ---
def can_send_archive() -> bool:
    """Kiểm tra cấu hình kênh lưu trữ có hợp lệ không."""
    return TELEGRAM_ENABLED and bool(TELEGRAM_BOT_TOKEN) and bool(TELEGRAM_ARCHIVE_CHAT_ID)
# --- KẾT THÚC THÊM MỚI ---

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
    """Gửi yêu cầu xóa một tin nhắn cụ thể khỏi kênh chính."""
    if not can_send_main() or not message_id:
        return
    try:
        logger.info(f"Đang yêu cầu Telegram xóa tin nhắn ID: {message_id} khỏi kênh chính {TELEGRAM_CHAT_ID}")
        resp = requests.post(_bot_api("deleteMessage"), json={
            "chat_id": TELEGRAM_CHAT_ID,
            "message_id": message_id
        }, timeout=10)

        response_json = resp.json()
        if not response_json.get("ok"):
             logger.warning(f"Không thể xóa tin nhắn Telegram {message_id}. Phản hồi từ Telegram: {resp.text}")
        else:
             logger.info(f"Đã xóa thành công tin nhắn ID: {message_id}")
    except Exception as e:
        logger.error(f"Ngoại lệ khi xóa tin nhắn Telegram {message_id}: {e}")

# --- BỎ HÀM forward_telegram_message ---
# Logic này không còn cần thiết theo yêu cầu mới.

def send_telegram_message(text: str, chat_id: str) -> dict:
    """Gửi một tin nhắn văn bản đến một chat_id cụ thể. Trả về JSON phản hồi."""
    # Kiểm tra chung xem bot token có hợp lệ không
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not chat_id:
         return {"ok": False, "skipped": True, "reason": "Telegram disabled or missing token/chat_id"}
    try:
        logger.info(f"Đang gửi tin nhắn tới chat_id: {chat_id}")
        resp = requests.post(_bot_api("sendMessage"), json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML" # Sử dụng HTML để định dạng
        }, timeout=10)
        resp_json = resp.json()
        if not resp_json.get("ok"):
            logger.error(f"Gửi tin nhắn tới {chat_id} thất bại. Phản hồi: {resp.text}")
        else:
            logger.info(f"Gửi tin nhắn tới {chat_id} thành công.")
        return resp_json
    except Exception as e:
        logger.error(f"Ngoại lệ khi gửi tin nhắn tới {chat_id}: {e}")
        return {"ok": False, "error": str(e)}

def format_pending_list_for_telegram(pending_guests: List[models.Guest]) -> str:
    """Định dạng danh sách khách đang chờ cho kênh chính."""
    now = get_local_time().strftime('%H:%M:%S %d/%m/%Y') # Thêm giây

    if not pending_guests:
        return f"✅ <b>Tất cả khách đã được xác nhận vào.</b>\n<i>(Cập nhật lúc {now})</i>"

    header = f"📢 <b>DANH SÁCH KHÁCH CHỜ VÀO ({len(pending_guests)} người)</b>\n<i>(Cập nhật lúc {now})</i>"

    lines = [header]
    for i, guest in enumerate(pending_guests, 1):
        # Escape HTML entities để tránh lỗi parse_mode
        full_name = guest.full_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        id_card = (guest.id_card_number or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        supplier = (guest.supplier_name or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        plate = (guest.license_plate or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # --- SỬA LỖI (V3): "Ép" trừ 7 giờ theo yêu cầu ---
        estimated_datetime_str = "N/A"
        if guest.estimated_datetime:
            try:
                # KỊCH BẢN 1: Giả định datetime từ DB là "naive" và là giờ LOCAL (ví dụ: 14:00)
                # nhưng nó đang bị hiểu lầm là UTC (14:00 UTC).
                # Ta cần "ép" nó về đúng UTC (07:00 UTC) bằng cách trừ 7 giờ.
                
                # 1. Lấy múi giờ UTC và múi giờ Local
                utc_tz = pytz.utc
                local_tz = pytz.timezone(settings.TZ)
                
                # 2. "Ép" trừ 7 giờ
                corrected_utc_naive_time = guest.estimated_datetime - timedelta(hours=7)

                # 3. "Áp" múi giờ UTC cho datetime "naive" đã sửa
                aware_utc_dt = utc_tz.localize(corrected_utc_naive_time)
                
                # 4. Chuyển đổi sang múi giờ local
                local_dt = aware_utc_dt.astimezone(local_tz)
                
                estimated_datetime_str = local_dt.strftime("%d/%m %H:%M") # Format: 30/10 14:00

            except Exception as e:
                # KỊCH BẢN 2: "localize" thất bại, có thể vì datetime đã "aware" (có TZ).
                # Đây là trường hợp phổ biến của PostgreSQL.
                # Thử chuyển đổi trực tiếp.
                try:
                    local_dt = guest.estimated_datetime.astimezone(pytz.timezone(settings.TZ))
                    estimated_datetime_str = local_dt.strftime("%d/%m %H:%M")
                except Exception as e2:
                    # Fallback cuối cùng nếu cả hai đều thất bại
                    logger.warning(f"Không thể chuyển đổi múi giờ cho estimated_datetime (ID khách: {guest.id}). Lỗi 1: {e}, Lỗi 2: {e2}")
                    estimated_datetime_str = str(guest.estimated_datetime)
        
        estimated_datetime_str = estimated_datetime_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # --- KẾT THÚC SỬA LỖI (V3) ---

        # Lấy tên người đăng ký trực tiếp nếu có joinload
        registered_by_name = guest.registered_by.full_name if guest.registered_by else "Không rõ"
        registered_by_name = registered_by_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        lines.append("--------------------")
        lines.append(f"{i} - <b>{full_name}</b> - {id_card}")
        # --- SỬA LỖI: Hiển thị Ngày giờ dự kiến ---
        lines.append(f"   Dự kiến: {estimated_datetime_str}")
        # --- KẾT THÚC SỬA LỖI ---
        lines.append(f"   BKS: {plate}")
        lines.append(f"   NCC: {supplier}")
        lines.append(f"   Người ĐK: {registered_by_name}") # Thêm tên người đăng ký

    lines.append("--------------------")

    message = "\n".join(lines)

    # Giới hạn độ dài tin nhắn Telegram
    if len(message) > 4096:
        message = message[:4090] + "\n..."

    return message

# --- SỬA ĐỔI: Hàm định dạng tin nhắn sự kiện cho kênh lưu trữ theo mẫu mới ---
def format_event_for_archive(guest: models.Guest, event_type: str, user_who_triggered: models.User) -> str:
    """Định dạng chi tiết sự kiện của khách cho kênh lưu trữ."""

    # 1. Xác định event_title và event_icon
    event_title = ""
    event_icon = ""
    if "Đăng ký mới" in event_type:
        event_title = "KHÁCH MỚI ĐĂNG KÝ"
        event_icon = "🆕"
        if "theo đoàn" in event_type:
             event_title = "KHÁCH MỚI ĐĂNG KÝ (THEO ĐOÀN)"
    elif event_type == "Xác nhận vào cổng":
        event_title = "KHÁCH ĐÃ VÀO CỔNG"
        event_icon = "✅"
    else:
        event_title = event_type.upper() # Fallback
        event_icon = "ℹ️"

    # 2. Lấy thời gian
    # Dùng định dạng ngắn cho dòng cuối
    now_short = get_local_time().strftime('%H:%M %d/%m/%Y')

    # 3. Chuẩn bị & Escape dữ liệu
    # Escape HTML entities để tránh lỗi parse_mode
    full_name = guest.full_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    id_card = (guest.id_card_number or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    plate = (guest.license_plate or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # "Đơn vị" trong mẫu là "supplier_name"
    supplier = (guest.supplier_name or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    reason = (guest.reason or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # --- SỬA LỖI (V3): "Ép" trừ 7 giờ theo yêu cầu ---
    estimated_datetime_str = "N/A"
    if guest.estimated_datetime:
        try:
            # KỊCH BẢN 1: Giả định datetime từ DB là "naive" và là giờ LOCAL (ví dụ: 14:00)
            # nhưng nó đang bị hiểu lầm là UTC (14:00 UTC).
            # Ta cần "ép" nó về đúng UTC (07:00 UTC) bằng cách trừ 7 giờ.
            
            # 1. Lấy múi giờ UTC và múi giờ Local
            utc_tz = pytz.utc
            local_tz = pytz.timezone(settings.TZ)
            
            # 2. "Ép" trừ 7 giờ
            corrected_utc_naive_time = guest.estimated_datetime - timedelta(hours=7)

            # 3. "Áp" múi giờ UTC cho datetime "naive" đã sửa
            aware_utc_dt = utc_tz.localize(corrected_utc_naive_time)
            
            # 4. Chuyển đổi sang múi giờ local
            local_dt = aware_utc_dt.astimezone(local_tz)
            
            estimated_datetime_str = local_dt.strftime("%d/%m %H:%M") # Format: 30/10 14:00

        except Exception as e:
            # KỊCH BẢN 2: "localize" thất bại, có thể vì datetime đã "aware" (có TZ).
            # Đây là trường hợp phổ biến của PostgreSQL.
            # Thử chuyển đổi trực tiếp.
            try:
                local_dt = guest.estimated_datetime.astimezone(pytz.timezone(settings.TZ))
                estimated_datetime_str = local_dt.strftime("%d/%m %H:%M")
            except Exception as e2:
                # Fallback cuối cùng nếu cả hai đều thất bại
                logger.warning(f"Không thể chuyển đổi múi giờ cho estimated_datetime (ID khách: {guest.id}). Lỗi 1: {e}, Lỗi 2: {e2}")
                estimated_datetime_str = str(guest.estimated_datetime)
    
    estimated_datetime_str = estimated_datetime_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # --- KẾT THÚC SỬA LỖI (V3) ---

    # Lấy tên người đăng ký gốc (luôn cần)
    # guest.registered_by đã được joinedload trong send_event_to_archive_background
    registered_by_original = "Không rõ"
    if guest.registered_by:
         registered_by_original = guest.registered_by.full_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # Lấy tên người thực hiện sự kiện
    triggered_by = user_who_triggered.full_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # 4. Xây dựng tin nhắn
    lines = [
        f"{event_icon} <b>[SỰ KIỆN] {event_title}</b>",
        "", # Dòng trống
        f"👤 <b>Khách:</b> {full_name} ({id_card})",
        # --- SỬA LỖI: Hiển thị Ngày giờ dự kiến ---
        f"⏰ <b>Dự kiến:</b> {estimated_datetime_str}",
        # --- KẾT THÚC SỬA LỖI ---
        f"📝 <b>Người ĐK:</b> {registered_by_original}",
        f"🚗 <b>BKS:</b> {plate}",
        f"💼 <b>Đơn vị:</b> {supplier}",
        f"📝 <b>Lý do:</b> {reason}",
        "" # Dòng trống
    ]

    # 5. Thêm dòng cuối tùy theo sự kiện
    if event_type == "Xác nhận vào cổng":
        lines.append(f"Xác nhận bởi: {triggered_by} (lúc {now_short})")
    elif "Đăng ký mới" in event_type:
         lines.append(f"Đăng ký bởi: {triggered_by} (lúc {now_short})")
    else:
         lines.append(f"Thực hiện bởi: {triggered_by} (lúc {now_short})")

    message = "\n".join(lines)

    # Giới hạn độ dài tin nhắn Telegram
    if len(message) > 4096:
        message = message[:4090] + "\n..."
    return message
# --- KẾT THÚC SỬA ĐỔI ---

# --- THÊM MỚI: Hàm chạy nền để gửi sự kiện đến kênh lưu trữ ---
def send_event_to_archive_background(guest_id: int, event_type: str, triggered_by_user_id: int):
    """Hàm chạy nền để lấy thông tin và gửi sự kiện đến kênh lưu trữ."""
    if not can_send_archive():
        logger.info("Bỏ qua gửi sự kiện lưu trữ: Kênh lưu trữ chưa được cấu hình hoặc Telegram bị tắt.")
        return

    logger.info(f"Bắt đầu tác vụ gửi sự kiện '{event_type}' cho guest ID {guest_id} đến kênh lưu trữ...")
    db: Session = SessionLocal()
    try:
        # Tải thông tin khách và người dùng liên quan
        guest = db.query(models.Guest)\
                  .options(joinedload(models.Guest.registered_by))\
                  .filter(models.Guest.id == guest_id)\
                  .first()
        triggered_by_user = db.query(models.User).get(triggered_by_user_id)

        if not guest:
            logger.error(f"Không tìm thấy khách với ID {guest_id} để gửi sự kiện lưu trữ.")
            return
        if not triggered_by_user:
            logger.error(f"Không tìm thấy người dùng với ID {triggered_by_user_id} để ghi nhận sự kiện.")
            # Có thể dùng thông tin mặc định hoặc bỏ qua
            return

        message_text = format_event_for_archive(guest, event_type, triggered_by_user)
        send_telegram_message(message_text, TELEGRAM_ARCHIVE_CHAT_ID)
        logger.info(f"Đã gửi sự kiện '{event_type}' cho guest ID {guest_id} đến kênh lưu trữ thành công.")

    except Exception as e:
        logger.error(f"Lỗi khi gửi sự kiện lưu trữ cho guest ID {guest_id}: {e}", exc_info=True)
    finally:
        db.close()
# --- KẾT THÚC THÊM MỚI ---

def run_pending_list_notification():
    """
    Hàm chạy nền cho KÊNH CHÍNH: Xóa tin nhắn cũ, lấy danh sách khách chờ và gửi thông báo tổng hợp mới.
    """
    if not can_send_main():
        logger.info("Bỏ qua cập nhật kênh chính: Kênh chính chưa được cấu hình hoặc Telegram bị tắt.")
        return

    logger.info("Bắt đầu tác vụ cập nhật danh sách chờ trên kênh chính...")

    # 1. Đọc và Xóa tin nhắn cũ trên kênh chính
    last_message_id = _read_last_message_id()
    if last_message_id:
        logger.info(f"Đã tìm thấy ID tin nhắn cũ trên kênh chính: {last_message_id}. Đang tiến hành xóa...")
        delete_telegram_message(last_message_id)
        # --- BỎ LOGIC FORWARD TẠI ĐÂY ---
    else:
        logger.info("Không tìm thấy ID tin nhắn cũ trên kênh chính, sẽ gửi tin nhắn mới.")

    # 2. Lấy danh sách mới và tạo nội dung
    db: Session = SessionLocal()
    try:
        # Load cả thông tin người đăng ký để hiển thị tên
        pending_guests = db.query(models.Guest)\
                           .options(joinedload(models.Guest.registered_by))\
                           .filter(models.Guest.status == 'pending')\
                           .order_by(models.Guest.created_at.asc())\
                           .all()
        logger.info(f"Tìm thấy {len(pending_guests)} khách đang chờ trên kênh chính.")
        message_text = format_pending_list_for_telegram(pending_guests)

        # 3. Gửi tin nhắn mới đến kênh chính
        logger.info("Đang gửi tin nhắn mới đến kênh chính...")
        response_data = send_telegram_message(message_text, TELEGRAM_CHAT_ID)

        # 4. Lưu ID của tin nhắn mới nếu gửi thành công
        if response_data.get("ok"):
            new_message_id = response_data.get("result", {}).get("message_id")
            if new_message_id:
                logger.info(f"Gửi tin nhắn mới đến kênh chính thành công. ID mới: {new_message_id}. Đang lưu lại...")
                _save_last_message_id(new_message_id)
            else:
                logger.warning("Gửi tin nhắn kênh chính thành công nhưng không nhận được ID tin nhắn mới.")
        else:
            logger.error(f"Gửi tin nhắn mới đến kênh chính thất bại. Phản hồi từ Telegram: {response_data}")

    finally:
        db.close()
    logger.info("Hoàn tất tác vụ cập nhật kênh chính.")


