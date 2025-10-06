from __future__ import annotations
import csv, os
from datetime import datetime, timezone
from typing import Iterable, Dict, List

ENCODING = "utf-8"
ISO = "%Y-%m-%dT%H:%M:%S.%fZ"


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO)


def ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def append_csv(path: str, row: Dict[str, object], header: Iterable[str]) -> None:
    ensure_dir(path)
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding=ENCODING) as f:
        w = csv.DictWriter(f, fieldnames=list(header))
        if not exists:
            w.writeheader()
        w.writerow(row)


def read_csv_rows(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding=ENCODING) as f:
        return list(csv.DictReader(f))

