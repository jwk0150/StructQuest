from typing import Dict, Any, List

from app.agents.base import BaseAgent
from app.agents.state import LearningState
from app.utils.logger import get_logger

logger = get_logger("profile_update_agent")


class ProfileUpdateAgent(BaseAgent):
    """根据行为特征对学生画像做动态更新。"""

    @property
    def name(self) -> str:
        return "profile_update_agent"

    @property
    def description(self) -> str:
        return "融合基础画像、行为特征和测评结果，输出动态画像"

    def run(self, state: LearningState) -> Dict[str, Any]:
        profile = dict(state.get("student_profile", {}))
        behavior = state.get("behavior_features", {})
        assessment = state.get("assessment", {})
        cognitive = dict(profile.get("cognitive", {}))

        focus_score = int(behavior.get("focus_score", 70))
        engagement_score = int(behavior.get("engagement_score", 70))
        execution_score = int(behavior.get("execution_score", 60))
        recommendation = assessment.get("recommendation", "")
        gaps_found: List[str] = assessment.get("gaps_found", []) or profile.get("weaknesses", [])

        profile["resource_preference"] = behavior.get("resource_preference", "notes")
        profile["focus_score"] = focus_score
        profile["engagement_score"] = engagement_score
        profile["execution_score"] = execution_score
        profile["predicted_score"] = int((assessment.get("overall_score", 65) * 0.6) + execution_score * 0.4)
        profile["weaknesses"] = list(dict.fromkeys((profile.get("weaknesses", []) + gaps_found)))[:6]
        profile["daily_strategy"] = self._build_strategy(focus_score, behavior.get("resource_preference", "notes"))
        profile["summary"] = self._build_summary(profile, behavior, recommendation)

        confidence_score = float(profile.get("confidence_score", 60))
        confidence_score = min(100, max(30, confidence_score * 0.7 + execution_score * 0.3))
        profile["confidence_score"] = round(confidence_score, 1)

        cognitive["error_tolerance"] = round(
            min(1.0, max(0.1, float(cognitive.get("error_tolerance", 0.6)) + (engagement_score - 70) / 200)),
            2,
        )
        cognitive["concrete_example_need"] = round(
            min(1.0, max(0.1, float(cognitive.get("concrete_example_need", 0.6)) + (75 - focus_score) / 200)),
            2,
        )
        profile["cognitive"] = cognitive

        log = self._log(
            state,
            f"🧠 动态画像更新完成 | 预测成绩 {profile['predicted_score']} | 关注薄弱点 {', '.join(profile['weaknesses'][:2]) or '无'}",
        )
        return {
            **log,
            "student_profile": profile,
            "next_action": "plan_path",
        }

    @staticmethod
    def _build_strategy(focus_score: int, resource_preference: str) -> str:
        if focus_score < 60:
            return f"采用 15-20 分钟短任务节奏，优先推送 {resource_preference} 和即时练习。"
        if focus_score < 80:
            return f"采用 25 分钟稳态学习节奏，交替推送 {resource_preference} 与复习题。"
        return f"可进入较长学习块，优先用 {resource_preference} 做深度理解后再测评。"

    @staticmethod
    def _build_summary(profile: Dict[str, Any], behavior: Dict[str, Any], recommendation: str) -> str:
        ability_level = profile.get("ability_level", "beginner")
        focus_score = behavior.get("focus_score", 70)
        preference = behavior.get("resource_preference", "notes")
        summary = (
            f"该学生当前为 {ability_level} 水平，近期专注度约 {focus_score}/100，"
            f"更适合以 {preference} 为核心的学习材料。"
        )
        if recommendation:
            summary += f" 当前建议：{recommendation[:60]}"
        return summary[:220]
