import urllib.request

req = urllib.request.Request('http://127.0.0.1:5001/api/health', headers={'Origin':'http://127.0.0.1:3000'})
with urllib.request.urlopen(req) as r:
    print('status', r.status)
    print('ACAO', r.headers.get('Access-Control-Allow-Origin'))

