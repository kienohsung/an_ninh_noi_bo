from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
from datetime import datetime, date, timedelta
import io
import pandas as pd

from ..services.gsheets_reader import filter_and_aggregate

router = APIRouter(prefix="/vehicle-log", tags=["vehicle-log"])

def parse_date(s: Optional[str]) -> Optional[date]:
    if not s: return None
    return datetime.strptime(s, "%Y-%m-%d").date()

def quick_range_to_dates(quick: Optional[str] -> tuple[Optional[date], Optional[date]]):
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

@router.get("")
def list_vehicle_log(
    quick: Optional[str] = Query(None, description="today|last7|last30|thisWeek|thisMonth|prevMonth"),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = 1,
    pageSize: int = 50
):
    sd, ed = quick_range_to_dates(quick)
    if start: sd = parse_date(start)
    if end: ed = parse_date(end)

    if sd and ed and sd > ed:
        raise HTTPException(400, "start must be <= end")

    rows, charts, kpi = filter_and_aggregate(q=q, start=sd, end=ed)

    total = len(rows)
    start_idx = max(0, (page-1) * pageSize)
    end_idx = min(total, start_idx + pageSize)
    paged = rows[start_idx:end_idx]

    items = [{
        "plate": r["plate"],
        "date": r["date"].isoformat() if r["date"] else "",
        "time": r["time"].strftime("%H:%M") if r["time"] else ""
    } for r in paged]

    return JSONResponse({
        "total": total,
        "page": page,
        "pageSize": pageSize,
        "items": items,
        "chart": charts,
        "kpi": kpi
    })

@router.get("/export")
def export_excel(
    quick: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    sd, ed = quick_range_to_dates(quick)
    if start: sd = parse_date(start)
    if end: ed = parse_date(end)
    rows, charts, kpi = filter_and_aggregate(q=q, start=sd, end=ed)
    df = pd.DataFrame([{
        "Số xe": r["plate"],
        "Ngày": r["date"].isoformat() if r["date"] else "",
        "Giờ": r["time"].strftime("%H:%M") if r["time"] else ""
    } for r in rows])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="NhatKyXe")
    output.seek(0)
    filename = f"nhat_ky_xe_{(sd or date.today()).isoformat()}_{(ed or date.today()).isoformat()}.xlsx"
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="{filename}"})
