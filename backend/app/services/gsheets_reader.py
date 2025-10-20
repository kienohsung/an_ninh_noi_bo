# File: backend/app/services/gsheets_reader.py
from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from datetime import datetime, date
from collections import Counter, defaultdict
import pytz
import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
TZ = pytz.timezone(settings.TZ)
logger = logging.getLogger("[GSheet Reader]")

def _get_service():
    """Builds and returns a Google Sheets API service object."""
    logger.info("Attempting to build Google Sheets service...")
    try:
        creds = Credentials.from_service_account_file(settings.GSHEETS_CREDENTIALS_PATH, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        logger.info("Successfully built Google Sheets service.")
        return service
    except FileNotFoundError:
        logger.error(f"FATAL: Credentials file not found at '{settings.GSHEETS_CREDENTIALS_PATH}'.")
        raise
    except Exception as e:
        logger.error(f"FATAL: Failed to build Google Sheets service: {e}")
        raise

def read_sheet_all(service, sheet_id: str, sheet_name: str) -> List[List]:
    """Reads all values from a given sheet."""
    logger.info(f"Reading sheet ID '{sheet_id[:10]}...' name '{sheet_name}'...")
    try:
        range_name = f"'{sheet_name}'!A:C"
        resp = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
        values = resp.get("values", [])
        logger.info(f"Successfully read {len(values)} rows from sheet '{sheet_name}'.")
        return values
    except HttpError as e:
        logger.error(f"API Error reading sheet ID '{sheet_id[:10]}...', name '{sheet_name}': {e.reason}")
        if e.status_code == 403:
            logger.error("Error 403: PERMISSION_DENIED. Please ensure the service account email has 'Viewer' access to this Google Sheet.")
        elif e.status_code == 404:
            logger.error(f"Error 404: Not Found. Check if Sheet ID '{sheet_id}' and Sheet Name '{sheet_name}' are correct.")
        return [] # Return empty on error to avoid crashing
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading sheet '{sheet_name}': {e}")
        return []

def parse_rows(values: List[List]) -> List[Dict]:
    """Parses raw sheet values into structured dictionaries."""
    if not values or len(values) <= 1:
        return []
    
    parsed_count = 0
    rows = []
    for r in values[1:]:
        if not r or len(r) < 3 or not r[0] or not r[1] or not r[2]:
            continue

        plate = r[0].strip()
        d_raw, t_raw = r[1], r[2]
        d_obj, t_obj = None, None

        if isinstance(d_raw, str) and d_raw:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try: d_obj = datetime.strptime(d_raw, fmt).date(); break
                except (ValueError, TypeError): continue
        
        if isinstance(t_raw, str) and t_raw:
            for fmt in ("%H:%M:%S", "%H:%M"):
                try: t_obj = datetime.strptime(t_raw, fmt).time(); break
                except (ValueError, TypeError): continue
        
        if plate and d_obj and t_obj:
            rows.append({"plate": plate, "date": d_obj, "time": t_obj})
            parsed_count += 1
            
    logger.info(f"Successfully parsed {parsed_count} valid rows from raw data.")
    return rows

def month_span(start: date, end: date) -> List[Tuple[int,int]]:
    res = []
    y, m = start.year, start.month
    while True:
        res.append((y, m))
        if y == end.year and m == end.month: break
        m += 1;
        if m > 12: m = 1; y += 1
    return res

def normalize_text(s: Optional[str]) -> str:
    import unicodedata
    return unicodedata.normalize("NFD", (s or "")).encode("ascii", "ignore").decode("ascii").lower().strip()

def filter_and_aggregate(q: Optional[str], start: Optional[date], end: Optional[date]):
    try:
        service = _get_service()
    except Exception:
        # If service fails to build, return empty data to prevent frontend crash
        return [], {"daily": {}, "hours": {}, "heatmap": {}, "top10": {}}, {"totalInRange": "Lỗi"}

    values_all = []
    if settings.GSHEETS_LIVE_SHEET_ID:
        live_values = read_sheet_all(service, settings.GSHEETS_LIVE_SHEET_ID, settings.GSHEETS_SHEET_NAME)
        if live_values and len(live_values) > 1:
            values_all.extend(live_values[1:])

    if start and end:
        logger.info(f"Date range detected. Reading from archive files between {start} and {end}.")
        for y, m in month_span(start, end):
            arch_id = settings.GSHEETS_ARCHIVE_SHEETS.get(str(y))
            if arch_id:
                sheet_name = f"Thang{str(m).zfill(2)}_{y}"
                v = read_sheet_all(service, arch_id, sheet_name)
                if v and len(v) > 1:
                    values_all.extend(v[1:])
    
    rows = parse_rows([["Số xe", "Ngày", "Giờ"]] + values_all)
    logger.info(f"Successfully parsed {len(rows)} rows from all sources.")

    qn = normalize_text(q) if q else ""
    out = []
    for r in rows:
        if start and r["date"] and r["date"] < start: continue
        if end and r["date"] and r["date"] > end: continue
        if qn and qn not in normalize_text(r["plate"]): continue
        out.append(r)

    out.sort(key=lambda x: (x["date"] or date.min, x["time"] or datetime.min.time()), reverse=True)
    logger.info(f"{len(out)} rows remaining after filtering.")

    # --- Aggregation logic (unchanged but now more reliable) ---
    daily, hours, plate_cnt = Counter(), Counter(), Counter()
    heatmap = defaultdict(lambda: Counter())
    for r in out:
        if r["date"]: daily[str(r["date"])] += 1
        if r["time"]: hours[f"{r['time'].hour:02d}"] += 1
        if r["plate"]: plate_cnt[r["plate"]] += 1
        if r["date"] and r["time"]: heatmap[str(r["date"])][f"{r['time'].hour:02d}"] += 1

    daily_labels = sorted(daily.keys())
    daily_series = [daily[k] for k in daily_labels]
    hour_labels = [f"{i:02d}" for i in range(24)]
    hour_series = [hours.get(h, 0) for h in hour_labels]
    top = plate_cnt.most_common(10)
    top_labels = [p for p,_ in top]
    top_series = [c for _,c in top]

    heat_rows = sorted(heatmap.keys())
    matrix = [[heatmap[dkey].get(h, 0) for h in hour_labels] for dkey in heat_rows]

    total = len(out)
    peak_hour = hour_labels[hour_series.index(max(hour_series))] if total>0 and max(hour_series)>0 else None
    top_plate = top_labels[0] if top_labels else None
    avg_per_day = round(sum(daily_series)/len(daily_series), 1) if daily_series else 0.0

    charts = {
        "daily": {"labels": daily_labels, "series": daily_series},
        "hours": {"labels": hour_labels, "series": hour_series},
        "heatmap": {"rows": heat_rows, "cols": hour_labels, "matrix": matrix},
        "top10": {"labels": top_labels, "series": top_series}
    }
    kpi = {"totalInRange": total, "peakHour": peak_hour, "topPlate": top_plate, "avgPerDay": avg_per_day}
    
    return out, charts, kpi

