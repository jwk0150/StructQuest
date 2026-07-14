"""用户画像 API：保存/获取学习画像、学习升级建议"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth import get_current_user, get_required_user
from app.models.user import User, LEARNING_MODE_BASIC, LEARNING_MODE_CHOICES
from app.services.learning_record_service import learning_record_service

router = APIRouter(prefix="/api/profile", tags=["profile"])


# ════════════════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════════════════

class SaveProfileRequest(BaseModel):
    profile_data: dict


# ════════════════════════════════════════════════════════
# 用户画像接口
# ════════════════════════════════════════════════════════

@router.get("/")
async def get_profile(user: Optional[User] = Depends(get_current_user)):
    """获取当前用户的完整画像信息 + 学习模式
    
    支持可选认证：已登录返回 DB 数据，未登录返回空（前端用本地 store 兜底）。
    """
    if user is None:
        return {
            "id": None,
            "username": None,
            "has_completed_onboarding": False,
            "profile_data": None,
            "learning_mode": '',
            "learning_mode_info": None,
        }
    # ★ 未选模式的用户返回空字符串，不要默认 basic
    mode = user.learning_mode if user.learning_mode else ''
    return {
        "id": user.id,
        "username": user.username,
        "has_completed_onboarding": user.has_completed_onboarding,
        "profile_data": user.profile_data,
        "learning_mode": mode,
        "learning_mode_info": LEARNING_MODE_CHOICES.get(mode) if mode else None,
    }


@router.post("/save")
async def save_profile(
    req: SaveProfileRequest,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """保存用户画像数据（新用户完成问卷调查后调用）
    
    支持可选认证：如果用户已登录则保存到数据库，否则仅返回成功（不报 401）。
    前端在 catch 块中已有本地保存的容错逻辑。
    """
    if user is not None:
        user.profile_data = req.profile_data
        user.has_completed_onboarding = True
        await learning_record_service.create_profile_snapshot(
            db=db,
            user_id=user.id,
            profile_data=req.profile_data,
            source="manual",
            summary=req.profile_data.get("summary"),
        )
        await db.commit()
        return {
            "message": "画像保存成功",
            "has_completed_onboarding": True,
            "next_step": "app",
        }
    # 未登录用户：不保存 DB，返回成功状态（避免 401 触发前端跳转登录页）
    return {
        "message": "画像已接收（未登录模式，数据仅保存在本地）",
        "has_completed_onboarding": False,
        "next_step": "app",
    }


@router.post("/sync")
async def sync_profile(
    req: SaveProfileRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """同步更新用户画像（学习中触发，需要登录）"""
    user.profile_data = req.profile_data
    await learning_record_service.create_profile_snapshot(
        db=db,
        user_id=user.id,
        profile_data=req.profile_data,
        source="event",
        summary=req.profile_data.get("summary"),
    )
    await db.commit()
    return {"message": "画像已同步"}


# ════════════════════════════════════════════════════════
# 学习升级建议
# ════════════════════════════════════════════════════════

@router.post("/check-upgrade")
async def check_upgrade_suggestion(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """检测用户是否满足升级条件，返回升级建议
    
    前端在每次学习完成后调用此接口，
    若返回 suggested_mode 则弹窗提示用户切换模式。
    """
    from app.services.learning_mode_service import check_upgrade, check_downgrade
    from sqlalchemy.future import select
    from app.models.learning_progress import LearningProgress

    # 统计用户学习数据
    result = await db.execute(
        select(LearningProgress).where(LearningProgress.user_id == user.id)
    )
    progress_records = result.scalars().all()

    # 计算统计数据
    total_sessions = len(progress_records)
    avg_score = (
        sum(r.score for r in progress_records if r.score is not None) / total_sessions
        if total_sessions > 0 else 0
    )
    consecutive_low = 0
    for r in reversed(progress_records[-5:]):
        if r.score is not None and r.score < 60:
            consecutive_low += 1
        else:
            break

    user_stats = {
        "days_active": total_sessions,  # 简化：用完成次数代替天数
        "total_study_minutes": total_sessions * 15,  # 估算
        "tasks_completed": total_sessions,
        "avg_accuracy": avg_score / 100 if avg_score > 1 else avg_score,
        "consecutive_low_scores": consecutive_low,
    }

    current_mode = user.learning_mode or LEARNING_MODE_BASIC

    # 先检查是否建议升级
    upgrade = check_upgrade(user_stats, current_mode)
    if upgrade:
        return {"suggested": True, **upgrade}

    # 再检查是否建议降级（仅考试模式）
    downgrade = check_downgrade(user_stats, current_mode)
    if downgrade:
        return {"suggested": True, **downgrade}

    return {"suggested": False}
