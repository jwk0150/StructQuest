from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_ecosystem import (
    LearningEvent,
    ProfileSnapshot,
    LearningPlan,
    LearningPlanStep,
    ResourceAsset,
)


class LearningRecordService:
    """多智能体学习过程的持久化服务。"""

    async def log_event(
        self,
        db: AsyncSession,
        user_id: int,
        event_type: str,
        subject: Optional[str] = None,
        node_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_id: Optional[int] = None,
        duration_seconds: int = 0,
        score: Optional[float] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> LearningEvent:
        event = LearningEvent(
            user_id=user_id,
            event_type=event_type,
            subject=subject,
            node_id=node_id,
            session_id=session_id,
            resource_id=resource_id,
            duration_seconds=duration_seconds,
            score=score,
            event_data=event_data or {},
        )
        db.add(event)
        await db.flush()
        return event

    async def create_profile_snapshot(
        self,
        db: AsyncSession,
        user_id: int,
        profile_data: Dict[str, Any],
        source: str = "manual",
        summary: Optional[str] = None,
    ) -> ProfileSnapshot:
        version_result = await db.execute(
            select(func.max(ProfileSnapshot.profile_version)).where(ProfileSnapshot.user_id == user_id)
        )
        max_version = version_result.scalar() or 0
        snapshot = ProfileSnapshot(
            user_id=user_id,
            profile_version=max_version + 1,
            source=source,
            summary=summary or profile_data.get("summary"),
            profile_data=profile_data,
        )
        db.add(snapshot)
        await db.flush()
        return snapshot

    async def save_learning_session_result(
        self,
        db: AsyncSession,
        user_id: int,
        subject: str,
        goal: str,
        result: Dict[str, Any],
        profile_snapshot_id: Optional[int] = None,
    ) -> Optional[LearningPlan]:
        learning_path = result.get("learning_path") or []
        if not learning_path:
            return None

        plan = LearningPlan(
            user_id=user_id,
            subject=subject,
            goal=goal,
            plan_source="multi_agent",
            status=result.get("session_status", "active"),
            profile_snapshot_id=profile_snapshot_id,
            plan_data={
                "summary": result.get("_summary", {}),
                "student_profile": result.get("student_profile", {}),
                "assessment": result.get("assessment", {}),
                "behavior_features": result.get("behavior_features", {}),
                "reviewed_resources": result.get("reviewed_resources", []),
                "recommended_resources": result.get("recommended_resources", []),
                "learning_path": result.get("learning_path", []),
                "messages": result.get("messages", []),
            },
        )
        db.add(plan)
        await db.flush()

        for step in learning_path:
            db.add(
                LearningPlanStep(
                    plan_id=plan.id,
                    step_no=step.get("step_id", 0),
                    topic=step.get("topic", "未命名步骤"),
                    description=step.get("description"),
                    difficulty=step.get("difficulty", "medium"),
                    bloom_level=step.get("bloom_level"),
                    estimated_minutes=step.get("estimated_minutes", 15),
                    prerequisites=step.get("prerequisites", []),
                    step_status=step.get("status", "pending"),
                    score=step.get("score"),
                )
            )

        reviewed_map = {
            item.get("type"): item for item in (result.get("reviewed_resources") or [])
        }
        for item in result.get("resources", [])[:10]:
            review_info = reviewed_map.get(item.get("type"), {})
            db.add(
                ResourceAsset(
                    user_id=user_id,
                    plan_id=plan.id,
                    asset_type=item.get("type", "unknown"),
                    source_type="system",
                    title=item.get("title", "AI资源"),
                    topic=item.get("topic"),
                    subject=subject,
                    content_text=item.get("content"),
                    file_url=item.get("file_url"),
                    tags=item.get("tags", []),
                    review_status=review_info.get("review_status", "pending"),
                    quality_score=review_info.get("quality_score", 0),
                    relevance_score=review_info.get("relevance_score", 0),
                    recommendation_score=review_info.get("recommendation_score", 0),
                    review_notes=review_info.get("review_reason"),
                    metadata_json=item.get("meta", {}),
                )
            )

        await self.log_event(
            db=db,
            user_id=user_id,
            event_type="learning_session_created",
            subject=subject,
            session_id=str(plan.id),
            event_data={
                "goal": goal,
                "step_count": len(learning_path),
                "recommended_count": len(result.get("recommended_resources", [])),
            },
        )
        return plan


learning_record_service = LearningRecordService()
