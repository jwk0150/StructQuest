"""管理员 API：总览/资源审核/学生管理/智能体审核统计"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_admin_user
from app.db.session import get_db
from app.models.user import User
from app.models.learning_ecosystem import (
    LearningEvent,
    ProfileSnapshot,
    LearningPlan,
    ResourceAsset,
    ResourceReview,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ReviewRequest(BaseModel):
    action: str
    reason: str = ""
    score: Optional[float] = None


# ═══════════════════════════════════════════
#  总览
# ═══════════════════════════════════════════

@router.get("/overview")
async def get_admin_overview(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_snapshots = (await db.execute(select(func.count(ProfileSnapshot.id)))).scalar() or 0
    total_plans = (await db.execute(select(func.count(LearningPlan.id)))).scalar() or 0
    total_events = (await db.execute(select(func.count(LearningEvent.id)))).scalar() or 0
    total_assets = (await db.execute(select(func.count(ResourceAsset.id)))).scalar() or 0
    pending_assets = (
        await db.execute(
            select(func.count(ResourceAsset.id)).where(ResourceAsset.review_status.in_(("pending", "needs_revision")))
        )
    ).scalar() or 0

    recent_events_result = await db.execute(
        select(LearningEvent).order_by(desc(LearningEvent.created_at)).limit(10)
    )
    recent_events = [
        {
            "id": item.id,
            "user_id": item.user_id,
            "event_type": item.event_type,
            "subject": item.subject,
            "node_id": item.node_id,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in recent_events_result.scalars().all()
    ]

    return {
        "operator": user.username,
        "metrics": {
            "total_users": total_users,
            "profile_snapshots": total_snapshots,
            "learning_plans": total_plans,
            "learning_events": total_events,
            "resource_assets": total_assets,
            "pending_assets": pending_assets,
        },
        "recent_events": recent_events,
    }


# ═══════════════════════════════════════════
#  资源审核
# ═══════════════════════════════════════════

@router.get("/resources")
async def get_admin_resources(
    status: Optional[str] = Query(default=None),
    limit: int = 20,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ResourceAsset).order_by(desc(ResourceAsset.created_at)).limit(limit)
    if status:
        query = select(ResourceAsset).where(ResourceAsset.review_status == status).order_by(desc(ResourceAsset.created_at)).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()
    return {
        "operator": user.username,
        "items": [
            {
                "id": item.id,
                "title": item.title,
                "asset_type": item.asset_type,
                "topic": item.topic,
                "subject": item.subject,
                "review_status": item.review_status,
                "quality_score": item.quality_score,
                "relevance_score": item.relevance_score,
                "recommendation_score": item.recommendation_score,
                "review_notes": item.review_notes,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
    }


@router.post("/resources/{asset_id}/review")
async def review_resource_asset(
    asset_id: int,
    req: ReviewRequest,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ResourceAsset).where(ResourceAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="资源不存在")

    normalized_action = req.action.strip().lower()
    if normalized_action not in {"approved", "rejected", "needs_revision"}:
        raise HTTPException(status_code=400, detail="action 仅支持 approved / rejected / needs_revision")

    asset.review_status = normalized_action
    asset.review_notes = req.reason
    if req.score is not None:
        asset.recommendation_score = req.score

    db.add(
        ResourceReview(
            resource_asset_id=asset.id,
            reviewer_id=user.id,
            action=normalized_action,
            score=req.score,
            reason=req.reason,
            review_data={"operator": user.username},
        )
    )
    await db.commit()

    return {
        "message": "审核已更新",
        "asset_id": asset.id,
        "review_status": asset.review_status,
    }


# ═══════════════════════════════════════════
#  学生管理
# ═══════════════════════════════════════════

@router.get("/students")
async def get_admin_students(
    limit: int = 20,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    users_result = await db.execute(select(User).order_by(desc(User.id)).limit(limit))
    users = users_result.scalars().all()

    items = []
    for item in users:
        snapshot_result = await db.execute(
            select(ProfileSnapshot).where(ProfileSnapshot.user_id == item.id).order_by(desc(ProfileSnapshot.created_at)).limit(1)
        )
        latest_snapshot = snapshot_result.scalar_one_or_none()
        plan_count = (
            await db.execute(select(func.count(LearningPlan.id)).where(LearningPlan.user_id == item.id))
        ).scalar() or 0
        event_count = (
            await db.execute(select(func.count(LearningEvent.id)).where(LearningEvent.user_id == item.id))
        ).scalar() or 0
        items.append(
            {
                "id": item.id,
                "username": item.username,
                "is_admin": getattr(item, 'is_admin', False),
                "learning_mode": item.learning_mode,
                "has_completed_onboarding": item.has_completed_onboarding,
                "plan_count": plan_count,
                "event_count": event_count,
                "latest_profile_summary": latest_snapshot.summary if latest_snapshot else "",
                "latest_profile_time": latest_snapshot.created_at.isoformat() if latest_snapshot and latest_snapshot.created_at else None,
            }
        )

    return {"operator": user.username, "items": items}


# ═══════════════════════════════════════════
#  智能体审核统计（新增）
# ═══════════════════════════════════════════

@router.get("/agent-reviews")
async def get_agent_reviews(
    limit: int = 50,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """从学习计划中提取所有智能体审核资源记录"""
    result = await db.execute(
        select(LearningPlan).order_by(desc(LearningPlan.created_at)).limit(limit)
    )
    plans = result.scalars().all()

    all_reviewed = []
    for plan in plans:
        plan_data = plan.plan_data or {}
        reviewed = plan_data.get("reviewed_resources", [])
        recommended = plan_data.get("recommended_resources", [])
        for r in reviewed:
            r["plan_id"] = plan.id
            r["user_id"] = plan.user_id
            r["subject"] = plan.subject
            r["session_created"] = plan.created_at.isoformat() if plan.created_at else None
            all_reviewed.append(r)
        # ★ 标记推荐资源
        rec_types = {(x.get("type"), x.get("title")) for x in recommended}
        for r in all_reviewed:
            if (r.get("type"), r.get("title")) in rec_types:
                r["is_recommended"] = True

    return {
        "operator": user.username,
        "total": len(all_reviewed),
        "items": all_reviewed,
    }


@router.get("/agent-sessions")
async def get_agent_sessions(
    limit: int = 20,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """列出最近的多智能体学习会话"""
    result = await db.execute(
        select(LearningPlan).order_by(desc(LearningPlan.created_at)).limit(limit)
    )
    plans = result.scalars().all()

    sessions = []
    for plan in plans:
        plan_data = plan.plan_data or {}
        summary = plan_data.get("_summary", {})
        profile = plan_data.get("student_profile", {})
        assessment = plan_data.get("assessment", {})
        path = plan_data.get("learning_path", [])

        # ★ 从 messages 中提取各 Agent 的日志
        messages = plan_data.get("messages", [])
        agent_names = list(dict.fromkeys(
            m.get("agent", "") for m in messages if m.get("agent")
        ))

        sessions.append({
            "plan_id": plan.id,
            "user_id": plan.user_id,
            "subject": plan.subject,
            "goal": plan.goal,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "ability_level": profile.get("ability_level", ""),
            "mbti_style": profile.get("cognitive", {}).get("mbti_style", ""),
            "feynman_adaptation": profile.get("cognitive", {}).get("feynman_adaptation"),
            "total_steps": summary.get("total_steps", len(path)),
            "completed_steps": summary.get("completed_steps", 0),
            "final_score": assessment.get("overall_score"),
            "bloom_scores": assessment.get("bloom_scores", {}),
            "iterations": summary.get("iterations", 0),
            "elapsed_seconds": summary.get("elapsed_seconds", 0),
            "session_status": summary.get("session_status", ""),
            "profile_summary": profile.get("summary", ""),
            "agents_executed": agent_names,
            "reviewed_count": len(plan_data.get("reviewed_resources", [])),
            "recommended_count": len(plan_data.get("recommended_resources", [])),
        })

    return {
        "operator": user.username,
        "total": len(sessions),
        "items": sessions,
    }


@router.get("/agent-stats")
async def get_agent_stats(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """聚合统计：多智能体运行数据"""
    result = await db.execute(select(LearningPlan))
    plans = result.scalars().all()

    total_sessions = len(plans)
    if total_sessions == 0:
        return {"total_sessions": 0, "message": "暂无数据"}

    scores = []
    iterations = []
    total_steps = 0
    completed_steps = 0
    total_reviewed = 0
    total_recommended = 0
    agent_exec_counts = {}
    ability_dist = {}
    mbti_dist = {}

    for plan in plans:
        rj = plan.plan_data or {}
        summary = rj.get("_summary", {})
        assessment = rj.get("assessment", {})
        profile = rj.get("student_profile", {})

        score = assessment.get("overall_score")
        if score is not None:
            scores.append(score)

        it = summary.get("iterations", 0)
        iterations.append(it)

        total_steps += summary.get("total_steps", 0)
        completed_steps += summary.get("completed_steps", 0)
        total_reviewed += len(rj.get("reviewed_resources", []))
        total_recommended += len(rj.get("recommended_resources", []))

        # 统计各 Agent 执行情况
        for m in rj.get("messages", []):
            agent = m.get("agent", "")
            if agent:
                agent_exec_counts[agent] = agent_exec_counts.get(agent, 0) + 1

        # 能力分布
        al = profile.get("ability_level", "unknown")
        ability_dist[al] = ability_dist.get(al, 0) + 1

        # MBTI 分布
        mb = profile.get("cognitive", {}).get("mbti_style", "unknown")
        mbti_dist[mb] = mbti_dist.get(mb, 0) + 1

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    avg_iterations = round(sum(iterations) / len(iterations), 1)
    avg_steps_per_session = round(total_steps / total_sessions, 1)
    completion_rate = round(completed_steps / max(total_steps, 1) * 100, 1)

    # 审核通过率
    approved_count = sum(
        1 for p in plans
        for r in (p.plan_data or {}).get("reviewed_resources", [])
        if r.get("review_status") == "approved"
    )
    total_review_items = sum(
        len((p.plan_data or {}).get("reviewed_resources", []))
        for p in plans
    )
    approval_rate = round(approved_count / max(total_review_items, 1) * 100, 1)

    return {
        "operator": user.username,
        "total_sessions": total_sessions,
        "avg_score": avg_score,
        "avg_iterations": avg_iterations,
        "avg_steps_per_session": avg_steps_per_session,
        "completion_rate": completion_rate,
        "total_reviewed_resources": total_reviewed,
        "total_recommended_resources": total_recommended,
        "approval_rate": approval_rate,
        "agent_exec_counts": agent_exec_counts,
        "ability_distribution": ability_dist,
        "mbti_distribution": mbti_dist,
    }
