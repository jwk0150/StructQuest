"""测试讯飞 VMS HTTP API — 文本驱动"""
import sys, json, base64, hmac, hashlib, httpx, asyncio, uuid, os
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = 'ea31bddc1d511b6bd7557f2331e8a7a0'
API_SECRET = 'MzgyOWZhMWQ4N2FmYTgzODJiYzI3NDg4'
APP_ID = 'df0a8ac1'
HOST = 'vms.cn-huadong-1.xf-yun.com'

def build_auth(method, path):
    tz = timezone.utc
    date_str = datetime.now(tz).strftime('%a, %d %b %Y %H:%M:%S GMT')
    sig_origin = f'host: {HOST}\ndate: {date_str}\n{method} {path} HTTP/1.1'
    sig = base64.b64encode(hmac.new(API_SECRET.encode(), sig_origin.encode(), hashlib.sha256).digest()).decode()
    auth_raw = f'api_key="{API_KEY}",algorithm="hmac-sha256",headers="host date request-line",signature="{sig}"'
    auth = base64.b64encode(auth_raw.encode()).decode()
    return date_str, auth

async def test_start():
    date_str, auth = build_auth('POST', '/v1/private/vms2d_start')
    headers = {'Host': HOST, 'Date': date_str, 'Authorization': auth, 'Content-Type': 'application/json'}
    body = {'app_id': APP_ID, 'avatar_id': '201165002', 'width': 1080, 'height': 1920}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f'https://{HOST}/v1/private/vms2d_start', headers=headers, json=body)
        print(f'Start: HTTP {r.status_code}')
        print(r.text[:800])
        return r.json() if r.status_code == 200 else None

async def test_ctrl():
    # Try text drive without start first
    date_str, auth = build_auth('POST', '/v1/private/vms2d_ctrl')
    headers = {'Host': HOST, 'Date': date_str, 'Authorization': auth, 'Content-Type': 'application/json'}
    body = {
        'app_id': APP_ID,
        'avatar_id': '201165002',
        'task_id': str(uuid.uuid4()),
        'text': base64.b64encode('你好数据结构'.encode()).decode(),
        'tts_vcn': 'x4_lingxiaoxuan_oral',
        'width': 1080, 'height': 1920
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f'https://{HOST}/v1/private/vms2d_ctrl', headers=headers, json=body)
        print(f'\nCtrl: HTTP {r.status_code}')
        print(r.text[:800])

async def main():
    print('=== Test Start ===')
    await test_start()
    await asyncio.sleep(1)
    print('\n=== Test Ctrl ===')
    await test_ctrl()

asyncio.run(main())
