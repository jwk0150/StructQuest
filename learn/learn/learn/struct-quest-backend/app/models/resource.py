from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.db.session import Base


# 来源平台常量
SOURCE_CSDN = "csdn"
SOURCE_ZHIHU = "zhihu"
SOURCE_JUEJIN = "juejin"
SOURCE_GITHUB = "github"
SOURCE_BILIBILI = "bilibili"
SOURCE_DOUYIN = "douyin"

SOURCE_CHOICES = {
    SOURCE_CSDN: {"label": "CSDN", "color": "#fc5531", "icon": "📝"},
    SOURCE_ZHIHU: {"label": "知乎", "color": "#0084ff", "icon": "💡"},
    SOURCE_JUEJIN: {"label": "掘金", "color": "#1e80ff", "icon": "⛏️"},
    SOURCE_GITHUB: {"label": "GitHub", "color": "#24292e", "icon": "💻"},
    SOURCE_BILIBILI: {"label": "B站", "color": "#00a1d6", "icon": "📺"},
    SOURCE_DOUYIN: {"label": "抖音", "color": "#fe2c55", "icon": "🎵"},
}

# 难度等级
DIFFICULTY_BEGINNER = "beginner"
DIFFICULTY_INTERMEDIATE = "intermediate"
DIFFICULTY_ADVANCED = "advanced"


class ExternalResource(Base):
    """外部资源模型 - 存储爬取的外部学习资源"""
    __tablename__ = "external_resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)          # 资源标题
    url = Column(String(500), nullable=False, unique=True)           # 原始链接（去重依据）
    source = Column(String(30), nullable=False, index=True)          # 来源平台
    category = Column(String(50), index=True)                        # 分类标签
    tags = Column(JSON, nullable=True)                               # 标签数组
    summary = Column(Text, nullable=True)                            # AI生成的摘要
    difficulty = Column(String(20), default=DIFFICULTY_INTERMEDIATE) # 难度等级
    heat_score = Column(Float, default=0.0)                          # 热度评分 (0~100)
    cover_image = Column(String(500), nullable=True)                 # 封面图URL
    author = Column(String(100), nullable=True)                      # 作者/UP主
    is_recommended = Column(Boolean, default=False)                  # 是否被推荐过
    ai_recommend_reason = Column(Text, nullable=True)                # AI 推荐理由
    crawled_at = Column(DateTime(timezone=True), server_default=func.now())   # 爬取时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())         # 更新时间

    def to_dict(self):
        source_info = SOURCE_CHOICES.get(self.source, {"label": self.source, "color": "#666", "icon": "🔗"})
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "source_label": source_info["label"],
            "source_color": source_info["color"],
            "source_icon": source_info["icon"],
            "category": self.category,
            "tags": self.tags or [],
            "summary": self.summary or "",
            "difficulty": self.difficulty,
            "heat_score": round(self.heat_score, 1),
            "cover_image": self.cover_image,
            "author": self.author,
            "ai_recommend_reason": self.ai_recommend_reason,
            "crawled_at": self.crawled_at.isoformat() if self.crawled_at else None,
        }
