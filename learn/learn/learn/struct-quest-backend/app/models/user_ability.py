"""用户能力表——存储动态计算的六项学习能力值"""
from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class UserAbility(Base):
    """用户六维学习能力——基于真实学习行为动态计算，不作为随机值"""
    __tablename__ = "user_ability"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    visual_score = Column(Float, default=0.0, comment="视觉感知——基于视频学习、图片内容完成率")
    comprehensive_score = Column(Float, default=0.0, comment="综合能力——基于整体学习进度与各维度聚合")
    stability_score = Column(Float, default=0.0, comment="稳健程度——基于连续学习天数、错题订正率")
    exploration_score = Column(Float, default=0.0, comment="探索精神——基于AI提问、扩展学习次数")
    theory_score = Column(Float, default=0.0, comment="理论推导——基于练习正确率、考试成绩")
    practice_score = Column(Float, default=0.0, comment="动手实践——基于实验完成、编程练习成绩")
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="上次更新时间")
