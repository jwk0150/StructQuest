"""
每日任务服务——管理任务的接取、自动完成判定、徽章计数
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_task import UserTaskRecord
from app.models.study_session import StudySession
from app.models.learning_progress import LearningProgress
from app.models.exam_result import ExamResult

logger = logging.getLogger(__name__)


class TaskService:
    """每日任务系统服务"""

    def _today(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ════════════════════════════════════════════════════════════
    # 1. 获取今日任务概览（含接取状态）
    # ════════════════════════════════════════════════════════════

    async def get_today_task_status(self, db: AsyncSession, user_id: int) -> Dict:
        """获取今日所有任务的接取/完成状态，返回 {task_id: {claimed, completed}}"""
        date_str = self._today()
        result = await db.execute(
            select(UserTaskRecord).where(
                UserTaskRecord.user_id == user_id,
                UserTaskRecord.task_date == date_str,
            )
        )
        records = result.scalars().all()
        status_map = {}
        for r in records:
            status_map[r.task_id] = {
                "claimed": r.claimed,
                "completed": r.completed,
            }
        return status_map

    async def get_unclaimed_count(self, db: AsyncSession, user_id: int, all_task_ids: List[str]) -> int:
        """计算尚未接取的任务数量"""
        status = await self.get_today_task_status(db, user_id)
        count = 0
        for tid in all_task_ids:
            s = status.get(tid)
            if s is None or not s["claimed"]:
                count += 1
        return count

    # ════════════════════════════════════════════════════════════
    # 2. 接取任务
    # ════════════════════════════════════════════════════════════

    async def claim_task(
        self,
        db: AsyncSession,
        user_id: int,
        task_id: str,
        task_title: str,
        task_type: str,
        node_id: Optional[str] = None,
    ) -> Dict:
        """接取一个今日任务"""
        date_str = self._today()
        # 查找是否已有记录
        result = await db.execute(
            select(UserTaskRecord).where(
                UserTaskRecord.user_id == user_id,
                UserTaskRecord.task_id == task_id,
                UserTaskRecord.task_date == date_str,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            record = UserTaskRecord(
                user_id=user_id,
                task_id=task_id,
                task_title=task_title,
                task_type=task_type,
                node_id=node_id,
                task_date=date_str,
                claimed=True,
                claimed_at=datetime.now(timezone.utc),
            )
            db.add(record)
        else:
            if not record.claimed:
                record.claimed = True
                record.claimed_at = datetime.now(timezone.utc)
        await db.commit()
        return {"task_id": task_id, "claimed": True, "completed": record.completed if record else False}

    # ════════════════════════════════════════════════════════════
    # 3. 自动完成判定
    # ════════════════════════════════════════════════════════════

    async def auto_complete_tasks(
        self,
        db: AsyncSession,
        user_id: int,
        event_type: str,
        event_data: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        根据学习行为自动完成匹配的今日任务。
        event_type: exam_submit | quiz_save | node_complete | resource_done | ai_chat | study_session
        返回已完成的任务列表
        """
        date_str = self._today()
        now = datetime.now(timezone.utc)

        # 查询今日已接取但未完成的任务
        result = await db.execute(
            select(UserTaskRecord).where(
                UserTaskRecord.user_id == user_id,
                UserTaskRecord.task_date == date_str,
                UserTaskRecord.claimed == True,
                UserTaskRecord.completed == False,
            )
        )
        pending = result.scalars().all()
        if not pending:
            return []

        completed_tasks = []
        node_id = event_data.get("node_id") if event_data else None

        for task in pending:
            should_complete = False

            if event_type == "exam_submit":
                # 完成章节测试 → 匹配 review 类型的任务，或匹配对应节点的 continue 任务
                if task.task_type == "review":
                    should_complete = True
                elif task.task_type == "continue" and node_id and task.node_id == node_id:
                    should_complete = True

            elif event_type == "quiz_save":
                # 完成练习 → 匹配 review 类型任务
                if task.task_type == "review":
                    should_complete = True

            elif event_type == "node_complete":
                # 节点完成 → 匹配 continue 类型任务（对应 nodeId）
                if task.task_type == "continue" and node_id and task.node_id == node_id:
                    should_complete = True
                elif task.task_type == "explore":
                    should_complete = True
                elif task.task_type == "review":
                    should_complete = True

            elif event_type == "resource_done":
                # 学习资源完成 → 匹配 continue 类型任务
                if task.task_type == "continue" and node_id and task.node_id == node_id:
                    should_complete = True

            elif event_type == "ai_chat":
                # AI 问答 → 匹配 ai 类型任务
                if task.task_type == "ai":
                    should_complete = True

            elif event_type == "study_session":
                # 学习会话 → 匹配 continue 或 explore 类型任务
                if task.task_type == "continue" and node_id and task.node_id == node_id:
                    should_complete = True
                elif task.task_type == "explore":
                    should_complete = True

            if should_complete:
                task.completed = True
                task.completed_at = now
                completed_tasks.append({
                    "task_id": task.task_id,
                    "task_title": task.task_title,
                    "task_type": task.task_type,
                })

        if completed_tasks:
            await db.commit()
            logger.info(f"[Task] user={user_id} auto-completed: {[t['task_id'] for t in completed_tasks]}")

        return completed_tasks

    # ════════════════════════════════════════════════════════════
    # 4. 查询已接取任务列表（用于前端渲染）
    # ════════════════════════════════════════════════════════════

    async def get_claimed_tasks(self, db: AsyncSession, user_id: int) -> List[Dict]:
        """获取今日已接取的任务列表"""
        date_str = self._today()
        result = await db.execute(
            select(UserTaskRecord).where(
                UserTaskRecord.user_id == user_id,
                UserTaskRecord.task_date == date_str,
                UserTaskRecord.claimed == True,
            ).order_by(UserTaskRecord.claimed_at)
        )
        records = result.scalars().all()
        return [
            {
                "task_id": r.task_id,
                "task_title": r.task_title,
                "task_type": r.task_type,
                "node_id": r.node_id,
                "claimed": True,
                "completed": r.completed,
                "claimed_at": r.claimed_at.isoformat() if r.claimed_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in records
        ]


# 全局实例
task_service = TaskService()
