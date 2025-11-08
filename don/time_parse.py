import re
from datetime import datetime, timedelta, time as dtime
from typing import Optional

# Simple mappings for parts of day
PARTS = {
    "subah": 8,   # morning default 8 AM
    "dopahar": 13,
    "shaam": 18,
    "raat": 21,
}


def _next_day(base: datetime) -> datetime:
    return (base + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)


def parse_natural_time(text: str, now: Optional[datetime] = None) -> Optional[float]:
    """Parse phrases like 'kal subah 8 baje', 'aaj shaam', '8 baje', return epoch seconds.
    Heuristics; not exhaustive, but covers common Urdu/Roman patterns.
    """
    if not text:
        return None
    s = text.lower()
    ref = now or datetime.now()
    day = ref

    # Determine day: aaj/kal (today/tomorrow)
    if re.search(r"\bkal\b", s):
        day = ref + timedelta(days=1)
    elif re.search(r"\baaj\b|\baaj\s*ka\b|\baaj\s*subah\b", s):
        day = ref

    hour = None
    minute = 0

    # Extract explicit HH[:MM]
    m = re.search(r"\b(\d{1,2})(?:\s*[:\.](\d{1,2}))?\s*(?:baje|am|pm)?\b", s)
    if m:
        hour = int(m.group(1))
        if m.group(2):
            minute = int(m.group(2))

    # AM/PM hints
    if re.search(r"\bpm\b", s) and hour is not None and hour < 12:
        hour += 12
    if re.search(r"\bam\b", s) and hour == 12:
        hour = 0

    # Part of day default hours
    for part, def_hour in PARTS.items():
        if part in s and hour is None:
            hour = def_hour
            break

    # If only 'baje' found without number, default to 9 AM today/tomorrow
    if hour is None and "baje" in s:
        hour = 9

    if hour is None:
        return None

    target = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
    # If computed time already passed today and not explicitly 'kal', push to next day
    if target <= ref and not re.search(r"\bkal\b", s):
        target = target + timedelta(days=1)

    return target.timestamp()
