"""
推荐结果持久化模型

RecommendationAgent 写入，前端拉取展示。
支持记录用户点击/忽略行为，优化后续推荐。
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class Recommendation(Base):
    """个性化推荐缓存表"""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 推荐资源
    resource_id = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)   # notes/mindmap/quiz/code_example/animation/learning_path
    title = Column(String(255), nullable=False)
    topic = Column(String(200), nullable=True)
    difficulty = Column(String(20), nullable=True)

    # 评分与理由
    relevance_score = Column(Float, default=0.0)
    reason = Column(String(500), nullable=True)          # 个性化推荐理由

    # 来源
    source = Column(String(50), default="generated")     # cached/generated/external/planner

    # 用户反馈
    clicked = Column(Boolean, default=False)             # 是否点击
    dismissed = Column(Boolean, default=False)           # 是否忽略
    completed = Column(Boolean, default=False)           # 是否完成

    # 扩展
    tags = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # 时间
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
