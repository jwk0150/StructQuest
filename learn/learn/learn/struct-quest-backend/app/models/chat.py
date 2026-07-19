from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from app.db.session import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)  # ★ 所属用户ID
    title = Column(String(200), default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String(20))  # 'user' or 'ai'
    content = Column(Text)
    # ★ v4 新增：多模态附件
    attachments = Column(JSON, nullable=True)       # 多模态附件列表 List[TutorResourceAttachment]
    primary_format = Column(String(30), nullable=True)  # e.g., "mindmap_enhanced"
    format_reason = Column(String(200), nullable=True)  # e.g., "用户偏好视觉学习"
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatResource(Base):
    """
    聊天中生成的资源关联表（v4 新增）

    用于追踪：
    - 哪个会话、哪条消息生成了什么资源
    - 资源的类型、格式、内容
    - 便于历史回放和资源复用

    小资源（文本类）直接存 content_text
    大资源（视频/PPT）存 file_url 路径
    """
    __tablename__ = "chat_resources"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("generated_contents.id"), nullable=True)  # 关联 GeneratedContent

    resource_type = Column(String(30), nullable=False, index=True)  # mindmap/animation/ppt_outline/code_example/notes/exercise
    format = Column(String(20), nullable=False)                      # markmap/video/pptx/python/markdown/json
    title = Column(String(200), nullable=False)

    # 内容存储
    content_text = Column(Text, nullable=True)     # 小资源直接存（如思维导图 Markdown）
    content_json = Column(JSON, nullable=True)     # 结构化资源（如练习题 JSON）
    file_url = Column(String(500), nullable=True)  # 大资源路径（如动画 MP4）
    thumbnail_url = Column(String(500), nullable=True)

    # 元数据
    generated_for = Column(String(100), nullable=True)  # 生成原因
    quality_score = Column(Float, default=0)
    file_size_bytes = Column(Integer, default=0)
    generation_time_seconds = Column(Float, default=0)
    extra_meta = Column(JSON, nullable=True)              # 扩展元数据

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "content_id": self.content_id,
            "resource_type": self.resource_type,
            "format": self.format,
            "title": self.title,
            "content_text": self.content_text,
            "content_json": self.content_json,
            "file_url": self.file_url,
            "thumbnail_url": self.thumbnail_url,
            "generated_for": self.generated_for,
            "quality_score": self.quality_score,
            "file_size_bytes": self.file_size_bytes,
            "generation_time_seconds": self.generation_time_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
