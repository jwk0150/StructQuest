from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, ForeignKey
from sqlalchemy.sql import func

from app.db.session import Base


class LearningEvent(Base):
    """统一学习事件日志，用于行为分析与画像更新。"""

    __tablename__ = "learning_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    subject = Column(String(100), nullable=True, index=True)
    node_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    resource_id = Column(Integer, nullable=True, index=True)
    duration_seconds = Column(Integer, default=0)
    score = Column(Float, nullable=True)
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ProfileSnapshot(Base):
    """动态画像快照，支持初始化、事件更新、每日汇总。"""

    __tablename__ = "profile_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    profile_version = Column(Integer, default=1)
    source = Column(String(30), default="manual", index=True)  # manual/event/daily/agent
    summary = Column(Text, nullable=True)
    profile_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class LearningPlan(Base):
    """个性化学习计划主表。"""

    __tablename__ = "learning_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    subject = Column(String(100), nullable=False, index=True)
    goal = Column(String(255), nullable=False)
    plan_source = Column(String(30), default="agent")
    status = Column(String(20), default="active", index=True)
    profile_snapshot_id = Column(Integer, ForeignKey("profile_snapshots.id"), nullable=True)
    plan_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LearningPlanStep(Base):
    """学习计划步骤表。"""

    __tablename__ = "learning_plan_steps"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=False, index=True)
    step_no = Column(Integer, nullable=False)
    topic = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), default="medium")
    bloom_level = Column(String(20), nullable=True)
    estimated_minutes = Column(Integer, default=15)
    prerequisites = Column(JSON, nullable=True)
    step_status = Column(String(20), default="pending", index=True)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ResourceAsset(Base):
    """统一资源资产表，承接系统生成资源与审核流程。"""

    __tablename__ = "resource_assets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    plan_id = Column(Integer, ForeignKey("learning_plans.id"), nullable=True, index=True)
    asset_type = Column(String(50), nullable=False, index=True)
    source_type = Column(String(30), default="system", index=True)  # system/external/manual
    title = Column(String(255), nullable=False)
    topic = Column(String(200), nullable=True, index=True)
    subject = Column(String(100), nullable=True, index=True)
    content_text = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    source_url = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=True)
    review_status = Column(String(30), default="pending", index=True)
    quality_score = Column(Float, default=0)
    relevance_score = Column(Float, default=0)
    recommendation_score = Column(Float, default=0)
    review_notes = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ResourceReview(Base):
    """资源审核记录。"""

    __tablename__ = "resource_reviews"

    id = Column(Integer, primary_key=True, index=True)
    resource_asset_id = Column(Integer, ForeignKey("resource_assets.id"), nullable=False, index=True)
    reviewer_id = Column(Integer, nullable=True, index=True)
    action = Column(String(30), nullable=False, index=True)  # approved/rejected/revised
    score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    review_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
