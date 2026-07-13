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
