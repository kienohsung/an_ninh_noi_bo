# File: backend/app/routers/vehicle_log.py
from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from datetime import datetime, date, timedelta
import io
import pandas as pd
import logging

# Import hàm xử lý logic chính từ services
from ..services.gsheets_reader import filter_and_aggregate
# Import các thành phần xác thực
from ..auth import get_current_user
from .. import models

# Khởi tạo logger
logger = logging.getLogger(__name__)

# Khởi tạo router, yêu cầu xác thực cho tất cả các endpoint trong file này
router = APIRouter(
    prefix="/vehicle-log", 
    tags=["Vehicle Log"],
    dependencies=[Depends(get_current_user)]
)

def parse_date(s: Optional[str]) -> Optional[date]:
    """Hàm tiện ích để chuyển đổi chuỗi YYYY-MM-DD thành đối tượng date."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        # Trả về None nếu định dạng ngày không hợp lệ
        logger.warning(f"Invalid date format received: {s}")
        return None

def quick_range_to_dates(quick: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    """Chuyển đổi các khoảng thời gian nhanh (VD: 'last7') thành ngày bắt đầu và kết thúc cụ thể."""
    if not quick:
        return (None, None)
    
    today = date.today()
    if quick == "today":
        return (today, today)
    if quick == "last7":
        return (today - timedelta(days=6), today)
    if quick == "last30":
        return (today - timedelta(days=29), today)
    # Lấy ngày đầu tuần là thứ Hai (weekday() == 0)
    if quick == "thisWeek":
        start_of_week = today - timedelta(days=today.weekday())
        return (start_of_week, today)
    if quick == "thisMonth":
        start_of_month = today.replace(day=1)
        return (start_of_month, today)
    if quick == "prevMonth":
        first_day_of_this_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_this_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        return (first_day_of_last_month, last_day_of_last_month)
    
    return (None, None)

@router.get("", response_class=JSONResponse)
def list_vehicle_log(
    quick: Optional[str] = Query(None, description="Khoảng thời gian nhanh: today, last7, last30, thisWeek, thisMonth, prevMonth"),
    start: Optional[str] = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm (biển số xe)"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200)
):
    """
    API chính để lấy dữ liệu nhật ký xe, đã được phân trang và tổng hợp cho biểu đồ.
    """
    try:
        # Xác định khoảng thời gian lọc
        start_date, end_date = quick_range_to_dates(quick)
        if start: start_date = parse_date(start)
        if end: end_date = parse_date(end)

        if start_date and end_date and start_date > end_date:
            raise HTTPException(status_code=400, detail="Ngày bắt đầu không thể lớn hơn ngày kết thúc.")

        # Gọi service để lấy và xử lý dữ liệu từ Google Sheets
        rows, charts, kpi = filter_and_aggregate(q=q, start=start_date, end=end_date)

        # Logic phân trang
        total_records = len(rows)
        start_index = (page - 1) * pageSize
        end_index = start_index + pageSize
        paginated_rows = rows[start_index:end_index]

        # Định dạng lại dữ liệu trả về cho frontend
        items = [{
            "plate": r.get("plate", ""),
            "date": r["date"].isoformat() if r.get("date") else "",
            "time": r["time"].strftime("%H:%M:%S") if r.get("time") else ""
        } for r in paginated_rows]

        return {
            "total": total_records,
            "page": page,
            "pageSize": pageSize,
            "items": items,
            "chart": charts,
            "kpi": kpi
        }
    except HTTPException as http_exc:
        # Nếu có lỗi HTTP đã biết, throw lại nó
        raise http_exc
    except Exception as e:
        logger.error(f"Lỗi không xác định khi lấy nhật ký xe: {e}", exc_info=True)
        # Trả về lỗi 500 chung chung để bảo mật
        raise HTTPException(status_code=500, detail=f"Lỗi máy chủ nội bộ: {e}")

@router.get("/export")
def export_vehicle_log_to_excel(
    quick: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    """
    API để xuất dữ liệu đã lọc ra file Excel.
    """
    try:
        start_date, end_date = quick_range_to_dates(quick)
        if start: start_date = parse_date(start)
        if end: end_date = parse_date(end)

        rows, _, _ = filter_and_aggregate(q=q, start=start_date, end=end_date)
        
        # Chuyển đổi dữ liệu sang định dạng phù hợp cho DataFrame
        export_data = [{
            "Số xe": r.get("plate", ""),
            "Ngày": r["date"].strftime("%Y-%m-%d") if r.get("date") else "",
            "Giờ": r["time"].strftime("%H:%M:%S") if r.get("time") else ""
        } for r in rows]
        
        df = pd.DataFrame(export_data)

        # Tạo file Excel trong bộ nhớ
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="NhatKyXe")
        output.seek(0)

        # Tạo tên file động
        today_str = date.today().strftime("%Y%m%d")
        filename = f"NhatKyXe_Export_{today_str}.xlsx"
        
        # SỬA LỖI F-STRING: Đảm bảo chuỗi được định dạng đúng và an toàn.
        # Dấu ngoặc kép bên trong được bao bởi dấu ngoặc đơn bên ngoài của f-string.
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }

        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        logger.error(f"Lỗi khi xuất file Excel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Không thể tạo file Excel: {e}")

