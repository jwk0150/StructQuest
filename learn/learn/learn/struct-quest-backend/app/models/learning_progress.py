from sqlalchemy import Column, Integer, String, DateTime, Float, UniqueConstraint, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class LearningProgress(Base):
    """用户学习进度——每个用户在每个知识点节点上的状态"""
    __tablename__ = "learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="available")   # available | in_progress | completed
    progress = Column(Integer, default=0)            # 0-100 综合进度
    score = Column(Float, default=0)                 # 评测得分
    resource_progress = Column(JSON, default=dict)   # {"notes": false, "quiz": false}
    completed_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "node_id", name="uq_user_node"),
    )
