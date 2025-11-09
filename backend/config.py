import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.getenv("API_HOST", "127.0.0.1")
try:
    API_PORT = int(os.getenv("API_PORT", "5001"))
    if not (1024 <= API_PORT <= 65535):
        raise ValueError("API_PORT must be between 1024 and 65535")
except ValueError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:3000")
# Support multiple origins via FRONTEND_ORIGINS (comma-separated) or fallback to FRONTEND_ORIGIN
_origins_raw = os.getenv("FRONTEND_ORIGINS", FRONTEND_ORIGIN)
FRONTEND_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]
# Common local aliases to reduce CORS surprises (Vite dev/preview)
for o in [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3010",
    "http://127.0.0.1:3010",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]:
    if o not in FRONTEND_ORIGINS:
        FRONTEND_ORIGINS.append(o)

MT5_PATH = os.getenv("MT5_PATH", r"C:\\Program Files\\MetaTrader 5\\terminal64.exe")
DATA_DIR = os.getenv("DATA_DIR", "./data")
LOG_DIR = os.getenv("LOG_DIR", "./logs")
CONFIG_DIR = os.getenv("CONFIG_DIR", "./config")
AUGMENT_API_KEY = os.getenv("AUGMENT_API_KEY", "")

# Validate critical paths exist or can be created
for directory in [DATA_DIR, LOG_DIR, CONFIG_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

