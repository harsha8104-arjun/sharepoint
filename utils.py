from datetime import datetime
import os

def get_env(name: str, default: str | None = None) -> str:
    val = os.getenv(name, default)
    if val is None or val.strip() == "":
        raise ValueError(f"Missing required environment variable: {name}")
    return val

def timestamped_name(filename: str) -> str:
    """
    report.pdf -> report_2026-01-05_1530.pdf
    """
    base, dot, ext = filename.rpartition(".")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    if dot == "":  # no extension
        return f"{filename}_{ts}"
    return f"{base}_{ts}.{ext}"
