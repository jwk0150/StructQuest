"""每日任务 API——任务接取、自动完成、徽章计数"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth import get_required_user
from app.models.user import User
from app.services.task_service import task_service

router = APIRouter(prefix="/api/study", tags=["tasks"])


class ClaimTaskRequest(BaseModel):
    task_id: str
    task_title: str
    task_type: str
    node_id: Optional[str] = None


class AutoCompleteRequest(BaseModel):
    event_type: str  # exam_submit | quiz_save | node_complete | resource_done | ai_chat | study_session
    node_id: Optional[str] = None


@router.get("/tasks/status")
async def get_task_status(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日任务的接取/完成状态映射"""
    status = await task_service.get_today_task_status(db, user.id)
    return {"status": status}


@router.get("/tasks/badge")
async def get_task_badge(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取侧边栏徽章数字（未接取任务数量）"""
    # 需要知道今日所有任务的 ID 列表
    # 直接从 daily-tasks 接口获取任务列表
    from app.api.study_api import generate_daily_tasks
    tasks_result = await generate_daily_tasks(db, user)
    all_task_ids = [t["id"] for t in tasks_result.get("tasks", [])]
    count = await task_service.get_unclaimed_count(db, user.id, all_task_ids)
    return {"count": count}


@router.post("/tasks/claim")
async def claim_task(
    req: ClaimTaskRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """接取一个今日任务"""
    result = await task_service.claim_task(
        db, user.id, req.task_id, req.task_title, req.task_type, req.node_id,
    )
    # 返回接取后的徽章计数
    from app.api.study_api import generate_daily_tasks
    tasks_result = await generate_daily_tasks(db, user)
    all_task_ids = [t["id"] for t in tasks_result.get("tasks", [])]
    unclaimed = await task_service.get_unclaimed_count(db, user.id, all_task_ids)
    return {
        "task": result,
        "unclaimed_count": unclaimed,
    }


@router.post("/tasks/auto-complete")
async def auto_complete_tasks(
    req: AutoCompleteRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """
    根据学习行为自动完成匹配的任务。
    前端在学习行为完成后调用此接口，让对应任务自动变为已完成。
    """
    completed = await task_service.auto_complete_tasks(
        db, user.id, req.event_type, {"node_id": req.node_id},
    )
    # 同时返回最新的徽章计数
    from app.api.study_api import generate_daily_tasks
    tasks_result = await generate_daily_tasks(db, user)
    all_task_ids = [t["id"] for t in tasks_result.get("tasks", [])]
    unclaimed = await task_service.get_unclaimed_count(db, user.id, all_task_ids)
    return {
        "completed_tasks": completed,
        "unclaimed_count": unclaimed,
    }
