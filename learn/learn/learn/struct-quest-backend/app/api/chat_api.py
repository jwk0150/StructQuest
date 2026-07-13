"""
聊天历史 + AI 生成内容的 CRUD API

提供：
1. 聊天会话的增删改查（带 Redis 缓存）
2. 聊天消息的持久化
3. AI 生成内容的管理接口
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, delete

from app.db.session import get_db, AsyncSessionLocal
from app.models.chat import ChatSession, ChatMessage
from app.models.generated_content import GeneratedContent
from app.services.cache_service import cache_service
from app.auth import get_required_user, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat-history"])


# ══════════════════════ 请求/响应模型 ══════════════════════

class CreateChatRequest(BaseModel):
    title: str = "新对话"


class SendMessageRequest(BaseModel):
    content: str
    role: str = "user"  # 'user' or 'ai'


class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: str
    message_count: int = 0


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str


# ══════════════════════ 聊天会话 API ══════════════════════

@router.post("/sessions", response_model=ChatResponse)
async def create_session(
    req: CreateChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """创建新的聊天会话"""
    session = ChatSession(title=req.title, user_id=current_user.id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    # 清除用户的会话缓存
    await cache_service.invalidate_user_cache(current_user.id)
    
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "message_count": 0,
    }


@router.get("/sessions", response_model=List[ChatResponse])
async def get_sessions(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """
    获取当前用户的所有聊天会话（优先从 Redis 缓存读取）
    """
    # 1. 先尝试从缓存读取
    cached = await cache_service.get_cached_sessions(current_user.id)
    if cached:
        logger.debug(f"[Chat] 从缓存返回 {len(cached)} 个会话")
        return cached[:limit]
    
    # 2. 缓存未命中，查询数据库
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.updated_at))
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    # 构建响应（包含消息数量）
    response = []
    for s in sessions:
        msg_count_result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == s.id)
        )
        msg_count = len(msg_count_result.scalars().all())
        
        response.append({
            "id": s.id,
            "title": s.title or "新对话",
            "created_at": s.created_at.isoformat(),
            "message_count": msg_count,
        })
    
    # 3. 写入缓存
    await cache_service.cache_chat_sessions(current_user.id, response)
    
    return response


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """获取某个聊天的所有消息历史（带 Redis 缓存）"""
    # 1. 先尝试从缓存读取
    cached = await cache_service.get_cached_messages(session_id)
    if cached:
        logger.debug(f"[Chat] 从缓存返回会话 {session_id} 的 {len(cached)} 条消息")
        return cached[:limit]
    
    # 2. 验证会话归属
    session = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    if not session.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="会话不存在或不属于你")
    
    # 3. 查询数据库
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    
    response = [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
    
    # 4. 写入缓存
    await cache_service.cache_chat_messages(session_id, response)
    
    return response


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: int,
    req: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """发送消息并持久化到数据库"""
    # 验证会话归属
    session = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session_obj = session.scalar_one_or_none()
    if not session_obj:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 保存消息到数据库
    message = ChatMessage(
        session_id=session_id,
        role=req.role,
        content=req.content,
    )
    db.add(message)
    
    # 更新会话的最后活跃时间
    from datetime import datetime
    session_obj.updated_at = datetime.now()
    
    await db.commit()
    await db.refresh(message)
    
    # 清除该会话的消息缓存
    await cache_service.delete(f"chat:messages:{session_id}")
    
    # ★ 触发能力值更新（AI 提问 → 探索精神）
    if req.role == "user":
        try:
            from app.services.ability_service import ability_service
            await ability_service.on_event(db, current_user.id, "ai_chat", {"session_id": session_id})
        except Exception as e:
            print(f"[Ability] AI提问能力值更新失败: {e}")
    
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """删除聊天会话及所有消息"""
    session = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session_obj = session.scalar_one_or_none()
    if not session_obj:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 删除关联消息
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    
    # 删除会话
    await db.delete(session_obj)
    await db.commit()
    
    # 清除缓存
    await cache_service.invalidate_user_cache(current_user.id)
    await cache_service.delete(f"chat:messages:{session_id}")
    
    return {"message": "删除成功"}


# ══════════════════════ AI 生成内容 API ══════════════════════

class ContentResponse(BaseModel):
    id: int
    content_type: str
    title: str
    file_url: Optional[str]
    topic_tag: Optional[str]
    created_at: str


@router.get("/contents", response_model=List[ContentResponse])
async def get_my_contents(
    content_type: Optional[str] = None,  # document | ppt | mindmap | video
    topic_tag: Optional[str] = None,     # ★ 按节点ID过滤
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """获取当前用户的所有 AI 生成内容"""
    query = select(GeneratedContent).where(GeneratedContent.user_id == current_user.id)
    
    if content_type:
        query = query.where(GeneratedContent.content_type == content_type)

    if topic_tag:
        query = query.where(GeneratedContent.topic_tag == topic_tag)
    
    query = query.order_by(desc(GeneratedContent.created_at)).limit(limit)
    
    result = await db.execute(query)
    contents = result.scalars().all()
    
    return [c.to_dict() for c in contents]


@router.get("/contents/{content_id}")
async def get_content_detail(
    content_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """获取某个生成内容的详情"""
    content = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.id == content_id,
            GeneratedContent.user_id == current_user.id,
        )
    )
    obj = content.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    # 更新查看次数
    obj.view_count += 1
    await db.commit()
    
    return obj.to_dict()


class SaveContentRequest(BaseModel):
    content_type: str
    title: str
    file_path: Optional[str] = None
    content_text: Optional[str] = None
    content_json: Optional[dict] = None
    topic_tag: Optional[str] = None
    format: str = 'html'
    chat_session_id: Optional[int] = None


@router.post("/contents")
async def save_generated_content(
    req: SaveContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """
    保存 AI 生成的内容
    
    在 PPT/文档/思维导图/视频生成完成后调用此接口保存元数据
    """
    # 构建 file URL
    file_url = None
    if req.file_path:
        _fp = req.file_path.replace('\\', '/')
        file_url = f"/static/{_fp}"
    
    content = GeneratedContent(
        user_id=current_user.id,
        chat_session_id=req.chat_session_id,
        content_type=req.content_type,
        title=req.title,
        file_path=req.file_path,
        file_url=file_url,
        content_text=req.content_text,
        content_json=req.content_json,
        topic_tag=req.topic_tag,
        format=req.format,
    )
    
    db.add(content)
    await db.commit()
    await db.refresh(content)
    
    logger.info(f"[Content] 保存生成内容: type={req.content_type}, id={content.id}, user={current_user.id}")
    
    return {"id": content.id, "file_url": file_url, "message": "保存成功"}
