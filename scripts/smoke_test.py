import os
import sys
import subprocess
import time
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ROOT / "config" / "symbol_map.csv",
    ROOT / "config" / "sessions.csv",
    ROOT / "config" / "risk_limits.csv",
]

REQUIRED_IMPORTS = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "dotenv",
    "sse_starlette",
    "watchdog",
]


def check_deps():
    missing = []
    for name in REQUIRED_IMPORTS:
        try:
            __import__(name)
        except Exception:
            missing.append(name)
    if missing:
        print(f"Missing deps: {missing}")
        return False
    return True


def check_config_files():
    bad = []
    for p in REQUIRED_FILES:
        if not p.exists() or p.stat().st_size == 0:
            bad.append(str(p))
    if bad:
        print(f"Missing/empty config files: {bad}")
        return False
    return True


def start_backend():
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "5001",
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Wait for startup
    t0 = time.time()
    ok = False
    while time.time() - t0 < 20:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.2)
            continue
        if "Application startup complete" in line or "Uvicorn running" in line:
            ok = True
            break
    return proc if ok else None


def http_get(url):
    import urllib.request

    with urllib.request.urlopen(url) as r:
        return r.getcode(), r.read().decode("utf-8")


def main():
    ok = check_deps() and check_config_files()
    if not ok:
        sys.exit(1)
    proc = start_backend()
    if not proc:
        print("Backend failed to start")
        sys.exit(2)
    try:
        code, body = http_get("http://127.0.0.1:5001/api/health")
        if code != 200:
            print("Health check failed", code, body)
            sys.exit(3)
        print("Health:", body)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    print("Smoke test passed")


if __name__ == "__main__":
    main()
