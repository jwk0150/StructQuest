from sqlalchemy import Column, String, Integer, Text, JSON
from app.db.session import Base


class KnowledgeNode(Base):
    """知识图谱节点——预定义的课程知识点树"""
    __tablename__ = "knowledge_nodes"

    id = Column(String(50), primary_key=True)                  # e.g. "linked_list"
    title = Column(String(100), nullable=False)                 # e.g. "链表"
    description = Column(Text, nullable=True)                   # 详细描述
    full_desc = Column(Text, nullable=True)                     # 完整说明
    category = Column(String(50), nullable=False)               # 所属大类
    difficulty = Column(Integer, default=1)                     # 难度 1-5
    order_index = Column(Integer, default=0)                    # 排序
    parent_id = Column(String(50), nullable=True)               # 分类节点 id
    prerequisites = Column(JSON, nullable=True)                 # 前置节点 id 列表
    icon = Column(String(10), nullable=True)                    # 图标 emoji
    points = Column(JSON, nullable=True)                        # 包含的知识点列表
    ai_suggestion = Column(Text, nullable=True)                 # AI 学习建议
