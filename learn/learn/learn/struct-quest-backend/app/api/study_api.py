"""学习计时 API：开始/停止学习会话、获取学习统计"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case, and_, or_
sa_func = func  # 兼容旧代码中的 sa_func 别名
from app.db.session import get_db
from app.auth import get_required_user, get_current_user
from app.models.user import User
from app.models.study_session import StudySession
from app.models.learning_progress import LearningProgress
from app.models.knowledge_graph import KnowledgeNode
from app.models.exam_result import ExamResult
from app.services.learning_record_service import learning_record_service
import json

router = APIRouter(prefix="/api/study", tags=["study"])


class StartSessionRequest(BaseModel):
    node_id: str


class StopSessionRequest(BaseModel):
    node_id: str
    duration_seconds: int  # 前端实际统计的学习时长（秒）


# ════════════════════════════════════════════════════════
# 学习会话管理
# ════════════════════════════════════════════════════════

@router.post("/start")
async def start_study_session(
    req: StartSessionRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """开始学习会话（用户进入学习节点时调用）"""
    session = StudySession(
        user_id=user.id,
        node_id=req.node_id,
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await learning_record_service.log_event(
        db=db,
        user_id=user.id,
        event_type="study_start",
        node_id=req.node_id,
        event_data={"started_at": datetime.now(timezone.utc).isoformat()},
    )
    await db.commit()
    await db.refresh(session)
    return {
        "message": "学习会话已开始",
        "session_id": session.id,
        "started_at": session.started_at.isoformat(),
    }


@router.post("/stop")
async def stop_study_session(
    req: StopSessionRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """结束学习会话（用户离开学习节点时调用）"""
    # 找最近一条未结束的会话
    result = await db.execute(
        select(StudySession)
        .where(
            StudySession.user_id == user.id,
            StudySession.node_id == req.node_id,
            StudySession.ended_at.is_(None),
        )
        .order_by(StudySession.started_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if session is None:
        # 没找到开放会话，创建一个兜底
        session = StudySession(
            user_id=user.id,
            node_id=req.node_id,
            started_at=datetime.now(timezone.utc) - timedelta(seconds=req.duration_seconds),
        )
        db.add(session)

    session.duration_seconds = req.duration_seconds
    session.ended_at = datetime.now(timezone.utc)
    await learning_record_service.log_event(
        db=db,
        user_id=user.id,
        event_type="study_stop",
        node_id=req.node_id,
        duration_seconds=req.duration_seconds,
        event_data={"ended_at": session.ended_at.isoformat()},
    )
    await db.commit()

    # ★ 触发能力值更新（完成学习会话）
    try:
        from app.services.ability_service import ability_service
        await ability_service.on_event(db, user.id, "study_session", {"node_id": req.node_id, "duration": req.duration_seconds})
    except Exception as e:
        print(f"[Ability] 学习会话能力值更新失败: {e}")

    return {
        "message": "学习会话已结束",
        "duration_seconds": session.duration_seconds,
    }


# ════════════════════════════════════════════════════════
# 学习统计
# ════════════════════════════════════════════════════════

@router.get("/stats")
async def get_study_stats(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户学习统计（今日/本周时长、活跃度等）"""
    now = datetime.now(timezone.utc)
    
    # 今日开始时间（UTC+8）
    tz = timezone(timedelta(hours=8))
    local_now = now.astimezone(tz)
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_utc = today_start.astimezone(timezone.utc)
    
    # 本周开始（周一）
    week_start = today_start - timedelta(days=today_start.weekday())
    week_start_utc = week_start.astimezone(timezone.utc)

    # 今日学习时长
    result = await db.execute(
        select(sa_func.coalesce(sa_func.sum(StudySession.duration_seconds), 0))
        .where(
            StudySession.user_id == user.id,
            StudySession.started_at >= today_start_utc,
        )
    )
    today_seconds = result.scalar() or 0
    today_hours = today_seconds // 3600
    today_minutes = (today_seconds % 3600) // 60

    # 本周学习时长
    result = await db.execute(
        select(sa_func.coalesce(sa_func.sum(StudySession.duration_seconds), 0))
        .where(
            StudySession.user_id == user.id,
            StudySession.started_at >= week_start_utc,
        )
    )
    week_seconds = result.scalar() or 0
    week_hours = week_seconds // 3600

    # 登录次数：learning_progress 中 distinct user 的活跃天数
    result = await db.execute(
        select(sa_func.count(sa_func.distinct(sa_func.date(LearningProgress.started_at))))
        .where(
            LearningProgress.user_id == user.id,
            LearningProgress.started_at >= week_start_utc,
        )
    )
    active_days = result.scalar() or 0

    # 学习次数：本周内有几条 study_sessions
    result = await db.execute(
        select(sa_func.count(StudySession.id))
        .where(
            StudySession.user_id == user.id,
            StudySession.started_at >= week_start_utc,
        )
    )
    study_count = result.scalar() or 0

    # 任务完成率
    result = await db.execute(
        select(
            sa_func.count(LearningProgress.id),
            sa_func.sum(
                case((LearningProgress.status == 'completed', 1), else_=0)
            ),
        ).where(
            LearningProgress.user_id == user.id,
        )
    )
    row = result.one()
    total_tasks = row[0] or 0
    completed_tasks = row[1] or 0
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # 活跃度计算：加权组合
    # 学习时长得分 (max 35): 今日>=1h给35, 否则按比例
    time_score = min(35, (today_seconds / 3600) * 35)
    # 学习次数得分 (max 25): 今日>=3次给25
    count_score = min(25, study_count * 8)
    # 活跃天数得分 (max 25): 本周>=5天给25
    day_score = min(25, active_days * 5)
    # 完成率得分 (max 15): 完成率*15
    complete_score = (completion_rate / 100) * 15
    activity = min(100, round(time_score + count_score + day_score + complete_score))

    # 激励文案
    daily_encouragement = _get_daily_encouragement(today_seconds)
    weekly_encouragement = _get_weekly_encouragement(week_seconds)

    # ★ 章节完成统计（使用 ExamResult + LearningProgress 双重判断）
    total_nodes_result = await db.execute(select(sa_func.count(KnowledgeNode.id)))
    total_nodes = total_nodes_result.scalar() or 0
    completed_chapters_result = await db.execute(
        select(sa_func.count(LearningProgress.id)).where(
            LearningProgress.user_id == user.id,
            LearningProgress.status == "completed",
        )
    )
    completed_chapters = completed_chapters_result.scalar() or 0
    chapter_completion_rate = round(completed_chapters / max(total_nodes, 1) * 100, 1)

    # ★ 总学习时长
    total_seconds_result = await db.execute(
        select(sa_func.coalesce(sa_func.sum(StudySession.duration_seconds), 0))
        .where(StudySession.user_id == user.id)
    )
    total_study_seconds = total_seconds_result.scalar() or 0
    total_hours = total_study_seconds // 3600

    # ★ 最近完成的章节
    recent_result = await db.execute(
        select(LearningProgress)
        .where(
            LearningProgress.user_id == user.id,
            LearningProgress.status == "completed",
        )
        .order_by(LearningProgress.completed_at.desc())
        .limit(5)
    )
    recent_completed = recent_result.scalars().all()
    recent_chapters = []
    for rp in recent_completed:
        nr = await db.execute(select(KnowledgeNode).where(KnowledgeNode.id == rp.node_id))
        node = nr.scalar_one_or_none()
        if node:
            recent_chapters.append({"node_id": node.id, "title": node.title})

    # ★ 连续学习天数
    streak_days = await _calc_streak(db, user.id)

    # ★ 本周每日打卡情况
    week_active_days = await _calc_week_days(db, user.id, week_start_utc)

    # ★ 热门知识点（学习人数最多的节点）
    hot_topics = await _calc_hot_topics(db)

    # ★ 今日学习任务（从learning_progress中取pending/in_progress的）
    today_tasks = await _calc_today_tasks(db, user.id)

    return {
        "today_seconds": today_seconds,
        "today_display": f"{today_hours}小时{today_minutes}分钟",
        "week_seconds": week_seconds,
        "week_display": f"{week_hours}小时",
        "total_seconds": total_study_seconds,
        "total_display": f"{total_hours}小时",
        "activity": activity,
        "study_count": study_count,
        "active_days": active_days,
        "completion_rate": round(completion_rate, 1),
        "total_chapters": total_nodes,
        "completed_chapters": completed_chapters,
        "chapter_completion_rate": chapter_completion_rate,
        "recent_chapters": recent_chapters,
        "daily_encouragement": daily_encouragement,
        "weekly_encouragement": weekly_encouragement,
        # ★ 新增字段
        "streak_days": streak_days,
        "week_days": week_active_days,
        "hot_topics": hot_topics,
        "today_tasks": today_tasks,
    }


async def _calc_streak(db: AsyncSession, user_id: int) -> int:
    """计算连续学习天数"""
    from sqlalchemy import desc
    result = await db.execute(
        select(StudySession.started_at)
        .where(StudySession.user_id == user_id)
        .order_by(desc(StudySession.started_at))
        .limit(60)
    )
    dates = set()
    tz = timezone(timedelta(hours=8))
    for row in result.scalars().all():
        if row:
            local_date = row.astimezone(tz).date()
            dates.add(local_date)

    if not dates:
        return 0

    # 从今天往回数连续天数
    today = datetime.now(tz).date()
    streak = 0
    for i in range(60):
        check_date = today - timedelta(days=i)
        if check_date in dates:
            streak += 1
        else:
            if i == 0:  # 今天还没学习，从昨天开始算
                continue
            break
    return streak


async def _calc_week_days(db: AsyncSession, user_id: int, week_start_utc) -> list:
    """计算本周哪些天有学习活动（返回1-7的列表）"""
    tz = timezone(timedelta(hours=8))
    result = await db.execute(
        select(StudySession.started_at)
        .where(
            StudySession.user_id == user_id,
            StudySession.started_at >= week_start_utc,
        )
    )
    active_days = set()
    for row in result.scalars().all():
        if row:
            local_date = row.astimezone(tz).date()
            dow = local_date.weekday() + 1  # 1=Monday
            active_days.add(dow)
    return list(active_days)


async def _calc_hot_topics(db: AsyncSession) -> list:
    """计算热门知识点（学习人数最多的前5个）"""
    from sqlalchemy import desc
    cnt_col = sa_func.count(sa_func.distinct(LearningProgress.user_id)).label("cnt")
    result = await db.execute(
        select(
            LearningProgress.node_id,
            cnt_col,
        )
        .group_by(LearningProgress.node_id)
        .order_by(desc("cnt"))
        .limit(5)
    )
    hot = []
    for i, row in enumerate(result.all()):
        node_id = row[0]
        count = row[1] or 0
        nr = await db.execute(select(KnowledgeNode).where(KnowledgeNode.id == node_id))
        node = nr.scalar_one_or_none()
        hot.append({
            "name": node.title if node else node_id,
            "nodeId": node_id,
            "rank": i + 1,
            "count": count,
        })
    return hot


async def _calc_today_tasks(db: AsyncSession, user_id: int) -> list:
    """获取今日学习任务"""
    from sqlalchemy import desc
    result = await db.execute(
        select(LearningProgress)
        .where(
            LearningProgress.user_id == user_id,
            LearningProgress.status.in_(["in_progress", "learning"]),
        )
        .order_by(desc(LearningProgress.started_at))
        .limit(5)
    )
    tasks = []
    for rp in result.scalars().all():
        nr = await db.execute(select(KnowledgeNode).where(KnowledgeNode.id == rp.node_id))
        node = nr.scalar_one_or_none()
        tasks.append({
            "id": rp.id,
            "name": node.title if node else rp.node_id,
            "status": "active" if rp.status in ("in_progress", "learning") else "pending",
            "progress": rp.progress or (50 if rp.status == "in_progress" else 0),
            "nodeId": rp.node_id,
        })
    return tasks


def _get_daily_encouragement(seconds: int) -> str:
    """根据今日学习时长生成激励文案"""
    hours = seconds / 3600
    if hours < 0.5:
        return "今天已经开始学习，继续保持。"
    elif hours < 1:
        return "不错，你已经超过很多普通学习者。"
    elif hours < 2:
        return "学习状态很好，正在持续积累知识。"
    elif hours < 4:
        return "优秀的学习习惯正在形成。"
    else:
        return "今天的投入非常出色，坚持下去会有巨大收获。"


def _get_weekly_encouragement(seconds: int) -> str:
    """根据本周学习时长生成激励文案"""
    hours = seconds / 3600
    if hours < 5:
        return ""
    elif hours < 10:
        return "本周学习状态良好。"
    elif hours < 20:
        return "本周学习效率优秀。"
    elif hours < 30:
        return "本周表现非常突出。"
    else:
        return "你的学习投入已经达到高水平。"


# ════════════════════════════════════════════════════════
# ★ 今日任务推荐（基于学习情况动态生成）
# ════════════════════════════════════════════════════════

class DailyTask(BaseModel):
    id: str
    title: str
    duration: str
    type: str          # 错题复习 | 继续学习 | 弱项强化 | AI 学习 | 新内容探索
    difficulty: str = ""
    nodeId: str = ""
    completed: bool = False
    isCurrent: bool = False
    reason: str = ""   # 推荐原因


async def generate_daily_tasks(
    db: AsyncSession,
    user: User,
) -> dict:
    """生成今日任务推荐（可被 task_api 复用）"""
    tasks: List[DailyTask] = []
    user_id = getattr(user, 'id', None)
    if user_id is None:
        return _default_guide_tasks()

    # 1. 查询错题
    mistake_chapters = {}
    try:
        exam_results = await db.execute(
            select(ExamResult).where(
                ExamResult.user_id == user_id,
                ExamResult.details.isnot(None),
                ExamResult.passed == False,
            ).order_by(ExamResult.completed_at.desc()).limit(5)
        )
        for result in exam_results.scalars().all():
            try:
                details = json.loads(result.details) if result.details else []
                mistake_count = sum(
                    1 for d in details if not d.get('removed', False) and not d.get('correct', True)
                )
                if mistake_count > 0 and result.node_id:
                    mistake_chapters[result.node_id] = (mistake_chapters.get(result.node_id) or 0) + mistake_count
            except (json.JSONDecodeError, TypeError):
                pass
    except Exception:
        pass

    # 2. 查询未完成的学习节点
    incomplete_nodes = []
    try:
        progress_result = await db.execute(
            select(LearningProgress).where(
                LearningProgress.user_id == user_id,
                LearningProgress.status != 'completed',
            ).order_by(LearningProgress.started_at.desc()).limit(5)
        )
        for prog in progress_result.scalars().all():
            if prog.node_id:
                node_result = await db.execute(
                    select(KnowledgeNode).where(KnowledgeNode.id == prog.node_id)
                )
                node = node_result.scalar_one_or_none()
                title = node.title if node else prog.node_id
                prog_pct = (prog.progress or 0)
                incomplete_nodes.append({
                    'node_id': prog.node_id,
                    'title': title,
                    'progress': prog_pct,
                })
    except Exception:
        pass

    # 3. 查询弱项
    weak_nodes = []
    try:
        weak_result = await db.execute(
            select(ExamResult).where(
                ExamResult.user_id == user_id,
                ExamResult.passed == True,
                ExamResult.score < 70,
            ).order_by(ExamResult.score.asc()).limit(3)
        )
        for result in weak_result.scalars().all():
            if result.node_id and result.node_id not in mistake_chapters:
                node_result = await db.execute(
                    select(KnowledgeNode).where(KnowledgeNode.id == result.node_id)
                )
                node = node_result.scalar_one_or_none()
                weak_nodes.append({
                    'node_id': result.node_id,
                    'title': node.title if node else result.node_id,
                    'score': result.score,
                })
    except Exception:
        pass

    # ── 构建任务列表 ──
    for node_id, count in list(mistake_chapters.items())[:3]:
        node_result = await db.execute(select(KnowledgeNode).where(KnowledgeNode.id == node_id))
        node = node_result.scalar_one_or_none()
        chapter_name = node.title if node else node_id
        tasks.append(DailyTask(
            id=f"review-{node_id}",
            title=f"复习「{chapter_name}」的 {count} 道错题",
            duration=f"{count * 5} 分钟",
            type="错题复习",
            nodeId="review",
            reason=f"该章节有 {count} 道错题待复习",
        ))

    for node in incomplete_nodes[:2]:
        pct = node['progress']
        reason_text = f"已完成约 {pct}%，继续加油" if pct > 0 else "刚刚开始，快去学习吧 ✨"
        tasks.append(DailyTask(
            id=f"continue-{node['node_id']}",
            title=f"继续「{node['title']}」的学习",
            duration="20 分钟",
            type="继续学习",
            nodeId=node['node_id'],
            reason=reason_text,
        ))

    for node in weak_nodes[:2]:
        tasks.append(DailyTask(
            id=f"strengthen-{node['node_id']}",
            title=f"强化「{node['title']}」知识点",
            duration="25 分钟",
            type="弱项强化",
            difficulty="中级",
            nodeId=node['node_id'],
            reason=f"该章节得分 {node['score']} 分，有提升空间",
        ))

    if len(tasks) == 0:
        try:
            all_nodes_result = await db.execute(
                select(KnowledgeNode).limit(3)
            )
            for node in all_nodes_result.scalars().all():
                tasks.append(DailyTask(
                    id=f"explore-{node.id}",
                    title=f"探索「{node.title}」",
                    duration="15 分钟",
                    type="新内容探索",
                    nodeId=node.id,
                    reason="推荐你学习新章节",
                ))
        except Exception:
            pass

    if tasks:
        tasks[0].isCurrent = True

    # 如果没有任何任务数据
    if not tasks:
        default_tasks = _default_guide_tasks()
        return default_tasks

    return {"tasks": [t.model_dump() for t in tasks], "total": len(tasks)}


def _default_guide_tasks() -> dict:
    """未登录或新用户的默认引导任务"""
    return {
        "tasks": [
            DailyTask(
                id="guide-onboarding",
                title="完成引导测试，生成你的学习计划",
                duration="10 分钟",
                type="新内容探索",
                nodeId="onboarding",
                isCurrent=True,
                reason="AI 需要了解你的水平才能生成个性化计划",
            ).model_dump(),
            DailyTask(
                id="guide-explore",
                title="浏览知识图谱，了解数据结构全貌",
                duration="5 分钟",
                type="新内容探索",
                nodeId="map",
                reason="了解学习路线，做到心中有数",
            ).model_dump(),
        ],
        "total": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── 对外 HTTP 端点 ──

@router.get("/daily-tasks")
async def get_daily_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日推荐任务"""
    return await generate_daily_tasks(db, user)


# ════════════════════════════════════════════════════════
# 学习日历数据
# ════════════════════════════════════════════════════════

@router.get("/calendar")
async def get_calendar_data(
    year: int = None,
    month: int = None,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户学习日历数据（按日期聚合学习记录，包含具体知识点名称）"""
    from sqlalchemy import func, extract, case

    now = datetime.now(timezone.utc)
    target_year = year or now.year
    target_month = month or (now.month if now.tzinfo else (now - timedelta(hours=8)).month)

    start_date = datetime(target_year, target_month, 1, tzinfo=timezone(timedelta(hours=8)))
    if target_month == 12:
        end_date = datetime(target_year + 1, 1, 1, tzinfo=timezone(timedelta(hours=8)))
    else:
        end_date = datetime(target_year, target_month + 1, 1, tzinfo=timezone(timedelta(hours=8)))

    start_utc = start_date.astimezone(timezone.utc)
    end_utc = end_date.astimezone(timezone.utc)

    # ═══ 1. 按日期聚合学习时长 ═══
    session_result = await db.execute(
        select(
            func.date(StudySession.started_at).label('date'),
            sa_func.sum(StudySession.duration_seconds).label('total_seconds'),
            sa_func.count(StudySession.id).label('session_count'),
        )
        .where(
            StudySession.user_id == user.id,
            StudySession.started_at >= start_utc,
            StudySession.started_at < end_utc,
        )
        .group_by(func.date(StudySession.started_at))
        .order_by(func.date(StudySession.started_at))
    )
    daily_sessions = session_result.all()

    # ═══ 2. 每天学习过哪些节点（从 StudySession 去重） ═══
    session_nodes_result = await db.execute(
        select(
            func.date(StudySession.started_at).label('date'),
            StudySession.node_id,
        )
        .where(
            StudySession.user_id == user.id,
            StudySession.started_at >= start_utc,
            StudySession.started_at < end_utc,
        )
        .distinct()
        .order_by(func.date(StudySession.started_at))
    )
    session_node_rows = session_nodes_result.all()

    # ═══ 3. 当天完成的节点 ═══
    completed_result = await db.execute(
        select(
            func.date(LearningProgress.completed_at).label('date'),
            LearningProgress.node_id,
        )
        .where(
            LearningProgress.user_id == user.id,
            LearningProgress.status == 'completed',
            LearningProgress.completed_at >= start_utc,
            LearningProgress.completed_at < end_utc,
        )
    )
    completed_rows = completed_result.all()

    # ═══ 4. 当天考试记录 ═══
    exam_result = await db.execute(
        select(
            func.date(ExamResult.completed_at).label('date'),
            ExamResult.node_id,
            ExamResult.score,
            ExamResult.passed,
        )
        .where(
            ExamResult.user_id == user.id,
            ExamResult.completed_at >= start_utc,
            ExamResult.completed_at < end_utc,
        )
        .order_by(ExamResult.completed_at)
    )
    exam_rows = exam_result.all()

    # ═══ 构建节点名称映射 ═══
    all_node_ids = set()
    for rec in session_node_rows:
        if rec.node_id:
            all_node_ids.add(rec.node_id)
    for cr in completed_rows:
        if cr.node_id:
            all_node_ids.add(cr.node_id)
    for er in exam_rows:
        if er.node_id:
            all_node_ids.add(er.node_id)

    node_map = {}
    if all_node_ids:
        nodes_res = await db.execute(
            select(KnowledgeNode).where(KnowledgeNode.id.in_(list(all_node_ids)))
        )
        for n in nodes_res.scalars().all():
            node_map[n.id] = n.title

    # ═══ 组装 calendar_data ═══
    calendar_data = {}

    # 基础结构（学习时长）
    for rec in daily_sessions:
        date_str = str(rec.date)
        minutes = (rec.total_seconds or 0) // 60
        calendar_data[date_str] = {
            'minutes': minutes,
            'sessionCount': rec.session_count or 0,
            'completedNodes': [],
            'learningNodes': [],
            'examResults': [],
            'completedCount': 0,
        }

    # 填充学习中的节点（按日期分组去重）
    date_learning_map = {}  # date_str → set(node_title)
    for row in session_node_rows:
        date_str = str(row.date)
        title = node_map.get(row.node_id, row.node_id)
        if date_str not in date_learning_map:
            date_learning_map[date_str] = set()
        date_learning_map[date_str].add(title)

    for date_str, titles in date_learning_map.items():
        if date_str not in calendar_data:
            calendar_data[date_str] = {
                'minutes': 0, 'sessionCount': 0,
                'completedNodes': [], 'learningNodes': [], 'examResults': [],
            }
        calendar_data[date_str]['learningNodes'] = list(titles)

    # 填充已完成节点
    date_completed_map = {}  # date_str → set(node_title)
    for cr in completed_rows:
        date_str = str(cr.date)
        title = node_map.get(cr.node_id, cr.node_id)
        if date_str not in date_completed_map:
            date_completed_map[date_str] = set()
        date_completed_map[date_str].add(title)

    for date_str, titles in date_completed_map.items():
        if date_str not in calendar_data:
            calendar_data[date_str] = {
                'minutes': 0, 'sessionCount': 0,
                'completedNodes': [], 'learningNodes': [], 'examResults': [],
            }
        calendar_data[date_str]['completedNodes'] = list(titles)
        calendar_data[date_str]['completedCount'] = len(titles)

    # ★ 去重：已完成的节点从 learningNodes 中移除
    for date_str, day_data in calendar_data.items():
        completed_set = set(day_data.get('completedNodes', []))
        learning = day_data.get('learningNodes', [])
        day_data['learningNodes'] = [n for n in learning if n not in completed_set]

    # 填充考试结果
    for er in exam_rows:
        date_str = str(er.date)
        if date_str not in calendar_data:
            calendar_data[date_str] = {
                'minutes': 0, 'sessionCount': 0,
                'completedNodes': [], 'learningNodes': [], 'examResults': [],
            }
        node_title = node_map.get(er.node_id, er.node_id)
        calendar_data[date_str]['examResults'].append({
            'node': node_title,
            'score': er.score,
            'passed': er.passed,
        })

    # ═══ AI 点评（基于当天实际内容） ═══
    for date_str, data in calendar_data.items():
        parts = []
        if data.get('completedCount', 0) > 0:
            parts.append(f"完成了 {data['completedCount']} 个章节")
        if data.get('minutes', 0) >= 30:
            parts.append(f"学习了 {data['minutes']} 分钟")
        exam_pass = sum(1 for ex in data.get('examResults', []) if ex.get('passed'))
        if exam_pass > 0:
            parts.append(f"通过了 {exam_pass} 场测试")

        if parts:
            data['aiComment'] = '，'.join(parts) + '，表现很棒！'
        elif data.get('minutes', 0) > 0:
            data['aiComment'] = f"学习了 {data['minutes']} 分钟，继续保持节奏。"
        else:
            data['aiComment'] = '当日暂无学习记录，记得抽空复习哦。'

    return {
        "year": target_year,
        "month": target_month,
        "records": calendar_data,
        "total_days_with_activity": len(calendar_data),
    }


# ════════════════════════════════════════════════════════
# 图表数据（供 Analysis 页面使用）
# ════════════════════════════════════════════════════════

@router.get("/chart-data")
async def get_chart_data(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 Analysis 页面所需的全部图表数据"""
    from sqlalchemy import extract, func as sa_func

    now = datetime.now(timezone.utc)
    tz = timezone(timedelta(hours=8))
    local_now = now.astimezone(tz)

    # 1. 雷达图数据：知识掌握度（基于 AssessmentAgent 的测评结果或 LearningProgress）
    # 从 learning_progress 中按节点类型聚合完成情况
    radar_result = await db.execute(
        select(
            sa_func.count(LearningProgress.id).label('total'),
            sa_func.sum(
                case((LearningProgress.status == 'completed', 1), else_=0)
            ).label('completed'),
            KnowledgeNode.category,
        )
        .outerjoin(KnowledgeNode, LearningProgress.node_id == KnowledgeNode.id)
        .where(LearningProgress.user_id == user.id)
        .group_by(KnowledgeNode.category)
    )
    radar_rows = radar_result.all()

    # 默认6个维度
    categories = ['线性表', '栈与队列', '树形结构', '图论', '查找算法', '排序算法']
    category_map = {cat: {'total': 0, 'completed': 0} for cat in categories}
    for row in radar_rows:
        if row.category and row.category in category_map:
            category_map[row.category]['total'] = row.total or 0
            category_map[row.category]['completed'] = row.completed or 0

    radar_values = []
    for cat in categories:
        data = category_map[cat]
        if data['total'] > 0:
            score = round((data['completed'] / data['total']) * 100, 1)
        else:
            score = 0
        radar_values.append(score)

    # 如果没有任何学习记录，给默认值（基于用户画像中的能力等级）
    if sum(radar_values) == 0:
        radar_values = [30, 20, 10, 5, 15, 25]  # 初学者默认值

    # 2. 折线图数据：最近7天/周的学习时长趋势
    week_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=local_now.weekday())
    week_start_utc = week_start.astimezone(timezone.utc)

    trend_result = await db.execute(
        select(
            func.date(StudySession.started_at).label('date'),
            sa_func.sum(StudySession.duration_seconds).label('minutes'),
        )
        .where(
            StudySession.user_id == user.id,
            StudySession.started_at >= week_start_utc,
        )
        .group_by(func.date(StudySession.started_at))
        .order_by(func.date(StudySession.started_at))
    )
    trend_records = trend_result.all()

    trend_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    trend_data = [0] * 7

    for record in trend_records:
        date_str = str(record.date)
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            day_of_week = dt.weekday()  # 0=Monday
        except ValueError:
            continue
        minutes = (record.minutes or 0) // 60
        if 0 <= day_of_week < 7:
            trend_data[day_of_week] = minutes

    # 如果本周无数据，显示上周的数据作为参考
    if sum(trend_data) == 0:
        last_week_start_utc = week_start_utc - timedelta(days=7)
        last_week_result = await db.execute(
            select(
                func.date(StudySession.started_at).label('date'),
                sa_func.sum(StudySession.duration_seconds).label('minutes'),
            )
            .where(
                StudySession.user_id == user.id,
                StudySession.started_at >= last_week_start_utc,
                StudySession.started_at < week_start_utc,
            )
            .group_by(func.date(StudySession.started_at))
            .order_by(func.date(StudySession.started_at))
        )
        last_week_records = last_week_result.all()
        for record in last_week_records:
            day_of_week = record.date.weekday()
            minutes = (record.minutes or 0) // 60
            if 0 <= day_of_week < 7:
                trend_data[day_of_week] = minutes

    # 3. 饼图数据：学习时长分布（基于学习事件类型）
    # 简化版：根据 session 数量估算分布
    total_sessions_result = await db.execute(
        select(sa_func.count(StudySession.id)).where(StudySession.user_id == user.id)
    )
    total_sessions = total_sessions_result.scalar() or 0

    exam_count_result = await db.execute(
        select(sa_func.count(ExamResult.id)).where(ExamResult.user_id == user.id)
    )
    exam_count = exam_count_result.scalar() or 0

    # 根据实际活动计算分布比例
    if total_sessions > 0:
        base_study_pct = max(10, min(60, 100 - exam_count * 2))
        practice_pct = max(5, min(35, exam_count * 3))
        ai_chat_pct = max(10, min(30, 50 - exam_count))
        video_pct = max(0, min(15, 100 - base_study_pct - practice_pct - ai_chat_pct))

        # 归一化到100%
        total = base_study_pct + practice_pct + ai_chat_pct + video_pct
        if total > 0:
            pie_data = [
                {"value": round(base_study_pct / total * 40 + 30, 1), "name": '阅读讲解'},
                {"value": round(practice_pct / total * 30 + 10, 1), "name": '动手练习'},
                {"value": round(ai_chat_pct / total * 20 + 10, 1), "name": 'AI 交流'},
                {"value": max(5, round(video_pct / total * 10 + 5, 1)), "name": '视频观看'},
            ]
        else:
            pie_data = [
                {"value": 40, "name": '阅读讲解'},
                {"value": 30, "name": '动手练习'},
                {"value": 20, "name": 'AI 交流'},
                {"value": 10, "name": '视频观看'},
            ]
    else:
        pie_data = [
            {"value": 40, "name": '阅读讲解'},
            {"value": 30, "name": '动手练习'},
            {"value": 20, "name": 'AI 交流'},
            {"value": 10, "name": '视频观看'},
        ]

    # 4. 热力图数据：全年学习活跃度
    year_start = datetime(local_now.year, 1, 1, tzinfo=tz).astimezone(timezone.utc)
    heatmap_result = await db.execute(
        select(
            func.date(StudySession.started_at).label('date'),
            sa_func.sum(StudySession.duration_seconds).label('seconds'),
        )
        .where(
            StudySession.user_id == user.id,
            StudySession.started_at >= year_start,
        )
        .group_by(func.date(StudySession.started_at))
    )
    heatmap_records = heatmap_result.all()

    heatmap_data = []
    for record in heatmap_records:
        date_str = str(record.date)
        seconds = record.seconds or 0
        # 转换为分钟级别，用于热力图颜色深浅
        activity_level = min(1000, int(seconds // 6))  # 映射到 0-1000
        heatmap_data.append([date_str, activity_level])

    # 5. 弱项分析文字（基于最低分的维度）
    scores_with_cats = list(zip(categories, radar_values))
    scores_with_cats.sort(key=lambda x: x[1])
    weakest_categories = scores_with_cats[:2]

    weak_analysis = ''
    if weakest_categories[0][1] > 70:
        weak_analysis = f'你的知识掌握情况良好！继续保持当前的学习节奏。'
    else:
        weak_names = '和'.join([f'{wc[0]}' for wc in weakest_categories if wc[1] < 60])
        weak_analysis = f'数据显示你在**{weak_names}**上的掌握程度还有提升空间。建议多花时间复习这些章节。'

    # 6. 个性化建议（基于学习模式和行为特征）
    suggestions = []

    if radar_values[categories.index('线性表')] < 50:
        suggestions.append('线性结构是所有数据结构的基础，建议先从数组和链表开始系统复习。')

    if radar_values[categories.index('树形结构')] < 40:
        suggestions.append('二叉树的遍历和应用是高频考点，推荐用递归+迭代两种方式实现。')

    if total_sessions > 10 and sum(trend_data) / len([d for d in trend_data if d > 0]) > 120:
        suggestions.append('你每天的学习强度很大，注意劳逸结合，避免疲劳学习。')

    if not suggestions:
        suggestions = [
            '尝试使用 AI 助手的"费曼模拟"功能，向它解释一次最近学到的概念。',
            '建议定期回顾错题本中的题目，巩固薄弱环节。',
            '可以尝试做几道综合性练习题，检验知识点的融会贯通程度。',
        ]

    return {
        'radar': {
            'categories': categories,
            'values': radar_values,
        },
        'trend': {
            'labels': trend_labels,
            'data': trend_data,
        },
        'pie': pie_data,
        'heatmap': heatmap_data,
        'weak_analysis': weak_analysis,
        'suggestions': suggestions[:3],
    }
