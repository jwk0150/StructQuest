"""
每日学习任务进度模型——跟踪用户三个阶段的任务状态

任务流程:
  任务一: 学习知识点（用户提及知识点名称即完成）
  任务二: 练习题（全部答对完成）
  任务三: 温故知新（复习错题）
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date
from sqlalchemy.sql import func
from app.db.session import Base


class DailyLearningProgress(Base):
    """每日学习任务进度——每天每个用户一条记录"""
    __tablename__ = "daily_learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    task_date = Column(Date, nullable=False, index=True)  # 任务日期
    node_id = Column(String(50), nullable=True)            # 今日知识点ID
    node_name = Column(String(100), nullable=True)         # 今日知识点名称

    # 任务一: 学习知识点
    task1_status = Column(String(20), default='pending')   # pending / completed
    task1_completed_at = Column(DateTime(timezone=True), nullable=True)

    # 任务二: 练习题
    task2_status = Column(String(20), default='pending')   # pending / in_progress / completed
    current_question_index = Column(Integer, default=0)    # 当前题目索引
    total_questions = Column(Integer, default=0)           # 总题数
    correct_count = Column(Integer, default=0)             # 答对题数
    task2_completed_at = Column(DateTime(timezone=True), nullable=True)

    # 任务三: 温故知新
    task3_status = Column(String(20), default='pending')   # pending / in_progress / completed
    review_question_ids = Column(Text, nullable=True)      # 待复习错题ID列表 (JSON array)
    current_review_index = Column(Integer, default=0)
    total_review = Column(Integer, default=0)
    reviewed_count = Column(Integer, default=0)
    task3_completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
