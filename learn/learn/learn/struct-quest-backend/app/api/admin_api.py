"""管理员 API：总览/资源审核/学生管理/智能体审核统计 + 数据CRUD"""
import json
import traceback
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, desc, text, and_
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
from app.models.generated_content import GeneratedContent
from app.models.knowledge_graph import KnowledgeNode
from app.services.profile_service import recalculate_profile

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ═══════════════════════════════════════════
#  中文翻译映射（不改数据库，只在API返回时附加 _cn 字段）
# ═══════════════════════════════════════════

ABILITY_CN = {"beginner": "初级", "intermediate": "中级", "advanced": "高级", "expert": "专家"}
STYLE_CN = {"visual": "视觉型", "auditory": "听觉型", "reading": "阅读型", "hands_on": "动手型"}
RISK_CN = {"low": "低风险", "medium": "中风险", "high": "高风险"}
TREND_CN = {"improving": "进步中", "stable": "稳定", "declining": "下滑"}
MODE_CN = {"basic": "基础模式", "beginner": "入门模式", "exam": "考试模式"}
EVENT_CN = {
    "study_start": "开始学习", "ai_chat": "AI对话", "exam_completed": "考试完成",
    "quiz_completed": "练习完成", "node_completed": "节点完成",
    "view_notes": "查看讲义", "video_watched": "视频观看",
}
SOURCE_CN = {"agent": "AI生成", "manual": "手动录入", "event": "事件触发", "admin_recalc": "管理员重算"}


class ReviewRequest(BaseModel):
    action: str
    reason: str = ""
    score: Optional[float] = None


class ExamAddRequest(BaseModel):
    node_id: str
    score: float
    passed: bool = False
    node_title: str = ""  # 用于画像更新时的知识点名称


class EventAddRequest(BaseModel):
    event_type: str
    node_id: Optional[str] = None
    subject: Optional[str] = None
    duration_seconds: int = 0
    score: Optional[float] = None
    event_data: Optional[dict] = None


class RowInsertRequest(BaseModel):
    data: dict


class RowUpdateRequest(BaseModel):
    data: dict


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
                "learning_mode_cn": MODE_CN.get(item.learning_mode, item.learning_mode),
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


# ═══════════════════════════════════════════
#  学生详情 API（新增 — 数据可视化）
# ═══════════════════════════════════════════

@router.get("/students/{user_id}/detail")
async def get_student_detail(
    user_id: int,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个学生的完整数据"""
    # 基础信息
    student_row = await db.execute(select(User).where(User.id == user_id))
    student = student_row.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 画像数据
    from app.models.student_profile import StudentProfile
    profile_row = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = profile_row.scalar_one_or_none()

    # 考试统计
    from app.models.exam_result import ExamResult
    exam_rows = await db.execute(
        select(ExamResult).where(ExamResult.user_id == user_id).order_by(desc(ExamResult.completed_at))
    )
    exams = exam_rows.scalars().all()
    exam_list = [
        {
            "id": e.id, "node_id": e.node_id, "score": e.score,
            "passed": e.passed,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        }
        for e in exams
    ]

    # 学习事件
    event_rows = await db.execute(
        select(LearningEvent).where(LearningEvent.user_id == user_id)
        .order_by(desc(LearningEvent.created_at)).limit(50)
    )
    events = event_rows.scalars().all()
    event_list = [
        {
            "id": e.id, "event_type": e.event_type, "node_id": e.node_id,
            "score": e.score, "duration_seconds": e.duration_seconds,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "event_data": e.event_data if isinstance(e.event_data, dict) else {},
        }
        for e in events
    ]

    # 聊天消息统计
    from app.models.chat import ChatMessage, ChatSession
    chat_count = (await db.execute(
        select(func.count(ChatMessage.id))
    )).scalar() or 0
    chat_sessions = (await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == user_id)
    )).scalar() or 0

    # 学习进度
    from app.models.learning_progress import LearningProgress
    progress_rows = await db.execute(
        select(LearningProgress).where(LearningProgress.user_id == user_id)
    )
    progresses = progress_rows.scalars().all()

    # 画像数据（附加中文翻译）
    profile_dict = profile.to_dict() if profile else None
    if profile_dict:
        profile_dict["ability_level_cn"] = ABILITY_CN.get(profile_dict.get("ability_level", ""), "")
        profile_dict["learning_style_cn"] = STYLE_CN.get(profile_dict.get("learning_style", ""), "")
        profile_dict["risk_level_cn"] = RISK_CN.get(profile_dict.get("risk_level", ""), "")
        profile_dict["mastery_trend_cn"] = TREND_CN.get(profile_dict.get("mastery_trend", ""), "")

    return {
        "student": {
            "id": student.id,
            "username": student.username,
            "is_admin": getattr(student, 'is_admin', False),
            "learning_mode": student.learning_mode,
            "learning_mode_cn": MODE_CN.get(student.learning_mode, student.learning_mode),
            "has_completed_onboarding": student.has_completed_onboarding,
        },
        "profile": profile_dict,
        "stats": {
            "exam_count": len(exams),
            "event_count": len(event_list),
            "chat_sessions": chat_sessions,
            "progress_count": len(progresses),
            "avg_exam_score": round(sum(e.score for e in exams) / max(len(exams), 1), 1),
        },
        "exams": exam_list[:20],
        "events": event_list,
    }


@router.get("/students/{user_id}/profile-radar")
async def get_student_radar(
    user_id: int,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """学生六维画像雷达图数据"""
    from app.models.student_profile import StudentProfile
    profile_row = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = profile_row.scalar_one_or_none()

    if not profile:
        return {
            "dimensions": ["知识", "行为", "偏好", "错误", "成长", "风险"],
            "values": [50, 50, 50, 50, 50, 50],
            "ability_level": "unknown",
        }

    # 六维归一化到 0-100
    knowledge_score = min(100, len(profile.knowledge_mastery or {}) * 8)
    behavior_score = (profile.activity_score + profile.focus_score + profile.engagement_score) / 3
    preference_score = sum(profile.resource_preferences.values()) / max(len(profile.resource_preferences), 1) if profile.resource_preferences else 50
    error_score = max(0, 100 - (len(profile.error_patterns or []) * 15))
    growth_score = 75 if profile.mastery_trend == "improving" else (50 if profile.mastery_trend == "stable" else 30)
    risk_score = 80 if profile.risk_level == "low" else (50 if profile.risk_level == "medium" else 20)

    return {
        "dimensions": ["知识", "行为", "偏好", "错误", "成长", "风险"],
        "values": [
            round(knowledge_score, 1),
            round(behavior_score, 1),
            round(preference_score, 1),
            round(error_score, 1),
            round(growth_score, 1),
            round(risk_score, 1),
        ],
        "ability_level": profile.ability_level or "unknown",
        "ability_level_cn": ABILITY_CN.get(profile.ability_level, profile.ability_level or "未知"),
        "learning_style": profile.learning_style or "reading",
        "learning_style_cn": STYLE_CN.get(profile.learning_style, profile.learning_style or "阅读型"),
        "risk_level": profile.risk_level or "low",
        "risk_level_cn": RISK_CN.get(profile.risk_level, profile.risk_level or "低风险"),
    }


@router.get("/students/{user_id}/mastery-heatmap")
async def get_mastery_heatmap(
    user_id: int,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """知识点掌握度热力图数据"""
    from app.models.student_profile import StudentProfile
    from app.models.knowledge_graph import KnowledgeNode
    from app.models.exam_result import ExamResult

    profile_row = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    profile = profile_row.scalar_one_or_none()

    # 获取所有知识点
    node_rows = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.parent_id.isnot(None)).order_by(KnowledgeNode.parent_id, KnowledgeNode.order_index)
    )
    nodes = node_rows.scalars().all()

    # 考试分数
    exam_rows = await db.execute(
        select(ExamResult).where(ExamResult.user_id == user_id)
    )
    exam_scores = {e.node_id: e.score for e in exam_rows.scalars().all()}

    knowledge_mastery = profile.knowledge_mastery if profile else {}

    chapters = []
    current_chapter = None
    for node in nodes:
        chapter_name = node.category or node.parent_id or "其他"
        mastery = knowledge_mastery.get(node.title, None)
        exam_score = exam_scores.get(node.id, None)
        if mastery is None and exam_score is not None:
            mastery = exam_score
        if current_chapter is None or current_chapter["name"] != chapter_name:
            current_chapter = {
                "name": chapter_name,
                "nodes": [],
            }
            chapters.append(current_chapter)
        current_chapter["nodes"].append({
            "id": node.id,
            "title": node.title,
            "mastery": round(mastery, 1) if mastery is not None else None,
            "exam_score": exam_score,
        })

    return {
        "chapters": chapters,
        "total_nodes": len(nodes),
        "mastered_count": sum(1 for n in nodes if knowledge_mastery.get(n.title, 0) >= 70),
    }


@router.get("/students/{user_id}/event-timeline")
async def get_event_timeline(
    user_id: int,
    limit: int = 50,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """学生学习事件时间轴"""
    event_rows = await db.execute(
        select(LearningEvent).where(LearningEvent.user_id == user_id)
        .order_by(desc(LearningEvent.created_at)).limit(limit)
    )
    events = event_rows.scalars().all()

    timeline = []
    for e in events:
        timeline.append({
            "id": e.id,
            "date": e.created_at.strftime("%Y-%m-%d") if e.created_at else "",
            "time": e.created_at.strftime("%H:%M") if e.created_at else "",
            "event_type": e.event_type,
            "event_type_cn": EVENT_CN.get(e.event_type, e.event_type),
            "node_id": e.node_id,
            "score": e.score,
            "duration_seconds": e.duration_seconds,
        })

    # 按日期统计每日事件数
    daily_counts = {}
    for t in timeline:
        daily_counts[t["date"]] = daily_counts.get(t["date"], 0) + 1

    return {
        "timeline": timeline,
        "daily_counts": [{"date": k, "count": v} for k, v in sorted(daily_counts.items())],
    }


@router.get("/knowledge-nodes")
async def get_knowledge_nodes_simple(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """返回知识点 ID+标题 的下拉列表"""
    from app.models.knowledge_graph import KnowledgeNode
    result = await db.execute(
        select(KnowledgeNode.id, KnowledgeNode.title, KnowledgeNode.category)
        .order_by(KnowledgeNode.order_index)
    )
    nodes = result.all()
    return {
        "nodes": [
            {"id": n[0], "title": n[1], "category": n[2] or ""}
            for n in nodes
        ]
    }


# ═══════════════════════════════════════════
#  数据库浏览器 API（新增 — SQLite 直接浏览）
# ═══════════════════════════════════════════

DB_TABLES = [
    "users", "student_profiles", "learning_events", "exam_results",
    "study_sessions", "learning_progress", "chat_sessions", "chat_messages",
    "knowledge_nodes", "knowledge_documents", "learning_plans", "resource_assets",
    "learning_behaviors", "profile_snapshots",
]


@router.get("/db/tables")
async def get_db_tables(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """列出所有表和行数"""
    from sqlalchemy import text
    tables_info = []
    for table_name in DB_TABLES:
        try:
            count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = count_result.scalar() or 0
            tables_info.append({"name": table_name, "rows": count})
        except Exception:
            tables_info.append({"name": table_name, "rows": 0, "error": "表不存在"})

    return {"tables": tables_info}


@router.get("/db/browse")
async def browse_table(
    table_name: str = "users",
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """通用 SQLite 表浏览器（只读）"""
    from sqlalchemy import text

    if table_name not in DB_TABLES:
        raise HTTPException(status_code=400, detail=f"不支持的表名: {table_name}")

    try:
        # 获取总行数
        count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        total_rows = count_result.scalar() or 0

        # 获取列名
        col_result = await db.execute(text(f"SELECT * FROM {table_name} LIMIT 0"))
        columns = list(col_result.keys())

        # 获取数据
        data_result = await db.execute(
            text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"),
            {"limit": limit, "offset": offset}
        )
        rows = []
        for row in data_result.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                if isinstance(val, str) and (val.startswith("{") or val.startswith("[")):
                    try:
                        val = json.loads(val)
                    except Exception:
                        pass
                elif hasattr(val, 'isoformat'):
                    val = val.isoformat()
                row_dict[col] = val
            rows.append(row_dict)

        return {
            "table": table_name,
            "columns": columns,
            "total_rows": total_rows,
            "rows": rows,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/db/stats")
async def get_db_overview_stats(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """数据库整体统计（增强版overview）"""
    from app.models.exam_result import ExamResult
    from app.models.chat import ChatMessage, ChatSession
    from app.models.learning_progress import LearningProgress
    from app.models.student_profile import StudentProfile
    from app.models.study_session import StudySession

    # 总用户数
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    # 总事件数
    total_events = (await db.execute(select(func.count(LearningEvent.id)))).scalar() or 0
    # 总考试数
    total_exams = (await db.execute(select(func.count(ExamResult.id)))).scalar() or 0
    # 平均分
    avg_score = (await db.execute(select(func.avg(ExamResult.score)))).scalar()
    # 总对话数
    total_chats = (await db.execute(select(func.count(ChatMessage.id)))).scalar() or 0
    # 总学习时长
    total_study = (await db.execute(select(func.sum(StudySession.duration_seconds)))).scalar() or 0
    # 完成节点
    completed = (await db.execute(
        select(func.count(LearningProgress.id)).where(LearningProgress.status == "completed")
    )).scalar() or 0
    # 画像数
    profiles = (await db.execute(select(func.count(StudentProfile.id)))).scalar() or 0

    # 最近7天事件趋势
    event_trend = []
    for days_ago in range(6, -1, -1):
        count = (await db.execute(
            select(func.count(LearningEvent.id)).where(
                LearningEvent.created_at >= text(f"datetime('now', '-{days_ago} days')")
            )
        )).scalar() or 0
        event_trend.append({"date": f"day-{days_ago}", "count": count})

    return {
        "total_users": total_users,
        "total_events": total_events,
        "total_exams": total_exams,
        "avg_exam_score": round(float(avg_score), 1) if avg_score else 0,
        "total_chat_messages": total_chats,
        "total_study_hours": round(total_study / 3600, 1),
        "completed_nodes": completed,
        "profile_count": profiles,
        "event_trend_7d": event_trend,
    }



# ═══════════════════════════════════════════
#  级联删除用户
# ═══════════════════════════════════════════

@router.delete("/students/{user_id}/cascade")
async def cascade_delete_user(
    user_id: int,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """级联删除用户所有数据：画像/考试/事件/聊天/进度/会话/计划等"""
    # 防止删除自己
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")

    # 检查用户存在
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 收集删除统计
    deleted = {}

    # 定义要清理的表（按外键依赖顺序）
    tables_to_clean = [
        ("learning_plan_steps", "plan_id IN (SELECT id FROM learning_plans WHERE user_id = :uid)"),
        ("learning_plans", "user_id = :uid"),
        ("resource_reviews", "resource_asset_id IN (SELECT id FROM resource_assets WHERE user_id = :uid)"),
        ("resource_assets", "user_id = :uid"),
        ("profile_snapshots", "user_id = :uid"),
        ("learning_events", "user_id = :uid"),
        ("exam_results", "user_id = :uid"),
        ("study_sessions", "user_id = :uid"),
        ("learning_progress", "user_id = :uid"),
        ("chat_messages", "session_id IN (SELECT id FROM chat_sessions WHERE user_id = :uid)"),
        ("chat_sessions", "user_id = :uid"),
        ("student_profiles", "user_id = :uid"),
        ("learning_behaviors", "user_id = :uid"),
        ("daily_learning_progress", "user_id = :uid"),
        ("daily_tasks", "user_id = :uid"),
        ("user_tasks", "user_id = :uid"),
        ("wrong_questions", "user_id = :uid"),
        ("user_abilities", "user_id = :uid"),
        ("user_task_records", "user_id = :uid"),
        ("generated_content", "user_id = :uid"),
        ("external_resources", "user_id = :uid"),
    ]

    for table_name, where_clause in tables_to_clean:
        try:
            result = await db.execute(
                text(f"DELETE FROM {table_name} WHERE {where_clause}"),
                {"uid": user_id}
            )
            deleted[table_name] = result.rowcount
        except Exception as e:
            # 表可能不存在，忽略
            pass

    # 最后删除用户本身
    await db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
    deleted["users"] = 1

    await db.commit()

    return {
        "message": f"用户 {target.username} (ID:{user_id}) 已彻底删除",
        "deleted_tables": deleted,
        "total_rows_deleted": sum(deleted.values()),
    }


# ═══════════════════════════════════════════
#  手动添加考试记录 + 自动重算画像
# ═══════════════════════════════════════════

@router.post("/students/{user_id}/exams")
async def admin_add_exam(
    user_id: int,
    req: ExamAddRequest,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员手动添加考试记录，自动触发画像重算"""
    from app.models.exam_result import ExamResult
    from datetime import datetime as dt

    # 检查用户存在
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已有同 node_id 的考试
    existing = (await db.execute(
        select(ExamResult).where(
            ExamResult.user_id == user_id,
            ExamResult.node_id == req.node_id
        )
    )).scalar_one_or_none()

    if existing:
        # 更新已有记录
        existing.score = req.score
        existing.passed = req.passed
        existing.completed_at = dt.now()
    else:
        # 新建
        exam = ExamResult(
            user_id=user_id,
            node_id=req.node_id,
            score=req.score,
            passed=req.passed,
            completed_at=dt.now(),
        )
        db.add(exam)

    await db.flush()

    # 触发画像重算
    node_title = req.node_title or req.node_id
    try:
        updated_profile = await recalculate_profile(
            user_id=user_id,
            db=db,
            node_title=node_title,
            trigger_score=req.score,
        )
        profile_dict = updated_profile.to_dict() if updated_profile else None
    except Exception as e:
        traceback.print_exc()
        profile_dict = None

    return {
        "message": f"考试记录 {'已更新' if existing else '已添加'}: {req.node_id} → {req.score}分",
        "node_id": req.node_id,
        "score": req.score,
        "passed": req.passed,
        "profile_updated": profile_dict is not None,
        "profile_summary": profile_dict.get("summary", "") if profile_dict else "",
    }


# ═══════════════════════════════════════════
#  手动添加学习事件 + 自动重算画像
# ═══════════════════════════════════════════

@router.post("/students/{user_id}/events")
async def admin_add_event(
    user_id: int,
    req: EventAddRequest,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员手动添加学习事件，自动触发画像重算"""
    # 检查用户存在
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    event = LearningEvent(
        user_id=user_id,
        event_type=req.event_type,
        node_id=req.node_id,
        subject=req.subject,
        duration_seconds=req.duration_seconds,
        score=req.score,
        event_data=req.event_data or {},
    )
    db.add(event)
    await db.flush()

    # 触发画像重算
    try:
        updated_profile = await recalculate_profile(
            user_id=user_id,
            db=db,
            node_title=req.node_id or "",
            trigger_score=req.score,
        )
        profile_dict = updated_profile.to_dict() if updated_profile else None
    except Exception as e:
        traceback.print_exc()
        profile_dict = None

    return {
        "message": f"学习事件已添加: {req.event_type}",
        "event_id": event.id,
        "event_type": req.event_type,
        "profile_updated": profile_dict is not None,
        "profile_summary": profile_dict.get("summary", "") if profile_dict else "",
    }


# ═══════════════════════════════════════════
#  强制重算画像（基于数据库中已有数据）
# ═══════════════════════════════════════════

@router.post("/students/{user_id}/recalculate-profile")
async def admin_recalculate_profile(
    user_id: int,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """强制重算用户画像（基于数据库中所有已有数据）"""
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    try:
        updated_profile = await recalculate_profile(user_id=user_id, db=db)
        return {
            "message": "画像已重算",
            "profile": updated_profile.to_dict(),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"画像重算失败: {str(e)}")


# ═══════════════════════════════════════════
#  数据库 CRUD 操作
# ═══════════════════════════════════════════

@router.delete("/db/{table}/{row_id}")
async def delete_db_row(
    table: str,
    row_id: int,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除指定表中的一行"""
    if table not in DB_TABLES:
        raise HTTPException(status_code=400, detail=f"不支持的表名: {table}")

    try:
        result = await db.execute(text(f"DELETE FROM {table} WHERE id = :row_id"), {"row_id": row_id})
        await db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="记录不存在")
        return {"message": f"已从 {table} 删除 id={row_id}", "deleted": True}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.put("/db/{table}/{row_id}")
async def update_db_row(
    table: str,
    row_id: int,
    req: RowUpdateRequest,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新指定表中的一行"""
    if table not in DB_TABLES:
        raise HTTPException(status_code=400, detail=f"不支持的表名: {table}")

    data = req.data
    if not data:
        raise HTTPException(status_code=400, detail="没有提供更新数据")

    # 构建 SET 子句
    set_parts = []
    params = {"row_id": row_id}
    for key, val in data.items():
        if key == "id":
            continue  # 不允许修改主键
        param_name = f"val_{key}"
        set_parts.append(f"{key} = :{param_name}")
        # JSON 字段特殊处理
        if isinstance(val, (dict, list)):
            params[param_name] = json.dumps(val, ensure_ascii=False)
        else:
            params[param_name] = val

    if not set_parts:
        raise HTTPException(status_code=400, detail="没有可更新的字段")

    try:
        sql = f"UPDATE {table} SET {', '.join(set_parts)} WHERE id = :row_id"
        result = await db.execute(text(sql), params)
        await db.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="记录不存在")
        return {"message": f"已更新 {table} id={row_id}", "updated": True}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/db/{table}")
async def insert_db_row(
    table: str,
    req: RowInsertRequest,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """向指定表插入一行"""
    if table not in DB_TABLES:
        raise HTTPException(status_code=400, detail=f"不支持的表名: {table}")

    data = req.data
    if not data:
        raise HTTPException(status_code=400, detail="没有提供插入数据")

    # 构建 INSERT 语句
    columns = []
    values = []
    params = {}
    for key, val in data.items():
        columns.append(key)
        param_name = f"val_{key}"
        values.append(f":{param_name}")
        if isinstance(val, (dict, list)):
            params[param_name] = json.dumps(val, ensure_ascii=False)
        else:
            params[param_name] = val

    try:
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)})"
        result = await db.execute(text(sql), params)
        await db.commit()
        return {
            "message": f"已向 {table} 插入新行",
            "id": result.lastrowid,
            "inserted": True,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"插入失败: {str(e)}")


@router.get("/db/{table}/columns")
async def get_table_columns(
    table: str,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取表结构（列名和类型）"""
    if table not in DB_TABLES:
        raise HTTPException(status_code=400, detail=f"不支持的表名: {table}")

    try:
        # pragma 获取表信息
        info_result = await db.execute(text(f"PRAGMA table_info({table})"))
        columns = [
            {"name": row[1], "type": row[2], "nullable": not row[3], "pk": bool(row[5])}
            for row in info_result.fetchall()
        ]
        return {"table": table, "columns": columns}
    except Exception as e:
        # 尝试用 SELECT LIMIT 0 获取列名
        try:
            col_result = await db.execute(text(f"SELECT * FROM {table} LIMIT 0"))
            columns = [{"name": c, "type": "unknown", "nullable": True, "pk": c == "id"} for c in col_result.keys()]
            return {"table": table, "columns": columns}
        except Exception:
            raise HTTPException(status_code=500, detail=f"获取表结构失败: {str(e)}")


# ═══════════════════════════════════════════
#  知识库聚合 API（新增 — 知识库大管家）
# ═══════════════════════════════════════════

KI_TYPE_META = {
    "notes": {"icon": "📖", "label": "学习讲义", "format": "markdown"},
    "mindmap": {"icon": "🧠", "label": "思维导图", "format": "markmap"},
    "quiz": {"icon": "✏️", "label": "练习题", "format": "json"},
    "code_example": {"icon": "💻", "label": "代码案例", "format": "python"},
    "animation": {"icon": "🎬", "label": "动画演示", "format": "video"},
    "ppt_outline": {"icon": "📊", "label": "PPT大纲", "format": "markdown"},
}


class KnowledgeHubAddRequest(BaseModel):
    type: str  # uploaded / ai_resources / generated_content
    asset_type: str = "notes"
    topic: str = ""
    subject: str = "数据结构"
    content_text: str = ""
    title: str = ""
    description: str = ""


@router.get("/knowledge-hub")
async def get_knowledge_hub_overview(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """知识库聚合总览：ChromaDB + 上传文档 + AI生成资源 + 用户保存内容"""
    overview = {
        "chromadb": {"total_chunks": 0, "document_count": 0, "status": "未知"},
        "uploaded_docs": {"total": 0, "active": 0, "items": []},
        "ai_resources": {"total": 0, "approved": 0, "pending": 0, "by_type": {}, "items": []},
        "generated_content": {"total": 0, "by_type": {}, "items": []},
    }

    # ── ChromaDB 统计 ──
    try:
        from app.services.rag import rag_service
        stats = rag_service.get_stats()
        overview["chromadb"] = {
            "total_chunks": stats.get("total_chunks", 0),
            "document_count": stats.get("document_count", 0),
            "status": "正常" if stats.get("total_chunks", 0) > 0 else "空",
            "model": stats.get("embedding_model", ""),
        }
    except Exception as e:
        overview["chromadb"]["status"] = f"异常: {e}"

    # ── 上传文档 (knowledge_documents) ──
    try:
        from app.models.knowledge import KnowledgeDocument
        docs_result = await db.execute(
            select(KnowledgeDocument).order_by(desc(KnowledgeDocument.created_at)).limit(30)
        )
        docs = docs_result.scalars().all()
        overview["uploaded_docs"]["total"] = len(docs)
        overview["uploaded_docs"]["active"] = sum(1 for d in docs if getattr(d, 'status', 'active') == 'active')
        overview["uploaded_docs"]["items"] = [
            {
                "id": d.id,
                "filename": d.filename,
                "file_type": getattr(d, 'file_type', ''),
                "status": getattr(d, 'status', 'active'),
                "file_size": getattr(d, 'file_size', 0),
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "doc_id": getattr(d, 'doc_id', ''),
            }
            for d in docs
        ]
    except Exception as e:
        overview["uploaded_docs"]["error"] = str(e)

    # ── AI 生成资源 (resource_assets) ──
    try:
        assets_result = await db.execute(
            select(ResourceAsset).order_by(desc(ResourceAsset.created_at)).limit(50)
        )
        assets = assets_result.scalars().all()
        overview["ai_resources"]["total"] = len(assets)
        overview["ai_resources"]["approved"] = sum(1 for a in assets if a.review_status == "approved")
        overview["ai_resources"]["pending"] = sum(1 for a in assets if a.review_status in ("pending", "needs_revision"))

        type_counts = {}
        for a in assets:
            t = a.asset_type or "unknown"
            type_counts[t] = type_counts.get(t, 0) + 1
        overview["ai_resources"]["by_type"] = type_counts

        overview["ai_resources"]["items"] = [
            {
                "id": a.id,
                "asset_type": a.asset_type,
                "type_meta": KI_TYPE_META.get(a.asset_type, {}),
                "topic": a.topic,
                "subject": a.subject,
                "title": a.title,
                "review_status": a.review_status,
                "quality_score": a.quality_score,
                "relevance_score": a.relevance_score,
                "review_notes": a.review_notes,
                "content_preview": (a.content_text or "")[:200],
                "content_length": len(a.content_text or ""),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in assets
        ]
    except Exception as e:
        overview["ai_resources"]["error"] = str(e)

    # ── 用户保存的生成内容 (generated_content) ──
    try:
        gen_result = await db.execute(
            select(GeneratedContent).order_by(desc(GeneratedContent.created_at)).limit(30)
        )
        gens = gen_result.scalars().all()
        overview["generated_content"]["total"] = len(gens)

        gc_type_counts = {}
        for g in gens:
            t = g.content_type or "unknown"
            gc_type_counts[t] = gc_type_counts.get(t, 0) + 1
        overview["generated_content"]["by_type"] = gc_type_counts

        overview["generated_content"]["items"] = [
            {
                "id": g.id,
                "content_type": g.content_type,
                "title": g.title,
                "description": g.description,
                "topic_tag": g.topic_tag,
                "difficulty": g.difficulty,
                "format": g.format,
                "file_url": g.file_url,
                "content_preview": (g.content_text or "")[:200],
                "view_count": g.view_count or 0,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in gens
        ]
    except Exception as e:
        overview["generated_content"]["error"] = str(e)

    return {"operator": user.username, **overview}


@router.get("/knowledge-hub/{hub_type}")
async def get_knowledge_hub_items(
    hub_type: str,
    status: Optional[str] = Query(default="all"),
    limit: int = 50,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    按类型查看知识库内容列表
    hub_type: uploaded | ai_resources | generated_content
    """
    if hub_type not in ("uploaded", "ai_resources", "generated_content"):
        raise HTTPException(status_code=400, detail="类型仅支持: uploaded / ai_resources / generated_content")

    items = []

    if hub_type == "uploaded":
        from app.models.knowledge import KnowledgeDocument
        query = select(KnowledgeDocument).order_by(desc(KnowledgeDocument.created_at)).limit(limit)
        result = await db.execute(query)
        docs = result.scalars().all()
        items = [
            {
                "id": d.id, "filename": d.filename,
                "file_type": getattr(d, 'file_type', ''),
                "status": getattr(d, 'status', 'active'),
                "file_size": getattr(d, 'file_size', 0),
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
            if status == "all" or getattr(d, 'status', 'active') == status
        ]

    elif hub_type == "ai_resources":
        query = select(ResourceAsset)
        if status != "all":
            query = query.where(ResourceAsset.review_status == status)
        query = query.order_by(desc(ResourceAsset.created_at)).limit(limit)
        result = await db.execute(query)
        assets = result.scalars().all()
        items = [
            {
                "id": a.id, "asset_type": a.asset_type,
                "type_meta": KI_TYPE_META.get(a.asset_type, {}),
                "topic": a.topic, "subject": a.subject,
                "title": a.title, "review_status": a.review_status,
                "quality_score": a.quality_score,
                "relevance_score": a.relevance_score,
                "review_notes": a.review_notes,
                "content_text": a.content_text or "",
                "content_preview": (a.content_text or "")[:500],
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in assets
        ]

    elif hub_type == "generated_content":
        query = select(GeneratedContent).order_by(desc(GeneratedContent.created_at)).limit(limit)
        result = await db.execute(query)
        gens = result.scalars().all()
        items = [
            {
                "id": g.id, "content_type": g.content_type,
                "title": g.title, "description": g.description,
                "topic_tag": g.topic_tag,
                "difficulty": g.difficulty,
                "format": g.format,
                "content_text": g.content_text or "",
                "content_preview": (g.content_text or "")[:500],
                "file_url": g.file_url,
                "view_count": g.view_count or 0,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in gens
        ]

    return {"operator": user.username, "type": hub_type, "total": len(items), "items": items}


@router.delete("/knowledge-hub/{hub_type}/{item_id}")
async def delete_knowledge_hub_item(
    hub_type: str,
    item_id: int,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除知识库中的一条记录（同步清理 ChromaDB 向量）"""
    if hub_type not in ("uploaded", "ai_resources", "generated_content"):
        raise HTTPException(status_code=400, detail="类型仅支持: uploaded / ai_resources / generated_content")

    deleted_chunks = 0
    try:
        if hub_type == "uploaded":
            from app.models.knowledge import KnowledgeDocument
            doc = (await db.execute(select(KnowledgeDocument).where(KnowledgeDocument.id == item_id))).scalar_one_or_none()
            if not doc:
                raise HTTPException(status_code=404, detail="文档不存在")
            # 删除 ChromaDB 向量
            doc_id = getattr(doc, 'doc_id', '')
            if doc_id:
                from app.services.rag import rag_service
                deleted_chunks = rag_service.delete_document(doc_id)
            await db.delete(doc)

        elif hub_type == "ai_resources":
            asset = (await db.execute(select(ResourceAsset).where(ResourceAsset.id == item_id))).scalar_one_or_none()
            if not asset:
                raise HTTPException(status_code=404, detail="资源不存在")
            # 删除 ChromaDB 对应向量
            if asset.asset_type and asset.topic:
                try:
                    from app.services.rag import rag_service
                    collection = rag_service._get_collection()
                    where = {
                        "$and": [
                            {"cache_type": asset.asset_type},
                            {"cache_topic": asset.topic},
                        ]
                    }
                    existing = collection.get(where=where, include=[])
                    existing_ids = existing.get("ids", []) if existing else []
                    if existing_ids:
                        collection.delete(ids=existing_ids)
                        deleted_chunks = len(existing_ids)
                except Exception:
                    pass
            await db.delete(asset)

        elif hub_type == "generated_content":
            gen = (await db.execute(select(GeneratedContent).where(GeneratedContent.id == item_id))).scalar_one_or_none()
            if not gen:
                raise HTTPException(status_code=404, detail="内容不存在")
            await db.delete(gen)

        await db.commit()
        return {
            "message": f"已删除 {hub_type} id={item_id}",
            "deleted": True,
            "chromadb_chunks_cleaned": deleted_chunks,
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/knowledge-hub")
async def add_knowledge_hub_item(
    req: KnowledgeHubAddRequest,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """手动添加资源到知识库"""
    try:
        if req.type == "ai_resources":
            asset = ResourceAsset(
                user_id=user.id,
                asset_type=req.asset_type,
                source_type="manual",
                title=req.title or f"{req.asset_type}: {req.topic}",
                topic=req.topic or req.subject,
                subject=req.subject,
                content_text=req.content_text,
                review_status="pending",
                quality_score=70,
            )
            db.add(asset)
            await db.commit()
            await db.refresh(asset)

            # 同步写入 ChromaDB
            try:
                from app.services.content_cache import cache_service
                await cache_service._save_to_chromadb(
                    req.asset_type, req.topic or req.subject, req.subject, req.content_text
                )
            except Exception:
                pass

            return {"message": "AI资源已添加", "id": asset.id, "type": "ai_resources"}

        elif req.type == "generated_content":
            gen = GeneratedContent(
                user_id=user.id,
                content_type=req.asset_type,
                title=req.title or f"{req.asset_type}: {req.topic}",
                description=req.description,
                content_text=req.content_text,
                topic_tag=req.topic or req.subject,
                difficulty="intermediate",
                format=KI_TYPE_META.get(req.asset_type, {}).get("format", "text"),
            )
            db.add(gen)
            await db.commit()
            await db.refresh(gen)
            return {"message": "内容已添加", "id": gen.id, "type": "generated_content"}

        else:
            raise HTTPException(status_code=400, detail="类型仅支持: ai_resources / generated_content")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")


@router.get("/knowledge-hub/{hub_type}/{item_id}")
async def get_knowledge_hub_item_detail(
    hub_type: str,
    item_id: int,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """查看知识库单项详情（完整内容）"""
    if hub_type not in ("ai_resources", "generated_content"):
        raise HTTPException(status_code=400, detail="仅支持 ai_resources / generated_content")

    if hub_type == "ai_resources":
        asset = (await db.execute(select(ResourceAsset).where(ResourceAsset.id == item_id))).scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="资源不存在")
        return {
            "id": asset.id, "asset_type": asset.asset_type,
            "type_meta": KI_TYPE_META.get(asset.asset_type, {}),
            "topic": asset.topic, "subject": asset.subject,
            "title": asset.title, "review_status": asset.review_status,
            "quality_score": asset.quality_score,
            "relevance_score": asset.relevance_score,
            "review_notes": asset.review_notes,
            "content_text": asset.content_text or "",
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
        }

    elif hub_type == "generated_content":
        gen = (await db.execute(select(GeneratedContent).where(GeneratedContent.id == item_id))).scalar_one_or_none()
        if not gen:
            raise HTTPException(status_code=404, detail="内容不存在")
        return {
            "id": gen.id, "content_type": gen.content_type,
            "title": gen.title, "description": gen.description,
            "topic_tag": gen.topic_tag, "difficulty": gen.difficulty,
            "format": gen.format, "content_text": gen.content_text or "",
            "file_url": gen.file_url,
            "view_count": gen.view_count or 0,
            "created_at": gen.created_at.isoformat() if gen.created_at else None,
        }
