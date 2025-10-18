# File: id_card_extractor_service/main.py
import os
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image
import google.generativeai as genai
import json
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import List

# --- Cấu hình ứng dụng ---
class Settings(BaseSettings):
    GEMINI_API_KEY: str
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# --- Cấu hình Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ID Card Extractor Service", version="1.2.0")

# --- Cấu hình Gemini API ---
try:
    if not settings.GEMINI_API_KEY:
        logger.error("Lỗi: Biến môi trường GEMINI_API_KEY chưa được thiết lập trong file .env.")
    else:
        genai.configure(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Lỗi khi cấu hình Gemini: {e}")

# --- Prompt được thiết kế để yêu cầu Gemini trả về kết quả dạng JSON ---
prompt = """
Bạn là một hệ thống OCR chuyên nghiệp, được huấn luyện để nhận diện Căn cước công dân (CCCD) của Việt Nam.
Nhiệm vụ của bạn là phân tích hình ảnh được cung cấp và trích xuất chính xác hai thông tin sau:
1. Số Căn cước công dân (bao gồm 12 chữ số).
2. Họ và tên đầy đủ (viết IN HOA, có dấu).

Hãy trả về kết quả dưới dạng một đối tượng JSON hợp lệ duy nhất, tuân thủ nghiêm ngặt cấu trúc sau:
{
  "ho_ten": "...",
  "so_cccd": "..."
}

Nếu một trong hai thông tin không thể tìm thấy hoặc không rõ ràng, hãy để giá trị của trường đó là một chuỗi rỗng ("").
Không thêm bất kỳ giải thích, ghi chú hay định dạng markdown nào khác vào phản hồi. Chỉ trả về đối tượng JSON.
"""

class ExtractedInfo(BaseModel):
    ho_ten: str = Field(default="", description="Họ và tên đầy đủ")
    so_cccd: str = Field(default="", description="Số Căn cước công dân")

async def extract_info_with_gemini(image_file: UploadFile) -> ExtractedInfo:
    """
    Gửi ảnh đến Gemini API và yêu cầu trích xuất thông tin.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("API Key của Gemini chưa được cấu hình.")

    try:
        # THAY ĐỔI 1: Cập nhật tên model để khớp với module TypeScript gốc
        model = genai.GenerativeModel('gemini-2.5-flash')

        image = Image.open(image_file.file)

        # THAY ĐỔI 2: Sử dụng JSON Mode để Gemini trả về JSON sạch
        response = await model.generate_content_async(
            contents=[prompt, image],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        # Không cần dọn dẹp markdown nữa, response.text đã là một JSON string
        data = json.loads(response.text)
        
        return ExtractedInfo(
            ho_ten=data.get("ho_ten", ""),
            so_cccd=data.get("so_cccd", "")
        )
    except Exception as e:
        logger.error(f"Đã xảy ra lỗi khi xử lý ảnh với Gemini: {e}", exc_info=True)
        raise e

@app.post("/extract", response_model=ExtractedInfo)
async def extract_cccd_info_endpoint(file: UploadFile = File(...)):
    """
    Endpoint nhận file ảnh CCCD và trả về dữ liệu đã trích xuất.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"Tệp {file.filename} không phải là ảnh.")
    
    try:
        result = await extract_info_with_gemini(file)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi từ Gemini API: {str(e)}"
        )

