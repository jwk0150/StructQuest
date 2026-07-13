from typing import Dict, Any, List

from app.agents.base import BaseAgent
from app.agents.state import LearningState
from app.utils.logger import get_logger

logger = get_logger("behavior_agent")


class BehaviorAnalysisAgent(BaseAgent):
    """把学习行为转成可复用的行为特征。"""

    CONFUSION_KEYWORDS = ("不会", "不懂", "为什么", "没理解", "卡住", "难")

    @property
    def name(self) -> str:
        return "behavior_agent"

    @property
    def description(self) -> str:
        return "分析聊天、答题、时长和资源使用行为，输出行为特征"

    def run(self, state: LearningState) -> Dict[str, Any]:
        user_messages: List[str] = state.get("user_messages", [])
        assessment = state.get("assessment", {})
        profile = state.get("student_profile", {})
        learning_path = state.get("learning_path", [])
        resources = state.get("resources", [])

        total_messages = len(user_messages)
        confusion_hits = sum(
            1
            for message in user_messages
            if any(keyword in (message or "") for keyword in self.CONFUSION_KEYWORDS)
        )
        answer_length = len(state.get("user_answer") or "")
        completed_steps = sum(1 for step in learning_path if step.get("status") == "completed")

        pace = profile.get("pace", "moderate")
        attention_span = profile.get("attention_span", 25)
        resource_preference = self._infer_resource_preference(resources)

        confusion_ratio = round(confusion_hits / max(total_messages, 1), 2)
        focus_score = max(30, min(95, int(85 - confusion_ratio * 30 + completed_steps * 5)))
        engagement_score = max(35, min(98, int(total_messages * 8 + answer_length / 20 + len(resources) * 6)))
        execution_score = max(20, min(100, int(completed_steps * 18 + assessment.get("overall_score", 0) * 0.4)))

        features = {
            "total_messages": total_messages,
            "confusion_hits": confusion_hits,
            "confusion_ratio": confusion_ratio,
            "focus_score": focus_score,
            "engagement_score": engagement_score,
            "execution_score": execution_score,
            "resource_preference": resource_preference,
            "pace_signal": pace,
            "attention_signal": attention_span,
            "behavior_summary": self._build_summary(
                focus_score, engagement_score, confusion_ratio, resource_preference
            ),
        }

        log = self._log(
            state,
            f"📈 行为分析完成 | 专注度 {focus_score} | 参与度 {engagement_score} | 资源偏好 {resource_preference}",
        )
        return {
            **log,
            "behavior_features": features,
            "next_action": "update_profile",
        }

    @staticmethod
    def _infer_resource_preference(resources: List[Dict[str, Any]]) -> str:
        if not resources:
            return "notes"
        type_scores: Dict[str, int] = {}
        for item in resources:
            res_type = item.get("type", "notes")
            type_scores[res_type] = type_scores.get(res_type, 0) + len(item.get("content", "")[:200])
        return max(type_scores, key=type_scores.get)

    @staticmethod
    def _build_summary(
        focus_score: int,
        engagement_score: int,
        confusion_ratio: float,
        resource_preference: str,
    ) -> str:
        if confusion_ratio >= 0.5:
            status = "近期存在较明显的概念疑惑"
        elif focus_score >= 80:
            status = "学习状态较稳定"
        else:
            status = "需要通过更短任务维持节奏"
        return f"{status}，更偏好 {resource_preference} 类资源，参与度约为 {engagement_score}/100。"
