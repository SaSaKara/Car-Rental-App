import re
import datetime

_PLATE_RE = re.compile(r"^\s*(\d{2})\s*([A-Z]{1,3})\s*(\d{2,4})\s*$", re.IGNORECASE)


def normalize_plate(raw: str) -> str:
    """
    Validate and normalize Turkish license plates.

    Accepted examples:
    - 34 ABC 456
    - 34ABC456
    - 06 AB 1234

    Returns normalized format: "PP LLL NNNN" (single spaces).
    Raises ValueError if invalid.
    """
    raw = (raw or "").strip()
    m = _PLATE_RE.match(raw)
    if not m:
        raise ValueError("Invalid license plate format.")
    province, letters, numbers = m.group(1), m.group(2).upper(), m.group(3)
    return f"{province} {letters} {numbers}"


def now_ts() -> str:
    """Return a stable timestamp string for logs."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_log(event: str, **fields) -> str:
    """
    Create a consistent, machine-readable log line.

    Example:
    2026-02-25 13:10:02 | EVENT=VEHICLE_RENTED | plate="34 ABC 456" | days=3 | fee=1200
    """
    ts = now_ts()
    parts = [f'{ts} | EVENT={event}']
    for k, v in fields.items():
        if isinstance(v, str):
            parts.append(f'{k}="{v}"')
        else:
            parts.append(f"{k}={v}")
    return " | ".join(parts)