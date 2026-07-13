"""
数字人后端服务
- SSE 流式 LLM 对话 (SiliconFlow / Qwen2.5-7B)
- Edge TTS 语音合成
- 静态文件服务
"""
import os
import json
import asyncio
from pathlib import Path

import httpx
import edge_tts
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict

# ═══════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════

LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-pxgkxtrufditsutwzbpquvlmwjqtdzfvleiqemibakiwsdjd")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

FALLBACK_API_KEY = os.getenv("FALLBACK_API_KEY", "sk-f187f0c07ef64c96b1c4abd36ccfca91")
FALLBACK_BASE_URL = os.getenv("FALLBACK_BASE_URL", "https://api.deepseek.com/v1")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "deepseek-chat")

# 数字人系统提示词
SYSTEM_PROMPT = """你是一个名叫"小智"的AI数字人助手，你以虚拟形象出现在用户面前，通过语音和文字与用户实时交流。

你的性格特点：
- 亲切自然，像朋友一样聊天，不使用过于正式或机械的语气
- 回答简洁口语化，每次回答控制在2-4句话，适合语音播报
- 有自己的观点和情感，偶尔表达个人喜好
- 对不懂的问题坦诚说不清楚，不编造信息
- 适当使用语气词让对话更自然（如"嗯"、"让我想想"、"其实"等）

回答原则：
- 保持口语风格，避免长篇大论
- 不使用Markdown格式（因为要语音播报）
- 回答要有温度，不是冷冰冰的信息检索
- 如果用户用中文提问就用中文回答，用英文提问就用英文回答"""

# TTS 音色列表
TTS_VOICES = {
    "xiaoxiao": {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 - 温柔女声", "gender": "female"},
    "yunxi": {"id": "zh-CN-YunxiNeural", "name": "云希 - 阳光男声", "gender": "male"},
    "xiaoyi": {"id": "zh-CN-XiaoyiNeural", "name": "晓伊 - 知性女声", "gender": "female"},
    "yunyang": {"id": "zh-CN-YunyangNeural", "name": "云扬 - 沉稳男声", "gender": "male"},
    "xiaobei": {"id": "zh-CN-XiaobeiNeural", "name": "晓贝 - 活泼女声", "gender": "female"},
    "yunjian": {"id": "zh-CN-YunjianNeural", "name": "云健 - 浑厚男声", "gender": "male"},
}

# ═══════════════════════════════════════════
# FastAPI 应用
# ═══════════════════════════════════════════

app = FastAPI(title="数字人系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"


# ═══════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = []


# ═══════════════════════════════════════════
# LLM 流式对话 (SSE)
# ═══════════════════════════════════════════

async def call_llm_stream(message: str, history: list):
    """调用 LLM API 并以 SSE 格式流式返回"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history[-10:]:  # 保留最近10轮对话
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})

    # 主 API 配置
    configs = [
        {"key": LLM_API_KEY, "url": LLM_BASE_URL, "model": LLM_MODEL},
        {"key": FALLBACK_API_KEY, "url": FALLBACK_BASE_URL, "model": FALLBACK_MODEL},
    ]

    for cfg in configs:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{cfg['url']}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {cfg['key']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": cfg["model"],
                        "messages": messages,
                        "stream": True,
                        "max_tokens": 512,
                        "temperature": 0.8,
                    },
                ) as resp:
                    if resp.status_code != 200:
                        error_text = await resp.aread()
                        print(f"[LLM] API {cfg['model']} 返回 {resp.status_code}: {error_text[:200]}")
                        continue

                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield f"data: {json.dumps({'type': 'done'})}\n\n"
                            return

                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                        except json.JSONDecodeError:
                            continue

                    return  # 成功完成，不再尝试备用 API

        except Exception as e:
            print(f"[LLM] {cfg['model']} 请求失败: {e}")
            continue

    # 所有 API 都失败了
    yield f"data: {json.dumps({'type': 'error', 'content': '抱歉，我暂时无法连接到服务器，请稍后再试。'})}\n\n"


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """SSE 流式对话接口"""
    return StreamingResponse(
        call_llm_stream(req.message, req.history or []),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ═══════════════════════════════════════════
# TTS 语音合成
# ═══════════════════════════════════════════

@app.get("/api/voices")
async def get_voices():
    """获取可用音色列表"""
    return TTS_VOICES


@app.post("/api/tts")
async def text_to_speech(request: Request):
    """文本转语音，返回 MP3 音频流"""
    body = await request.json()
    text = body.get("text", "")
    voice_key = body.get("voice", "xiaoxiao")

    if not text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    # 截断过长文本
    if len(text) > 800:
        text = text[:800]

    voice_id = TTS_VOICES.get(voice_key, TTS_VOICES["xiaoxiao"])["id"]

    try:
        communicate = edge_tts.Communicate(text, voice_id)
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        if not audio_chunks:
            raise HTTPException(status_code=500, detail="语音合成失败")

        audio_data = b"".join(audio_chunks)
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/mpeg",
            headers={"Content-Length": str(len(audio_data))},
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[TTS] 错误: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {e}")


# ═══════════════════════════════════════════
# 静态文件 & 健康检查
# ═══════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {"status": "ok", "llm_model": LLM_MODEL}


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


# ═══════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 50)
    print("  数字人系统启动中...")
    print(f"  LLM: {LLM_MODEL}")
    print(f"  TTS: Edge TTS (6种音色)")
    print("  访问地址: http://localhost:8765")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8765)
