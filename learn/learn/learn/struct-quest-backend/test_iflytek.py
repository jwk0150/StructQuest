"""深入测试工作的方法"""
import asyncio, sys, json, uuid, base64, os
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
os.environ['IFYTEK_VH_AVATAR_ID'] = '201165002'
from app.services.iflytek_virtual_human import iflytek_vh_service
import websockets

TEXT = '你好，欢迎学习数据结构！'
APP_ID = iflytek_vh_service.app_id
SCENE = iflytek_vh_service.scene_id

async def main():
    url = iflytek_vh_service._build_auth_url()
    rid = uuid.uuid4().hex

    start = {
        'header': {'app_id': APP_ID, 'request_id': rid,
                   'ctrl': 'start', 'scene_id': SCENE},
        'parameter': {
            'avatar': {'stream': {'protocol': 'xrtc', 'fps': 25, 'bitrate': 2000, 'alpha': 0},
                       'avatar_id': '201165002', 'width': 1080, 'height': 1920},
            'tts': {'vcn': 'x4_lingxiaoxuan_oral', 'speed': 50, 'pitch': 50, 'volume': 50,
                    'text': base64.b64encode(TEXT.encode()).decode()}
        }
    }

    async with websockets.connect(url, additional_headers={'Content-Type': 'application/json'},
                                   ping_timeout=10, close_timeout=5, max_size=16*1024*1024) as ws:
        await ws.send(json.dumps(start, ensure_ascii=False))
        print('Start sent')

        chunks = 0; total_bytes = 0; msgs = []
        for i in range(60):
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(raw, str):
                    msg = json.loads(raw)
                    msgs.append(msg)
                    h = msg.get('header', {})
                    p = msg.get('payload', {})
                    ctrl = h.get('ctrl', '?')
                    code = h.get('code', 0)
                    print(f'  [{i}] ctrl={ctrl} code={code} msg={h.get("message","")}')

                    # Print full message if it has useful content
                    if p:
                        print(f'       payload keys: {list(p.keys())}')
                        for k, v in p.items():
                            if isinstance(v, dict) and 'url' in v:
                                print(f'       URL in {k}: {v["url"][:100]}')
                    if ctrl in ('end', 'stop'): break
                elif isinstance(raw, bytes) and len(raw) > 0:
                    chunks += 1; total_bytes += len(raw)
                    print(f'  [{i}] BINARY {len(raw)} bytes (total: {total_bytes})')
            except asyncio.TimeoutError:
                print(f'  [{i}] Timeout')
                break

        print(f'\nTotal: {chunks} chunks, {total_bytes/1024:.1f} KB')
        if total_bytes > 0:
            # Save audio
            print('Saving to test_output...')

        # Print last few messages for debugging
        print(f'\nLast 3 messages:')
        for m in msgs[-3:]:
            print(json.dumps(m, ensure_ascii=False, indent=2)[:500])

asyncio.run(main())
