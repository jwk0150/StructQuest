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
import asyncio
import shutil
from app.services.llm import llm_service
from app.services.rag import rag_service
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
from app.api.evaluation_api import router as evaluation_router  # ★ v5: AI学习效果评估中心
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
from app.models.resource_adjustment import ResourceAdjustment  # ★ v5: AI资源调整记录

app = FastAPI(title="Learn AI Chat API", version="1.0.0")  # reload trigger

# 静态文件服务（PPTX 下载 + 视频播放）
# ★ Windows/Linux 兼容：无 STATIC_DIR 环境变量时，用项目 static 目录
_static_base = os.environ.get("STATIC_DIR")
if not _static_base:
    _static_base = str(_pl.Path(__file__).resolve().parent / "static")
os.makedirs(_static_base, exist_ok=True)
os.makedirs(os.path.join(_static_base, "pptx"), exist_ok=True)
os.makedirs(os.path.join(_static_base, "videos"), exist_ok=True)
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
app.include_router(evaluation_router)  # ★ v5: AI学习效果评估中心（六模块Dashboard）

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
#                 AI 算法实验室 WebSocket
# ================================================================

@app.websocket("/ws/algo-lab")
async def algo_lab_websocket(websocket: WebSocket):
    """
    AI 算法实验室专用 WebSocket:
    1. 接收用户自然语言请求
    2. 先本地匹配预设 → 命中直接返回 algo_id
    3. 未命中 → 调用 AnimationAgent 生成动画步骤
    4. 流式推送生成的步骤（带进度）
    5. 自动缓存
    """
    await websocket.accept()
    print("[AlgoLab] WebSocket 连接已建立")
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")
            prompt = msg.get("prompt", "").strip()
            user_level = msg.get("user_level", "beginner")

            if not prompt:
                await websocket.send_text(json.dumps({
                    "type": "error", "message": "请输入算法请求"
                }, ensure_ascii=False))
                continue

            print(f"[AlgoLab] 请求: {prompt[:60]} | 水平: {user_level}")

            # ═══ 步骤1：预设匹配 ═══
            await websocket.send_text(json.dumps({
                "type": "matching",
                "message": "正在分析你的请求..."
            }, ensure_ascii=False))

            from app.agents.animation_agent import match_preset
            preset_id = match_preset(prompt)

            if preset_id:
                print(f"[AlgoLab] 命中预设: {preset_id}")
                await websocket.send_text(json.dumps({
                    "type": "matched_preset",
                    "algo_id": preset_id,
                    "message": f"匹配到预设算法，直接播放"
                }, ensure_ascii=False))
                continue  # 前端会用本地预设数据播放

            # ═══ 步骤2：AI 生成 ═══
            await websocket.send_text(json.dumps({
                "type": "generating",
                "message": "AI 正在生成动画步骤..."
            }, ensure_ascii=False))

            try:
                from app.agents.animation_agent import generate_animation

                result = await generate_animation(
                    user_request=prompt,
                    user_level=user_level,
                    use_cache=True,
                )

                if result.get("source") == "ai" or result.get("source") == "ai_cached":
                    # 返回 AI 生成的完整数据
                    total = len(result.get("steps", []))
                    print(f"[AlgoLab] AI 生成完成: {result.get('algorithm')} | {total} 步 | 来源:{result.get('source')}")

                    # 先推送元信息
                    await websocket.send_text(json.dumps({
                        "type": "ai_meta",
                        "algorithm": result.get("algorithm", "自定义算法"),
                        "category": result.get("category", "other"),
                        "complexity": result.get("complexity", {}),
                        "code": result.get("code", ""),
                        "total_steps": total,
                        "source": result.get("source"),
                    }, ensure_ascii=False))

                    # 流式推送步骤（模拟进度条）
                    steps = result.get("steps", [])
                    for i, step in enumerate(steps):
                        await websocket.send_text(json.dumps({
                            "type": "ai_step",
                            "index": i,
                            "total": total,
                            "step": {
                                "step": i + 1,
                                "narration": step.get("narration", ""),
                                "commands": step.get("commands", []),
                                "code_line": step.get("code_line", -1),
                                "code_explanation": step.get("code_explanation", ""),
                            }
                        }, ensure_ascii=False))
                        await asyncio.sleep(0.05)  # 50ms 间隔，模拟进度

                    # 推送总结
                    await websocket.send_text(json.dumps({
                        "type": "ai_done",
                        "summary": result.get("summary", "学习完成！"),
                        "total_steps": total,
                    }, ensure_ascii=False))

            except Exception as gen_err:
                print(f"[AlgoLab] AI 生成失败: {gen_err}")
                import traceback; traceback.print_exc()
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"AI 生成失败，请尝试从预设算法开始：{str(gen_err)[:150]}"
                }, ensure_ascii=False))

    except WebSocketDisconnect:
        print("[AlgoLab] 客户端断开")
    except Exception as e:
        print(f"[AlgoLab] 异常: {e}")
        import traceback; traceback.print_exc()


# ================================================================
#                        聊天接口 (WebSocket)
# ================================================================

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """
    方案 A：TutorAgent 接管聊天回答

    流程：
    1. 异步运行 TutorAgent（asyncio.to_thread 包装，不阻塞事件循环）
       → 结合学生画像/知识库RAG/错题本/聊天历史生成个性化回答 + 多模态资源
    2. 将个性化回答模拟流式分块推送给前端（保留打字效果）
    3. 推送多模态资源附件
    4. 持久化聊天记录
    5. TTS（讯飞前端直连）

    降级：TutorAgent 不可用时，回退到 llm_service.chat_with_failover 流式回答
    """
    await websocket.accept()
    print("WebSocket connection accepted")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data: {data}")
            message_data = json.loads(data)

            user_messages = message_data.get("messages", [])
            voice_key = message_data.get("voice", "xiaoxiao")
            enable_tts = message_data.get("enable_tts", True)
            tts_mode = message_data.get("tts_mode", "iflytek")  # 仅支持讯飞虚拟人
            avatar_key = message_data.get("avatar", "teacher_female")  # D-ID 形象
            # ★ 可选：每日学习任务系统提示（来自前端 NodeLearning 页面）
            system_prompt = message_data.get("system_prompt", None)
            # ★ 用户ID + 会话ID（用于持久化）
            user_id = message_data.get("user_id", None)
            chat_session_id = message_data.get("session_id", None)
            # ★ v4.1 格式手动覆盖（前端格式选择器）
            format_override = message_data.get("format_override", "")
            request_id = message_data.get("request_id", None)

            async def send_chat_event(payload: dict):
                if request_id is not None:
                    payload["request_id"] = request_id
                await websocket.send_text(json.dumps(payload, ensure_ascii=False))

            question_text = user_messages[-1].get("content", "") if user_messages else ""

            full_response = ""
            resource_attachments = []
            primary_format = None
            format_reason = None
            tutor_resp = {}
            actual_provider = "tutor_agent"

            # ═══ 步骤1：TutorAgent 生成个性化回答（方案A 核心）═══
            tutor_ok = False
            print(f"[WS-DEBUG] user_id={user_id} question_text={repr(question_text[:30] if question_text else None)} providers={bool(llm_service.providers)}", flush=True)
            if user_id and question_text and llm_service.providers:
                try:
                    from app.agents.graph import run_learning_session
                    from app.agents.state import EventType

                    # 通知前端正在思考
                    await send_chat_event({"type": "thinking", "message": "AI 导师正在为你个性化解答..."})

                    payload = {"question": question_text}
                    if format_override:
                        payload["format_override"] = format_override
                    # 传入聊天历史供 TutorAgent 查重
                    if user_messages:
                        payload["chat_history"] = [
                            m.get("content", "") for m in user_messages
                            if m.get("role") == "user"
                        ][-8:]

                    # ★ asyncio.to_thread 包装同步调用，避免阻塞 FastAPI 事件循环
                    print(f"[WS] TutorAgent: 生成个性化回答 + 多模态资源...")
                    agent_result = await asyncio.to_thread(
                        run_learning_session,
                        event_type=EventType.ASK_QUESTION,
                        event_payload=payload,
                        user_id=str(user_id),
                        max_iterations=3,
                    )

                    tutor_resp = agent_result.get("tutor_response", {}) or {}
                    # ★ 使用 TutorAgent 的个性化回答（不再丢弃）
                    full_response = (
                        tutor_resp.get("answer_text")
                        or agent_result.get("chat_response", "")
                    )
                    resource_attachments = tutor_resp.get("resource_attachments", [])
                    primary_format = tutor_resp.get("primary_format", "text_only")
                    format_reason = tutor_resp.get("format_reason", "")

                    if full_response:
                        tutor_ok = True
                        print(f"[TutorAgent] [OK] 回复: {full_response[:80]}... | "
                              f"资源: {len(resource_attachments)} 项 | 格式: {primary_format}", flush=True)
                    else:
                        print("[TutorAgent] [WARN] full_response 为空，将降级到流式 LLM", flush=True)
                except Exception as tutor_err:
                    print(f"[TutorAgent] [WARN] 个性化回答失败，降级到流式 LLM: {tutor_err}", flush=True)
                    import traceback; traceback.print_exc()

            # 确保 full_response 始终是字符串（防止 TutorAgent 返回 None 导致后 + = 崩溃）
            if full_response is None:
                full_response = ""

            # ═══ 步骤2：降级路径 — TutorAgent 不可用时用流式 LLM ═══
            if not tutor_ok:
                if not llm_service.providers:
                    print("[LLM] [ERR] 没有可用的 AI 服务")
                    await send_chat_event({"type": "error", "error": "未配置任何 AI 服务，请在 .env 中设置 LLM_API_KEY"})
                    continue

                async for event in llm_service.chat_with_failover(user_messages, system_prompt=system_prompt):
                    if event["type"] == "chunk":
                        full_response += event["content"]
                        await send_chat_event(event)
                    elif event["type"] == "failover":
                        print(f"[LLM] [WARN] 自动切换到备用服务: {event.get('reason','')}")
                        actual_provider = event.get("provider", "llm_failover")
                        await send_chat_event({"type": "failover", "message": f"AI 服务切换中，请稍候...（{event.get('reason','')}）"})
                    elif event["type"] == "error":
                        await send_chat_event({"type": "error", "status_code": event.get("status_code", 0), "message": event.get("message", "AI 服务异常"), "detail": event.get("detail", "")})
                        break

                if not full_response:
                    continue

            # ═══ 步骤3：TutorAgent 成功时，模拟流式推送个性化回答 ═══
            if tutor_ok and full_response:
                chunk_size = 40  # 每次推送约40字符，保留打字效果
                for i in range(0, len(full_response), chunk_size):
                    chunk = full_response[i:i + chunk_size]
                    await send_chat_event({"type": "chunk", "content": chunk})
                    await asyncio.sleep(0.02)  # 20ms 间隔

            print(f"[Chat] [OK] 回复完成: {len(full_response)} chars")
            await send_chat_event({"type": "done", "full_content": full_response})

            # ═══ 步骤4：推送多模态资源附件 ═══
            if resource_attachments:
                print(f"[WS] 多模态资源: {len(resource_attachments)} 项 | 格式: {primary_format}")
                for att in resource_attachments:
                    await send_chat_event({"type": "resource_done", "resource": att})

            # ═══ 步骤4.5：推送结构化消息卡片（v5 新增）═══
            message_cards = tutor_resp.get("message_cards", []) if tutor_resp else []
            if message_cards:
                print(f"[WS] 消息卡片: {len(message_cards)} 个 | 类型: {[c['type'] for c in message_cards]}")
                await send_chat_event({"type": "message_cards", "cards": message_cards})

            # ═══ 步骤5：持久化聊天记录到数据库 ═══
            if full_response and user_id:
                try:
                    from app.db.session import AsyncSessionLocal
                    from app.services.learning_record_service import learning_record_service
                    from app.models.chat import ChatSession as ChatSessionModel
                    from app.models.chat import ChatMessage as ChatMessageModel
                    async with AsyncSessionLocal() as db:
                        uid = int(user_id)
                        # 1. 如果没有 session_id，创建新会话
                        if not chat_session_id:
                            chat_session = ChatSessionModel(
                                user_id=uid,
                                title=(question_text[:50] if question_text else "新对话"),
                            )
                            db.add(chat_session)
                            await db.flush()
                            chat_session_id_val = str(chat_session.id)
                        else:
                            chat_session_id_val = str(chat_session_id)

                        # 2. 保存本轮用户提问（仅最后一条 user 消息，避免历史重复）
                        for msg in reversed(user_messages):
                            if msg.get("role") == "user":
                                db.add(ChatMessageModel(
                                    session_id=int(chat_session_id_val),
                                    role="user",
                                    content=msg.get("content", ""),
                                ))
                                break

                        # 3. 保存 AI 回复（含多模态字段）
                        ai_msg = ChatMessageModel(
                            session_id=int(chat_session_id_val),
                            role="ai",
                            content=full_response,
                            attachments=resource_attachments if resource_attachments else None,
                            primary_format=primary_format,
                            format_reason=format_reason,
                        )
                        db.add(ai_msg)
                        await db.flush()

                        # 4. 保存 ChatResource 记录
                        if resource_attachments:
                            from app.models.chat import ChatResource as ChatResourceModel
                            for att in resource_attachments:
                                db.add(ChatResourceModel(
                                    message_id=ai_msg.id,
                                    session_id=int(chat_session_id_val),
                                    user_id=uid,
                                    resource_type=att.get("type", "unknown"),
                                    format=att.get("format", "text"),
                                    title=att.get("title", ""),
                                    content_text=att.get("content_text"),
                                    content_json=att.get("content_json"),
                                    file_url=att.get("file_url"),
                                    thumbnail_url=att.get("thumbnail_url"),
                                    generated_for=att.get("generated_for"),
                                    quality_score=att.get("quality_score", 0),
                                    generation_time_seconds=att.get("generation_time_seconds", 0),
                                    extra_meta=att.get("metadata"),
                                ))

                        # 5. 写入 learning_events（供 Agent 读取）
                        await learning_record_service.log_event(
                            db=db,
                            user_id=uid,
                            event_type="ai_chat",
                            duration_seconds=len(full_response) // 10,
                            event_data={
                                "question": question_text[:200] if question_text else "",
                                "answer_length": len(full_response),
                                "provider": actual_provider,
                                "session_id": chat_session_id_val,
                            },
                        )
                        await db.commit()
                        print(f"[WS] 行为数据已持久化 (user={uid}, session={chat_session_id_val})")
                        # 把 session_id 回传给前端（首次创建时）
                        if not chat_session_id:
                            await send_chat_event({"type": "chat_session_created", "session_id": int(chat_session_id_val)})
                except Exception as e:
                    print(f"[WS] 行为记录失败: {e}")

            # ═══ 步骤6：数字人 TTS（讯飞 SDK 前端直连，后端不参与语音合成）═══
            if enable_tts and full_response.strip():
                if tts_mode == "iflytek":
                    # 前端使用 AvatarPlatform SDK 直接调用 writeText()，后端不参与
                    print(f"[iFlytek-VH] 前端 SDK 模式，后端跳过 ({len(full_response)} 字)")
                else:
                    await send_chat_event({"type": "tts_error", "message": f"不支持的 TTS 模式: {tts_mode}，仅支持讯飞虚拟人"})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"[WS] 异常: {e}")
        import traceback; traceback.print_exc()
        try:
            await websocket.send_text(json.dumps({"error": str(e)[:200]}))
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
