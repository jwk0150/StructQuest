from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from app.db.session import Base


class GeneratedContent(Base):
    """
    AI 生成的内容存储模型
    
    用于持久化：
    - 教学文档（Markdown/HTML）
    - PPT 文件（PPTX/HTML）
    - 思维导图（JSON/SVG）
    - 教学视频（MP4/路径）
    """
    __tablename__ = "generated_contents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)          # 所属用户
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True)  # 关联的聊天会话
    
    # 内容基本信息
    content_type = Column(String(30), nullable=False, index=True)   # document | ppt | mindmap | video
    title = Column(String(200), nullable=False)                     # 标题
    description = Column(Text, nullable=True)                       # 描述/AI摘要
    
    # 内容存储方式
    storage_type = Column(String(20), default='file')               # file | url | database
    file_path = Column(String(500), nullable=True)                  # 本地文件路径（/static/pptx/xxx.pptx）
    file_url = Column(String(500), nullable=True)                   # 访问URL（http://.../static/pptx/xxx.pptx）
    
    # 内容主体（小型内容直接存数据库）
    content_text = Column(Text, nullable=True)                      # Markdown文档内容 / 思维导图JSON
    content_json = Column(JSON, nullable=True)                      # 结构化数据（如PPT大纲）
    
    # 元数据
    topic_tag = Column(String(100), nullable=True)                  # 知识点标签：链表、二叉树...
    difficulty = Column(String(20), default='intermediate')         # 难度等级
    template_used = Column(String(50), nullable=True)               # 使用模板（academic/minimal等）
    format = Column(String(20), default='html')                     # 输出格式：html | pptx | json | mp4
    
    # 统计信息
    file_size_bytes = Column(Integer, default=0)                    # 文件大小（字节）
    generation_time_seconds = Column(Float, default=0)              # 生成耗时（秒）
    view_count = Column(Integer, default=0)                         # 查看次数
    download_count = Column(Integer, default=0)                     # 下载次数
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "chat_session_id": self.chat_session_id,
            "content_type": self.content_type,
            "title": self.title,
            "description": self.description,
            "content_text": self.content_text,
            "content_json": self.content_json or {},
            "file_url": self.file_url or f"/static/{self.file_path}" if self.file_path else None,
            "topic_tag": self.topic_tag,
            "difficulty": self.difficulty,
            "format": self.format,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "view_count": self.view_count,
            "download_count": self.download_count,
        }
