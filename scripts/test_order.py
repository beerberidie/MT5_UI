import json, urllib.request, sys, os
from dotenv import load_dotenv

load_dotenv()

API = 'http://127.0.0.1:5001'
body = {
    "canonical": "EURUSD",
    "side": "buy",
    "volume": 0.01,
    "sl": None,
    "tp": None,
    "deviation": 10,
    "comment": "demo",
    "magic": 123
}

headers = {'Content-Type': 'application/json'}
api_key = os.getenv("AUGMENT_API_KEY")
if api_key:
    headers['X-API-Key'] = api_key

req = urllib.request.Request(
    f"{API}/api/order",
    data=json.dumps(body).encode('utf-8'),
    headers=headers
)
try:
    resp = urllib.request.urlopen(req)
    print(resp.read().decode('utf-8'))
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    raise

