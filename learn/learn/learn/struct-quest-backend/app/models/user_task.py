"""用户每日任务接取记录——记录用户接取、完成每日任务的状态"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class UserTaskRecord(Base):
    """用户每日任务接取/完成记录"""
    __tablename__ = "user_task_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    # 任务标识：与后端 daily-tasks 返回的 task id 对应
    # 格式如: "review_mistakes", "continue_learning:{nodeId}", "explore_new", "ai_learning"
    task_id = Column(String(100), nullable=False, index=True)
    # 任务标题（冗余存储，便于直接展示）
    task_title = Column(String(200), nullable=False)
    # 任务类型: review | continue | explore | ai
    task_type = Column(String(30), nullable=False, index=True)
    # 关联节点ID（可选）
    node_id = Column(String(50), nullable=True)
    # 是否已接取
    claimed = Column(Boolean, default=False, index=True)
    # 是否已完成
    completed = Column(Boolean, default=False, index=True)
    # 接取日期（用于区分每日任务）
    task_date = Column(String(20), nullable=False, index=True)  # 格式: "2026-06-27"
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
