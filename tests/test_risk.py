import os
from backend import risk


def test_symbol_map_reads(temp_dirs):
    rows = risk.symbol_map()
    assert rows and rows[0]["canonical"] == "EURUSD"


def test_sessions_map_and_rule(temp_dirs):
    smap = risk.sessions_map()
    assert "EURUSD" in smap
    start, end, block = smap["EURUSD"]
    assert start == "00:00:00" and end == "23:59:59"

