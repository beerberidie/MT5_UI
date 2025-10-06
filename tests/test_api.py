import os
import json
from backend.csv_io import append_csv, utcnow_iso


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_symbols(client):
    r = client.get("/api/symbols")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_account_with_fake_mt5(client):
    r = client.get("/api/account")
    assert r.status_code == 200
    body = r.json()
    assert "equity" in body and body["equity"] == 10000.0


def test_positions_with_fake_mt5(client):
    r = client.get("/api/positions")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_order_success(client):
    payload = {"canonical": "EURUSD", "side": "buy", "volume": 0.01, "deviation": 10, "comment": "t", "magic": 1}
    r = client.post("/api/order", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert int(body.get("result_code", 0)) >= 10000


def test_cors_preflight(client):
    # Test OPTIONS preflight
    r = client.options("/api/health", headers={
        "Origin": "http://127.0.0.1:3000",
        "Access-Control-Request-Method": "GET",
    })
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") in ("*", "http://127.0.0.1:3000")

