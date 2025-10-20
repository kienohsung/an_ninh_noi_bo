# File: backend/app/routers/vehicle_log.py
from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from datetime import datetime, date, timedelta
import io
import pandas as pd
import logging

from ..services.gsheets_reader import filter_and_aggregate
from ..auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/vehicle-log", 
    tags=["Vehicle Log"],
    dependencies=[Depends(get_current_user)]
)

# ... (các hàm parse_date và quick_range_to_dates giữ nguyên)
def parse_date(s: Optional[str]) -> Optional[date]:
    if not s: return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        logger.warning(f"Invalid date format received: {s}")
        return None

def quick_range_to_dates(quick: Optional[str]) -> tuple[Optional[date], Optional[date]]:
    if not quick: return (None, None)
    today = date.today()
    if quick == "today":
        return (today, today)
    if quick == "last7":
        return (today - timedelta(days=6), today)
    if quick == "last30":
        return (today - timedelta(days=29), today)
    if quick == "thisWeek":
        start = today - timedelta(days=today.weekday())
        return (start, today)
    if quick == "thisMonth":
        start = today.replace(day=1)
        return (start, today)
    if quick == "prevMonth":
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        start = last_prev.replace(day=1)
        end = last_prev
        return (start, end)
    return (None, None)


@router.get("", response_class=JSONResponse)
def list_vehicle_log(
    # ... (các tham số giữ nguyên)
    quick: Optional[str] = Query(None, description="Khoảng thời gian nhanh: today, last7, last30, thisWeek, thisMonth, prevMonth"),
    start: Optional[str] = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm (biển số xe)"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=200)
):
    try:
        start_date, end_date = quick_range_to_dates(quick)
        if start: start_date = parse_date(start)
        if end: end_date = parse_date(end)

        if start_date and end_date and start_date > end_date:
            raise HTTPException(status_code=400, detail="Ngày bắt đầu không thể lớn hơn ngày kết thúc.")

        # --- CẢI TIẾN: Bắt lỗi cụ thể từ service ---
        try:
            rows, charts, kpi = filter_and_aggregate(q=q, start=start_date, end=end_date)
        except FileNotFoundError as e:
            # Đây là lỗi quan trọng nhất: không tìm thấy credentials.json
            logger.critical(f"CRITICAL ERROR in GSheet service: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Lỗi nghiêm trọng: Không tìm thấy file credentials.json của Google. Vui lòng kiểm tra lại cấu hình."
            )
        except Exception as service_exc:
            # Bắt các lỗi khác từ Google API (ví dụ: sai Sheet ID, không có quyền,...)
            logger.error(f"Error calling GSheet service: {service_exc}", exc_info=True)
            raise HTTPException(
                status_code=503, # 503 Service Unavailable
                detail=f"Không thể kết nối hoặc đọc dữ liệu từ Google Sheets. Chi tiết: {service_exc}"
            )

        total_records = len(rows)
        start_index = (page - 1) * pageSize
        end_index = start_index + pageSize
        paginated_rows = rows[start_index:end_index]

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
        raise http_exc
    except Exception as e:
        logger.error(f"Lỗi không xác định trong endpoint vehicle-log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi máy chủ nội bộ không xác định: {e}")

# ... (hàm export giữ nguyên)
@router.get("/export")
def export_vehicle_log_to_excel(
    quick: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    try:
        start_date, end_date = quick_range_to_dates(quick)
        if start: start_date = parse_date(start)
        if end: end_date = parse_date(end)

        rows, _, _ = filter_and_aggregate(q=q, start=start_date, end=end_date)
        
        export_data = [{
            "Số xe": r.get("plate", ""),
            "Ngày": r["date"].strftime("%Y-%m-%d") if r.get("date") else "",
            "Giờ": r["time"].strftime("%H:%M:%S") if r.get("time") else ""
        } for r in rows]
        
        df = pd.DataFrame(export_data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="NhatKyXe")
        output.seek(0)

        today_str = date.today().strftime("%Y%m%d")
        filename = f"NhatKyXe_Export_{today_str}.xlsx"
        
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

