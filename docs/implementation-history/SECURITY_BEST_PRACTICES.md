# Security Best Practices - MT5_UI Development Guide

## Table of Contents

1. [API Development](#api-development)
2. [Frontend Development](#frontend-development)
3. [Configuration Management](#configuration-management)
4. [Logging & Monitoring](#logging--monitoring)
5. [Testing](#testing)
6. [Deployment](#deployment)

---

## API Development

### 1. Always Use Pydantic Models for Input Validation

**✅ Good**:
```python
from pydantic import BaseModel, Field

class OrderRequest(BaseModel):
    canonical: str = Field(..., min_length=1, max_length=20, pattern=r'^[A-Z0-9_-]+$')
    side: Literal["buy", "sell"]
    volume: float = Field(..., gt=0, le=100)
    deviation: int = Field(10, ge=0, le=100)
```

**❌ Bad**:
```python
@app.post("/api/order")
def post_order(canonical: str, side: str, volume: float):
    # No validation!
    ...
```

### 2. Protect Trading Endpoints with API Key

**✅ Good**:
```python
@app.post("/api/order", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
def post_order(request: Request, req: OrderRequest):
    ...
```

**❌ Bad**:
```python
@app.post("/api/order")  # No authentication!
def post_order(req: OrderRequest):
    ...
```

### 3. Apply Rate Limiting to All Endpoints

**✅ Good**:
```python
@app.get("/api/positions")
@limiter.limit("60/minute")
def get_positions(request: Request):
    ...
```

**❌ Bad**:
```python
@app.get("/api/positions")  # No rate limit!
def get_positions():
    ...
```

### 4. Validate and Sanitize All User Input

**✅ Good**:
```python
def get_ticks(canonical: str):
    # Validate format
    if not canonical.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(400, detail="invalid_symbol_format")
    
    # Validate length
    if len(canonical) > 20:
        raise HTTPException(400, detail="symbol_too_long")
    
    # Use validated input
    path = os.path.join(DATA_DIR, "ticks", canonical, f"{today}.csv")
```

**❌ Bad**:
```python
def get_ticks(canonical: str):
    # Direct use without validation - path traversal risk!
    path = os.path.join(DATA_DIR, "ticks", canonical, f"{today}.csv")
```

### 5. Log Security Events

**✅ Good**:
```python
def require_api_key(request: Request):
    provided_key = request.headers.get("X-API-Key")
    client_ip = getattr(request.client, 'host', 'unknown')
    
    if provided_key != AUGMENT_API_KEY:
        _log_security_event(
            "invalid_api_key_attempt",
            f"Invalid API key from {client_ip}",
            client_ip
        )
        raise HTTPException(401, detail="invalid_api_key")
```

**❌ Bad**:
```python
def require_api_key(request: Request):
    if request.headers.get("X-API-Key") != AUGMENT_API_KEY:
        raise HTTPException(401)  # No logging!
```

### 6. Sanitize Error Messages

**✅ Good**:
```python
def _log_error(scope: str, message: str):
    sanitized = _sanitize_message(message)  # Remove API keys, passwords
    append_csv("logs/errors.csv", {"message": sanitized})
```

**❌ Bad**:
```python
def _log_error(scope: str, message: str):
    append_csv("logs/errors.csv", {"message": message})  # May contain secrets!
```

### 7. Use Structured Error Responses

**✅ Good**:
```python
raise HTTPException(
    409,
    detail={
        "error": {
            "code": "DAILY_LOSS_LIMIT_EXCEEDED",
            "message": "Daily loss limit exceeded",
            "details": {"current_pnl": -500, "limit": 400}
        }
    }
)
```

**❌ Bad**:
```python
raise HTTPException(409, detail="Error")  # Not helpful!
```

---

## Frontend Development

### 1. Never Hardcode API Keys

**✅ Good**:
```typescript
// index.html
window.AUGMENT_API_KEY = 'AC135782469AD';

// api.ts
const hdrs = (window as any).getAuthHeaders?.() || {};
```

**❌ Bad**:
```typescript
const API_KEY = 'AC135782469AD';  // Hardcoded!
```

### 2. Use Environment-Based Configuration

**✅ Good**:
```typescript
const base = (window as any).CONFIG?.API_BASE || "http://127.0.0.1:5001";
```

**❌ Bad**:
```typescript
const base = "http://127.0.0.1:5001";  // Hardcoded!
```

### 3. Implement Request Timeouts

**✅ Good**:
```typescript
const controller = new AbortController();
const timeout = (window as any).CONFIG?.CONNECTION_TIMEOUT || 10000;
const tHandle = setTimeout(() => controller.abort(), timeout);

const res = await fetch(url, { signal: controller.signal });
clearTimeout(tHandle);
```

**❌ Bad**:
```typescript
const res = await fetch(url);  // No timeout!
```

### 4. Handle Errors Gracefully

**✅ Good**:
```typescript
try {
  const data = await apiCall('/api/order', { method: 'POST', body: JSON.stringify(order) });
  toast({ title: 'Success', description: 'Order placed' });
} catch (error: any) {
  const message = error.message || 'Failed to place order';
  toast({ title: 'Error', description: message, variant: 'destructive' });
}
```

**❌ Bad**:
```typescript
const data = await apiCall('/api/order', { method: 'POST', body: JSON.stringify(order) });
// No error handling!
```

### 5. Sanitize User Input Before Display

**✅ Good**:
```typescript
// Use React's built-in XSS protection
<div>{userInput}</div>  // React escapes by default

// For HTML content, use DOMPurify
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(htmlContent) }} />
```

**❌ Bad**:
```typescript
<div dangerouslySetInnerHTML={{ __html: userInput }} />  // XSS risk!
```

---

## Configuration Management

### 1. Use Environment Variables for Secrets

**✅ Good**:
```bash
# .env (gitignored)
AUGMENT_API_KEY=AC135782469AD
DATABASE_PASSWORD=secret123
```

**❌ Bad**:
```python
# config.py (committed to git)
API_KEY = "AC135782469AD"  # Exposed in git history!
```

### 2. Provide Secure Defaults

**✅ Good**:
```python
API_HOST = os.getenv("API_HOST", "127.0.0.1")  # Local-only by default
AUGMENT_API_KEY = os.getenv("AUGMENT_API_KEY", "")  # Empty = auth disabled
```

**❌ Bad**:
```python
API_HOST = os.getenv("API_HOST", "0.0.0.0")  # Exposed to network!
```

### 3. Validate Configuration on Startup

**✅ Good**:
```python
def validate_config():
    if API_HOST == "0.0.0.0" and not AUGMENT_API_KEY:
        raise ValueError("API_KEY required when binding to 0.0.0.0")
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

validate_config()
```

**❌ Bad**:
```python
# No validation - fails at runtime!
```

---

## Logging & Monitoring

### 1. Log All Security Events

**Events to Log**:
- ✅ Authentication attempts (success and failure)
- ✅ Authorization failures
- ✅ Rate limit violations
- ✅ Input validation failures
- ✅ Risk limit violations
- ✅ Configuration changes

### 2. Sanitize Logs

**✅ Good**:
```python
def _sanitize_message(message: str) -> str:
    patterns = [
        (r'[Aa]pi[_-]?[Kk]ey["\s]*[:=]["\s]*[A-Za-z0-9]{8,}', 'API_KEY=***'),
        (r'[Pp]assword["\s]*[:=]["\s]*[^\s"]+', 'password=***'),
    ]
    for pattern, replacement in patterns:
        message = re.sub(pattern, replacement, message)
    return message
```

**❌ Bad**:
```python
print(f"Error: {error_message}")  # May contain secrets!
```

### 3. Use Structured Logging

**✅ Good**:
```python
_log_security_event(
    event_type="invalid_api_key_attempt",
    details=f"Invalid key from {client_ip}",
    client_ip=client_ip
)
```

**❌ Bad**:
```python
print("Invalid API key")  # No context!
```

### 4. Implement Log Rotation

**✅ Good**:
```python
# Use Python's logging with RotatingFileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

**❌ Bad**:
```python
# Logs grow indefinitely!
with open('logs/app.log', 'a') as f:
    f.write(message)
```

---

## Testing

### 1. Test Authentication

**✅ Good**:
```python
def test_order_without_api_key():
    response = client.post("/api/order", json=payload)
    assert response.status_code == 401
    assert "invalid_api_key" in response.json()["detail"]
```

### 2. Test Rate Limiting

**✅ Good**:
```python
def test_rate_limiting():
    for i in range(15):  # Exceed 10/minute limit
        response = client.post("/api/order", json=payload, headers=headers)
    
    assert response.status_code == 429  # Too Many Requests
```

### 3. Test Input Validation

**✅ Good**:
```python
def test_invalid_symbol():
    payload = {"canonical": "../../../etc/passwd", ...}
    response = client.post("/api/order", json=payload)
    assert response.status_code == 400
```

### 4. Test Error Handling

**✅ Good**:
```python
def test_error_no_sensitive_data():
    response = client.post("/api/order", json=invalid_payload)
    error_text = response.text
    assert "API_KEY" not in error_text
    assert "password" not in error_text
```

---

## Deployment

### 1. Use HTTPS in Production

**✅ Good**:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
    }
}
```

### 2. Bind to Localhost by Default

**✅ Good**:
```python
uvicorn.run(app, host="127.0.0.1", port=5001)
```

**❌ Bad**:
```python
uvicorn.run(app, host="0.0.0.0", port=5001)  # Exposed to network!
```

### 3. Use Strong API Keys

**✅ Good**:
```bash
# Generate strong random key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**❌ Bad**:
```bash
AUGMENT_API_KEY=123456  # Weak!
```

### 4. Keep Dependencies Updated

**✅ Good**:
```bash
# Regular updates
pip install --upgrade -r requirements.txt
npm update

# Security audits
pip-audit
npm audit
```

### 5. Disable Debug Mode in Production

**✅ Good**:
```python
app = FastAPI(
    debug=False,  # Production
    docs_url=None,  # Disable Swagger UI
    redoc_url=None  # Disable ReDoc
)
```

**❌ Bad**:
```python
app = FastAPI(debug=True)  # Exposes stack traces!
```

---

## Security Checklist

Before deploying to production, verify:

- [ ] API key authentication enabled
- [ ] Rate limiting configured
- [ ] All endpoints have input validation
- [ ] Logging and monitoring in place
- [ ] Secrets stored in environment variables
- [ ] CORS configured correctly
- [ ] Error messages don't expose sensitive data
- [ ] Dependencies are up to date
- [ ] Security tests passing
- [ ] Debug mode disabled
- [ ] HTTPS enabled (if network-accessible)
- [ ] Firewall configured
- [ ] Log rotation configured
- [ ] Backup strategy in place

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [Python Logging](https://docs.python.org/3/library/logging.html)

---

**Last Updated**: 2025-10-10  
**Version**: 1.0.0

