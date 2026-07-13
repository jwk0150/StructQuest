# ═══ 必须最先加载 .env（否则所有服务的 API Key 都是空的！）═══
from dotenv import load_dotenv
import os as _os, pathlib as _pl

# 加载两个 .env 文件：先根目录（含 DID_API_KEY），后本地覆盖
_script_dir = _pl.Path(__file__).resolve().parent  # app/
_root_env = (_script_dir / '..' / '..' / '.env').resolve()  # learn/.env
_local_env = (_script_dir / '..' / '.env').resolve()   # struct-quest-backend/.env
load_dotenv(str(_root_env))      # learn/.env (DID_API_KEY)
load_dotenv(str(_local_env), override=True)  # 本地 .env 覆盖

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os
import hashlib
import shutil
from app.services.llm import llm_service
from app.services.rag import rag_service
from app.services.tts import tts_service
from app.services.iflytek_virtual_human import iflytek_vh_service
from app.db.session import engine, Base, get_db, AsyncSessionLocal
from app.api.learning import router as learning_router
from app.api.auth_api import router as auth_router
from app.api.knowledge_api import router as knowledge_router
from app.api.knowledge_doc_api import router as knowledge_doc_router
from app.api.profile_api import router as profile_router
from app.api.study_api import router as study_router
from app.api.exam_api import router as exam_router
from app.api.ppt_generator import router as ppt_generator_router  # PPT智能生成器
from app.api.recommendation_api import router as recommendation_router  # AI推荐资源
from app.api.chat_api import router as chat_api_router  # ★ 新增：聊天历史 & 内容管理
from app.api.admin_api import router as admin_router
from app.api.ability_api import router as ability_router
from app.api.task_api import router as task_router
from app.api.daily_task_api import router as daily_task_router
from app.api.daily_learning_api import router as daily_learning_router
from app.api.onboarding_api import router as onboarding_router  # 冷启动画像引导
from app.api.orchestrated_api import router as orchestrated_router  # Orchestrator统一入口
from app.api.behavior_api import router as behavior_router  # 行为上报+动态画像+推荐Feed
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat import ChatSession, ChatMessage
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.models.knowledge_graph import KnowledgeNode
from app.models.learning_progress import LearningProgress
from app.models.study_session import StudySession
from app.models.exam_result import ExamResult
from app.models.resource import ExternalResource
from app.models.user_ability import UserAbility
from app.models.user_task import UserTaskRecord
from app.models.wrong_question import WrongQuestion
from app.models.daily_task import DailyTask
from app.models.learning_ecosystem import (
    LearningEvent,
    ProfileSnapshot,
    LearningPlan,
    LearningPlanStep,
    ResourceAsset,
    ResourceReview,
)
from app.models.student_profile import StudentProfile  # 六维动态画像
from app.models.learning_behavior import LearningBehavior  # 学习行为日志
from app.models.recommendation import Recommendation  # 推荐缓存

app = FastAPI(title="Learn AI Chat API", version="1.0.0")  # reload trigger

# 静态文件服务（PPTX 下载 + 视频播放）
_static_base = os.environ.get("STATIC_DIR", "/app/static")
os.makedirs(_static_base, exist_ok=True)
os.makedirs(os.path.join(_static_base, "pptx"), exist_ok=True)
os.makedirs(os.path.join(_static_base, "videos"), exist_ok=True)
os.makedirs(os.path.join(_static_base, "audio", "tts"), exist_ok=True)  # TTS 音频缓存目录
os.makedirs(os.path.join(_static_base, "videos", "iflytek"), exist_ok=True)  # 讯飞虚拟人视频缓存目录
os.makedirs(os.path.join(_static_base, "ppt"), exist_ok=True)  # PPT HTML输出目录
app.mount("/static", StaticFiles(directory=_static_base), name="static")


# 注册路由
app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(knowledge_doc_router)  # 知识库文档管理（管理员权限）
app.include_router(profile_router)
app.include_router(learning_router)
app.include_router(study_router)
app.include_router(exam_router)
app.include_router(ppt_generator_router)  # PPT智能生成器（三阶段流程）
app.include_router(recommendation_router)  # AI推荐资源（爬虫+用户画像）
app.include_router(chat_api_router)  # ★ 新增：聊天历史 & 生成内容管理
app.include_router(admin_router)  # 轻量管理员平台
app.include_router(ability_router)  # 能力值接口
app.include_router(task_router)     # 每日任务接口
app.include_router(daily_task_router)  # 每日任务重构接口
app.include_router(daily_learning_router)  # 每日学习任务（三阶段：知识点→练习题→温故知新）
app.include_router(onboarding_router)  # 冷启动画像引导（问卷+诊断+生成画像）
app.include_router(orchestrated_router)  # Orchestrator统一入口
app.include_router(behavior_router)  # 行为上报+动态画像+推荐Feed

# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup():
    print("[Startup] 正在初始化数据库...")
    from app.db.session import init_database
    await init_database()

    # ★ 确保 master 管理员账号存在
    from app.db.session import AsyncSessionLocal
    from app.auth import get_password_hash
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == "master"))
        master = result.scalar_one_or_none()
        if not master:
            master = User(
                username="master",
                hashed_password=get_password_hash("123456"),
                is_admin=True,
                has_completed_onboarding=True,
                learning_mode="basic",
            )
            db.add(master)
            await db.commit()
            print("[Startup] [OK] 管理员账号已创建: master / 123456")
        else:
            # 确保已有 master 的 is_admin 为 True
            if not getattr(master, 'is_admin', False):
                master.is_admin = True
                await db.commit()
                print("[Startup] [OK] 已有 master 账号已升级为管理员")
            else:
                print("[Startup] [OK] 管理员账号 master 已存在")

    print("[Startup] 数据库初始化完成")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 请求/响应模型 ====================

class QueryRequest(BaseModel):
    question: str
    k: int = 4


# ==================== 健康检查 ====================

@app.get("/")
async def root():
    return {"message": "Learn AI Chat API is running"}

@app.get("/api/health")
async def health_check():
    """AI 服务健康检查"""
    from app.services.llm import llm_service
    healths = await llm_service.check_all_health()
    all_ok = all(h["ok"] for h in healths)
    available = [h for h in healths if h["ok"]]
    return {
        "status": "ok" if available else "degraded",
        "llm_ok": len(available) > 0,
        "llm_model": getattr(getattr(llm_service, 'providers', {}).get('primary'), 'model', 'unknown'),
        "message": f"{len(available)}/{len(healths)} AI 服务可用" if healths else "未配置 AI 服务",
        "services": healths,
    }

# 知识库文档管理已移至 app/api/knowledge_doc_api.py（管理员权限）

@app.post("/api/knowledge-query")
async def knowledge_query(req: QueryRequest):
    """
    独立 RAG 问答接口：
    用户提问 -> 检索相关知识 -> 直接返回检索到的上下文（不调用 LLM）
    前端可自行决定是否将结果发给 LLM
    """
    context = rag_service.retrieve_context(query=req.question, k=req.k)

    if not context:
        return {
            "question": req.question,
            "found": False,
            "message": "未找到相关知识片段，请先上传相关 PDF 文档",
        }

    # 同时返回带分数的详细结果
    scored_results = rag_service.retrieve_with_scores(query=req.question, k=req.k)

    return {
        "question": req.question,
        "found": True,
        "context": context,
        "sources": scored_results,
    }


# ================================================================
#                     TTS 语音合成接口
# ================================================================

@app.get("/api/tts/voices")
async def get_tts_voices():
    """获取所有可用的 TTS 音色列表"""
    return tts_service.list_voices()


# ================================================================
#                讯飞虚拟人 接口
# ================================================================

@app.get("/api/iflytek/status")
async def iflytek_status():
    """检查讯飞虚拟人服务状态 + 返回前端配置"""
    quota = await iflytek_vh_service.check_quota()
    quota["config"] = {
        "appId": iflytek_vh_service.app_id,
        "apiKey": iflytek_vh_service.api_key,
        "apiSecret": iflytek_vh_service.api_secret,
        "avatarId": iflytek_vh_service.avatar_id or "201165002",
    } if iflytek_vh_service.is_available else None
    return quota


@app.get("/api/iflytek/voices")
async def iflytek_voices():
    """获取讯飞虚拟人可用音色列表"""
    return iflytek_vh_service.list_voices()


class IflytekGenerateRequest(BaseModel):
    text: str
    voice: str = "xiaoxiao"
    avatar_id: str = ""       # 空 = 使用场景默认形象
    use_cache: bool = True


@app.post("/api/iflytek/generate")
async def iflytek_generate(req: IflytekGenerateRequest):
    """
    生成讯飞数字人视频（带缓存）

    - 相同文本 + 相同音色 → 直接返回已缓存的视频 URL
    - 不同文本 → 调用讯飞 API 生成，生成后缓存到本地
    """
    try:
        result = await iflytek_vh_service.generate(
            text=req.text,
            voice_key=req.voice,
            avatar_id=req.avatar_id or None,
            use_cache=req.use_cache,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
#                        聊天接口 (WebSocket)
# ================================================================

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            message_data = json.loads(data)

            user_messages = message_data.get("messages", [])
            provider_name = message_data.get("provider", "openai")
            voice_key = message_data.get("voice", "xiaoxiao")
            enable_tts = message_data.get("enable_tts", True)
            tts_mode = message_data.get("tts_mode", "edge_tts")  # edge_tts / did / iflytek
            avatar_key = message_data.get("avatar", "teacher_female")  # D-ID 形象
            # ★ 可选：每日学习任务系统提示（来自前端 NodeLearning 页面）
            system_prompt = message_data.get("system_prompt", None)

            # ═══ 使用带故障切换的 AI 服务（主服务失败自动切备用）═══
            full_response = ""
            generation_ok = False

            if not llm_service.providers:
                print("[LLM] [ERR] 没有可用的 AI 服务")
                await websocket.send_text(json.dumps({"error": "未配置任何 AI 服务，请在 .env 中设置 LLM_API_KEY"}))
                continue

            async for event in llm_service.chat_with_failover(user_messages, system_prompt=system_prompt):
                if event["type"] == "chunk":
                    full_response += event["content"]
                    await websocket.send_text(json.dumps(event))
                elif event["type"] == "failover":
                    print(f"[LLM] [WARN] 自动切换到备用服务: {event.get('reason','')}")
                    await websocket.send_text(json.dumps({
                        "type": "failover",
                        "message": f"AI 服务切换中，请稍候...（{event.get('reason','')}）",
                    }))
                elif event["type"] == "error":
                    status_code = event.get("status_code", 0)
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "status_code": status_code,
                        "message": event.get("message", "AI 服务异常"),
                        "detail": event.get("detail", ""),
                    }))
                    generation_ok = False
                    break

            if not full_response and not generation_ok:
                continue

            print(f"[LLM] [OK] 回复完成: {len(full_response)} chars")
            await websocket.send_text(json.dumps({"type": "done", "full_content": full_response}))

            # ★ TTS / 数字人（讯飞 SDK 前端直连，后端仅做 Edge TTS 备选）
            if enable_tts and full_response.strip():
                if tts_mode == "iflytek":
                    # 前端使用 AvatarPlatform SDK 直接调用 writeText()，后端不参与
                    print(f"[iFlytek-VH] 前端 SDK 模式，后端跳过 ({len(full_response)} 字)")

                elif tts_mode == "edge_tts":
                    try:
                        await websocket.send_text(json.dumps({"type": "tts_start", "mode": "edge_tts"}))
                        audio_bytes = await tts_service.synthesize(text=full_response[:500], voice_key=voice_key)
                        _audio_hash = hashlib.md5(full_response[:200].encode()).hexdigest()[:12]
                        _audio_path = os.path.join(_static_base, "audio", "tts", f"tts_{_audio_hash}_{voice_key}.mp3")
                        os.makedirs(os.path.dirname(_audio_path), exist_ok=True)
                        with open(_audio_path, "wb") as f:
                            f.write(audio_bytes)
                        await websocket.send_text(json.dumps({
                            "type": "tts_audio", "audio_url": f"/static/audio/tts/tts_{_audio_hash}_{voice_key}.mp3",
                            "mode": "edge_tts", "voice": voice_key,
                        }))
                        print(f"[TTS] OK ({len(audio_bytes)} bytes)")
                    except Exception as tts_err:
                        print(f"[TTS] 失败: {tts_err}")
                        await websocket.send_text(json.dumps({"type": "tts_error", "message": f"语音合成失败: {str(tts_err)[:100]}"}))
                else:
                    # 未知模式，报错不降级
                    await websocket.send_text(json.dumps({"type": "tts_error", "message": f"不支持的 TTS 模式: {tts_mode}"}))

    except Exception as e:
        print(f"[WS] 异常: {e}")
        import traceback; traceback.print_exc()
        try:
            await websocket.send_text(json.dumps({"error": str(e)[:200]}))
        except Exception:
            pass

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
