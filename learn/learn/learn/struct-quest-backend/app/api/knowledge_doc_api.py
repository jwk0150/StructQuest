"""知识库文档管理 API（管理员专属）：上传/列表/删除/统计"""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.db.session import get_db
from app.auth import get_admin_user
from app.models.user import User
from app.models.knowledge import KnowledgeDocument
from app.services.rag import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["knowledge-docs"])


@router.get("/knowledge-docs")
async def get_knowledge_docs(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有已上传的知识文档列表（管理员权限）"""
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.status != "deleted")
        .order_by(KnowledgeDocument.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "doc_id": d.doc_id,
            "filename": d.filename,
            "file_size": d.file_size or 0,
            "chunks": d.chunks,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.get("/knowledge-stats")
async def get_knowledge_stats(
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取向量知识库统计信息（管理员权限）"""
    stats = rag_service.get_stats()
    result = await db.execute(
        select(func.count(KnowledgeDocument.id)).where(
            KnowledgeDocument.status != "deleted"
        )
    )
    document_count = result.scalar() or 0
    stats["db_document_count"] = document_count
    return stats


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """上传 PDF/PPTX -> RAG 处理 -> ChromaDB + 数据库记录（管理员权限）"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".pptx"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 和 PPTX 文件")

    content = await file.read()
    file_size_kb = round(len(content) / 1024, 2)

    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(content)

        if ext == ".pptx":
            process_result = rag_service.process_pptx(temp_file_path)
        else:
            process_result = rag_service.process_pdf(temp_file_path)
        chunks_count = process_result["chunks"]
        doc_id = process_result["doc_id"]

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    doc_record = KnowledgeDocument(
        doc_id=doc_id,
        filename=file.filename,
        file_size=file_size_kb,
        chunks=chunks_count,
        status="active",
    )
    db.add(doc_record)
    await db.commit()
    await db.refresh(doc_record)

    return {
        "message": f"成功处理: {file.filename}",
        "doc_id": doc_id,
        "filename": file.filename,
        "file_size_kb": file_size_kb,
        "chunks": chunks_count,
        "record_id": doc_record.id,
    }


@router.delete("/knowledge-docs/{doc_id}")
async def delete_knowledge_doc(
    doc_id: str,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除知识文档：ChromaDB 向量 + 数据库记录标记删除"""
    # 尝试多种方式查找记录：先按 id，再按 doc_id
    record = None
    if doc_id.isdigit():
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == int(doc_id))
        )
        record = result.scalar_one_or_none()

    if not record:
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.doc_id == doc_id)
        )
        record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail=f"文档不存在: {doc_id}")

    # 1. 从向量库删除
    vec_deleted = 0
    if record.doc_id:
        vec_deleted = rag_service.delete_document(record.doc_id)
        if vec_deleted < 0:
            raise HTTPException(status_code=500, detail="向量删除操作失败")

    # 2. 标记数据库记录为 deleted
    record.status = "deleted"
    await db.commit()

    return {
        "message": f"已删除: {record.filename}",
        "doc_id": record.doc_id,
        "deleted_chunks": vec_deleted or record.chunks,
    }
