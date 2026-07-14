"""
Orchestrator 统一入口 API

所有前端事件通过此 API 进入多智能体管线：
- 提问 → TutorAgent
- 完成练习 → AssessmentAgent → LearningAnalytics → Profile
- 资源查看 → LearningAnalytics (记录行为)

这样前端不需要知道内部 Agent 如何调度，
也不直接调用各个 Agent。
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth import get_current_user, get_required_user
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger("api.orchestrated")

router = APIRouter(prefix="/api/learning", tags=["orchestrated-learning"])


async def _persist_profile(db: AsyncSession, user_id: int, profile_data: dict):
    """画像持久化辅助函数"""
    from sqlalchemy.future import select
    from app.models.student_profile import StudentProfile

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

    await db.commit()
    logger.info("💾 [Orch] 画像已持久化: user=%s, level=%s", user_id, record.ability_level)


class OrchestratedRequest(BaseModel):
    """统一事件请求"""
    event_type: str                # ask_question / complete_practice / resource_viewed / daily_checkin
    subject: str = "数据结构"
    goal: str = ""
    payload: Dict[str, Any] = {}   # 事件携带数据
    user_messages: List[str] = []  # 历史消息（提问时使用）
    max_iterations: int = 3


@router.post("/orchestrated")
async def orchestrated_learning(
    req: OrchestratedRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    """
    统一学习入口 — 接收前端事件 → Orchestrator 管线

    事件类型:
    - ask_question: 学生提问 → TutorAgent
    - complete_practice: 完成练习 → Assessment→Analytics→Profile
    - resource_viewed: 查看资源 → Analytics (记录行为)
    - daily_checkin: 每日打卡 → Analytics→Recommendation
    - start_learning: 开始学习 → Analytics→Profile→Planner→Resource→Recommendation
    """
    from app.agents.graph import run_learning_session

    user_id = str(user.id) if user else "default"
    subject = req.subject or "数据结构"

    try:
        result = run_learning_session(
            subject=subject,
            goal=req.goal,
            user_id=user_id,
            user_messages=req.user_messages if req.user_messages else None,
            event_type=req.event_type,
            event_payload=req.payload,
            max_iterations=req.max_iterations,
        )

        summary = result.get("_summary", {})
        logger.info(
            "Orchestrated [%s] 完成: phase=%s, agents=%d",
            req.event_type,
            summary.get("session_phase", "?"),
            summary.get("iterations", 0),
        )

        # ★ 画像持久化
        if user and user.id:
            profile_data = result.get("student_profile", {})
            if profile_data and profile_data.get("ability_level"):
                try:
                    await _persist_profile(db, user.id, profile_data)
                except Exception as e:
                    logger.debug("画像持久化跳过: %s", e)

        return {
            "event_type": req.event_type,
            "chat_response": result.get("chat_response"),
            "profile": result.get("student_profile", {}),
            "learning_path": result.get("learning_path", []),
            "resources": result.get("resources", []),
            "recommendation": result.get("recommendation", {}),
            "assessment": result.get("assessment", {}),
            "analytics": result.get("learning_analytics", {}),
            "session_summary": summary,
        }

    except Exception as e:
        logger.error("Orchestrated [%s] 失败: %s", req.event_type, e)
        raise HTTPException(status_code=500, detail=f"学习服务暂时不可用: {str(e)[:200]}")
