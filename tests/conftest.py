import os
import tempfile
import shutil
import json
import contextlib
import types
import pytest

# Ensure app imports
import backend.app as app_module
import backend.risk as risk_module


class MockMT5Object:
    """Mock object that simulates MT5 named tuple behavior."""

    def __init__(self, data_dict):
        self._data = data_dict

    def _asdict(self):
        return self._data.copy()


class FakeMT5Client:
    def __init__(self):
        self._account = {
            "balance": 10000.0,
            "equity": 10000.0,
            "margin": 0.0,
            "margin_free": 10000.0,
            "margin_level": 0.0,
            "leverage": 100,
            "currency": "USD",
        }
        self._positions = []
        self._historical_bars = []
        self._historical_ticks = []
        self._deals = []
        self._orders = []

    def account_info(self):
        return dict(self._account)

    def positions(self):
        return list(self._positions)

    def order_send(self, **kwargs):
        # Return a success-like retcode
        return {"retcode": 10009, "order": 1, "position": 0, "comment": "ok"}

    def copy_rates_from_pos(
        self, symbol: str, timeframe, start_pos: int, count: int
    ) -> list:
        """Return mock historical bars data."""
        return self._historical_bars

    def copy_rates_range(self, symbol: str, timeframe, date_from, date_to) -> list:
        """Return mock historical bars data for date range."""
        return self._historical_bars

    def copy_ticks_range(self, symbol: str, date_from, date_to, flags) -> list:
        """Return mock historical ticks data."""
        return self._historical_ticks

    def history_deals_get(self, date_from, date_to, symbol=None) -> list:
        """Return mock trading deals."""
        return self._deals

    def history_orders_get(self, date_from, date_to, symbol=None) -> list:
        """Return mock trading orders."""
        return self._orders


@pytest.fixture()
def temp_dirs(monkeypatch):
    # Create temp dirs for data, logs, config
    root = tempfile.mkdtemp(prefix="mt5ui_tests_")
    data = os.path.join(root, "data")
    os.makedirs(data, exist_ok=True)
    logs = os.path.join(root, "logs")
    os.makedirs(logs, exist_ok=True)
    config = os.path.join(root, "config")
    os.makedirs(config, exist_ok=True)

    # Write minimal config CSVs
    with open(os.path.join(config, "symbol_map.csv"), "w", encoding="utf-8") as f:
        f.write("canonical,broker_symbol,enabled,min_vol,vol_step,comment\n")
        f.write("EURUSD,EURUSD,true,0.01,0.01,Default\n")
    with open(os.path.join(config, "risk_limits.csv"), "w", encoding="utf-8") as f:
        f.write("key,value,notes\n")
        f.write("daily_loss_limit_r,0,\n")
    with open(os.path.join(config, "sessions.csv"), "w", encoding="utf-8") as f:
        f.write("canonical,trade_start_utc,trade_end_utc,block_on_closed,notes\n")
        f.write("EURUSD,00:00:00,23:59:59,true,\n")

    # Patch config constants used by code
    monkeypatch.setattr(app_module, "DATA_DIR", data, raising=False)
    monkeypatch.setattr(app_module, "LOG_DIR", logs, raising=False)
    monkeypatch.setattr(
        app_module, "FRONTEND_ORIGINS", ["http://127.0.0.1:3000"], raising=False
    )
    monkeypatch.setattr(risk_module, "CONFIG_DIR", config, raising=False)

    try:
        yield {"root": root, "data": data, "logs": logs, "config": config}
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.fixture()
def fake_mt5(monkeypatch):
    fake = FakeMT5Client()
    # Patch the module-level mt5 client instance used by routes
    monkeypatch.setattr(app_module, "mt5", fake, raising=True)
    return fake


@pytest.fixture()
def client(temp_dirs, fake_mt5):
    from fastapi.testclient import TestClient

    # Disable API key requirement during tests so they pass regardless of env
    app_module.app.dependency_overrides[app_module.require_api_key] = lambda: None
    return TestClient(app_module.app)
