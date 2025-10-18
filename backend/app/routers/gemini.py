# File path: backend/app/routers/gemini.py
# MÔ TẢ: File này đã được viết lại hoàn toàn.
# Nó không còn gọi trực tiếp đến Gemini nữa mà đóng vai trò là một proxy,
# chuyển tiếp yêu cầu đến service API trích xuất CCCD độc lập.

import logging
import requests
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from ..config import settings
from ..auth import get_current_user

router = APIRouter(prefix="/gemini", tags=["gemini"])
logger = logging.getLogger(__name__)

@router.post("/extract-cccd-info")
async def extract_cccd_info_proxy(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    Endpoint này nhận file ảnh từ frontend, sau đó chuyển tiếp (proxy) đến
    ID Card Extractor Service để xử lý và trả kết quả về.
    """
    if not settings.ID_CARD_EXTRACTOR_URL:
        logger.error("URL của ID Card Extractor Service chưa được cấu hình trong file .env hoặc config.py")
        raise HTTPException(
            status_code=500,
            detail="Extractor service is not configured."
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Tệp {file.filename} không phải là ảnh.")
    
    try:
        # Đọc nội dung file để gửi đi
        file_content = await file.read()
        
        # Chuẩn bị payload dạng multipart/form-data để gửi cho service mới
        files_payload = {'file': (file.filename, file_content, file.content_type)}

        logger.info(f"Chuyển tiếp yêu cầu quét CCCD cho file '{file.filename}' đến service: {settings.ID_CARD_EXTRACTOR_URL}")

        # Gửi request POST đến service trích xuất, với timeout 30 giây
        response = requests.post(settings.ID_CARD_EXTRACTOR_URL, files=files_payload, timeout=30)
        
        # Nếu service trả về lỗi (vd: 4xx, 5xx), raise exception ở đây
        response.raise_for_status()

        # Trả về kết quả JSON từ service cho frontend
        return response.json()

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Lỗi kết nối đến ID card extractor service: {e}")
        raise HTTPException(
            status_code=503, # 503 Service Unavailable
            detail="Không thể kết nối đến dịch vụ quét CCCD. Vui lòng kiểm tra xem service đã được khởi chạy chưa."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi trong quá trình gọi đến service quét CCCD: {e}")
        # Lấy chi tiết lỗi từ service nếu có
        error_detail = "Không rõ lỗi"
        if e.response is not None:
            try:
                error_detail = e.response.json().get("detail", e.response.text)
            except:
                error_detail = e.response.text
        
        raise HTTPException(
            status_code=e.response.status_code if e.response is not None else 500,
            detail=f"Dịch vụ quét CCCD báo lỗi: {error_detail}"
        )
    except Exception as e:
        logger.error(f"Đã có lỗi không xác định xảy ra trong proxy: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Lỗi hệ thống khi xử lý yêu cầu quét CCCD."
        )
