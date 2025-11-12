import os
from backend.csv_io import append_csv, read_csv_rows, utcnow_iso


def test_append_and_read_csv(tmp_path):
    path = tmp_path / "orders.csv"
    header = ["ts_utc", "action", "volume"]
    append_csv(
        str(path), {"ts_utc": utcnow_iso(), "action": "buy", "volume": 0.1}, header
    )
    append_csv(
        str(path), {"ts_utc": utcnow_iso(), "action": "sell", "volume": 0.2}, header
    )
    rows = read_csv_rows(str(path))
    assert len(rows) == 2
    assert rows[0]["action"] == "buy"
    assert rows[1]["volume"] == "0.2"
