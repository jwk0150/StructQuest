"""
学生画像持久化模型 — 六维动态画像

存储 ProfileAgent 输出的完整画像数据，支持跨会话持久化。
刷新页面后数据不丢失。
"""
from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class StudentProfile(Base):
    """学生动态画像表 — 六维度画像持久化"""
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # ── 基础能力 ──
    ability_level = Column(String(20), default="beginner")  # beginner/intermediate/advanced/expert
    learning_style = Column(String(20), default="reading")   # visual/auditory/reading/hands_on
    pace = Column(String(20), default="moderate")            # fast/moderate/slow
    learning_rhythm = Column(String(20), default="持续型")    # 持续型/突击型/碎片型

    # ── 六维画像 ──
    # 1. Knowledge（知识画像）
    knowledge_mastery = Column(JSON, nullable=True)   # {"数组": 85, "链表": 70, ...}

    # 2. Behavior（行为画像）
    activity_score = Column(Float, default=0.0)       # 活跃度 0-100
    focus_score = Column(Float, default=75.0)         # 专注度 0-100
    engagement_score = Column(Float, default=70.0)    # 参与度 0-100
    total_study_hours = Column(Float, default=0.0)    # 总学习时长(小时)
    task_completion_rate = Column(Float, default=0.0)  # 任务完成率

    # 3. Preference（资源偏好）
    resource_preferences = Column(JSON, nullable=True)  # {"视频": 85, "PPT": 60, ...}

    # 4. Error（错误画像）
    error_patterns = Column(JSON, nullable=True)       # ["概念混淆", "计算错误", ...]
    primary_error_type = Column(String(50), nullable=True)

    # 5. Growth（成长画像）
    mastery_trend = Column(String(20), default="stable")  # improving/stable/declining
    growth_history = Column(JSON, nullable=True)        # [{date, overall_score, mastered_topics}, ...]

    # 6. Risk（学习风险）
    risk_level = Column(String(20), default="low")       # low/medium/high
    risk_factors = Column(JSON, nullable=True)            # ["连续3天未完成任务", "图知识点长期未掌握"]

    # ── 其他 ──
    strengths = Column(JSON, nullable=True)              # ["数组操作", "链表遍历", ...]
    weaknesses = Column(JSON, nullable=True)             # ["图算法", "动态规划", ...]
    interests = Column(JSON, nullable=True)              # ["二叉树", "排序算法", ...]

    # ── 认知特征 ──
    cognitive_profile = Column(JSON, nullable=True)       # {mbti_style, feynman_adaptation, ...}
    confidence_score = Column(Float, default=60.0)

    # ── 策略 ──
    daily_strategy = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    # ── 元数据 ──
    profile_version = Column(Integer, default=1)
    source = Column(String(30), default="agent")          # agent/manual/event
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        """转为字典（与 Agent State 中的 student_profile 格式兼容）"""
        return {
            "user_id": self.user_id,
            "ability_level": self.ability_level,
            "learning_style": self.learning_style,
            "pace": self.pace,
            "learning_rhythm": self.learning_rhythm,
            "knowledge_mastery": self.knowledge_mastery or {},
            "activity_score": self.activity_score,
            "focus_score": self.focus_score,
            "engagement_score": self.engagement_score,
            "resource_preferences": self.resource_preferences or {},
            "error_patterns": self.error_patterns or [],
            "primary_error_type": self.primary_error_type or "",
            "mastery_trend": self.mastery_trend,
            "risk_level": self.risk_level,
            "risk_factors": self.risk_factors or [],
            "strengths": self.strengths or [],
            "weaknesses": self.weaknesses or [],
            "interests": self.interests or [],
            "cognitive": self.cognitive_profile or {},
            "confidence_score": self.confidence_score,
            "daily_strategy": self.daily_strategy or "",
            "summary": self.summary or "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
