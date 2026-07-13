"""
Recommendation Agent（推荐Agent）— v3
====================================

定位：首页推荐。根据画像、学习路径、资源、知识掌握度进行个性化推荐排序。

输入：
  - 学生画像（能力、偏好、掌握度）
  - 学习路径（当前进度）
  - 资源库（可用资源）
  - 知识掌握度

推荐策略：
  - 薄弱点相关资源优先
  - 偏好资源类型加权
  - 已掌握内容降权
  - 基于当前学习路径的相关资源

它只负责：推荐 / 排序 / 个性化
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.agents.base import BaseAgent
from app.agents.state import LearningState, RecommendationItem, RecommendationResult
from app.utils.logger import get_logger

logger = get_logger("recommendation_agent")


class RecommendationAgent(BaseAgent):
    """
    推荐 Agent — 首页个性化推荐

    不生成资源，只排序和个性化推荐。
    """

    @property
    def name(self) -> str:
        return "recommendation_agent"

    @property
    def description(self) -> str:
        return "首页推荐 — 基于画像和知识掌握度进行个性化资源排序与推荐"

    # ═══════════════════════════════════════════
    #  核心 run 方法
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        logger.info("🎯 开始生成个性化推荐...")

        profile = state.get("student_profile", {})
        analytics = state.get("learning_analytics", {})
        learning_path = state.get("learning_path", [])
        resources = state.get("resources", [])
        event_payload = state.get("event_payload", {})

        # ── 收集推荐候选 ──
        candidates = self._collect_candidates(state, profile, resources, learning_path)

        # ── 个性化评分 ──
        scored = self._score_candidates(candidates, profile, analytics, learning_path)

        # ── 排序 + 截断 ──
        scored.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        top_items = scored[:8]  # 首页最多展示8条

        # ── 生成推荐理由 ──
        for item in top_items:
            if not item.get("reason"):
                item["reason"] = self._generate_reason(item, profile)

        # ── 组装结果 ──
        recommendation: Dict[str, Any] = {
            "items": top_items,
            "total": len(candidates),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "based_on": self._describe_basis(profile, analytics),
        }

        # 日志
        resource_types = [item.get("type", "?") for item in top_items[:3]]
        log = self._log(
            state,
            f"🎯 推荐完成 | {len(top_items)} 条 | "
            f"首推: {', '.join(resource_types)} | "
            f"依据: {recommendation['based_on']}"
        )

        return {
            **log,
            "recommendation": recommendation,
            "next_action": "orchestrate",
        }

    # ═══════════════════════════════════════════
    #  候选收集
    # ═══════════════════════════════════════════

    def _collect_candidates(
        self, state: LearningState, profile: Dict,
        resources: List[Dict], learning_path: List[Dict],
    ) -> List[Dict]:
        """收集推荐候选：已有资源 + 学习路径中的待学习主题"""
        candidates = []

        # 从已生成资源中收集
        for r in resources:
            candidates.append({
                "resource_id": id(r),
                "title": r.get("title", r.get("topic", "")),
                "type": r.get("type", ""),
                "topic": r.get("topic", ""),
                "difficulty": r.get("difficulty", "medium"),
                "source": r.get("source", "generated"),
                "tags": r.get("tags", []),
                "relevance_score": 50.0,  # 初始分
                "reason": "",
            })

        # 从学习路径中补充待学习的主题
        for step in learning_path:
            if step.get("status") in ("pending", "in_progress"):
                candidates.append({
                    "resource_id": step.get("step_id", 0),
                    "title": f"学习: {step.get('topic', '')}",
                    "type": "learning_path",
                    "topic": step.get("topic", ""),
                    "difficulty": step.get("difficulty", "medium"),
                    "source": "planner",
                    "tags": [step.get("topic", "")],
                    "relevance_score": 70.0,  # 当前路径优先级高
                    "reason": "",
                })

        return candidates

    # ═══════════════════════════════════════════
    #  评分引擎
    # ═══════════════════════════════════════════

    def _score_candidates(
        self, candidates: List[Dict], profile: Dict,
        analytics: Dict, learning_path: List[Dict],
    ) -> List[Dict]:
        """基于多维度评分"""
        weaknesses = set(profile.get("weaknesses", []))
        strengths = set(profile.get("strengths", []))
        prefs = profile.get("resource_preferences", {})
        knowledge_mastery = profile.get("knowledge_mastery", {})
        preferred_type = analytics.get("preferred_resource_type", "")

        # 学习路径上下文
        current_topics = set()
        for step in learning_path:
            if step.get("status") in ("pending", "in_progress"):
                current_topics.add(step.get("topic", ""))

        for item in candidates:
            score = item.get("relevance_score", 50.0)
            item_type = item.get("type", "")
            item_topic = item.get("topic", "")
            item_tags = set(item.get("tags", []))

            # 当前学习路径主题 → +25
            if item_topic in current_topics:
                score += 25

            # 薄弱点相关 → +20
            if item_topic in weaknesses or item_tags & weaknesses:
                score += 20

            # 资源类型偏好 → +15
            type_label_map = {
                "notes": "文档", "mindmap": "思维导图", "quiz": "练习题",
                "code_example": "案例", "animation": "视频",
            }
            pref_label = type_label_map.get(item_type, "")
            if pref_label and pref_label in prefs:
                pref_pct = prefs.get(pref_label, 50)
                score += pref_pct * 0.15  # 偏好百分比加权

            if item_type == preferred_type:
                score += 10

            # 已掌握 → -15（不需要再推荐）
            if item_topic in strengths or knowledge_mastery.get(item_topic, 0) > 80:
                score -= 15

            # 学习路径步骤优先级加成
            if item.get("source") == "planner":
                score += 10

            # 确保分数在合理范围
            item["relevance_score"] = round(max(10, min(98, score)), 1)

        return candidates

    # ═══════════════════════════════════════════
    #  推荐理由生成
    # ═══════════════════════════════════════════

    def _generate_reason(self, item: Dict, profile: Dict) -> str:
        """为推荐项生成个性化理由"""
        item_type = item.get("type", "")
        item_topic = item.get("topic", "")
        weaknesses = profile.get("weaknesses", [])
        strengths = profile.get("strengths", [])
        knowledge_mastery = profile.get("knowledge_mastery", {})

        reasons = []

        # 薄弱点相关
        if item_topic in weaknesses:
            reasons.append(f"针对你的薄弱点「{item_topic}」")

        # 当前路径
        if item.get("source") == "planner":
            reasons.append("学习路径下一步")

        # 掌握度低
        if knowledge_mastery.get(item_topic, 100) < 50:
            reasons.append(f"「{item_topic}」掌握度较低，建议加强")

        # 类型匹配
        type_labels = {
            "notes": "讲义", "mindmap": "思维导图", "quiz": "练习题",
            "code_example": "代码案例", "animation": "动画演示",
            "learning_path": "学习步骤",
        }
        label = type_labels.get(item_type, item_type)
        if not reasons:
            reasons.append(f"适合你当前阶段的{label}")

        return "；".join(reasons[:2])

    # ═══════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════

    @staticmethod
    def _describe_basis(profile: Dict, analytics: Dict) -> str:
        """描述推荐依据"""
        parts = []
        rhythm = profile.get("learning_rhythm", analytics.get("learning_rhythm", ""))
        if rhythm:
            parts.append(f"{rhythm}学习")
        prefs = profile.get("resource_preferences", {})
        if prefs:
            top = max(prefs, key=prefs.get)
            parts.append(f"偏好{top}")
        weak_count = len(profile.get("weaknesses", []))
        if weak_count > 0:
            parts.append(f"薄弱点覆盖")
        return " + ".join(parts) if parts else "综合推荐"

    # ═══════════════════════════════════════════
    #  降级策略
    # ═══════════════════════════════════════════

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        super().fallback(state, error)
        return {
            "next_action": "orchestrate",
            "recommendation": {
                "items": [],
                "total": 0,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "based_on": "默认推荐（推荐引擎暂不可用）",
            },
        }
