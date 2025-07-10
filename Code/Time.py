from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")
LOCAL = ZoneInfo("Europe/London")

def now_utc():
    return datetime.now(UTC)

def parse_time_utc(time_str):
    now = now_utc()
    dt = datetime.strptime(time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day, tzinfo=UTC)
    if dt < now:
        dt += timedelta(days=1)
    return dt