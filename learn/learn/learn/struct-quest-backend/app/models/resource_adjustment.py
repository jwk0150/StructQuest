"""
AI资源优化调整记录模型

记录 AI 根据学习效果动态调整资源推送策略的完整历史。
这是赛题核心诉求：「动态调整学习资源推送策略，实现学习方案持续优化」。
"""
from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class ResourceAdjustment(Base):
    """资源/计划调整历史记录"""
    __tablename__ = "resource_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 调整类型
    # resource_type_change: 资源类型调整 (视频→代码案例)
    # difficulty_adjust: 难度调整
    # path_reroute: 学习路径重规划
    # practice_volume_adjust: 练习数量调整
    # plan_reorder: 学习顺序调整
    adjustment_type = Column(String(50), nullable=False, index=True)

    # 调整前
    from_value = Column(JSON, nullable=True)   # {"resource_type": "video", "topic": "树的基础", ...}

    # 调整后
    to_value = Column(JSON, nullable=True)     # {"resource_type": "animation+code", "topic": "树的遍历", ...}

    # 触发原因
    trigger_event = Column(String(50), nullable=True)   # assessment_score_low / low_engagement / user_feedback
    reason = Column(Text, nullable=True)                # AI 解释为什么调整

    # 效果对比
    metric_name = Column(String(50), nullable=True)     # correct_rate / engagement / time_spent
    metric_before = Column(Float, nullable=True)
    metric_after = Column(Float, nullable=True)
    improvement = Column(Float, nullable=True)          # 提升百分比

    # 补充数据
    extra_data = Column(JSON, nullable=True)

    # 时间
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "adjustment_type": self.adjustment_type,
            "from_value": self.from_value,
            "to_value": self.to_value,
            "trigger_event": self.trigger_event,
            "reason": self.reason,
            "metric_name": self.metric_name,
            "metric_before": self.metric_before,
            "metric_after": self.metric_after,
            "improvement": self.improvement,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
