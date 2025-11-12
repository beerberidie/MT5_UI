from __future__ import annotations
import csv, os
from typing import Tuple
from .config import CONFIG_DIR


def _read_kv(path: str) -> dict:
    m: dict[str, str] = {}
    if not os.path.exists(path):
        return m
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m[row["key"]] = row["value"]
    return m


def risk_limits() -> dict:
    return _read_kv(os.path.join(CONFIG_DIR, "risk_limits.csv"))


def symbol_map() -> list[dict]:
    path = os.path.join(CONFIG_DIR, "symbol_map.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sessions_map() -> dict[str, Tuple[str, str, str]]:
    path = os.path.join(CONFIG_DIR, "sessions.csv")
    out: dict[str, Tuple[str, str, str]] = {}
    if not os.path.exists(path):
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["canonical"]] = (
                row["trade_start_utc"],
                row["trade_end_utc"],
                row.get("block_on_closed", "false"),
            )
    return out
