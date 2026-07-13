"""用户画像 + 学习模式 API：保存/获取学习画像、模式选择/切换"""
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth import get_current_user, get_required_user
from app.models.user import (
    User, LEARNING_MODE_BASIC, LEARNING_MODE_BEGINNER,
    LEARNING_MODE_EXAM, LEARNING_MODE_CHOICES
)
from app.services.learning_record_service import learning_record_service

router = APIRouter(prefix="/api/profile", tags=["profile"])


# ════════════════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════════════════

class SaveProfileRequest(BaseModel):
    profile_data: dict


class SetLearningModeRequest(BaseModel):
    learning_mode: str

    @classmethod
    def validate_mode(cls, v: str) -> str:
        if v not in (LEARNING_MODE_BASIC, LEARNING_MODE_BEGINNER, LEARNING_MODE_EXAM):
            raise ValueError(f"无效的学习模式: {v}，支持: basic / beginner / exam")
        return v


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
            "next_step": "choose_mode",  # 前端收到后跳转模式选择
        }
    # 未登录用户：不保存 DB，返回成功状态（避免 401 触发前端跳转登录页）
    return {
        "message": "画像已接收（未登录模式，数据仅保存在本地）",
        "has_completed_onboarding": False,
        "next_step": "choose_mode",
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
# 学习模式接口
# ════════════════════════════════════════════════════════

@router.get("/learning-modes")
async def get_learning_modes():
    """获取所有可选学习模式及其说明（前端模式选择页使用）"""
    return {
        "modes": [
            {
                "value": LEARNING_MODE_BASIC,
                "label": LEARNING_MODE_CHOICES[LEARNING_MODE_BASIC]["label"],
                "icon": LEARNING_MODE_CHOICES[LEARNING_MODE_BASIC]["icon"],
                "color": LEARNING_MODE_CHOICES[LEARNING_MODE_BASIC]["color"],
                "suitable_for": ["零基础用户", "初次接触该领域用户", "学习兴趣培养阶段"],
                "features": ["内容简单易懂", "学习压力低", "注重兴趣激发", "每日任务量较少"],
                "daily_tasks": "1~3个",
                "study_duration": "10~20分钟",
                "content_style": "碎片化、图文优先、视频辅助",
            },
            {
                "value": LEARNING_MODE_BEGINNER,
                "label": LEARNING_MODE_CHOICES[LEARNING_MODE_BEGINNER]["label"],
                "icon": LEARNING_MODE_CHOICES[LEARNING_MODE_BEGINNER]["icon"],
                "color": LEARNING_MODE_CHOICES[LEARNING_MODE_BEGINNER]["color"],
                "suitable_for": ["已具备基础认知", "希望系统学习用户"],
                "features": ["内容具有一定深度", "开始建立知识体系", "任务难度中等", "增加实践训练"],
                "daily_tasks": "3~5个",
                "study_duration": "20~40分钟",
                "content_style": "系统课程、知识体系构建、适量练习",
            },
            {
                "value": LEARNING_MODE_EXAM,
                "label": LEARNING_MODE_CHOICES[LEARNING_MODE_EXAM]["label"],
                "icon": LEARNING_MODE_CHOICES[LEARNING_MODE_EXAM]["icon"],
                "color": LEARNING_MODE_CHOICES[LEARNING_MODE_EXAM]["color"],
                "suitable_for": ["备考用户", "需要快速提升成绩用户"],
                "features": ["高强度学习", "重点考点覆盖", "高频真题训练", "强化知识点记忆"],
                "daily_tasks": "5~8个",
                "study_duration": "40~90分钟",
                "content_style": "专项训练、高频考点、真题模拟、阶段测试",
            },
        ]
    }


@router.post("/set-learning-mode")
async def set_learning_mode(
    req: SetLearningModeRequest,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """设置/切换学习模式
    
    已登录用户：保存到数据库
    未登录用户：返回 401，前端提示重新登录
    """
    SetLearningModeRequest.validate_mode(req.learning_mode)
    
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录后再切换学习模式")
    
    user.learning_mode = req.learning_mode
    user.learning_mode_set_at = datetime.now(timezone.utc)
    await db.commit()
    # ★ 强制 refresh，确保从 DB 获取最新值
    await db.refresh(user)
    mode_info = LEARNING_MODE_CHOICES.get(req.learning_mode)
    return {
        "message": f"已切换至【{mode_info['label']}】",
        "learning_mode": user.learning_mode,
        "learning_mode_info": mode_info,
    }


@router.get("/my-learning-mode")
async def get_my_learning_mode(user: User = Depends(get_required_user)):
    """获取当前用户的学习模式（要求登录）
    
    ★ 直接从数据库读取，返回用户最后一次保存的模式
    """
    mode = user.learning_mode if user.learning_mode else ''
    return {
        "learning_mode": mode,
        "learning_mode_info": LEARNING_MODE_CHOICES.get(mode) if mode else None,
    }


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
