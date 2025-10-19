from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from datetime import datetime, date
from collections import Counter, defaultdict
import pytz

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from ..config import GOOGLE_APPLICATION_CREDENTIALS, SHEET_NAME, TIMEZONE, LIVE_SHEET_ID, ARCHIVE_SHEETS

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
TZ = pytz.timezone(TIMEZONE)

def _get_service():
    creds = Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)

def read_sheet_all(sheet_id: str, sheet_name: str) -> List[List]:
    """Read all values from a given sheet name in spreadsheet."""
    service = _get_service()
    range_name = f"{sheet_name}!A:C"
    resp = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = resp.get("values", [])
    return values

def parse_rows(values: List[List]) -> List[Dict]:
    """Parse values (3 columns: A plate, B date, C time) into normalized rows."""
    if not values or len(values) <= 1:
        return []
    rows = []
    for r in values[1:]:
        plate = (r[0] if len(r) > 0 else "").strip()
        d_raw = r[1] if len(r) > 1 else ""
        t_raw = r[2] if len(r) > 2 else ""
        d_obj = None
        t_obj = None
        # Date may be like '2025-10-18' or '18/10/2025'
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                d_obj = datetime.strptime(d_raw, fmt).date()
                break
            except Exception:
                continue
        if isinstance(d_raw, str) and d_obj is None:
            try:
                d_obj = datetime.fromisoformat(d_raw).date()
            except Exception:
                d_obj = None
        # Time: 'HH:MM' or 'HH:MM:SS'
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t_obj = datetime.strptime(t_raw, fmt).time()
                break
            except Exception:
                continue
        rows.append({"plate": plate, "date": d_obj, "time": t_obj})
    return rows

def month_span(start: date, end: date) -> List[Tuple[int,int]]:
    """Return list of (year, month) inclusive covered by date range."""
    res = []
    y, m = start.year, start.month
    while True:
        res.append((y, m))
        if y == end.year and m == end.month:
            break
        m += 1
        if m > 12:
            m = 1
            y += 1
    return res

def sheet_name_for_month(year: int, month: int) -> str:
    return f"Thang{str(month).zfill(2)}_{year}"

def normalize_text(s: Optional[str]) -> str:
    import unicodedata
    return unicodedata.normalize("NFD", (s or "")).encode("ascii", "ignore").decode("ascii").lower().strip()

def filter_and_aggregate(
    q: Optional[str],
    start: Optional[date],
    end: Optional[date],
):
    """
    Read from live and archives (only required months), filter by date and plate search,
    then build chart & kpi aggregates.
    """
    # Read live first
    values_all = []
    live_values = read_sheet_all(LIVE_SHEET_ID, SHEET_NAME)
    values_all.extend(live_values[1:] if live_values else [])

    # If filter provided, read archives for those months
    if start and end:
        for y, m in month_span(start, end):
            arch_id = ARCHIVE_SHEETS.get(str(y))
            if arch_id:
                sheet_name = sheet_name_for_month(y, m)
                try:
                    v = read_sheet_all(arch_id, sheet_name)
                    if v:
                        values_all.extend(v[1:])
                except Exception:
                    continue

    # recompose with header
    values = [["Số xe","Ngày","Giờ"]] + values_all
    rows = parse_rows(values)

    qn = normalize_text(q) if q else ""
    out = []
    for r in rows:
        if start and r["date"] and r["date"] < start:
            continue
        if end and r["date"] and r["date"] > end:
            continue
        if qn and qn not in normalize_text(r["plate"]):
            continue
        out.append(r)

    out.sort(key=lambda x: (x["date"] or date.min, x["time"] or datetime.min.time()), reverse=True)

    daily = Counter()
    hours = Counter()
    plate_cnt = Counter()
    heatmap = defaultdict(lambda: Counter())

    for r in out:
        if r["date"]:
            daily[str(r["date"])] += 1
        if r["time"]:
            hh = f"{r['time'].hour:02d}"
            hours[hh] += 1
        if r["plate"]:
            plate_cnt[r["plate"]] += 1
        if r["date"] and r["time"]:
            day_key = str(r["date"])
            hour_key = f"{r['time'].hour:02d}"
            heatmap[day_key][hour_key] += 1

    daily_labels = sorted(daily.keys())
    daily_series = [daily[k] for k in daily_labels]
    hour_labels = [f"{i:02d}" for i in range(24)]
    hour_series = [hours.get(h, 0) for h in hour_labels]
    top = plate_cnt.most_common(10)
    top_labels = [p for p,_ in top]
    top_series = [c for _,c in top]

    heat_rows = sorted(heatmap.keys())
    matrix = []
    for dkey in heat_rows:
        row = []
        for h in hour_labels:
            row.append(heatmap[dkey].get(h, 0))
        matrix.append(row)

    total = len(out)
    peak_hour = hour_labels[hour_series.index(max(hour_series))] if total>0 and max(hour_series)>0 else None
    top_plate = top_labels[0] if top_labels else None
    avg_per_day = round(sum(daily_series)/len(daily_series), 2) if daily_series else 0.0

    charts = {
        "daily": {"labels": daily_labels, "series": daily_series},
        "hours": {"labels": hour_labels, "series": hour_series},
        "heatmap": {"rows": heat_rows, "cols": hour_labels, "matrix": matrix},
        "top10": {"labels": top_labels, "series": top_series}
    }
    kpi = {
        "totalInRange": total,
        "peakHour": peak_hour,
        "topPlate": top_plate,
        "avgPerDay": avg_per_day
    }
    return out, charts, kpi
