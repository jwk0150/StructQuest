"""
能力值计算服务（AbilityService）

集中管理六维学习能力的：
1. 初始化（新用户 → 全 0）
2. 增长（每次学习行为触发）
3. 平滑更新（新值 = 旧值 × 90% + 本次增长 × 10%）
4. 衰减（长期未学习）
5. 查询与自动衰减检查

六维能力与学习行为映射关系：
┌────────────────┬──────────────────────────────────────────────┐
│ 能力维度       │ 触发增长的学习行为                           │
├────────────────┼──────────────────────────────────────────────┤
│ 视觉感知       │ 完成讲义(notes)、视频资源、节点资源学习      │
│ 理论推导       │ 考试合格、练习题正确、理论章节完成           │
│ 动手实践       │ 完成练习(quiz)、考试高分、实践资源学习       │
│ 探索精神       │ AI提问、扩展资源浏览、主动发起学习会话       │
│ 稳健程度       │ 连续学习、错题订正、登录连续性               │
│ 综合能力       │ 节点完成、新章节解锁、综合以上五维聚合       │
└────────────────┴──────────────────────────────────────────────┘
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_ability import UserAbility
from app.models.learning_progress import LearningProgress
from app.models.study_session import StudySession
from app.models.exam_result import ExamResult
from app.models.chat import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

# ─── 能力增长常量 ──────────────────────────────────────────────
GROWTH_MAP = {
    "view_notes":      {"visual": 4.8,   "comprehensive": 1.8},
    "complete_quiz":   {"theory": 4.8,   "practice": 3.6,   "comprehensive": 1.8},
    "exam_passed":     {"theory": 9.0,   "practice": 6.0,   "comprehensive": 3.0},
    "exam_good_score": {"theory": 4.8,   "practice": 3.0},
    "node_completed":  {"comprehensive": 7.2, "visual": 3.0, "theory": 3.0, "practice": 3.0},
    "study_session":   {"exploration": 2.4, "stability": 1.8},
    "ai_chat":         {"exploration": 2.4},
    "mistake_correct": {"stability": 3.0,    "theory": 1.8},
    "daily_streak":    {"stability": 3.0},
    "daily_login":     {"stability": 0.9},
}

# 平滑因子：旧值占比越高，能力值变化越平缓
SMOOTH_FACTOR_OLD = 0.60      # 旧值权重
SMOOTH_FACTOR_NEW = 0.40      # 新增长权重

# ─── 衰减常量 ──────────────────────────────────────────────────
DECAY_PER_DAY = 0.3            # 每超过一天未学习，衰减 0.3 分
DECAY_MAX_DAYS = 14            # 最多衰减 14 天的量（防止归零）
STABILITY_DECAY_PER_DAY = 0.5  # 稳健程度衰减更快
MIN_SCORE = 0.0                # 最低不低于 0
MAX_SCORE = 100.0              # 最高不超过 100


class AbilityService:
    """能力值计算与更新服务"""

    # ════════════════════════════════════════════════════════════
    # 1. 查询能力值（含自动衰减检查）
    # ════════════════════════════════════════════════════════════

    async def get_ability(self, db: AsyncSession, user_id: int) -> Dict[str, float]:
        """获取用户六维能力值，返回 dict；如果不存在则初始化（全 0）"""
        ability = await self._get_or_create(db, user_id)
        # 每次查询前检查并应用衰减
        ability = await self._apply_decay_if_needed(db, ability)
        return self._to_dict(ability)

    async def get_ability_or_none(self, db: AsyncSession, user_id: int) -> Optional[Dict[str, float]]:
        """仅查询，不自动创建/初始化"""
        ability = await self._get(db, user_id)
        if ability is None:
            return None
        ability = await self._apply_decay_if_needed(db, ability)
        return self._to_dict(ability)

    def _to_dict(self, ability: UserAbility) -> Dict[str, float]:
        return {
            "visual": round(ability.visual_score, 1),
            "comprehensive": round(ability.comprehensive_score, 1),
            "stability": round(ability.stability_score, 1),
            "exploration": round(ability.exploration_score, 1),
            "theory": round(ability.theory_score, 1),
            "practice": round(ability.practice_score, 1),
        }

    # ════════════════════════════════════════════════════════════
    # 2. 触发能力增长（在各类学习行为发生后调用）
    # ════════════════════════════════════════════════════════════

    async def on_event(
        self,
        db: AsyncSession,
        user_id: int,
        event_type: str,
        event_data: Optional[Dict] = None,
    ) -> Dict[str, float]:
        """
        学习事件触发能力更新。

        event_type 支持的值：
          - view_notes        → 完成讲义阅读
          - complete_quiz     → 完成练习题
          - exam_passed       → 考试通过（>=60分）
          - exam_good_score   → 考试高分（>=80分，额外加分）
          - node_completed    → 节点全部完结（=100% progress）
          - study_session     → 完成一次学习会话
          - ai_chat           → AI 提问一次
          - mistake_corrected → 错题订正
          - daily_streak      → 连续学习达标
        """
        growth = GROWTH_MAP.get(event_type)
        if not growth:
            logger.debug(f"[Ability] 忽略未知事件类型: {event_type}")
            return await self.get_ability(db, user_id)

        ability = await self._get_or_create(db, user_id)

        # 对每个受影响的能力维度执行平滑更新
        changed = False
        for key, delta in growth.items():
            old_val = getattr(ability, f"{key}_score", 0.0)
            if old_val is None:
                old_val = 0.0
            new_val = old_val * SMOOTH_FACTOR_OLD + delta * SMOOTH_FACTOR_NEW
            # 允许额外累加效果：如果 old 已经很小但 delta 较大，保留更多新增
            # 实际使用 0.85/0.15 平滑 + 上不封顶累积
            new_val = min(new_val, MAX_SCORE)
            setattr(ability, f"{key}_score", new_val)
            changed = True

        if changed:
            ability.update_time = datetime.now(timezone.utc)
            await db.commit()

        logger.info(f"[Ability] user={user_id} event={event_type}: {self._to_dict(ability)}")
        return self._to_dict(ability)

    async def on_exam_submitted(
        self,
        db: AsyncSession,
        user_id: int,
        score: float,
        passed: bool,
        is_quiz: bool = False,
    ) -> Dict[str, float]:
        """考试/练习提交后的能力更新"""
        if passed:
            result = await self.on_event(db, user_id, "exam_passed")
            if score >= 80:
                result = await self.on_event(db, user_id, "exam_good_score")
            return result
        # 未通过也加一点理论推导（有练习行为）
        return await self.on_event(db, user_id, "complete_quiz" if is_quiz else "exam_passed")

    async def on_mistake_corrected(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Dict[str, float]:
        """错题订正后的能力更新"""
        return await self.on_event(db, user_id, "mistake_correct")

    async def on_node_completed(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Dict[str, float]:
        """节点完成后的能力更新"""
        return await self.on_event(db, user_id, "node_completed")

    # ════════════════════════════════════════════════════════════
    # 3. 全量重新计算（从数据库汇总，用于数据修复/迁移）
    # ════════════════════════════════════════════════════════════

    async def full_recalculate(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Dict[str, float]:
        """从数据库全量重新计算能力值（数据迁移/首次启用时使用）"""
        # 并行查询各类学习数据
        stat = await self._collect_stats(db, user_id)

        # --- 视觉感知 ---
        # 基于 已完成的笔记资源数 / 总节点数，加视频类资源
        visual = 0.0
        if stat["total_nodes"] > 0:
            notes_rate = stat["notes_completed"] / max(stat["total_nodes"], 1)
            completed_rate = stat["nodes_completed"] / max(stat["total_nodes"], 1)
            visual = (notes_rate * 40 + completed_rate * 60)  # 加权
            visual = min(visual, 100.0)

        # --- 理论推导 ---
        theory = 0.0
        if stat["exam_count"] > 0:
            avg_score = stat["avg_exam_score"] if stat["avg_exam_score"] else 0
            theory = avg_score * 0.7 + stat["high_score_rate"] * 30
            theory = min(theory, 100.0)
        elif stat["quiz_count"] > 0:
            theory = min(stat["quiz_count"] * 5, 40.0)

        # --- 动手实践 ---
        practice = 0.0
        if stat["exam_count"] > 0:
            passed_rate = stat["exam_passed_count"] / max(stat["exam_count"], 1)
            practice = passed_rate * 60 + (stat["avg_exam_score"] / 100) * 40
            practice = min(practice, 100.0)
        elif stat["quiz_count"] > 0:
            practice = min(stat["quiz_count"] * 8, 50.0)

        # --- 探索精神 ---
        exploration = 0.0
        exploration += min(stat["chat_count"] * 0.5, 40.0)
        exploration += min(stat["session_count"] * 2, 40.0)
        exploration = min(exploration, 100.0)

        # --- 稳健程度 ---
        stability = 0.0
        stability += min(stat["streak_days"] * 3, 45.0)
        stability += min(stat["session_count"] * 1.5, 35.0)
        if stat["exam_count"] > 0 and stat["mistake_count"] > 0:
            correct_rate = stat["mistake_corrected_count"] / max(stat["mistake_count"], 1)
            stability += correct_rate * 20
        stability = min(stability, 100.0)

        # --- 综合能力 ---
        comprehensive = (visual + theory + practice + exploration + stability) / 5
        comprehensive = min(comprehensive, 100.0)

        # 保存到数据库
        ability = await self._get_or_create(db, user_id)
        ability.visual_score = round(visual, 1)
        ability.theory_score = round(theory, 1)
        ability.practice_score = round(practice, 1)
        ability.exploration_score = round(exploration, 1)
        ability.stability_score = round(stability, 1)
        ability.comprehensive_score = round(comprehensive, 1)
        ability.update_time = datetime.now(timezone.utc)
        await db.commit()

        return self._to_dict(ability)

    # ════════════════════════════════════════════════════════════
    # 内部方法
    # ════════════════════════════════════════════════════════════

    async def _get(self, db: AsyncSession, user_id: int) -> Optional[UserAbility]:
        result = await db.execute(
            select(UserAbility).where(UserAbility.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create(self, db: AsyncSession, user_id: int) -> UserAbility:
        ability = await self._get(db, user_id)
        if ability is None:
            ability = UserAbility(user_id=user_id)
            db.add(ability)
            await db.commit()
            await db.refresh(ability)
        return ability

    async def _apply_decay_if_needed(
        self,
        db: AsyncSession,
        ability: UserAbility,
    ) -> UserAbility:
        """
        应用衰减：距离上次更新超过 1 天开始衰减。
        衰减策略：
          - 每超过一天未学习，所有能力轻微下降
          - 稳健程度衰减速度更快
          - 衰减有上限（最多衰减14天量）
          - 最低不低于 0
        """
        now = datetime.now(timezone.utc)
        last_update = ability.update_time
        if last_update is None:
            return ability

        # 计算上次更新到现在的天数差
        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=timezone.utc)

        days_diff = (now - last_update).days
        if days_diff < 1:
            return ability  # 24小时内不衰减

        decay_days = min(days_diff, DECAY_MAX_DAYS)
        changed = False

        for attr in ["visual_score", "comprehensive_score", "exploration_score", "theory_score", "practice_score"]:
            old = getattr(ability, attr) or 0.0
            decay = DECAY_PER_DAY * decay_days
            new = max(old - decay, MIN_SCORE)
            if abs(new - old) > 0.01:
                setattr(ability, attr, round(new, 1))
                changed = True

        # 稳健程度衰减更快
        stability_old = ability.stability_score or 0.0
        stability_new = max(stability_old - STABILITY_DECAY_PER_DAY * decay_days, MIN_SCORE)
        if abs(stability_new - stability_old) > 0.01:
            ability.stability_score = round(stability_new, 1)
            changed = True

        if changed:
            ability.update_time = now
            await db.commit()

        return ability

    async def _collect_stats(self, db: AsyncSession, user_id: int) -> Dict:
        """收集用户学习统计数据（用于全量重算）"""
        stats = {}

        # 节点总数
        from app.models.knowledge_graph import KnowledgeNode
        total_result = await db.execute(select(func.count(KnowledgeNode.id)))
        stats["total_nodes"] = total_result.scalar() or 0

        # 用户学习进度
        progress_result = await db.execute(
            select(LearningProgress).where(LearningProgress.user_id == user_id)
        )
        all_progress = progress_result.scalars().all()
        stats["nodes_completed"] = sum(1 for p in all_progress if p.status == "completed")
        stats["nodes_in_progress"] = sum(1 for p in all_progress if p.status == "in_progress")
        stats["notes_completed"] = sum(
            1 for p in all_progress
            if p.resource_progress and p.resource_progress.get("notes")
        )
        stats["quiz_completed"] = sum(
            1 for p in all_progress
            if p.resource_progress and p.resource_progress.get("quiz")
        )

        # 学习会话
        session_result = await db.execute(
            select(func.count(StudySession.id)).where(StudySession.user_id == user_id)
        )
        stats["session_count"] = session_result.scalar() or 0

        # 学习日历：连续天数
        streak = await self._calc_streak(db, user_id)
        stats["streak_days"] = streak

        # 考试
        exam_result = await db.execute(
            select(ExamResult).where(ExamResult.user_id == user_id)
        )
        all_exams = exam_result.scalars().all()
        stats["exam_count"] = len(all_exams)
        stats["exam_passed_count"] = sum(1 for e in all_exams if e.passed)
        scores = [e.score for e in all_exams if e.score is not None]
        stats["avg_exam_score"] = sum(scores) / len(scores) if scores else 0
        stats["high_score_rate"] = sum(1 for s in scores if s >= 80) / max(len(scores), 1)

        # 错题统计（从 exam_result.details 分析）
        mistake_count = 0
        corrected_count = 0
        import json as _json
        for exam in all_exams:
            if exam.details:
                try:
                    details = _json.loads(exam.details) if isinstance(exam.details, str) else exam.details
                    for d in details:
                        if not d.get("is_correct", True):
                            mistake_count += 1
                            if d.get("removed"):
                                corrected_count += 1
                except (TypeError, _json.JSONDecodeError):
                    pass
        stats["mistake_count"] = mistake_count
        stats["mistake_corrected_count"] = corrected_count

        # 练习统计（source=quiz的考试记录数量）
        quiz_count = sum(
            1 for e in all_exams
            if e.details and ("quiz" in str(e.details))
        )
        stats["quiz_count"] = quiz_count

        # AI 聊天
        chat_result = await db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatSession.user_id == user_id,
                ChatMessage.role == "user",
            )
        )
        stats["chat_count"] = chat_result.scalar() or 0

        return stats

    async def _calc_streak(self, db: AsyncSession, user_id: int) -> int:
        """计算用户连续学习天数"""
        result = await db.execute(
            select(func.date(StudySession.started_at).label("study_date"))
            .where(StudySession.user_id == user_id)
            .group_by(func.date(StudySession.started_at))
            .order_by(func.date(StudySession.started_at).desc())
        )
        dates = [row.study_date for row in result.all()]
        if not dates:
            return 0

        streak = 1
        from datetime import date as date_type
        today = date_type.today()

        # 找到最近的学习日
        for i in range(1, len(dates)):
            if (dates[0] - dates[i]).days == i:
                streak += 1
            else:
                break

        return streak


# 全局单例
ability_service = AbilityService()
