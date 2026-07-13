"""
Learning Analytics Agent（数据分析中心）
=======================================

定位：整个系统的数据分析中心。不生成资源、不回答问题。

输入：数据库中的 practice_record、chat_history、learning_behavior、video_progress 等
输出：统一的学习分析指标 → 交给 Profile Agent 更新画像

分析维度：
  1. 活跃度 — 登录次数、学习时长、任务完成率
  2. 专注度 — 暂停次数、页面切换、离开页面
  3. 资源偏好 — 统计视频/PPT/案例/文档的使用占比
  4. 知识掌握 — 各知识点的掌握度追踪
  5. 错误模式 — AI 分析用户错误答案，判断概念错误 vs 计算错误
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.agents.base import BaseAgent
from app.agents.state import LearningState, LearningAnalytics
from app.utils.logger import get_logger

logger = get_logger("learning_analytics")


# ══════════════════════════════════════════════════
#  错误模式分析 Prompt
# ══════════════════════════════════════════════════

ERROR_ANALYSIS_PROMPT = """你是一位学习诊断专家。请分析以下学生的错误答案，判断错误类型并给出模式总结。

## 学生信息
- 能力水平: {ability_level}
- 当前学习主题: {subject}

## 错误记录
{error_records}

## 要求
返回 JSON：
```json
{{
    "primary_error_type": "概念混淆|计算错误|逻辑漏洞|方法误用|理解偏差|无错误",
    "error_patterns": ["具体错误模式1", "错误模式2"],
    "analysis_detail": "一句话总结主要问题（50字以内）"
}}
```
只返回 JSON，不要其他内容。"""


class LearningAnalyticsAgent(BaseAgent):
    """
    数据分析中心 — 从学习行为数据中计算多维分析指标

    替代了旧版的 BehaviorAnalysisAgent + ProfileUpdateAgent 的分析部分。
    输出统一的 analytics 结果给 Orchestrator，由 Orchestrator 决定是否传给 ProfileAgent。
    """

    @property
    def name(self) -> str:
        return "learning_analytics_agent"

    @property
    def description(self) -> str:
        return "数据分析中心 — 计算活跃度/专注度/资源偏好/知识掌握/错误模式"

    # ═══════════════════════════════════════════
    #  核心 run 方法
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        logger.info("📊 开始学习数据分析...")

        user_id = state.get("user_id", "default")
        subject = state.get("subject", "")
        profile = state.get("student_profile", {})
        resources = state.get("resources", [])
        assessment = state.get("assessment", {})
        learning_path = state.get("learning_path", [])
        event_payload = state.get("event_payload", {})

        # ── 维度1：活跃度 ──
        activity = self._compute_activity(state, learning_path, resources)

        # ── 维度2：专注度 ──
        focus = self._compute_focus(state, profile)

        # ── 维度3：资源偏好 ──
        resource_prefs = self._compute_resource_preferences(state, resources)

        # ── 维度4：知识掌握度 ──
        knowledge = self._compute_knowledge_mastery(state, assessment, learning_path)

        # ── 维度5：错误模式分析（AI）──
        error_analysis = self._analyze_errors(state, assessment, profile, subject)

        # ── 维度6：学习节奏 ──
        rhythm = self._compute_learning_rhythm(state, profile)

        # ★ 维度7：成长画像（Growth）— v3.1 新增 ──
        growth = self._compute_growth(state, assessment, knowledge, profile)

        # ★ 维度8：学习风险（Risk）— v3.1 新增 ──
        risk = self._compute_risk(state, assessment, profile, learning_path)

        # ── 组装分析结果 ──
        analytics: Dict[str, Any] = {
            # 活跃度
            "activity_score": activity["score"],
            "login_frequency": activity["login_frequency"],
            "total_study_hours": activity["total_study_hours"],
            "task_completion_rate": activity["task_completion_rate"],

            # 专注度
            "focus_score": focus["score"],
            "pause_count": focus["pause_count"],
            "page_switch_count": focus["page_switch_count"],

            # 资源偏好
            "resource_preferences": resource_prefs,
            "preferred_resource_type": max(resource_prefs, key=resource_prefs.get) if resource_prefs else "notes",

            # 知识掌握
            "knowledge_mastery": knowledge["mastery"],
            "mastery_trend": knowledge["trend"],

            # 错误模式
            "error_patterns": error_analysis.get("error_patterns", []),
            "primary_error_type": error_analysis.get("primary_error_type", ""),
            "error_analysis_detail": error_analysis.get("analysis_detail", ""),

            # 学习节奏
            "learning_rhythm": rhythm["rhythm"],
            "peak_study_hours": rhythm["peak_hours"],

            # ★ Growth（成长画像）
            "growth_history": growth["history"],
            "growth_trend": growth["trend"],

            # ★ Risk（学习风险）
            "risk_level": risk["level"],
            "risk_factors": risk["factors"],
            "consecutive_missed_tasks": risk["consecutive_missed"],
            "consecutive_low_scores": risk["consecutive_low_scores"],
            "stagnant_topics": risk["stagnant_topics"],

            # 元数据
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "data_source_count": self._count_data_sources(state),
        }

        # 日志摘要
        log = self._log(
            state,
            f"📊 分析完成 | 活跃度 {analytics['activity_score']:.0f} | "
            f"专注度 {analytics['focus_score']:.0f} | "
            f"偏好 {analytics['preferred_resource_type']} | "
            f"掌握 {len(analytics['knowledge_mastery'])} 个知识点 | "
            f"错误类型 {analytics['primary_error_type']}"
        )

        return {
            **log,
            "learning_analytics": analytics,
            "next_action": "orchestrate",
        }

    # ═══════════════════════════════════════════
    #  维度1：活跃度计算
    # ═══════════════════════════════════════════

    def _compute_activity(
        self, state: LearningState, learning_path: List[Dict], resources: List[Dict]
    ) -> Dict[str, Any]:
        """计算学习活跃度"""
        user_messages = state.get("user_messages", [])
        total_messages = len(user_messages)

        # 从学习路径推断完成情况
        total_steps = len(learning_path)
        completed_steps = sum(1 for s in learning_path if s.get("status") == "completed")
        in_progress = sum(1 for s in learning_path if s.get("status") == "in_progress")

        # 从资源数量推断学习量
        resource_count = len(resources)

        # 估算学习时长（分钟）
        estimated_minutes = sum(
            s.get("estimated_minutes", 15) for s in learning_path
            if s.get("status") in ("completed", "in_progress")
        )
        total_study_hours = round(estimated_minutes / 60, 1)

        # 任务完成率
        task_completion_rate = round(completed_steps / max(total_steps, 1), 2)

        # 活跃度综合评分
        # 公式：消息量(30%) + 完成率(40%) + 资源使用(30%)
        msg_score = min(100, total_messages * 8)
        completion_score = task_completion_rate * 100
        resource_score = min(100, resource_count * 15)

        activity_score = round(msg_score * 0.3 + completion_score * 0.4 + resource_score * 0.3, 1)

        # 登录频率（基于消息分布估算）
        login_frequency = max(1, total_messages // 5)

        return {
            "score": activity_score,
            "login_frequency": login_frequency,
            "total_study_hours": total_study_hours,
            "task_completion_rate": task_completion_rate,
        }

    # ═══════════════════════════════════════════
    #  维度2：专注度计算
    # ═══════════════════════════════════════════

    def _compute_focus(self, state: LearningState, profile: Dict) -> Dict[str, Any]:
        """计算专注指数"""
        # 从事件数据和行为特征中推断
        event_payload = state.get("event_payload", {})
        behavior = state.get("behavior_features", {})  # 兼容旧版数据

        # 暂停次数和页面切换可从事件数据中获得
        pause_count = event_payload.get("pause_count",
                      behavior.get("pause_count", 0))
        page_switch_count = event_payload.get("page_switch_count",
                            behavior.get("page_switch_count", 0))

        # 基础专注度（从画像继承，或重新计算）
        base_focus = float(profile.get("focus_score",
                         behavior.get("focus_score", 75)))

        # 根据暂停和切换调整
        penalty = (pause_count * 3 + page_switch_count * 2) * 0.5
        focus_score = round(max(30, min(98, base_focus - penalty)), 1)

        return {
            "score": focus_score,
            "pause_count": pause_count,
            "page_switch_count": page_switch_count,
        }

    # ═══════════════════════════════════════════
    #  维度3：资源偏好计算
    # ═══════════════════════════════════════════

    def _compute_resource_preferences(
        self, state: LearningState, resources: List[Dict]
    ) -> Dict[str, float]:
        """统计各类型资源的使用占比"""
        prefs: Dict[str, float] = {
            "视频": 0.0, "PPT": 0.0, "案例": 0.0, "文档": 0.0,
            "练习题": 0.0, "思维导图": 0.0,
        }

        type_label_map = {
            "notes": "文档", "mindmap": "思维导图", "quiz": "练习题",
            "code_example": "案例", "animation": "视频",
        }

        if not resources:
            # 从画像中继承
            existing = state.get("student_profile", {}).get("resource_preferences", {})
            if existing:
                return existing
            return {"文档": 50.0, "案例": 30.0, "练习题": 20.0}

        # 统计每种资源类型的 content 长度作为使用量代理
        type_content_length: Dict[str, int] = {}
        for r in resources:
            res_type = r.get("type", "notes")
            label = type_label_map.get(res_type, "文档")
            length = len(str(r.get("content", "")))
            type_content_length[label] = type_content_length.get(label, 0) + length

        total = sum(type_content_length.values()) or 1
        for label in prefs:
            prefs[label] = round(type_content_length.get(label, 0) / total * 100, 1)

        return prefs

    # ═══════════════════════════════════════════
    #  维度4：知识掌握度
    # ═══════════════════════════════════════════

    def _compute_knowledge_mastery(
        self, state: LearningState, assessment: Dict, learning_path: List[Dict]
    ) -> Dict[str, Any]:
        """计算知识点掌握度追踪"""
        mastery: Dict[str, float] = {}

        # 从测评中的知识追踪获取
        knowledge_tracking = assessment.get("knowledge_tracking", {})
        if knowledge_tracking:
            for topic, data in knowledge_tracking.items():
                if isinstance(data, dict):
                    mastery[topic] = float(data.get("mastery_level", 0))
                else:
                    mastery[topic] = float(data) if data else 0

        # 从学习路径补充
        for step in learning_path:
            topic = step.get("topic", "")
            if topic and topic not in mastery:
                score = step.get("score")
                if score is not None:
                    mastery[topic] = float(score)
                elif step.get("status") == "completed":
                    mastery[topic] = 85.0

        # 从画像继承已有掌握度
        existing = state.get("student_profile", {}).get("knowledge_mastery", {})
        for topic, level in existing.items():
            if topic not in mastery:
                mastery[topic] = float(level)

        # 趋势判断
        trend = "stable"
        if assessment.get("overall_score"):
            prev_scores = []
            for msg in state.get("messages", []):
                if "测评" in msg.get("message", "") and "总分" in msg.get("message", ""):
                    prev_scores.append(True)
            if len(prev_scores) >= 2:
                trend = "improving"

        return {"mastery": mastery, "trend": trend}

    # ═══════════════════════════════════════════
    #  维度5：错误模式分析（AI）
    # ═══════════════════════════════════════════

    def _analyze_errors(
        self, state: LearningState, assessment: Dict, profile: Dict, subject: str
    ) -> Dict[str, Any]:
        """使用 AI 分析用户错误模式"""
        # 先检查 assessment 中已有的错误分析
        error_analysis = assessment.get("error_analysis", {})
        if error_analysis and error_analysis.get("error_patterns"):
            return {
                "primary_error_type": error_analysis.get("primary_error_type", ""),
                "error_patterns": error_analysis.get("error_patterns", []),
                "analysis_detail": error_analysis.get("suggested_fix", ""),
            }

        # 从 gaps 和用户消息中提取错误信息
        gaps = assessment.get("gaps_found", [])
        gap_details = assessment.get("gap_details", [])
        user_messages = state.get("user_messages", [])

        if not gaps and not gap_details and len(user_messages) < 2:
            return {"primary_error_type": "无错误", "error_patterns": [], "analysis_detail": ""}

        # 构建错误记录
        error_records = []
        for gd in gap_details[:5]:
            error_records.append(
                f"- 知识点: {gd.get('gap', gd.get('topic', '?'))} "
                f"严重度: {gd.get('severity', '?')} "
                f"原因: {gd.get('cause', gd.get('possible_cause', '?'))}"
            )
        if not error_records and gaps:
            error_records = [f"- 薄弱点: {g}" for g in gaps[:5]]
        if not error_records:
            error_records = ["无明显错误记录"]

        # 尝试 AI 分析
        try:
            prompt = ERROR_ANALYSIS_PROMPT.format(
                ability_level=profile.get("ability_level", "intermediate"),
                subject=subject or "数据结构",
                error_records="\n".join(error_records),
            )
            messages = [
                {"role": "system", "content": "你是学习诊断专家。只返回 JSON。"},
                {"role": "user", "content": prompt},
            ]
            response = self._call_llm(messages, temperature=0.3, max_tokens=500)
            result = self._parse_json(response)
            return result
        except Exception as e:
            logger.debug("AI 错误分析跳过: %s", e)

        # 规则兜底
        return {
            "primary_error_type": "理解偏差",
            "error_patterns": gaps[:3] if gaps else [],
            "analysis_detail": "建议加强基础概念学习和练习",
        }

    # ═══════════════════════════════════════════
    #  维度6：学习节奏
    # ═══════════════════════════════════════════

    def _compute_learning_rhythm(
        self, state: LearningState, profile: Dict
    ) -> Dict[str, str]:
        """判断学习节奏类型"""
        pace = profile.get("pace", "moderate")
        learning_path = state.get("learning_path", [])
        completed = sum(1 for s in learning_path if s.get("status") == "completed")
        total = len(learning_path)

        if pace == "fast" and total > 0 and completed / max(total, 1) > 0.6:
            rhythm = "突击型"
        elif pace == "slow":
            rhythm = "持续型"
        elif total > 0 and completed / max(total, 1) < 0.3:
            rhythm = "碎片型"
        else:
            rhythm = "持续型"

        # 高峰时段（从画像或消息时间戳推断）
        peak = "evening"  # 默认
        messages = state.get("messages", [])
        if messages:
            timestamps = [m.get("timestamp", "") for m in messages if m.get("timestamp")]
            # 简化：多数学生在晚间学习
            peak = "evening"

        return {"rhythm": rhythm, "peak_hours": peak}

    # ═══════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════

    @staticmethod
    def _count_data_sources(state: LearningState) -> int:
        """统计有多少数据源被用于分析"""
        count = 0
        if state.get("student_profile"):
            count += 1
        if state.get("learning_path"):
            count += 1
        if state.get("assessment"):
            count += 1
        if state.get("resources"):
            count += 1
        if state.get("user_messages"):
            count += 1
        return count

    # ═══════════════════════════════════════════
    #  维度7：成长画像（Growth）
    # ═══════════════════════════════════════════

    def _compute_growth(
        self, state: LearningState, assessment: Dict,
        knowledge: Dict, profile: Dict
    ) -> Dict[str, Any]:
        """计算成长画像 — 对比多次测评的知识掌握度趋势"""
        history = []

        # 从画像中获取历史成长记录
        existing_history = profile.get("growth_history", [])
        if isinstance(existing_history, list):
            history.extend(existing_history)

        # 本次测评结果追加
        if assessment and assessment.get("overall_score"):
            score = assessment["overall_score"]
            if isinstance(score, dict):
                score = score.get("overall_score", 0)
            score = float(score) if score else 0

            history.append({
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "overall_score": round(score, 1),
                "mastered_topics": [
                    t for t, s in knowledge.get("mastery", {}).items()
                    if float(s) >= 70
                ],
            })
            # 只保留最近10条
            history = history[-10:]

        # 趋势判断
        trend = "steady"
        scores = [h.get("overall_score", 0) for h in history if h.get("overall_score")]
        if len(scores) >= 3:
            recent_avg = sum(scores[-3:]) / 3
            earlier_avg = sum(scores[:3]) / 3 if len(scores) >= 6 else scores[0]
            if recent_avg > earlier_avg + 10:
                trend = "accelerating"
            elif recent_avg > earlier_avg + 3:
                trend = "steady"
            elif recent_avg < earlier_avg - 10:
                trend = "declining"
            else:
                trend = "plateauing"

        return {"history": history, "trend": trend}

    # ═══════════════════════════════════════════
    #  维度8：学习风险（Risk）
    # ═══════════════════════════════════════════

    def _compute_risk(
        self, state: LearningState, assessment: Dict,
        profile: Dict, learning_path: List[Dict]
    ) -> Dict[str, Any]:
        """计算学习风险画像"""
        factors = []
        consecutive_missed = 0
        consecutive_low = 0
        stagnant = []

        # 检查连续未完成任务
        for step in reversed(learning_path):
            if step.get("status") == "skipped":
                consecutive_missed += 1
            else:
                break

        if consecutive_missed >= 3:
            factors.append(f"连续{consecutive_missed}个任务被跳过")

        # 检查连续低分
        knowledge_tracking = assessment.get("knowledge_tracking", {})
        for topic, data in knowledge_tracking.items():
            if isinstance(data, dict):
                error_count = data.get("error_count", 0)
                if error_count >= 3:
                    consecutive_low += 1

        if consecutive_low >= 3:
            factors.append(f"连续{consecutive_low}次低分")

        # 检查长期未掌握的知识点
        mastery = knowledge_tracking if knowledge_tracking else profile.get("knowledge_mastery", {})
        for topic, data in mastery.items():
            level = float(data.get("mastery_level", data)) if isinstance(data, dict) else float(data)
            if level < 40:
                stagnant.append(topic)

        if len(stagnant) >= 3:
            factors.append(f"{len(stagnant)}个知识点长期未掌握: {', '.join(stagnant[:3])}")

        # 风险评估
        risk_score = len(factors)
        if risk_score >= 3:
            level = "high"
        elif risk_score >= 1:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "factors": factors,
            "consecutive_missed": consecutive_missed,
            "consecutive_low_scores": consecutive_low,
            "stagnant_topics": stagnant,
        }

    # ═══════════════════════════════════════════
    #  降级策略
    # ═══════════════════════════════════════════

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        super().fallback(state, error)
        return {
            "next_action": "orchestrate",
            "learning_analytics": {
                "activity_score": 50.0,
                "focus_score": 60.0,
                "resource_preferences": {"文档": 50.0, "案例": 30.0, "练习题": 20.0},
                "preferred_resource_type": "文档",
                "knowledge_mastery": {},
                "mastery_trend": "stable",
                "error_patterns": [],
                "primary_error_type": "",
                "learning_rhythm": "持续型",
                "peak_study_hours": "evening",
                "growth_history": [],
                "growth_trend": "steady",
                "risk_level": "low",
                "risk_factors": [],
                "consecutive_missed_tasks": 0,
                "consecutive_low_scores": 0,
                "stagnant_topics": [],
            },
        }
