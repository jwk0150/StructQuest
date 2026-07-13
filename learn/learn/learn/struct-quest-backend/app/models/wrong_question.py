"""错题记录模型——存储用户做错的题目，用于每日重温任务"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class WrongQuestion(Base):
    """用户错题记录——每道错题一条记录，支持每日重温抽取"""
    __tablename__ = "wrong_questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    question_text = Column(Text, nullable=False, comment="题目内容")
    options = Column(Text, nullable=True, comment="选项JSON")
    correct_answer = Column(String(200), nullable=False, comment="正确答案")
    user_answer = Column(String(200), nullable=False, comment="用户选择")
    explanation = Column(Text, nullable=True, comment="解析")
    source = Column(String(30), default="exam", comment="来源: exam/quiz")
    # 最近复习日期（用于每日不重复抽取）
    last_reviewed_date = Column(String(20), nullable=True, index=True)
    reviewed_count = Column(Integer, default=0, comment="已复习次数")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ═══ 新增字段（每日任务重构）═══
    error_count = Column(Integer, default=1, comment="错误次数")
    mastered = Column(Boolean, default=False, comment="是否已掌握")
    last_reviewed_at = Column(DateTime, nullable=True, comment="最近复习时间")
    question_type = Column(String(20), default='choice', comment="题目类型: choice/judge/short_answer")
