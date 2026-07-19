"""
统一画像重算服务
聚合 ExamResult + StudySession + LearningProgress → 计算 student_profiles 全部维度
并自动同步回 users.profile_data（个人中心兜底兼容）
"""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func as safunc
from datetime import datetime as dt

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════
# Node ID → 中文名 映射（与前端 knowledgeMap.js 对齐）
# ═══════════════════════════════════════════════════
_NODE_NAME_MAP: dict = None  # 延迟加载


async def _load_node_name_map(db: AsyncSession) -> dict:
    """从 KnowledgeNode 表加载 id→title 映射，缓存到模块变量"""
    global _NODE_NAME_MAP
    if _NODE_NAME_MAP is not None:
        return _NODE_NAME_MAP
    try:
        from app.models.knowledge_graph import KnowledgeNode
        result = await db.execute(select(KnowledgeNode.id, KnowledgeNode.title))
        rows = result.all()
        _NODE_NAME_MAP = {row[0]: row[1] for row in rows}
        logger.debug(f"加载了 {len(_NODE_NAME_MAP)} 个知识点名称映射")
    except Exception as e:
        logger.warning(f"加载知识点名称映射失败: {e}")
        _NODE_NAME_MAP = {}
    return _NODE_NAME_MAP


def _translate_id(id_str: str) -> str:
    """将 node ID 翻译为中文名，未命中原样返回"""
    if _NODE_NAME_MAP is None:
        return id_str
    return _NODE_NAME_MAP.get(id_str, id_str)


async def recalculate_profile(
    user_id: int,
    db: AsyncSession,
    node_title: str = "",
    trigger_score: Optional[float] = None,
    source: str = "auto_recalc",
):
    """从数据库重新计算用户画像（纯规则，聚合考试+学习时长+完成节点）

    数据源：ExamResult / StudySession / LearningProgress
    计算 14 个维度：ability_level / knowledge_mastery / strengths / weaknesses
    / activity_score / focus_score / engagement_score / risk_level / mastery_trend
    / growth_history / summary / total_study_hours / task_completion_rate / risk_factors
    """
    from app.models.student_profile import StudentProfile
    from app.models.exam_result import ExamResult
    from app.models.learning_progress import LearningProgress
    from app.models.study_session import StudySession

    # 1. 查找或创建画像
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    sp = result.scalar_one_or_none()
    if not sp:
        sp = StudentProfile(user_id=user_id)
        db.add(sp)
        await db.flush()

    # 2. 统计考试
    exam_rows = await db.execute(
        select(ExamResult).where(ExamResult.user_id == user_id)
    )
    exams = exam_rows.scalars().all()
    total_exams = len(exams)
    avg_score = sum(e.score for e in exams) / max(total_exams, 1) if exams else 0

    # 3. 总学习时长
    total_seconds = (await db.execute(
        select(safunc.sum(StudySession.duration_seconds)).where(StudySession.user_id == user_id)
    )).scalar() or 0

    # 4. 完成节点数
    completed_count = (await db.execute(
        select(safunc.count(LearningProgress.id)).where(
            LearningProgress.user_id == user_id,
            LearningProgress.status == "completed"
        )
    )).scalar() or 0

    # 5. 活跃度
    activity = min(100.0, total_exams * 12 + (total_seconds / 1800) * 8 + 20)
    sp.activity_score = round(activity, 1)
    sp.total_study_hours = round(total_seconds / 3600, 1)

    # 6. knowledge_mastery：从所有考试 EMA 平滑构建
    km = dict(sp.knowledge_mastery or {})
    for exam in exams:
        title = exam.node_id  # node_id 也作为知识点名
        old_val = float(km.get(title, 0))
        km[title] = round(old_val * 0.6 + exam.score * 0.4, 1) if old_val > 0 else round(exam.score, 1)
    # 如果传入了一个新的分数（还没入库的trigger_score），也合并
    if trigger_score is not None and node_title:
        old_val = float(km.get(node_title, 0))
        km[node_title] = round(old_val * 0.6 + trigger_score * 0.4, 1) if old_val > 0 else round(trigger_score, 1)
    sp.knowledge_mastery = km

    # 7. 强弱项 — ★ 翻译为中文名
    await _load_node_name_map(db)
    strengths = []
    weaknesses = []
    for title, score in km.items():
        cn_name = _translate_id(title)
        if score >= 80:
            strengths.append(cn_name)
        elif score < 60:
            weaknesses.append(cn_name)
    sp.strengths = strengths[:20]
    sp.weaknesses = weaknesses[:20]

    # 8. 风险等级
    if len(weaknesses) >= 5:
        sp.risk_level = "high"
        sp.risk_factors = [f"已积累 {len(weaknesses)} 个薄弱知识点: {', '.join(weaknesses[:3])}"]
    elif len(weaknesses) >= 3:
        sp.risk_level = "medium"
        sp.risk_factors = [f"有 {len(weaknesses)} 个薄弱知识点需关注"]
    else:
        sp.risk_level = "low"
        sp.risk_factors = []

    # 9. 能力等级（已有则保留升级，仅向上调整）
    prev_level = sp.ability_level
    if avg_score >= 80:
        new_level = "advanced"
    elif avg_score >= 65:
        new_level = "intermediate"
    else:
        new_level = "beginner"
    level_order = {"beginner": 0, "intermediate": 1, "advanced": 2, "expert": 3}
    if not prev_level or level_order.get(new_level, 0) > level_order.get(prev_level, 0):
        sp.ability_level = new_level

    # 10. 掌握趋势
    if avg_score >= 75:
        sp.mastery_trend = "improving"
    elif avg_score >= 60:
        sp.mastery_trend = sp.mastery_trend or "stable"
    else:
        sp.mastery_trend = "declining" if total_exams >= 3 else "stable"

    # 11. 其他指标
    sp.engagement_score = round(min(100.0, total_exams * 10 + completed_count * 15 + 30), 1)
    sp.task_completion_rate = round(completed_count / max(total_exams, 1), 2)
    sp.focus_score = min(98.0, max(50.0, sp.focus_score or 75))

    # 12. 摘要 — ★ 使用中文名
    cn_strengths = strengths[:3] if strengths else ["待发现"]
    cn_weaknesses = weaknesses[:3] if weaknesses else ["无"]
    sp.summary = (
        f"已参加 {total_exams} 次考试，平均分 {avg_score:.1f}，"
        f"完成 {completed_count} 个节点。强项: {', '.join(cn_strengths)}，"
        f"待加强: {', '.join(cn_weaknesses)}。"
    )

    # 13. 成长历史
    growth_history = list(sp.growth_history or [])
    today = dt.now().strftime("%Y-%m-%d")
    growth_history = [g for g in growth_history if g.get("date") != today]
    growth_history.append({
        "date": today,
        "overall_score": round(float(avg_score), 1),
        "exam_count": total_exams,
        "completed_nodes": completed_count,
    })
    sp.growth_history = growth_history[-30:]

    # 14. 标记来源
    sp.source = source
    sp.updated_at = safunc.now()

    await db.commit()
    await db.refresh(sp)

    # 15. ★ 同步回 users.profile_data（个人中心兜底兼容）
    await _sync_to_users_table(db, user_id, sp)

    logger.info("🔄 画像已重算: user=%s, level=%s, exams=%d, avg=%.1f, weak=%d",
                user_id, sp.ability_level, total_exams, avg_score, len(weaknesses))
    return sp


async def _sync_to_users_table(db: AsyncSession, user_id: int, sp) -> None:
    """将 student_profiles 数据同步回 users.profile_data"""
    try:
        from app.models.user import User
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.profile_data = sp.to_dict()
            await db.commit()
    except Exception as e:
        logger.warning("同步 users.profile_data 失败: %s", e)
