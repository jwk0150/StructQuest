"""用户画像 API：保存/获取学习画像、学习升级建议"""
import traceback
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth import get_current_user, get_required_user
from app.models.user import User, LEARNING_MODE_BASIC, LEARNING_MODE_CHOICES
from app.services.learning_record_service import learning_record_service
from app.services.profile_service import recalculate_profile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/profile", tags=["profile"])


# ════════════════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════════════════

class SaveProfileRequest(BaseModel):
    profile_data: dict


# ════════════════════════════════════════════════════════
# 用户画像接口
# ════════════════════════════════════════════════════════

# ★ 同时支持 /api/profile 和 /api/profile/（避免 307 重定向丢失 token）
@router.get("")
@router.get("/")
async def get_profile(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的完整画像信息 + 学习模式

    支持可选认证：已登录返回 DB 数据，未登录返回空（前端用本地 store 兜底）。
    ★ v2：优先读 student_profiles 表（实时行为画像），降级到 users.profile_data
    """
    if user is None:
        return {
            "id": None,
            "username": None,
            "has_completed_onboarding": False,
            "profile_data": None,
            "learning_mode": '',
            "learning_mode_info": None,
            "profile_source": None,
        }
    # ★ 未选模式的用户返回空字符串，不要默认 basic
    mode = user.learning_mode if user.learning_mode else ''

    # ★ 优先读取 student_profiles（真实行为画像）
    try:
        from app.models.student_profile import StudentProfile
        sp_result = await db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )
        sp = sp_result.scalar_one_or_none()
        if sp:
            logger.info(f"📊 个人中心读取 student_profiles: user={user.id}, level={sp.ability_level}")
            return {
                "id": user.id,
                "username": user.username,
                "has_completed_onboarding": user.has_completed_onboarding,
                "profile_data": sp.to_dict(),
                "learning_mode": mode,
                "learning_mode_info": LEARNING_MODE_CHOICES.get(mode) if mode else None,
                "profile_source": "student_profiles",
            }
    except Exception as e:
        logger.warning(f"读取 student_profiles 失败，降级到 users.profile_data: {e}")

    # 降级：users.profile_data（Onboarding 快照）
    return {
        "id": user.id,
        "username": user.username,
        "has_completed_onboarding": user.has_completed_onboarding,
        "profile_data": user.profile_data,
        "learning_mode": mode,
        "learning_mode_info": LEARNING_MODE_CHOICES.get(mode) if mode else None,
        "profile_source": "users.profile_data (fallback)",
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
        db_ok = False
        snap_ok = False
        err_msg = ""
        # 1. 核心：更新 users 表
        try:
            # ★★★ 临时调试 ★★★
            print(f"[DEBUG-SAVE] req.profile_data type={type(req.profile_data)}")
            if isinstance(req.profile_data, dict):
                print(f"[DEBUG-SAVE] req.profile_data keys={list(req.profile_data.keys())[:15]}")
                print(f"[DEBUG-SAVE] ability_level={req.profile_data.get('ability_level')}")
            print(f"[DEBUG-SAVE] user_id={user.id}, has_completed_onboarding={user.has_completed_onboarding}")
            # ★★★ 调试结束 ★★★

            # ★ 保护：如果已有完整 AI 画像，合并而非覆盖
            if user.has_completed_onboarding and user.profile_data and isinstance(user.profile_data, dict):
                existing_keys = set(user.profile_data.keys())
                new_keys = set(req.profile_data.keys()) if isinstance(req.profile_data, dict) else set()
                # 如果现有数据包含 AI 画像特征（ability_level等），而新数据只是瘦数据，则合并
                has_full_profile = 'ability_level' in existing_keys or 'learning_style' in existing_keys
                new_is_thin = new_keys and not ('ability_level' in new_keys or 'learning_style' in new_keys)
                if has_full_profile and new_is_thin:
                    print(f"[Profile] ⚠️ 检测到瘦数据覆盖，执行合并保护 (现有 {len(existing_keys)} key, 新数据 {len(new_keys)} key)")
                    merged = dict(req.profile_data)
                    for k, v in user.profile_data.items():
                        if k not in merged:
                            merged[k] = v
                    user.profile_data = merged
                else:
                    user.profile_data = req.profile_data
            else:
                user.profile_data = req.profile_data
            user.has_completed_onboarding = True
            await db.commit()
            db_ok = True
            print(f"[Profile] ✅ 画像保存成功 user_id={user.id}")
        except Exception as e:
            err_msg = str(e)
            print(f"[Profile] ❌ 保存画像失败 user_id={user.id}: {e}")
            traceback.print_exc()
            try:
                await db.rollback()
            except Exception:
                pass

        # 2. 非核心：写入画像快照到独立 session
        if db_ok:
            try:
                from app.db.session import AsyncSessionLocal
                async with AsyncSessionLocal() as snap_db:
                    await learning_record_service.create_profile_snapshot(
                        db=snap_db,
                        user_id=user.id,
                        profile_data=req.profile_data,
                        source="manual",
                        summary=req.profile_data.get("summary"),
                    )
                    await snap_db.commit()
                    snap_ok = True
                    print(f"[Profile] ✅ 快照写入成功 user_id={user.id}")
            except Exception as snap_err:
                print(f"[Profile] ⚠️ 快照写入失败（已降级跳过）: {snap_err}")
                traceback.print_exc()

        # 无论 DB 是否成功，都返回成功（前端有本地兜底，不应阻塞用户流程）
        return {
            "message": "画像保存成功" if db_ok else "画像已接收（本地保存，DB写入失败）",
            "has_completed_onboarding": True,
            "next_step": "app",
            "db_saved": db_ok,
            "snapshot_saved": snap_ok,
            "error": err_msg if not db_ok else None,
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
    db_ok = False
    try:
        user.profile_data = req.profile_data
        await db.commit()
        db_ok = True
        print(f"[Profile] ✅ 画像同步成功 user_id={user.id}")
    except Exception as e:
        print(f"[Profile] ❌ 同步画像失败 user_id={user.id}: {e}")
        traceback.print_exc()
        try:
            await db.rollback()
        except Exception:
            pass

    if db_ok:
        try:
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as snap_db:
                await learning_record_service.create_profile_snapshot(
                    db=snap_db,
                    user_id=user.id,
                    profile_data=req.profile_data,
                    source="event",
                    summary=req.profile_data.get("summary"),
                )
                await snap_db.commit()
        except Exception as snap_err:
            print(f"[Profile] ⚠️ 同步快照失败（已降级跳过）: {snap_err}")

    return {"message": "画像已同步" if db_ok else "同步失败（已降级）", "db_saved": db_ok}


@router.post("/refresh")
async def refresh_profile(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """★ 刷新画像：聚合考试+学习时长+完成节点，重算 student_profiles
    前端在进入个人中心时调用，确保看到最新的画像数据
    """
    try:
        sp = await recalculate_profile(user_id=user.id, db=db, source="manual_refresh")
        return {
            "message": "画像已刷新",
            "profile": sp.to_dict(),
            "profile_source": "student_profiles",
        }
    except Exception as e:
        logger.error(f"刷新画像失败 user={user.id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"画像刷新失败: {e}")


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
