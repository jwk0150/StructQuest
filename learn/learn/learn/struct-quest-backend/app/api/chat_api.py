"""
聊天历史 + AI 生成内容的 CRUD API

提供：
1. 聊天会话的增删改查（带 Redis 缓存）
2. 聊天消息的持久化
3. AI 生成内容的管理接口
"""
import logging
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, delete, func

from app.db.session import get_db, AsyncSessionLocal
from app.models.chat import ChatSession, ChatMessage, ChatResource
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
    # ★ v4 多模态扩展
    attachments: Optional[List[Dict]] = None
    primary_format: Optional[str] = None
    format_reason: Optional[str] = None


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
    # ★ v4 多模态扩展
    attachments: Optional[List[Dict]] = None
    primary_format: Optional[str] = None
    format_reason: Optional[str] = None


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
    
    # 批量查询每个会话的消息数量（避免 N+1 查询）
    session_ids = [s.id for s in sessions]
    if session_ids:
        count_result = await db.execute(
            select(ChatMessage.session_id, func.count(ChatMessage.id))
            .where(ChatMessage.session_id.in_(session_ids))
            .group_by(ChatMessage.session_id)
        )
        count_map = {sid: cnt for sid, cnt in count_result.all()}
    else:
        count_map = {}

    # 构建响应（包含消息数量）
    response = [
        {
            "id": s.id,
            "title": s.title or "新对话",
            "created_at": s.created_at.isoformat(),
            "message_count": count_map.get(s.id, 0),
        }
        for s in sessions
    ]
    
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
            # ★ v4 多模态字段
            "attachments": m.attachments or [],
            "primary_format": m.primary_format,
            "format_reason": m.format_reason,
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
    """发送消息并持久化到数据库（v4 支持多模态附件）"""
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

    # 保存消息到数据库（含 v4 多模态字段）
    message = ChatMessage(
        session_id=session_id,
        role=req.role,
        content=req.content,
        attachments=req.attachments,         # ★ v4
        primary_format=req.primary_format,   # ★ v4
        format_reason=req.format_reason,     # ★ v4
    )
    db.add(message)
    await db.flush()  # 获取 message.id

    # ★ v4 新增：保存 ChatResource 记录
    if req.role == "ai" and req.attachments:
        for att in req.attachments:
            chat_resource = ChatResource(
                message_id=message.id,
                session_id=session_id,
                user_id=current_user.id,
                resource_type=att.get("type", "unknown"),
                format=att.get("format", "text"),
                title=att.get("title", ""),
                content_text=att.get("content_text"),
                content_json=att.get("content_json"),
                file_url=att.get("file_url"),
                thumbnail_url=att.get("thumbnail_url"),
                generated_for=att.get("generated_for"),
                quality_score=att.get("quality_score", 0),
                generation_time_seconds=att.get("generation_time_seconds", 0),
                extra_meta=att.get("metadata"),
            )
            db.add(chat_resource)

            # 同步保存到 GeneratedContent（复用现有内容管理）
            if att.get("type") in ("mindmap", "animation", "notes", "ppt_outline", "code_example"):
                gen_content = GeneratedContent(
                    user_id=current_user.id,
                    chat_session_id=session_id,
                    content_type=att["type"],
                    title=att.get("title", ""),
                    content_text=att.get("content_text"),
                    content_json=att.get("content_json"),
                    file_url=att.get("file_url"),
                    topic_tag=att.get("type"),
                    format=att.get("format", "text"),
                    generation_time_seconds=att.get("generation_time_seconds", 0),
                )
                db.add(gen_content)

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
        "attachments": message.attachments or [],
        "primary_format": message.primary_format,
        "format_reason": message.format_reason,
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """删除聊天会话及所有消息（v4 含资源级联删除）"""
    session = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session_obj = session.scalar_one_or_none()
    if not session_obj:
        raise HTTPException(status_code=404, detail="会话不存在")

    # ★ v4：级联删除 ChatResource
    await db.execute(delete(ChatResource).where(ChatResource.session_id == session_id))
    # 删除关联消息
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    # 删除关联的 GeneratedContent
    await db.execute(
        delete(GeneratedContent).where(
            GeneratedContent.user_id == current_user.id,
            GeneratedContent.chat_session_id == session_id,
        )
    )
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


# ══════════════════════ ★ v4：聊天资源查询 API ══════════════════════

class ChatResourceResponse(BaseModel):
    id: int
    message_id: int
    session_id: int
    resource_type: str
    format: str
    title: str
    content_text: Optional[str] = None
    content_json: Optional[Dict] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    generated_for: Optional[str] = None
    quality_score: float = 0
    created_at: str


@router.get("/messages/{message_id}/resources", response_model=List[ChatResourceResponse])
async def get_message_resources(
    message_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """获取某条消息生成的所有资源（v4 新增）"""
    result = await db.execute(
        select(ChatResource).where(
            ChatResource.message_id == message_id,
            ChatResource.user_id == current_user.id,
        ).order_by(ChatResource.created_at.asc())
    )
    resources = result.scalars().all()
    return [r.to_dict() for r in resources]


@router.get("/sessions/{session_id}/resources", response_model=List[ChatResourceResponse])
async def get_session_resources(
    session_id: int,
    resource_type: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """
    获取某个会话中生成的所有资源（v4 新增）
    可按 resource_type 过滤
    """
    # 验证会话归属
    session = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    if not session.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="会话不存在")

    query = select(ChatResource).where(
        ChatResource.session_id == session_id,
        ChatResource.user_id == current_user.id,
    )
    if resource_type:
        query = query.where(ChatResource.resource_type == resource_type)

    query = query.order_by(ChatResource.created_at.desc()).limit(limit)
    result = await db.execute(query)
    resources = result.scalars().all()

    return [r.to_dict() for r in resources]


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """
    导出整个聊天会话（v4 新增）
    返回：所有对话记录 + 所有生成的多模态资源
    """
    # 验证会话归属
    session_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session_obj = session_result.scalar_one_or_none()
    if not session_obj:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取消息
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = msg_result.scalars().all()

    # 获取资源
    res_result = await db.execute(
        select(ChatResource)
        .where(ChatResource.session_id == session_id)
        .order_by(ChatResource.created_at.asc())
    )
    resources = res_result.scalars().all()

    return {
        "session": {
            "id": session_obj.id,
            "title": session_obj.title,
            "created_at": session_obj.created_at.isoformat(),
        },
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "attachments": m.attachments or [],
                "primary_format": m.primary_format,
                "format_reason": m.format_reason,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "resources": [r.to_dict() for r in resources],
    }


# ══════════════════════ ★ v4.1：资源反馈 API ══════════════════════

class ResourceFeedbackRequest(BaseModel):
    resource_type: str
    title: str
    feedback: str  # 'helpful' or 'not_helpful'
    generated_for: str = ""


@router.post("/resources/feedback")
async def record_resource_feedback(
    req: ResourceFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """记录用户对 AI 生成资源的反馈（v4.1 新增）

    用于追踪用户实际偏好，动态调整 resource_preferences 权重。
    前端在用户点击资源卡片上的 👍👎 时调用。
    """
    # 1. 写入学习行为事件
    try:
        from app.services.learning_record_service import learning_record_service
        await learning_record_service.log_event(
            db=db,
            user_id=current_user.id,
            event_type="resource_feedback",
            duration_seconds=0,
            event_data={
                "resource_type": req.resource_type,
                "title": req.title,
                "feedback": req.feedback,
                "generated_for": req.generated_for,
            },
        )
    except Exception as e:
        print(f"[Feedback] 行为记录失败: {e}")

    # 2. 更新用户的 resource_preferences 权重（即时生效）
    try:
        if current_user.profile_data and isinstance(current_user.profile_data, dict):
            prefs = current_user.profile_data.get("resource_preferences", {})
            if isinstance(prefs, dict):
                # 将资源类型映射到偏好名称
                type_map = {
                    "mindmap": "思维导图", "animation": "视频",
                    "code_example": "代码", "ppt_outline": "PPT",
                    "notes": "讲义", "quiz": "练习题",
                }
                pref_key = type_map.get(req.resource_type, req.resource_type)
                current_weight = prefs.get(pref_key, 50)
                # 有帮助 +10，没帮助 -10（限幅 0-100）
                delta = 10 if req.feedback == "helpful" else -10
                new_weight = max(0, min(100, current_weight + delta))
                prefs[pref_key] = new_weight
                current_user.profile_data["resource_preferences"] = prefs
                await db.commit()
                print(f"[Feedback] 更新偏好: {pref_key} → {new_weight} (用户 {current_user.id})")
    except Exception as e:
        print(f"[Feedback] 偏好更新失败: {e}")

    return {"message": "反馈已记录", "status": "ok"}
