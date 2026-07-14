"""
多智能体学习系统 API 接口（增强版）
================================

提供 RESTful 和 WebSocket 两种方式调用学习会话

增强点 (v2)：
- 更完善的错误处理和日志
- 会话快照支持（可用于断点续学）
- 响应结构优化，包含更多元数据
- WebSocket 消息类型扩展
- 请求校验增强
"""
import json
import asyncio
import time
import re
from typing import Optional, List

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, Field

from app.utils.logger import get_logger
from app.db.session import get_db
from app.auth import get_current_user, get_required_user
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.models.generated_content import GeneratedContent
from app.services.learning_record_service import learning_record_service

logger = get_logger("api.learning")

router = APIRouter(prefix="/api/learning", tags=["multi-agent-learning"])


# ====== 画像持久化辅助函数 ======

async def _persist_profile_to_api_db(db, user_id: int, profile_data: dict):
    """将 Agent 画像持久化到 student_profiles 表 + users.profile_data"""
    from sqlalchemy.future import select
    from app.models.student_profile import StudentProfile
    from app.models.user import User

    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    record = result.scalar_one_or_none()

    cognitive = profile_data.get("cognitive", {})

    if record:
        record.ability_level = profile_data.get("ability_level", record.ability_level)
        record.learning_style = profile_data.get("learning_style", record.learning_style)
        record.pace = profile_data.get("pace", record.pace)
        record.learning_rhythm = profile_data.get("learning_rhythm", record.learning_rhythm)
        record.knowledge_mastery = profile_data.get("knowledge_mastery", record.knowledge_mastery or {})
        record.activity_score = float(profile_data.get("activity_score", record.activity_score or 0))
        record.focus_score = float(profile_data.get("focus_score", record.focus_score or 75))
        record.resource_preferences = profile_data.get("resource_preferences", record.resource_preferences or {})
        record.error_patterns = profile_data.get("error_patterns", record.error_patterns or [])
        record.primary_error_type = profile_data.get("primary_error_type", record.primary_error_type or "")
        record.strengths = profile_data.get("strengths", record.strengths or [])
        record.weaknesses = profile_data.get("weaknesses", record.weaknesses or [])
        record.interests = profile_data.get("interests", record.interests or [])
        record.confidence_score = float(profile_data.get("confidence_score", record.confidence_score or 60))
        record.cognitive_profile = cognitive
        record.daily_strategy = profile_data.get("daily_strategy", record.daily_strategy or "")
        record.summary = profile_data.get("summary", record.summary or "")
        record.profile_version = (record.profile_version or 1) + 1
        record.source = "agent"
    else:
        record = StudentProfile(
            user_id=user_id,
            ability_level=profile_data.get("ability_level", "beginner"),
            learning_style=profile_data.get("learning_style", "reading"),
            pace=profile_data.get("pace", "moderate"),
            learning_rhythm=profile_data.get("learning_rhythm", "持续型"),
            knowledge_mastery=profile_data.get("knowledge_mastery", {}),
            activity_score=float(profile_data.get("activity_score", 0)),
            focus_score=float(profile_data.get("focus_score", 75)),
            resource_preferences=profile_data.get("resource_preferences", {}),
            error_patterns=profile_data.get("error_patterns", []),
            primary_error_type=profile_data.get("primary_error_type", ""),
            strengths=profile_data.get("strengths", []),
            weaknesses=profile_data.get("weaknesses", []),
            interests=profile_data.get("interests", []),
            confidence_score=float(profile_data.get("confidence_score", 60)),
            cognitive_profile=cognitive,
            daily_strategy=profile_data.get("daily_strategy", ""),
            summary=profile_data.get("summary", ""),
            source="agent",
        )
        db.add(record)

    # 同步 users.profile_data
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.profile_data = profile_data

    logger.info(
        "💾 [API] 画像已持久化: user=%s, level=%s, version=%d",
        user_id, record.ability_level, record.profile_version,
    )


# ====== 安全序列化工具 ======

def _safe_json_serialize(obj) -> any:
    """
    递归确保对象可以安全地进行 JSON 序列化

    处理：
    - 非 str/int/float/bool/list/dict 类型的值转为字符串
    - 嵌套的 dict/list 递归处理
    - None 值保留
    """
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, dict):
        return {str(k): _safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_safe_json_serialize(item) for item in obj]
    else:
        # 其他类型（如自定义对象、set 等）转为字符串
        try:
            return str(obj)
        except Exception:
            return "<unserializable>"


# ====== 请求/响应模型 ======

class LearningSessionRequest(BaseModel):
    """启动学习会话请求"""
    subject: str = Field(..., description="学科/主题，如 '数据结构'", min_length=1)
    goal: str = Field(..., description="学习目标", min_length=1)
    user_id: str = Field(default="default", description="用户标识")
    user_messages: List[str] = Field(default=[], description="历史交互消息")
    max_iterations: int = Field(default=5, ge=1, le=10, description="最大迭代次数")


class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    user_answer: str = Field(..., min_length=1, description="学生提交的答案")
    session_state: Optional[dict] = None


class AgentMessage(BaseModel):
    """Agent 实时消息"""
    agent: str
    level: str = "info"
    message: str
    timestamp: str
    data_type: str = "agent_log"


class ResourceMessage(BaseModel):
    """资源生成消息"""
    resource_type: str
    topic: str
    title: str
    content: str
    format: str
    difficulty: str
    tags: List[str] = []
    data_type: str = "resource"


class StepProgress(BaseModel):
    """步骤进度消息"""
    step_id: int
    topic: str
    status: str
    score: Optional[float] = None
    bloom_level: Optional[str] = None
    data_type: str = "step_progress"


class AssessmentMessage(BaseModel):
    """测评结果消息"""
    overall_score: int
    bloom_scores: dict = {}
    primary_error_type: str = ""
    recommendation: str = ""
    next_action: str = ""
    should_adjust_path: bool = False
    data_type: str = "assessment_result"


class SessionComplete(BaseModel):
    """会话完成消息"""
    summary: dict
    final_state: dict
    data_type: str = "session_complete"


# ================================================================
#                    RESTful API 端点
# ================================================================

@router.post("/session/start")
async def start_learning_session(
    req: LearningSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    启动一次多智能体学习会话（Onboarding 简化版）
    
    流程：
        画像分析 → 路径规划 → 返回结果
    
    返回：
        - student_profile: 学习画像（含认知特征、MBTI 风格、费曼适配度）
        - learning_path: 学习路径步骤（含布鲁姆层级）
        - _summary: 结果摘要
    """
    start_time = time.time()
    
    try:
        from app.agents.graph import run_learning_session
        
        result = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: run_learning_session(
                subject=req.subject,
                goal=req.goal,
                user_id=req.user_id,
                user_messages=req.user_messages,
                max_iterations=req.max_iterations,
            )
        )
        
        elapsed = time.time() - start_time
        
        persisted_plan_id = None
        resolved_user_id = current_user.id if current_user is not None else None
        if resolved_user_id is None and str(req.user_id).isdigit():
            resolved_user_id = int(req.user_id)

        if resolved_user_id is not None:
            snapshot = await learning_record_service.create_profile_snapshot(
                db=db,
                user_id=resolved_user_id,
                profile_data=result.get("student_profile", {}),
                source="agent",
                summary=result.get("_summary", {}).get("profile_summary"),
            )
            plan = await learning_record_service.save_learning_session_result(
                db=db,
                user_id=resolved_user_id,
                subject=req.subject,
                goal=req.goal,
                result=result,
                profile_snapshot_id=snapshot.id,
            )
            await db.commit()
            persisted_plan_id = plan.id if plan else None

        return {
            "success": True,
            "session_id": f"{req.user_id}_{int(time.time())}",
            "elapsed_seconds": round(elapsed, 2),
            "persisted_plan_id": persisted_plan_id,
            **result,
        }
    
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"缺少依赖: {str(e)}。请执行: pip install langgraph"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"学习会话执行失败: {str(e)}"
        )


@router.post("/session/continue")
async def continue_learning_session(
    session_state: dict,
    answer_req: Optional[SubmitAnswerRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    继续一个已有的学习会话
    
    用途：
    - 学生提交答案后，触发测评 → 可能调整路径/继续下一步
    - 或手动要求重新规划路径
    """
    if not session_state:
        raise HTTPException(status_code=400, detail="缺少会话状态")
    
    # 将用户答案加入状态
    if answer_req and answer_req.user_answer:
        session_state.setdefault("user_messages", []).append(answer_req.user_answer)
        session_state["user_answer"] = answer_req.user_answer

    try:
        from app.agents.graph import MultiAgentGraph
        
        graph = MultiAgentGraph().build()
        
        new_state = await asyncio.get_running_loop().run_in_executor(
            None, 
            lambda: graph._compiled.invoke(session_state),
        )
        
        resolved_user_id = session_state.get("user_id")
        if isinstance(resolved_user_id, str) and resolved_user_id.isdigit():
            await learning_record_service.log_event(
                db=db,
                user_id=int(resolved_user_id),
                event_type="session_continue",
                subject=session_state.get("subject"),
                session_id=str(session_state.get("session_snapshot", {}).get("session_id", "")),
                score=(new_state.get("assessment") or {}).get("overall_score"),
                event_data={
                    "next_action": new_state.get("next_action"),
                    "answer_length": len(answer_req.user_answer) if answer_req and answer_req.user_answer else 0,
                },
            )
            await db.commit()

        return {"success": True, **new_state}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================================
#                    v3 事件驱动入口（新）
# ================================================================

class LearningEventRequest(BaseModel):
    """事件驱动学习请求（v3）"""
    event_type: str = Field(
        ...,
        description="事件类型: user_registered / start_learning / ask_question / "
                    "submit_answer / complete_test / complete_learning / "
                    "request_mindmap / request_code_example / request_animation / "
                    "request_exercise / generate_resource / daily_checkin / continue_session"
    )
    subject: str = Field(default="数据结构", description="学科/主题")
    goal: str = Field(default="", description="学习目标")
    user_id: str = Field(default="default", description="用户标识")
    session_state: Optional[dict] = Field(default=None, description="已有会话状态（继续会话时传入）")
    event_data: Optional[dict] = Field(default=None, description="事件数据: {question, answer, resource_type, exam_days, ...}")
    max_iterations: int = Field(default=5, ge=1, le=10, description="最大迭代次数")


@router.post("/event")
async def handle_learning_event(
    req: LearningEventRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    统一事件驱动学习入口（v3）

    替代 session/start 和 session/continue 的单一事件接口。

    所有用户操作都通过此端点进入智能体系统，
    Orchestrator 根据 event_type 自动调度对应的 Agent 链。

    示例：
      # 新用户注册
      POST /api/learning/event
      {"event_type": "user_registered", "subject": "数据结构", "goal": "掌握链表"}

      # 提问
      POST /api/learning/event
      {"event_type": "ask_question", "event_data": {"question": "什么是DFS？"}, "session_state": {...}}

      # 提交答案
      POST /api/learning/event
      {"event_type": "submit_answer", "event_data": {"answer": "..."}, "session_state": {...}}

      # 请求思维导图
      POST /api/learning/event
      {"event_type": "request_mindmap", "event_data": {"topic": "二叉树"}, "session_state": {...}}

    返回字段：
      - session_phase: 会话阶段
      - wait_for_user: 是否需要等待用户下一步操作
      - chat_response: 辅导回答（ask_question 事件）
      - resources: 生成的资源（资源类事件）
      - recommendation: 推荐结果
      - session_state: 完整会话状态（下次调用时传回）
    """
    start_time = time.time()

    try:
        from app.agents.graph import MultiAgentGraph
        from app.agents.state import EventType

        event_payload = req.event_data or {}

        # 合并事件特有数据到状态
        if req.session_state:
            state = dict(req.session_state)
            state["event_type"] = req.event_type
            state["event_payload"] = event_payload
            state["session_status"] = "running"
            state["next_action"] = "orchestrate"

            # 根据事件类型合并数据
            if req.event_type == EventType.SUBMIT_ANSWER:
                answer = event_payload.get("answer", "")
                if answer:
                    state.setdefault("user_messages", []).append(answer)
                    state["user_answer"] = answer
            elif req.event_type == EventType.ASK_QUESTION:
                question = event_payload.get("question", "")
                if question:
                    state.setdefault("user_messages", []).append(question)
                    state["user_answer"] = question

            graph = MultiAgentGraph().build()
            new_state = await asyncio.get_running_loop().run_in_executor(
                None, lambda: graph._compiled.invoke(state)
            )
        else:
            # 新会话
            graph = MultiAgentGraph()
            new_state = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: graph.run(
                    subject=req.subject,
                    goal=req.goal,
                    user_id=req.user_id,
                    event_type=req.event_type,
                    event_payload=event_payload,
                    max_iterations=req.max_iterations,
                )
            )

        elapsed = time.time() - start_time

        # 持久化（如有登录用户）
        resolved_user_id = current_user.id if current_user is not None else None
        if resolved_user_id is None and str(req.user_id).isdigit():
            resolved_user_id = int(req.user_id)

        if resolved_user_id is not None:
            try:
                await learning_record_service.log_event(
                    db=db,
                    user_id=resolved_user_id,
                    event_type=req.event_type,
                    subject=req.subject,
                    session_id=str(new_state.get("session_snapshot", {}).get("session_id", "")),
                    event_data={
                        "session_phase": new_state.get("session_phase"),
                        "elapsed_seconds": round(elapsed, 2),
                    },
                )
                await db.commit()
            except Exception as e:
                logger.debug("事件日志持久化跳过: %s", e)

            # ★ 画像持久化（确保 graph 结果保存到 DB）
            try:
                profile_data = new_state.get("student_profile", {})
                if profile_data and profile_data.get("ability_level"):
                    await _persist_profile_to_api_db(db, resolved_user_id, profile_data)
                    await db.commit()
            except Exception as e:
                logger.debug("画像持久化跳过: %s", e)

        # 构建响应
        decision = new_state.get("orchestrator_decision", {})
        recommendation = new_state.get("recommendation", {})

        response = {
            "success": True,
            "event_type": req.event_type,
            "elapsed_seconds": round(elapsed, 2),
            "session_phase": new_state.get("session_phase", "unknown"),
            "wait_for_user": decision.get("wait_for_user", True),
            "orchestrator_reason": decision.get("reason", ""),
            "chat_response": new_state.get("chat_response"),
            "student_profile": new_state.get("student_profile"),
            "learning_analytics": new_state.get("learning_analytics"),
            "learning_path": new_state.get("learning_path"),
            "resources": new_state.get("resources"),
            "resource_bundle": new_state.get("resource_bundle"),
            "recommendation": recommendation,
            "assessment": new_state.get("assessment"),
            "tutor_response": new_state.get("tutor_response"),
            "session_state": new_state,
            "_summary": new_state.get("_summary"),
        }

        return response

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"缺少依赖: {str(e)}。请执行: pip install langgraph"
        )
    except Exception as e:
        logger.error("事件处理失败: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"事件处理失败: {str(e)}"
        )


@router.get("/graph/info")
async def get_graph_info():
    """获取图结构信息（v3 — Orchestrator 星型拓扑）"""
    from app.agents.graph import MultiAgentGraph
    return {
        "version": "3.0",
        "architecture": "Orchestrator 星型拓扑",
        "principle": "Agent 不直接互相调用，全部通过 Orchestrator 调度",
        "agents": [
            {
                "name": "orchestrator",
                "display_name": "总控 Agent",
                "description": "流程大脑 — 根据用户事件判断下一步调度哪个 Agent，不回答问题",
                "icon": "🧠",
                "outputs": ["orchestrator_decision", "pending_agents", "session_phase"],
                "triggers": "所有用户事件（注册/登录/提问/测试/资源生成等）",
            },
            {
                "name": "profile_agent",
                "display_name": "学生画像 Agent",
                "description": "维护 student_profile 表，建立/更新画像。不生成资源、不回答问题",
                "icon": "📊",
                "outputs": ["student_profile"],
                "inputs": "注册信息 + LearningAnalytics + Assessment",
            },
            {
                "name": "learning_analytics_agent",
                "display_name": "数据分析 Agent",
                "description": "数据分析中心 — 计算活跃度/专注度/资源偏好/知识掌握/错误模式",
                "icon": "📈",
                "outputs": ["learning_analytics"],
                "inputs": "数据库行为记录 + 测评结果 + 学习路径进展",
            },
            {
                "name": "planner_agent",
                "display_name": "学习规划 Agent",
                "description": "基于画像 + 知识图谱 + 考试时间规划个性化学习路径，支持动态调整",
                "icon": "📋",
                "outputs": ["learning_path"],
                "enhancements": ["掌握度驱动跳过", "学习节奏适配", "考试时间约束", "每日日程建议"],
            },
            {
                "name": "resource_agent",
                "display_name": "资源工厂 Agent",
                "description": "先检索资源库复用，无则 AI 生成。讲义/思维导图/练习题/代码案例/动画",
                "icon": "📦",
                "outputs": ["resources", "resource_bundle"],
                "strategy": "先检索后生成，保存到资源库供复用",
            },
            {
                "name": "recommendation_agent",
                "display_name": "推荐 Agent",
                "description": "首页个性化推荐 — 基于画像/知识掌握度/资源偏好排序",
                "icon": "🎯",
                "outputs": ["recommendation"],
                "strategy": "薄弱点优先 + 偏好加权 + 已掌握降权",
            },
            {
                "name": "tutor_agent",
                "display_name": "辅导 Agent",
                "description": "学习老师 — 结合知识库/画像/聊天历史/错题本给出个性化教学回答",
                "icon": "👨‍🏫",
                "outputs": ["tutor_response", "chat_response"],
                "context": "知识库 + 学生画像 + 聊天历史 + 错题本",
            },
            {
                "name": "assessment_agent",
                "display_name": "测评 Agent",
                "description": "多维度评估（布鲁姆六维），错误模式识别，知识掌握追踪",
                "icon": "📝",
                "outputs": ["assessment"],
            },
        ],
        "events": [
            {"type": "user_registered", "workflow": "profile → assessment", "description": "注册 → 建立画像 + 初始测试"},
            {"type": "start_learning", "workflow": "analytics → profile → planner → resource → recommendation", "description": "开始学习完整流程"},
            {"type": "ask_question", "workflow": "tutor", "description": "提问 → 直接辅导回答"},
            {"type": "complete_test", "workflow": "assessment → analytics → profile → planner → recommendation", "description": "完成测试 → 评估 + 更新 + 调整路径"},
            {"type": "submit_answer", "workflow": "assessment", "description": "提交答案 → 即时评估"},
            {"type": "request_mindmap", "workflow": "resource", "description": "请求思维导图 → 仅生成思维导图"},
            {"type": "request_code_example", "workflow": "resource", "description": "请求代码案例 → 仅生成代码"},
            {"type": "request_animation", "workflow": "resource", "description": "请求动画 → 仅生成动画"},
            {"type": "complete_learning", "workflow": "analytics → profile → recommendation", "description": "完成学习 → 分析 + 更新画像 + 刷新推荐"},
        ],
        "data_loop": "用户行为 → LearningAnalytics → Profile → Planner → Resource → Recommendation → Tutor → 新的学习行为",
        "state_model": {
            "inputs": ["subject", "goal", "user_id", "user_messages", "event_type", "event_payload"],
            "outputs": ["student_profile", "learning_analytics", "learning_path", "resources", "resource_bundle", "recommendation", "tutor_response", "chat_response", "assessment"],
            "control_fields": ["next_action", "orchestrator_decision", "pending_agents", "session_phase", "iteration_count", "session_status"],
        },
        "mermaid": MultiAgentGraph.get_graph_visualization() if hasattr(MultiAgentGraph, 'get_graph_visualization') else "",
    }


@router.get("/graph/mermaid")
async def get_mermaid_graph():
    """获取 Mermaid 图定义（前端可渲染流程图）"""
    from app.agents.graph import MultiAgentGraph
    return {
        "mermaid": MultiAgentGraph.get_graph_visualization()
    }


class GenerateResourceRequest(BaseModel):
    """单类型资源生成请求"""
    resource_type: str = Field(..., description="资源类型: notes/mindmap/quiz/code_example/animation。ppt_outline 请使用 /api/ppt/ 专用接口")
    subject: str = Field(..., description="学科/主题")
    topic: str = Field(default="", description="具体知识点（可选）")
    goal: str = Field(default="", description="学习目标（可选）")
    user_id: str = Field(default="default", description="用户标识")
    student_profile: Optional[dict] = None  # 可传入已有画像
    gaps_found: Optional[list] = None       # 可传入已知薄弱点


class GenerateBundleRequest(BaseModel):
    """资源包生成请求"""
    subject: str = Field(..., description="学科/主题", min_length=1)
    topic: str = Field(default="", description="具体知识点（可选）")
    goal: str = Field(default="", description="学习目标（可选）")
    user_id: str = Field(default="default", description="用户标识")
    student_profile: Optional[dict] = None
    gaps_found: Optional[list] = None


@router.post("/resource/generate")
async def generate_single_resource(req: GenerateResourceRequest):
    """
    按需生成单个类型的学习资源
    
    前端点击某个卡片上的(生成)按钮时调用此接口，
    只返回一种类型的资源，响应更快。
    
    支持的资源类型：
      - notes:        学习讲义 (Markdown)
      - mindmap:      思维导图 (Mermaid 格式)
      - quiz:         练习题 (结构化 JSON 数组)
      - code_example: 代码案例 (Python，可运行)
      - animation:    动画视频 (Manim)

    注：ppt_outline 已迁移至独立 PPT 智能生成器（/api/ppt/parse-mindmap + /api/ppt/render）。
    """
    import time as _time
    start_time = _time.time()

    # 校验类型
    valid_types = {"notes", "mindmap", "quiz", "code_example", "animation"}
    if req.resource_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"不支持的资源类型: {req.resource_type}，支持: {valid_types}")

    topic = req.topic or req.subject

    try:
        from app.agents.resource_agent import ResourceGenerationAgent

        agent = ResourceGenerationAgent()
        
        # 构造基础 state
        state = {
            "student_profile": req.student_profile or {
                "ability_level": "intermediate",
                "learning_preference": "visual",
                "weaknesses": [],
                "cognitive_profile": {"mbti_style": "balanced", "feynman_score": 0.7},
            },
            "learning_path": [{
                "step_id": 1,
                "topic": topic,
                "description": req.goal or f"深入学习{topic}",
                "difficulty": "medium",
                "bloom_level": "understand",
                "prerequisites": [],
                "status": "in_progress",
                "resources_generated": False,
                "estimated_minutes": 15,
            }],
            "assessment": {
                "gaps_found": req.gaps_found or [],
                "bloom_scores": {},
                "overall_score": 0,
            },
            "resources": [],
            "subject": req.subject,
            "current_step_index": 0,
            "messages": [],
        }

        # 只生成指定类型的那一个资源
        def gen_one():
            try:
                for res in agent.generate_resources(state, only_type=req.resource_type):
                    return res
            except Exception as gen_err:
                logger.error("❌ generate_resources 内部异常: %s", type(gen_err).__name__, exc_info=True)
                raise
            return None

        try:
            result = await asyncio.get_running_loop().run_in_executor(None, gen_one)
        except Exception as exec_err:
            logger.error("❌ run_in_executor 异常: %s", exec_err, exc_info=True)
            raise HTTPException(status_code=500, detail=f"执行异常: {str(exec_err)}")

        elapsed = _time.time() - start_time

        if not result:
            raise HTTPException(status_code=500, detail=f"资源生成未返回结果: {req.resource_type}")

        # 确保响应数据可以安全序列化
        try:
            # 先测试序列化，提前发现问题
            json.dumps(result, ensure_ascii=False)
        except (TypeError, ValueError) as ser_err:
            logger.warning("⚠️ 原始结果不可序列化，类型=%s, 错误=%s", type(result), ser_err)
            result = _safe_json_serialize(result)
            logger.info("✅ 安全转换完成")

        # 最终返回前再次校验整个响应
        try:
            response_data = {
                "success": True,
                "elapsed_seconds": round(elapsed, 2),
                "data": result,
            }
            json.dumps(response_data, ensure_ascii=False)  # 预检验整个响应
            return response_data
        except (TypeError, ValueError) as final_err:
            logger.error("❌ 最终响应仍不可序列化: %s", final_err, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"响应序列化失败（这是系统 Bug，请联系管理员）"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ 单资源生成异常 (%s): %s", req.resource_type, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"{req.resource_type} 资源生成失败: {str(e)}"
        )



# ================================================================
#              动画视频生成 API (Manim)
# ================================================================

class AnimationGenerateRequest(BaseModel):
    """动画视频生成请求"""
    topic: str = Field(default="", description="要可视化的算法/概念（自动识别时的标题）")
    subject: str = Field(default="数据结构与算法", description="学科")
    goal: str = Field(default="", description="描述（可选，旧版兼容）")
    difficulty: str = Field(default="medium", description="难度: easy/medium/hard")
    scene_name: str = Field(default="AlgorithmScene", description="Manim Scene 类名")

    # ── 智能识别模式 ──
    input_mode: str = Field(
        default="manim_code",
        description="输入模式: 'description'(自然语言描述) | 'code'(粘贴算法代码) | 'manim_code'(直接Manim代码)"
    )
    input_text: Optional[str] = Field(
        None,
        description="智能模式的输入文本（自然语言描述或算法代码）"
    )
    code_language: Optional[str] = Field(
        None,
        description="粘贴代码的语言（python/java/cpp/js等），帮助 LLM 理解"
    )

    # ── 旧版兼容 ──
    custom_code: Optional[str] = Field(None, description="用户自定义的 Manim 代码（旧版兼容，等同于 input_mode='manim_code'）")
    timeout: int = Field(default=120, ge=10, le=300, description="渲染超时(秒)")


# ── 智能识别：自然语言/代码 → Manim 动画代码 Prompt ──

def _build_smart_animation_prompt(
    input_text: str,
    input_mode: str,
    code_language: str | None = None,
    scene_name: str = "AlgorithmScene",
) -> str:
    """
    根据输入模式构建 LLM prompt

    Args:
        input_text: 用户输入的文字描述或代码
        input_mode: 'description'(文字描述) | 'code'(粘贴代码)
        code_language: 代码语言（仅 code 模式）
        scene_name: Manim Scene 类名
    """
    if input_mode == "description":
        return f"""你是一位算法可视化专家和 Manim 动画大师。

## 任务
用户用自然语言描述了一个想要可视化的算法/概念，请编写完整的 Manim Community Edition Python 代码生成教学动画。

## 用户描述
{input_text}

## 要求

### 代码结构：
```python
class {scene_name}(Scene):
    def construct(self):
        # 动画代码
        pass
```

### 动画设计原则：
1. **渐进式展示**：不要一次性显示所有内容
2. **颜色编码**：用不同颜色区分不同元素
3. **文字标注**：关键步骤添加文字说明
4. **节奏控制**：适当使用 wait() 让观众消化
5. **行列排列美观**：用 VGroup + arrange 保持整齐

### 技术约束：
- 使用 manim Community Edition 语法（兼容 v0.18+）
- ⚠️ 不要设置 config.media_width / config.media_height（系统会自动注入字符串值）
- 场景类名必须是 `{scene_name}`
- 只使用 manim + numpy
- 背景色: config.background_color = "#1a1a2e"
- 总帧数控制在 300~800 帧

### ⚠️ 重要提醒：
- 你只能输出 Python 代码，不要包含「```」标记
- 不要输出解释性文字
- 代码必须可执行

请直接输出完整 Python 代码："""

    elif input_mode == "code":
        lang_hint = f"（{code_language}语言）" if code_language else ""
        return f"""你是一位算法可视化专家和 Manim 动画大师。

## 任务
用户粘贴了一段算法代码{lang_hint}，请分析这段代码的算法逻辑，然后编写 Manim Community Edition Python 代码生成对应的动画演示。

## 用户代码
```{code_language or 'plain'}
{input_text}
```

## 你的工作
1. **分析算法**：理解代码的算法逻辑（数据结构、关键步骤、核心操作）
2. **设计可视化**：规划如何用动画展示算法执行过程
3. **编写动画**：输出完整的 Manim 代码

### 动画设计原则：
1. **展示算法核心步骤**：排序比较/交换、查找比较、遍历路径、递归展开等
2. **颜色编码**：不同状态用不同颜色（当前操作→黄色，已完成→绿色，待处理→蓝色）
3. **文字标注**：关键步骤添加 Text 说明（如 "比较 arr[2] 和 arr[3]"）
4. **节奏控制**：适当使用 wait()
5. **数据生成**：可用小规模随机数据演示（6~10个元素）

### 技术约束：
- 使用 manim Community Edition 语法（兼容 v0.18+）
- ⚠️ 不要设置 config.media_width / config.media_height（系统会自动注入字符串值）
- 场景类名必须是 `{scene_name}`
- 只使用 manim + numpy
- 背景色: config.background_color = "#1a1a2e"
- 总帧数 300~800 帧

### ⚠️ 重要提醒：
- 你只能输出 Python 代码，不要包含「```」标记
- 不要输出解释性文字
- 代码必须包含 `class {scene_name}(Scene):` 和 `def construct(self):`
- 如果用户代码是面向对象的（如 TreeNode 类），请在动画中展示其数据结构+遍历过程

请直接输出完整 Python 代码："""

    # fallback: manim_code mode
    return ""


@router.post("/animation/generate")
async def generate_animation_video(req: AnimationGenerateRequest):
    """
    生成算法动画视频 (LLM + Manim)

    支持三种输入模式：
    - input_mode='description': 自然语言描述 → LLM 生成动画
    - input_mode='code': 粘贴算法代码 → LLM 分析并生成动画
    - input_mode='manim_code' 或 custom_code: 直接渲染 Manim 代码

    流程：
    1. LLM 根据输入生成 Manim Python 代码
    2. 沙箱环境执行代码渲染 MP4
    3. 返回视频URL + 可编辑源码
    """
    import time as _time
    start_time = _time.time()

    # 确定 topic（用于标题和文档命名）
    topic = req.topic or req.subject or "算法动画"
    if req.input_text and not req.topic:
        # 从输入文本中提取简短标题
        topic = req.input_text.strip()[:30]

    try:
        from app.services.manim_renderer import get_renderer

        renderer = get_renderer()

        if not renderer.available:
            raise HTTPException(
                status_code=503,
                detail="Manim 渲染服务不可用（后端未安装 manim）"
            )

        # 步骤1：获取或生成 Manim 代码
        if req.custom_code:
            # 旧版兼容：直接 Manim 代码
            manim_code = req.custom_code
            logger.info("🎬 使用用户自定义 Manim 代码")
        elif req.input_mode in ("description", "code") and req.input_text:
            # 智能模式：自然语言/代码 → LLM 生成 Manim 代码
            logger.info("🎬 智能模式 [%s] 生成 Manim 代码", req.input_mode)
            prompt = _build_smart_animation_prompt(
                input_text=req.input_text,
                input_mode=req.input_mode,
                code_language=req.code_language,
                scene_name=req.scene_name,
            )

            def llm_gen_code():
                from app.agents.resource_agent import ResourceGenerationAgent
                agent = ResourceGenerationAgent()
                messages = [
                    {"role": "system", "content": "你是 Manim 动画专家。你只能输出 Python 代码，不要带 ``` 标记，不要输出解释文字。代码必须包含 class 和 def construct。"},
                    {"role": "user", "content": prompt},
                ]
                result = agent._call_llm(messages, temperature=0.7, max_tokens=4096)
                return result

            raw_code = await asyncio.get_running_loop().run_in_executor(None, llm_gen_code)
            manim_code = _clean_manim_code(raw_code)
            logger.info("✅ 智能生成 Manim 代码 (%d 字符)", len(manim_code))
        else:
            # 默认：根据 topic 生成（旧版自动模式）
            from app.services.manim_renderer import build_animation_prompt
            logger.info("🎬 调用 LLM 生成 Manim 代码: %s", topic)
            prompt = build_animation_prompt(
                topic=topic,
                description=req.goal,
                difficulty=req.difficulty,
                scene_name=req.scene_name,
            )

            def llm_gen_code():
                from app.agents.resource_agent import ResourceGenerationAgent
                agent = ResourceGenerationAgent()
                messages = [
                    {"role": "system", "content": "你是 Manim 动画专家。只输出可执行的 Python 代码，不要 markdown 包裹。"},
                    {"role": "user", "content": prompt},
                ]
                result = agent._call_llm(messages, temperature=0.8, max_tokens=4096)
                return result

            raw_code = await asyncio.get_running_loop().run_in_executor(None, llm_gen_code)
            manim_code = _clean_manim_code(raw_code)
            logger.info("✅ Manim 代码已生成 (%d 字符)", len(manim_code))

        # 步骤2：沙箱渲染
        logger.info("🎬 开始渲染 Manim 视频...")

        def do_render():
            return renderer.render(
                code=manim_code,
                scene_name=req.scene_name,
                timeout=req.timeout,
            )

        render_result = await asyncio.get_running_loop().run_in_executor(None, do_render)

        elapsed = _time.time() - start_time

        if not render_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"视频渲染失败: {render_result.get('error', '未知错误')}"
            )

        # 构建响应
        response_data = {
            "success": True,
            "elapsed_seconds": round(elapsed, 2),
            "data": {
                "type": "animation",
                "topic": topic,
                "title": f"🎬 动画演示：{topic}",
                "content": render_result.get("source_code", ""),
                "format": "manim",
                "video_url": render_result.get("video_url"),
                "thumbnail_url": render_result.get("thumbnail_url"),
                "render_time": render_result.get("render_time", 0),
                "scene_name": req.scene_name,
                "logs": render_result.get("logs", "")[-1000:] if render_result.get("logs") else "",
                "input_text": req.input_text or "",
                "input_mode": req.input_mode or "manim_code",
            },
        }

        # 序列化校验
        json.dumps(response_data, ensure_ascii=False)

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ 动画生成异常: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"动画生成失败: {str(e)}")


@router.post("/animation/rerender")
async def rerender_animation(req: AnimationGenerateRequest):
    """重新渲染动画（用户修改代码后调用）"""
    if not req.custom_code:
        raise HTTPException(status_code=400, detail="重新渲染需要提供 custom_code")

    req.topic = req.topic or "算法动画"
    return await generate_animation_video(req)


def _clean_manim_code(raw: str) -> str:
    """清理 LLM 输出的 Manim 代码"""
    code = raw.strip()

    # 移除 markdown 代码块标记
    code = re.sub(r"^```(?:python|manim)?\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"```\s*$", "", code, flags=re.MULTILINE)

    # 确保有 class 定义但没有重复 header
    if "from manim import" not in code and "class " in code:
        code = MANIM_HEADER_PREFIX + "\n" + code

    return code


MANIM_HEADER_PREFIX = '''from manim import *
import numpy as np

config.media_width = "1920"
config.media_height = "1080"
config.frame_rate = 30
config.background_color = "#1a1a2e"

'''


@router.post("/resource/bundle")
async def generate_resource_bundle(req: GenerateBundleRequest):
    """
    生成完整的资源包（一次返回）

    返回结构：
    {
        "notes": "学习讲义 (Markdown)",
        "mindmap": "思维导图 (Mermaid)",
        "quiz": [练习题数组],
        "code_example": "Python 代码案例",
        "animation": "动画视频 (Manim)"
    }

    注：ppt_outline 已迁移至独立 PPT 智能生成器（/api/ppt/ 接口）。
    """
    import time as _time
    start_time = _time.time()

    topic = req.topic or req.subject

    try:
        from app.agents.resource_agent import ResourceGenerationAgent

        agent = ResourceGenerationAgent()

        # 构造基础 state
        state = {
            "student_profile": req.student_profile or {
                "ability_level": "intermediate",
                "learning_style": "reading",
                "weaknesses": [],
                "cognitive": {"mbti_style": "sentinel", "feynman_adaptation": 0.5},
            },
            "learning_path": [{
                "step_id": 1,
                "topic": topic,
                "description": req.goal or f"深入学习{topic}",
                "difficulty": "medium",
                "bloom_level": "understand",
                "prerequisites": [],
                "status": "in_progress",
                "resources_generated": False,
                "estimated_minutes": 15,
            }],
            "assessment": {
                "gaps_found": req.gaps_found or [],
                "bloom_scores": {},
                "overall_score": 0,
            },
            "resources": [],
            "resource_bundle": {},
            "subject": req.subject,
            "current_step_index": 0,
            "messages": [],
        }

        # 生成完整资源包
        bundle = await asyncio.get_running_loop().run_in_executor(None, lambda: agent.generate_resource_bundle(state))

        elapsed = _time.time() - start_time

        if not bundle:
            raise HTTPException(status_code=500, detail="资源包生成未返回结果")

        # 确保响应数据可以安全序列化
        try:
            json.dumps(dict(bundle), ensure_ascii=False)
        except (TypeError, ValueError) as ser_err:
            logger.warning("⚠️ 资源包不可序列化，进行安全转换: %s", ser_err)
            bundle = _safe_json_serialize(dict(bundle))

        return {
            "success": True,
            "elapsed_seconds": round(elapsed, 2),
            "topic": topic,
            "data": dict(bundle) if isinstance(bundle, dict) else bundle,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ 资源包生成异常: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"资源包生成失败: {str(e)}"
        )


# ================================================================
#                   WebSocket 实时流式接口
# ================================================================

@router.websocket("/ws/session")
async def websocket_learning_session(websocket: WebSocket):
    """
    WebSocket 实时学习会话 — 支持流式推送
    
    Client → Server:
        {"action": "start", "subject": "...", "goal": "..."}
        {"action": "submit_answer", "answer": "..."}
        {"action": "cancel"}
    
    Server → Client:
        {"type": "status", "message": "..."}           — 状态更新
        {"type": "agent_log", ...}                     — Agent 决策日志
        {"type": "resource", ...}                       — 资源生成完成
        {"type": "step_progress", ...}                  — 步骤状态变更
        {"type": "assessment_result", ...}              — 测评结果推送
        {"type": "session_complete", ...}               — 会话结束
        {"type": "error", "message": "..."}             — 错误信息
    """
    await websocket.accept()
    logger.info("✅ WebSocket 连接已建立")

    current_state = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "无效的 JSON 格式"
                }, ensure_ascii=False))
                continue

            action = data.get("action", "")

            if action == "start":
                await _handle_ws_start(websocket, data)

            elif action == "submit_answer" and current_state:
                await _handle_ws_submit(websocket, data, current_state)

            elif action == "cancel":
                await websocket.send_text(json.dumps({
                    "type": "info",
                    "message": "会话已取消"
                }, ensure_ascii=False))
                break
            
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"未知操作: {action}"
                }, ensure_ascii=False))

    except WebSocketDisconnect:
        logger.info("🔌 客户端断开连接")
    except Exception as e:
        logger.error("❌ WebSocket 错误: %s", e)
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False))
        except:
            pass


async def _handle_ws_start(websocket: WebSocket, data: dict):
    """处理启动学习会话（WebSocket 版本）"""
    global current_state
    
    subject = data.get("subject", "")
    goal = data.get("goal", "")
    user_id = data.get("user_id", "default")
    max_iterations = data.get("max_iterations", 5)

    await _ws_send(websocket, {
        "type": "status",
        "message": f"🚀 启动学习会话 | 学科: {subject} | 目标: {goal}"
    })

    try:
        from app.agents.graph import run_learning_session

        def execute_session():
            return run_learning_session(
                subject=subject,
                goal=goal,
                user_id=user_id,
                max_iterations=max_iterations,
            )

        result = await asyncio.get_running_loop().run_in_executor(None, execute_session)
        current_state = result

        # 发送最终结果
        assessment = result.get("assessment", {})
        
        await _ws_send(websocket, {
            "type": "session_complete",
            "summary": result.get("_summary", {}),
            "final_state": {
                "student_profile": result.get("student_profile", {}),
                "learning_path": result.get("learning_path", []),
                "resources_count": len(result.get("resources", [])),
                "assessment": {
                    "overall_score": assessment.get("overall_score"),
                    "bloom_scores": assessment.get("bloom_scores", {}),
                    "primary_error_type": assessment.get("error_analysis", {}).get("primary_error_type"),
                    "recommendation": assessment.get("recommendation", ""),
                    "gaps_found": assessment.get("gaps_found", []),
                },
                "snapshot": result.get("session_snapshot"),
            },
        }, ensure_ascii=False)

    except ImportError as e:
        await _ws_send(websocket, {
            "type": "error",
            "message": f"缺少依赖: {str(e)}。请安装 langgraph"
        })
    except Exception as e:
        await _ws_send(websocket, {
            "type": "error",
            "message": f"会话执行失败: {str(e)}"
        })


async def _handle_ws_submit(
    websocket: WebSocket,
    data: dict,
    state: dict,
):
    """处理提交答案并触发后续流程（WebSocket 版本）"""
    global current_state
    
    answer = data.get("answer", "")
    
    state["user_messages"] = state.get("user_messages", []) + [answer]
    state["user_answer"] = answer

    await _ws_send(websocket, {
        "type": "status",
        "message": f"✅ 已收到答案 ({len(answer)} 字符)，正在进行测评..."
    })

    try:
        from app.agents.graph import MultiAgentGraph
        graph = MultiAgentGraph().build()

        new_state = await asyncio.get_running_loop().run_in_executor(
            None,
            lambda: graph._compiled.invoke(state),
        )

        current_state = new_state
        assessment = new_state.get("assessment", {})

        await _ws_send(websocket, {
            "type": "assessment_result",
            "overall_score": assessment.get("overall_score"),
            "bloom_scores": assessment.get("bloom_scores", {}),
            "primary_error_type": assessment.get("error_analysis", {}).get("primary_error_type", ""),
            "recommendation": assessment.get("recommendation", "")[:200],
            "next_action": new_state.get("next_action", ""),
            "should_adjust_path": assessment.get("should_adjust_path", False),
            "gaps_found": assessment.get("gaps_found", []),
        }, ensure_ascii=False)

    except Exception as e:
        await _ws_send(websocket, {
            "type": "error",
            "message": str(e)
        })


async def _ws_send(websocket: WebSocket, data: dict, **kwargs):
    """WebSocket 安全发送封装"""
    try:
        await websocket.send_text(json.dumps(data, **kwargs))
    except Exception as e:
        logger.warning("WebSocket 发送失败: %s", e)


# ================================================================
#              流式资源生成 WebSocket 接口
# ================================================================

@router.websocket("/ws/resources")
async def websocket_stream_resources(websocket: WebSocket):
    """
    流式资源生成接口 — 逐个推送 6 种学习资源
    
    Client → Server:
        {"action": "generate", "subject": "...", "goal": "...", "topic": "..."}
    
    Server → Client（流式推送）：
        {"type": "status", "message": "..."}           — 状态
        {"type": "resource_start", "resource_type": "lecture"}  — 开始生成某类型
        {"type": "resource", "data": {...}}             — 单个资源完成（共推送 6 次）
        {"type": "progress", "current": 3, "total": 6}  — 进度更新
        {"type": "complete", "total_resources": 6}      — 全部完成
        {"type": "error", "message": "..."}              — 错误
    
    前端可以实时展示每个资源的卡片，无需等待全部完成。
    """
    await websocket.accept()
    logger.info("✅ 流式资源生成连接已建立")

    try:
        while True:
            raw_data = await websocket.receive_text()
            
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await _ws_send(websocket, {
                    "type": "error", "message": "无效的 JSON 格式"
                })
                continue

            action = data.get("action", "")

            if action == "generate":
                await _handle_ws_generate_resources(websocket, data)
            elif action == "ping":
                await _ws_send(websocket, {"type": "pong"})
            else:
                await _ws_send(websocket, {
                    "type": "error",
                    "message": f"未知操作: {action}，支持: generate, ping"
                })

    except WebSocketDisconnect:
        logger.info("🔌 流式资源客户端断开")
    except Exception as e:
        logger.error("❌ 流式资源生成错误: %s", e)
        try:
            await _ws_send(websocket, {"type": "error", "message": str(e)})
        except:
            pass


async def _handle_ws_generate_resources(websocket: WebSocket, data: dict):
    """处理流式资源生成请求"""
    subject = data.get("subject", "数据结构与算法")
    goal = data.get("goal", "")
    topic = data.get("topic", subject)
    user_id = data.get("user_id", "default")

    # 先启动一次完整会话获取 state（包含画像、路径等）
    await _ws_send(websocket, {
        "type": "status",
        "message": f"🚀 开始为 {topic} 生成 AI 学习资源..."
    })

    try:
        from app.agents.graph import run_learning_session
        from app.agents.resource_agent import ResourceGenerationAgent

        # 步骤1：运行完整会话获取状态
        await _ws_send(websocket, {
            "type": "status",
            "message": "📊 正在分析学生画像 & 规划学习路径..."
        })

        loop = asyncio.get_running_loop()

        # 执行完整会话获取 state
        session_result = await loop.run_in_executor(
            None,
            lambda: run_learning_session(
                subject=subject,
                goal=goal or f"深入学习{topic}",
                user_id=user_id,
                max_iterations=1,  # 只需要一轮来获取资源和路径
            )
        )

        # 如果会话已经返回了资源，直接使用
        existing_resources = session_result.get("resources", [])
        if existing_resources:
            total = len(existing_resources)
            for i, res in enumerate(existing_resources, 1):
                await _ws_send(websocket, {
                    "type": "resource_start",
                    "resource_type": res.get("type", "unknown"),
                    "resource_title": res.get("title", ""),
                })
                
                # 模拟一点点延迟让前端有动画效果
                import asyncio as aio
                await aio.sleep(0.2)

                await _ws_send(websocket, {
                    "type": "resource",
                    "data": res,
                })

                await _ws_send(websocket, {
                    "type": "progress",
                    "current": i,
                    "total": total,
                    "resource_type": res.get("type"),
                })

            await _ws_send(websocket, {
                "type": "complete",
                "total_resources": total,
                "session_data": {
                    "profile": session_result.get("student_profile", {}),
                    "learning_path": session_result.get("learning_path", []),
                    "assessment": session_result.get("assessment", {}),
                },
            }, ensure_ascii=False)
            return

        # 步骤2：如果没有资源，用 Agent 的 generate_resources 流式生成
        agent = ResourceGenerationAgent()
        
        # 构造一个基础 state 用于资源生成
        state_for_resource = {
            "student_profile": session_result.get("student_profile", {}),
            "learning_path": session_result.get("learning_path", [
                {
                    "step_id": 1,
                    "topic": topic,
                    "description": goal or f"深入学习{topic}",
                    "difficulty": data.get("difficulty", "medium"),
                    "bloom_level": data.get("bloom_level", "understand"),
                    "prerequisites": [],
                    "status": "pending",
                    "resources_generated": False,
                    "estimated_minutes": 15,
                }
            ]),
            "assessment": session_result.get("assessment", {}),
            "resources": [],
            "subject": subject,
            "current_step_index": 0,
            "messages": [],
        }

        total_types = len(agent.RESOURCE_TYPES)
        generated_count = 0

        # 流式逐个生成并推送
        def gen_all():
            return list(agent.generate_resources(state_for_resource))

        resources = await asyncio.get_running_loop().run_in_executor(None, gen_all)

        for i, resource in enumerate(resources, 1):
            generated_count = i
            
            # 通知前端开始渲染这个资源
            await _ws_send(websocket, {
                "type": "resource_start",
                "resource_type": resource.get("type", "unknown"),
                "resource_title": resource.get("title", ""),
            })

            # 小延迟让 UI 有加载动画效果
            import asyncio as aio
            await aio.sleep(0.15)

            # 推送实际资源数据
            await _ws_send(websocket, {
                "type": "resource",
                "data": resource,
            })

            # 推送进度
            await _ws_send(websocket, {
                "type": "progress",
                "current": generated_count,
                "total": total_types,
                "resource_type": resource.get("type"),
            })

        # 全部完成
        await _ws_send(websocket, {
            "type": "complete",
            "total_resources": generated_count,
            "session_data": {
                "profile": session_result.get("student_profile", {}),
                "learning_path": session_result.get("learning_path", []),
                "assessment": session_result.get("assessment", {}),
            },
        }, ensure_ascii=False)

    except ImportError as e:
        await _ws_send(websocket, {
            "type": "error",
            "message": f"缺少依赖: {str(e)}"
        })
    except Exception as e:
        logger.error("❌ 资源生成异常: %s", e, exc_info=True)
        await _ws_send(websocket, {
            "type": "error",
            "message": f"资源生成失败: {str(e)}"
        })


# ══════════════════════════════════════════════════════════════════
#  学习资源持久化 API — 保存 / 查询 / 删除（温故知新）
# ══════════════════════════════════════════════════════════════════

class SaveResourceRequest(BaseModel):
    """保存生成的学习资源"""
    resource_type: str = Field(..., description="资源类型: mindmap/notes/quiz/code_example/example/common_mistakes/ppt/animation")
    title: str = Field(..., description="资源标题")
    content_text: Optional[str] = Field(None, description="文本内容（Markdown/代码/大纲等）")
    content_json: Optional[dict] = Field(None, description="结构化数据（练习题选项等）")
    file_url: Optional[str] = Field(None, description="视频/文件 URL")
    topic_tag: Optional[str] = Field(None, description="知识点 ID（如 ch04_string）")
    topic_name: Optional[str] = Field(None, description="知识点/章节名称")
    chapter_name: Optional[str] = Field(None, description="所属大章名称")
    format: str = Field(default="markdown", description="内容格式")


@router.post("/resource/saved")
async def save_resource(
    req: SaveResourceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """保存一个 AI 生成的学习资源到持久化存储"""
    content = GeneratedContent(
        user_id=current_user.id,
        content_type=req.resource_type,
        title=req.title,
        content_text=req.content_text,
        content_json=req.content_json or {},
        file_url=req.file_url,
        topic_tag=req.topic_tag,
        description=req.chapter_name,           # 用 description 存储章节名
        format=req.format,
    )

    db.add(content)
    await db.commit()
    await db.refresh(content)

    logger.info(f"[Resource] 保存学习资源: type={req.resource_type}, id={content.id}, "
                f"topic={req.topic_tag}, user={current_user.id}")

    return {"success": True, "id": content.id, "message": "保存成功"}


@router.get("/resource/saved")
async def list_saved_resources(
    resource_type: Optional[str] = None,
    topic_tag: Optional[str] = None,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """查询当前用户保存的所有学习资源，可按类型/知识点过滤"""
    query = select(GeneratedContent).where(GeneratedContent.user_id == current_user.id)

    if resource_type:
        query = query.where(GeneratedContent.content_type == resource_type)
    if topic_tag:
        query = query.where(GeneratedContent.topic_tag == topic_tag)

    query = query.order_by(desc(GeneratedContent.created_at)).limit(limit)

    result = await db.execute(query)
    contents = result.scalars().all()

    # 返回扁平列表 + 按章节分组的结构
    flat_list = [c.to_dict() for c in contents]

    # 按 chapter_name 分组
    grouped = {}
    for item in flat_list:
        chapter = item.get("description") or "其他"
        if chapter not in grouped:
            grouped[chapter] = {
                "chapter_name": chapter,
                "resources": [],
            }
        grouped[chapter]["resources"].append(item)

    return {
        "success": True,
        "total": len(flat_list),
        "items": flat_list,
        "chapters": list(grouped.values()),
    }


@router.delete("/resource/saved/{resource_id}")
async def delete_saved_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """删除一个已保存的学习资源"""
    result = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.id == resource_id,
            GeneratedContent.user_id == current_user.id,
        )
    )
    content = result.scalar_one_or_none()

    if not content:
        raise HTTPException(status_code=404, detail="资源不存在或无权限")

    db.delete(content)
    await db.commit()

    logger.info(f"[Resource] 删除学习资源: id={resource_id}, user={current_user.id}")

    return {"success": True, "message": "已删除"}
