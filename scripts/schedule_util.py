"""Small helper to compute a scheduled YouTube publish time (UTC ISO string)."""
import datetime as dt
from zoneinfo import ZoneInfo


def next_publish_iso(hour, tz_name, min_lead_minutes=15):
    """Return the next occurrence of `hour` (local) as a UTC ISO-8601 string.

    If that time today is already past (or too soon), it rolls to tomorrow.
    """
    tz = ZoneInfo(tz_name)
    now = dt.datetime.now(tz)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now + dt.timedelta(minutes=min_lead_minutes):
        target += dt.timedelta(days=1)
    return target.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
