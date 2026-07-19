"""
学习行为上报 + 动态画像 + 推荐 Feed API
"""
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.auth import get_current_user, get_required_user
from app.models.user import User
from app.models.learning_behavior import LearningBehavior
from app.models.student_profile import StudentProfile
from app.models.recommendation import Recommendation
from app.utils.logger import get_logger

logger = get_logger("api.behavior")

router = APIRouter(prefix="/api", tags=["behavior-profile-recommendation"])


# ════════════════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════════════════

class BehaviorLogRequest(BaseModel):
    behavior_type: str           # view_resource / complete_exercise / watch_video / etc.
    resource_type: str = ""      # video/notes/mindmap/code_example/quiz/ppt
    resource_id: str = ""
    resource_title: str = ""
    duration_seconds: int = 0
    completed: bool = False
    score: Optional[float] = None
    progress_percent: float = 0.0
    subject: str = ""
    node_id: str = ""
    session_id: str = ""
    event_data: dict = {}


# ════════════════════════════════════════════════════════
# 行为上报
# ════════════════════════════════════════════════════════

@router.post("/behaviors/log")
async def log_behavior(
    req: BehaviorLogRequest,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """记录学习行为（前端自动上报）

    前端在以下时机调用：
    - 打开资源（视频/讲义/思维导图/代码案例）
    - 完成练习题
    - 开始/暂停学习
    - 点击推荐
    """
    if not user:
        return {"message": "未登录，行为未记录"}

    behavior = LearningBehavior(
        user_id=user.id,
        behavior_type=req.behavior_type,
        resource_type=req.resource_type or None,
        resource_id=req.resource_id or None,
        resource_title=req.resource_title or None,
        duration_seconds=req.duration_seconds,
        completed=req.completed,
        score=req.score,
        progress_percent=req.progress_percent,
        subject=req.subject or None,
        node_id=req.node_id or None,
        session_id=req.session_id or None,
        event_data=req.event_data or None,
    )
    db.add(behavior)
    await db.commit()

    return {"message": "行为已记录", "behavior_id": behavior.id}


# ════════════════════════════════════════════════════════
# 动态画像查询
# ════════════════════════════════════════════════════════

@router.get("/profile/dynamic")
async def get_dynamic_profile(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取六维动态画像（从 DB 读取，跨会话持久化）"""
    if not user:
        return {"profile": None, "message": "未登录"}

    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    record = result.scalar_one_or_none()

    if not record:
        # ★★★ 临时调试 ★★★
        print(f"[DEBUG-DYNAMIC] user_id={user.id}")
        print(f"[DEBUG-DYNAMIC] user.profile_data type={type(user.profile_data)}")
        print(f"[DEBUG-DYNAMIC] user.profile_data bool={bool(user.profile_data) if user.profile_data else False}")
        if user.profile_data and isinstance(user.profile_data, dict):
            print(f"[DEBUG-DYNAMIC] user.profile_data keys={list(user.profile_data.keys())[:15]}")
            print(f"[DEBUG-DYNAMIC] ability_level={user.profile_data.get('ability_level')}")
        elif user.profile_data and isinstance(user.profile_data, str):
            print(f"[DEBUG-DYNAMIC] user.profile_data is STRING, len={len(user.profile_data)}, first 200 chars: {user.profile_data[:200]}")
        print(f"[DEBUG-DYNAMIC] StudentProfile record exists={record is not None}")
        # ★★★ 调试结束 ★★★

        # 尝试从 user.profile_data 降级
        if user.profile_data:
            return {
                "profile": user.profile_data,
                "source": "user.profile_data (fallback)",
            }
        return {"profile": None, "message": "暂无画像数据"}

    return {
        "profile": record.to_dict(),
        "source": "student_profiles",
    }


# ════════════════════════════════════════════════════════
# 推荐 Feed
# ════════════════════════════════════════════════════════

@router.get("/recommendations/feed")
async def get_recommendation_feed(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 8,
):
    """获取个性化推荐 Feed（从 DB 缓存读取）

    推荐由 RecommendationAgent 在 Orchestrator 管线中生成并写入 DB。
    前端定时或登录时拉取此接口展示。
    """
    if not user:
        return {"items": [], "total": 0}

    result = await db.execute(
        select(Recommendation)
        .where(
            Recommendation.user_id == user.id,
            Recommendation.dismissed == False,
        )
        .order_by(Recommendation.relevance_score.desc())
        .limit(limit)
    )
    records = result.scalars().all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "resource_id": r.resource_id,
            "resource_type": r.resource_type,
            "title": r.title,
            "topic": r.topic,
            "difficulty": r.difficulty,
            "relevance_score": r.relevance_score,
            "reason": r.reason,
            "source": r.source,
            "clicked": r.clicked,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
        })

    return {"items": items, "total": len(items)}


@router.post("/recommendations/{recommendation_id}/click")
async def record_recommendation_click(
    recommendation_id: int,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """记录推荐点击"""
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == user.id,
        )
    )
    record = result.scalar_one_or_none()
    if record:
        record.clicked = True
        record.clicked_at = datetime.now(timezone.utc)
        await db.commit()

    return {"message": "已记录"}
