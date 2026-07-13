"""
学习行为日志模型 — 供 LearningAnalyticsAgent 分析使用

记录用户的每一次学习行为，替代纯内存推断。
前端自动上报 + 后端事件触发写入。
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class LearningBehavior(Base):
    """学习行为日志表"""
    __tablename__ = "learning_behaviors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 行为类型
    behavior_type = Column(String(50), nullable=False, index=True)
    # view_resource / complete_exercise / watch_video / read_notes /
    # view_mindmap / view_code / start_study / pause_study / complete_task /
    # skip_task / ask_question / click_recommendation

    # 关联资源
    resource_type = Column(String(50), nullable=True)   # video/notes/mindmap/code_example/quiz/ppt
    resource_id = Column(String(100), nullable=True, index=True)
    resource_title = Column(String(255), nullable=True)

    # 行为数据
    duration_seconds = Column(Integer, default=0)        # 持续时间
    completed = Column(Boolean, default=False)           # 是否完成
    score = Column(Float, nullable=True)                 # 得分（如有）
    progress_percent = Column(Float, default=0.0)        # 进度百分比

    # 上下文
    subject = Column(String(100), nullable=True)         # 学科
    node_id = Column(String(100), nullable=True)         # 知识节点ID
    session_id = Column(String(100), nullable=True, index=True)

    # 扩展数据
    event_data = Column(JSON, nullable=True)             # 额外的事件数据

    # 时间
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
