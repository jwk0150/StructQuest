from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date
from app.db.session import Base
from datetime import datetime


class DailyTask(Base):
    """每日任务记录"""
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    task_date = Column(Date, nullable=False, index=True)  # 任务日期
    task_type = Column(String(20), nullable=False)  # simple / advanced / review
    task_title = Column(String(200), nullable=False)
    task_description = Column(Text, nullable=True)
    estimated_time = Column(String(20), default='5分钟')
    status = Column(String(20), default='pending')  # pending / in_progress / completed
    progress = Column(Integer, default=0)  # 0-100
    target_node_id = Column(String(50), nullable=True)  # 关联知识点
    ai_prompt = Column(Text, nullable=True)  # AI学习预设提示
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
