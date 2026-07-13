from typing import Dict, Any, List

from app.agents.base import BaseAgent
from app.agents.state import LearningState
from app.utils.logger import get_logger

logger = get_logger("review_agent")


class ReviewRecommendationAgent(BaseAgent):
    """对生成资源做轻量审核和推荐编排。"""

    @property
    def name(self) -> str:
        return "review_agent"

    @property
    def description(self) -> str:
        return "审核资源质量与相关度，并输出推荐资源"

    def run(self, state: LearningState) -> Dict[str, Any]:
        resources = state.get("resources", [])
        profile = state.get("student_profile", {})
        assessment = state.get("assessment", {})
        gaps = set(assessment.get("gaps_found", []) or profile.get("weaknesses", []))
        preference = profile.get("resource_preference", "notes")

        reviewed_resources: List[Dict[str, Any]] = []
        for item in resources:
            content = item.get("content", "") or ""
            tags = set(item.get("tags", []))
            quality_score = min(95, max(40, int(len(content) / 30) + 35))
            relevance_score = 75
            if item.get("type") == preference:
                relevance_score += 10
            if gaps.intersection(tags):
                relevance_score += 8
            if item.get("difficulty") == "medium":
                relevance_score += 4

            recommendation_score = min(100, int(quality_score * 0.45 + relevance_score * 0.55))
            review_status = "approved" if recommendation_score >= 65 else "needs_revision"
            reviewed_resources.append(
                {
                    "type": item.get("type"),
                    "title": item.get("title"),
                    "quality_score": quality_score,
                    "relevance_score": relevance_score,
                    "recommendation_score": recommendation_score,
                    "review_status": review_status,
                    "review_reason": self._build_reason(item, preference, gaps, recommendation_score),
                }
            )

        reviewed_resources.sort(key=lambda row: row["recommendation_score"], reverse=True)
        recommended = [item for item in reviewed_resources if item["review_status"] == "approved"][:3]

        log = self._log(
            state,
            f"✅ 资源审核完成 | 通过 {len(recommended)} 项 | 首推 {recommended[0]['type'] if recommended else '无'}",
        )
        return {
            **log,
            "reviewed_resources": reviewed_resources,
            "recommended_resources": recommended,
            "next_action": "assess",
        }

    @staticmethod
    def _build_reason(
        item: Dict[str, Any],
        preference: str,
        gaps: set,
        recommendation_score: int,
    ) -> str:
        reasons = []
        if item.get("type") == preference:
            reasons.append("符合当前资源偏好")
        if gaps.intersection(set(item.get("tags", []))):
            reasons.append("覆盖薄弱知识点")
        if not reasons:
            reasons.append("适合作为当前步骤补充材料")
        reasons.append(f"综合推荐分 {recommendation_score}")
        return "，".join(reasons)
