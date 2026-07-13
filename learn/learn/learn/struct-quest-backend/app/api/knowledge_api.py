"""知识图谱 API：获取图谱、开始学习、完成节点（全开放模式）"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.sql import func
from app.db.session import get_db
from app.auth import get_current_user, get_required_user
from app.models.user import User
from app.models.knowledge_graph import KnowledgeNode
from app.models.learning_progress import LearningProgress
from app.services.learning_record_service import learning_record_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# ★ 类别名称到中文标题的映射（与前端 knowledgeMap.js 对齐）
_CATEGORY_TITLES = {
    "ch01_intro": "绪论",
    "ch02_linear_list": "线性表",
    "ch03_stack_queue": "栈和队列",
    "ch04_string_array": "串、数组和广义表",
    "ch05_tree": "树和二叉树",
    "ch06_graph": "图",
    "ch07_search": "查找",
    "ch08_sort": "排序",
}


@router.get("/map")
async def get_knowledge_map(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取完整知识图谱 + 当前用户的学习进度（全开放，无锁定）"""
    result = await db.execute(
        select(KnowledgeNode).order_by(KnowledgeNode.order_index)
    )
    nodes = result.scalars().all()

    # 获取用户进度（仅登录用户）
    progress_map = {}
    if user is not None:
        progress_result = await db.execute(
            select(LearningProgress).where(LearningProgress.user_id == user.id)
        )
        progress_map = {p.node_id: p for p in progress_result.scalars().all()}

    node_list = []
    categories = {}

    for node in nodes:
        prog = progress_map.get(node.id)

        # ★ 全开放：所有节点默认 available，根据用户进度显示实际状态
        if prog:
            status = prog.status
        else:
            status = "available"

        node_data = {
            "id": node.id,
            "title": node.title,
            "description": node.description,
            "full_desc": node.full_desc,
            "category": node.category,
            "difficulty": node.difficulty,
            "order_index": node.order_index,
            "parent_id": node.parent_id,
            "prerequisites": node.prerequisites or [],
            "icon": node.icon,
            "points": node.points or [],
            "ai_suggestion": node.ai_suggestion,
            "status": status,
            "progress": prog.progress if prog else 0,
            "score": prog.score if prog else 0,
        }
        node_list.append(node_data)

        cat = node.category
        if cat not in categories:
            # ★ 使用与前端一致的 ID 格式：s1, s2, ... 或直接用 category 名作为 id
            categories[cat] = {
                "id": f"stage_{cat}",   # 统一格式: stage_linear, stage_tree 等
                "title": _CATEGORY_TITLES.get(cat, cat),
                "icon": "",
                "nodes": [],
            }

    for nd in node_list:
        cat = nd["category"]
        if cat in categories:
            categories[cat]["nodes"].append(nd)

    return {
        "nodes": node_list,
        "categories": list(categories.values()),
    }


@router.post("/nodes/{node_id}/start")
async def start_node(
    node_id: str,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """开始学习某个节点（全开放，无前置检查）"""
    result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="知识点不存在")

    p_result = await db.execute(
        select(LearningProgress).where(
            and_(
                LearningProgress.user_id == user.id,
                LearningProgress.node_id == node_id,
            )
        )
    )
    prog = p_result.scalar_one_or_none()

    if not prog:
        prog = LearningProgress(
            user_id=user.id,
            node_id=node_id,
            status="in_progress",
            started_at=func.now(),
        )
        db.add(prog)
    elif prog.status != "completed":
        prog.status = "in_progress"

    await db.commit()
    await learning_record_service.log_event(
        db=db,
        user_id=user.id,
        event_type="node_start",
        subject=node.category,
        node_id=node_id,
        event_data={"title": node.title},
    )
    await db.commit()

    return {
        "node_id": node_id,
        "status": "in_progress",
        "title": node.title,
        "message": f"开始学习「{node.title}」",
    }


def _calc_resource_progress(prog) -> int:
    """计算资源部分进度：讲义25% + 练习题25% = 最多50%"""
    rp = prog.resource_progress or {}
    base = 0
    if rp.get("notes"):
        base += 25
    if rp.get("quiz"):
        base += 25
    return base


async def _calc_total_progress(prog, db, user_id, node_id) -> int:
    """综合进度 = 资源部分(0-50%) + 章节测试部分(0-50%)"""
    from app.models.exam_result import ExamResult
    resource_base = _calc_resource_progress(prog)

    # 查找最新考试记录
    exam_result = await db.execute(
        select(ExamResult).where(
            and_(
                ExamResult.user_id == user_id,
                ExamResult.node_id == node_id,
            )
        ).order_by(ExamResult.completed_at.desc())
    )
    exam = exam_result.scalars().first() if exam_result else None

    if exam and exam.score >= 60:
        return 100  # 考试>=60直接满分
    elif exam:
        exam_add = int((exam.score / 60) * 50)
        return resource_base + exam_add
    else:
        return resource_base


@router.post("/nodes/{node_id}/resource-progress")
async def update_resource_progress(
    node_id: str,
    resource_type: str,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """标记某个学习资源完成（讲义25% / 练习题25%），实时更新综合进度"""
    if resource_type not in ("notes", "quiz"):
        raise HTTPException(status_code=400, detail="resource_type 必须为 notes 或 quiz")

    result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="知识点不存在")

    p_result = await db.execute(
        select(LearningProgress).where(
            and_(
                LearningProgress.user_id == user.id,
                LearningProgress.node_id == node_id,
            )
        )
    )
    prog = p_result.scalar_one_or_none()

    if not prog:
        prog = LearningProgress(
            user_id=user.id,
            node_id=node_id,
            status="in_progress",
            started_at=func.now(),
        )
        db.add(prog)
    elif prog.status != "completed":
        prog.status = "in_progress"

    # 标记资源完成
    if prog.resource_progress is None:
        prog.resource_progress = {}
    prog.resource_progress[resource_type] = True

    # 重新计算综合进度
    total = await _calc_total_progress(prog, db, user.id, node_id)
    prog.progress = total
    if total >= 100:
        prog.status = "completed"
        prog.completed_at = func.now()

    await db.commit()

    # ★ 触发能力值更新
    try:
        from app.services.ability_service import ability_service
        if resource_type == "notes":
            await ability_service.on_event(db, user.id, "view_notes", {"node_id": node_id})
        elif resource_type == "quiz":
            await ability_service.on_event(db, user.id, "complete_quiz", {"node_id": node_id})
    except Exception as e:
        logger.warning(f"[Ability] 更新能力值失败: {e}")

    return {
        "node_id": node_id,
        "resource_type": resource_type,
        "resource_progress": prog.resource_progress,
        "progress": prog.progress,
        "status": prog.status,
        "message": f"「{node.title}」{('学习讲义' if resource_type == 'notes' else '练习题')}已完成，当前综合进度 {prog.progress}%",
    }


@router.post("/nodes/{node_id}/complete")
async def complete_node(
    node_id: str,
    score: float = 0,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """完成某个节点的学习（兼容旧接口：标记所有资源完成 = 50%）"""
    from sqlalchemy.sql import func

    result = await db.execute(
        select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="知识点不存在")

    p_result = await db.execute(
        select(LearningProgress).where(
            and_(
                LearningProgress.user_id == user.id,
                LearningProgress.node_id == node_id,
            )
        )
    )
    prog = p_result.scalar_one_or_none()

    if not prog:
        prog = LearningProgress(user_id=user.id, node_id=node_id)
        db.add(prog)

    # ★ 如果已经完结，保持完结状态（只更新分数），不降级
    if prog.status == "completed":
        prog.score = max(prog.score or 0, score)
        await db.commit()
        return {
            "node_id": node_id,
            "status": "completed",
            "score": prog.score,
            "learning_completed": True,
            "exam_passed": True,
            "chapter_completed": True,
            "message": f"「{node.title}」已完结，无需重复学习。",
        }

    # 标记所有资源完成（兼容旧行为：两边都标记为完成 → 资源部分=50%）
    if prog.resource_progress is None:
        prog.resource_progress = {}
    prog.resource_progress["notes"] = True
    prog.resource_progress["quiz"] = True

    # 重新计算综合进度
    total = await _calc_total_progress(prog, db, user.id, node_id)
    prog.progress = total
    if total >= 100:
        prog.status = "completed"
        prog.completed_at = func.now()
    else:
        prog.status = "in_progress"

    await db.commit()
    chapter_completed = prog.status == "completed"

    # 检查考试状态
    from app.models.exam_result import ExamResult
    exam_check = await db.execute(
        select(ExamResult).where(
            and_(
                ExamResult.user_id == user.id,
                ExamResult.node_id == node_id,
            )
        )
    )
    existing_exam = exam_check.scalar_one_or_none()
    exam_passed = existing_exam is not None and existing_exam.passed

    await learning_record_service.log_event(
        db=db,
        user_id=user.id,
        event_type="node_complete",
        subject=node.category,
        node_id=node_id,
        score=score,
        event_data={
            "title": node.title,
            "chapter_completed": chapter_completed,
            "exam_passed": exam_passed,
            "progress": prog.progress,
        },
    )
    await db.commit()

    # ★ 触发能力值更新（节点完成）
    try:
        from app.services.ability_service import ability_service
        if chapter_completed or prog.status == "completed":
            await ability_service.on_node_completed(db, user.id)
        else:
            await ability_service.on_event(db, user.id, "complete_quiz", {"node_id": node_id})
    except Exception as e:
        logger.warning(f"[Ability] 更新能力值失败: {e}")

    return {
        "node_id": node_id,
        "status": prog.status,
        "score": score,
        "progress": prog.progress,
        "learning_completed": True,
        "exam_passed": exam_passed,
        "chapter_completed": chapter_completed,
        "message": f"完成「{node.title}」的学习！当前综合进度 {prog.progress}%",
    }


@router.get("/progress")
async def get_progress(
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户学习进度统计"""
    if user is None:
        total_result = await db.execute(select(KnowledgeNode))
        total_nodes = len(total_result.scalars().all())
        return {
            "total_nodes": total_nodes,
            "completed": 0,
            "in_progress": 0,
            "available": total_nodes,
            "completion_rate": 0,
        }
    progress_result = await db.execute(
        select(LearningProgress).where(LearningProgress.user_id == user.id)
    )
    all_progress = progress_result.scalars().all()

    # 总节点数
    total_result = await db.execute(select(KnowledgeNode))
    total_nodes = len(total_result.scalars().all())

    completed = sum(1 for p in all_progress if p.status == "completed")
    in_progress = sum(1 for p in all_progress if p.status == "in_progress")
    available = total_nodes - completed - in_progress

    return {
        "total_nodes": total_nodes,
        "completed": completed,
        "in_progress": in_progress,
        "available": available,
        "completion_rate": round(completed / max(total_nodes, 1) * 100, 1),
    }


@router.get("/recent")
async def get_recent_learning(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户最近学习的知识点（用于首页推荐）"""
    result = await db.execute(
        select(LearningProgress)
        .where(
            LearningProgress.user_id == user.id,
        )
        .order_by(LearningProgress.started_at.desc())
        .limit(10)
    )
    recent = result.scalars().all()

    recent_nodes = []
    for p in recent:
        node_result = await db.execute(
            select(KnowledgeNode).where(KnowledgeNode.id == p.node_id)
        )
        node = node_result.scalar_one_or_none()
        if node:
            recent_nodes.append({
                "node_id": node.id,
                "title": node.title,
                "category": node.category,
                "status": p.status,
                "progress": p.progress,
            })

    return {"recent_nodes": recent_nodes}
