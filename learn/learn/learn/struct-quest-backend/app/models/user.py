from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.db.session import Base

# 学习模式常量
LEARNING_MODE_BASIC = "basic"      # 基础模式
LEARNING_MODE_BEGINNER = "beginner" # 入门模式
LEARNING_MODE_EXAM = "exam"        # 考试模式

LEARNING_MODE_CHOICES = {
    LEARNING_MODE_BASIC: {"label": "基础模式", "color": "#22c55e", "icon": "🌱"},
    LEARNING_MODE_BEGINNER: {"label": "入门模式", "color": "#3b82f6", "icon": "📚"},
    LEARNING_MODE_EXAM: {"label": "考试模式", "color": "#f97316", "icon": "🎯"},
}

# 学习目的常量（冷启动问卷）
LEARNING_PURPOSE_CHOICES = [
    "course_preview",     # 课程预习
    "daily_study",        # 日常学习
    "final_exam",         # 期末考试
    "postgraduate",       # 考研
    "project_practice",   # 项目实践
    "algorithm_contest",  # 算法竞赛
]

# 学习方式偏好常量
LEARNING_STYLE_OPTIONS = [
    "video",         # 视频讲解
    "diagram",       # 图解
    "reading",       # 阅读讲义
    "coding",        # 动手写代码
    "practice",      # 刷题
]

# 每日学习时间选项
DAILY_STUDY_TIME_OPTIONS = [
    "15min",    # 15分钟
    "30min",    # 30分钟
    "1hour",    # 1小时
    "2hours",   # 2小时以上
]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    has_completed_onboarding = Column(Boolean, default=False)
    profile_data = Column(JSON, nullable=True)  # AI 生成的完整学习画像
    learning_mode = Column(String(20), default=LEARNING_MODE_BASIC, nullable=False)  # 学习模式
    learning_mode_set_at = Column(DateTime(timezone=True), nullable=True)  # 模式设置时间
    is_admin = Column(Boolean, default=False, comment="是否为管理员")

    # ═══ 冷启动画像：第一阶段 — 基础信息 ═══
    major = Column(String(100), nullable=True, comment="专业")
    grade = Column(String(50), nullable=True, comment="年级")
    course = Column(String(100), nullable=True, comment="课程")
    learning_goal = Column(String(100), nullable=True, comment="学习目标（期末考试/考研/项目实践等）")
    target_score = Column(String(20), nullable=True, comment="目标成绩（可选）")
    daily_study_time = Column(String(20), nullable=True, comment="每天学习时间")
    exam_date = Column(String(50), nullable=True, comment="考试时间（可选）")

    # ═══ 冷启动画像：第二阶段 — 学习目标问卷 ═══
    learning_purpose = Column(String(50), nullable=True, comment="学习目的")
    preferred_styles = Column(JSON, nullable=True, comment="学习方式偏好（多选数组）")

    # ═══ 冷启动画像：第三阶段 — 诊断测试结果 ═══
    diagnostic_results = Column(JSON, nullable=True, comment="诊断测试结果（含行为数据）")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
