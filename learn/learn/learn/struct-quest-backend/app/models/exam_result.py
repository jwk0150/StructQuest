"""章节考试结果模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, UniqueConstraint, Text
from sqlalchemy.sql import func
from app.db.session import Base


class ExamResult(Base):
    """用户章节考试结果"""
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    score = Column(Float, default=0)         # 考试得分
    passed = Column(Boolean, default=False)   # 是否通过
    details = Column(Text, nullable=True)     # JSON 字符串，存储每道题的详细答题情况（含错题）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "node_id", name="uq_exam_user_node"),
    )
