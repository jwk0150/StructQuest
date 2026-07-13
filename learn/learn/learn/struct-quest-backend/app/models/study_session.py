"""学习计时模型——记录用户的每次学习会话"""
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.db.session import Base


class StudySession(Base):
    """用户学习会话——每次进入/退出节点学习时创建一条记录"""
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    node_id = Column(String(50), nullable=True, index=True)  # 学习哪个节点
    duration_seconds = Column(Integer, default=0)            # 本次学习时长（秒）
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
