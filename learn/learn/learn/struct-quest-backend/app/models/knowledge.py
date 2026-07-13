from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.db.session import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String(64), index=True, nullable=True)
    filename = Column(String(255), index=True)
    file_size = Column(Float, default=0.0, nullable=True, comment="文件大小(KB)")
    chunks = Column(Integer, default=0)
    status = Column(String(20), default="active", comment="active/deleted")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
