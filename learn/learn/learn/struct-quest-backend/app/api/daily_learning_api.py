"""
每日学习任务 API —— 实现三阶段任务流程

路由前缀: /api/daily-learning

任务流程:
  任务一: 学习知识点（用户提及知识点名称即完成）
  任务二: 练习题（全部答对完成）
  任务三: 温故知新（复习错题）
"""
import json
import random
import os as _os
from datetime import date, datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func as sa_func

from app.db.session import get_db
from app.auth import get_required_user
from app.models.user import User
from app.models.daily_learning_progress import DailyLearningProgress
from app.models.wrong_question import WrongQuestion
from app.models.knowledge_graph import KnowledgeNode

router = APIRouter(prefix="/api/daily-learning", tags=["daily-learning"])


# ═══════════════════════════════════════════
# 请求/响应模型
# ═══════════════════════════════════════════

class TaskStatusResponse(BaseModel):
    """今日任务状态响应"""
    task_date: str
    node_id: Optional[str] = None
    node_name: Optional[str] = None
    task1_status: str = 'pending'     # pending / completed
    task2_status: str = 'pending'     # pending / in_progress / completed
    current_question_index: int = 0
    total_questions: int = 0
    correct_count: int = 0
    task3_status: str = 'pending'     # pending / in_progress / completed
    total_review: int = 0
    reviewed_count: int = 0
    all_completed: bool = False


class PracticeQuestion(BaseModel):
    """练习题"""
    id: int
    question: str
    options: List[str]
    correct_answer: str
    explanation: str
    knowledge: str


class AnswerSubmitRequest(BaseModel):
    user_answer: str
    question_id: int


class AnswerResultResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str
    next_question: Optional['PracticeQuestion'] = None
    all_completed: bool = False
    task_completed: bool = False


class ReviewQuestion(BaseModel):
    id: int
    question_text: str
    options: Optional[list] = None
    correct_answer: str
    explanation: Optional[str] = None
    knowledge: str


class ReviewSubmitRequest(BaseModel):
    wrong_question_id: int
    user_answer: str


class ReviewResultResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    mastered: bool = False
    next_question: Optional[ReviewQuestion] = None
    all_completed: bool = False


class TaskUpdateRequest(BaseModel):
    task_type: str  # task1 / task2 / task3
    status: str     # completed / in_progress
    metadata: Optional[dict] = None


# ═══════════════════════════════════════════
# 静态数据：练习题池
# ═══════════════════════════════════════════

_QUESTIONS_POOL = {
    "队列": [
        {
            "id": 1,
            "question": "队列（Queue）是一种什么样的数据结构？",
            "options": ["后进先出（LIFO）", "先进先出（FIFO）", "随机访问", "按优先级排序"],
            "correct_answer": "先进先出（FIFO）",
            "explanation": "队列是先进先出（FIFO, First In First Out）的线性表。只允许在队尾插入、队头删除，与日常排队类似。"
        },
        {
            "id": 2,
            "question": "循环队列中，判断队满的条件是（rear指向队尾元素的下一个位置）：",
            "options": ["rear == front", "(rear + 1) % MaxSize == front", "rear - front == MaxSize", "front == (rear + 1) % MaxSize"],
            "correct_answer": "(rear + 1) % MaxSize == front",
            "explanation": "循环队列中通常牺牲一个存储单元来区分队空和队满。队空：rear == front；队满：(rear + 1) % MaxSize == front。"
        },
        {
            "id": 3,
            "question": "队列的典型应用场景不包括以下哪项？",
            "options": ["CPU进程调度", "广度优先搜索（BFS）", "函数调用栈", "打印机任务队列"],
            "correct_answer": "函数调用栈",
            "explanation": "函数调用使用栈结构（后进先出），而非队列。CPU进程调度（先到先服务）、BFS、打印机任务队列都是队列的典型应用。"
        },
        {
            "id": 4,
            "question": "链队列中，出队操作的时间复杂度是？",
            "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"],
            "correct_answer": "O(1)",
            "explanation": "链队列维护队头指针和队尾指针，出队只需修改头指针指向下一个结点，时间复杂度为O(1)。"
        },
        {
            "id": 5,
            "question": "以下哪种不是队列的实现方式？",
            "options": ["顺序队列", "链队列", "循环队列", "二叉队列"],
            "correct_answer": "二叉队列",
            "explanation": "队列的实现方式有顺序队列（数组）、链队列（链表）和循环队列（解决假溢出）。二叉队列不是标准的数据结构概念。"
        },
    ],
    "栈": [
        {
            "id": 101,
            "question": "栈（Stack）是一种什么样的数据结构？",
            "options": ["先进先出（FIFO）", "后进先出（LIFO）", "随机访问", "双端访问"],
            "correct_answer": "后进先出（LIFO）",
            "explanation": "栈是后进先出（LIFO, Last In First Out）的线性表。只允许在栈顶进行插入和删除操作。"
        },
        {
            "id": 102,
            "question": "栈的典型应用不包括？",
            "options": ["括号匹配", "表达式求值", "函数递归调用", "进程调度"],
            "correct_answer": "进程调度",
            "explanation": "进程调度通常使用队列（先来先服务）或优先级队列，不是栈。括号匹配、表达式求值、函数递归调用都是栈的典型应用。"
        },
        {
            "id": 103,
            "question": "一个栈的入栈序列是a,b,c,d,e，则不可能的出栈序列是？",
            "options": ["edcba", "decba", "dceab", "abcde"],
            "correct_answer": "dceab",
            "explanation": "dceab不可能：d出栈时，栈内有a,b,c（d出后c在栈顶），c出栈后e入栈，e出栈后栈顶是b，b出栈后a出栈——正确的顺序是dceba。"
        },
    ],
    "链表": [
        {
            "id": 201,
            "question": "单链表中，在已知结点p后面插入新结点s的操作是？",
            "options": ["s.next = p.next; p.next = s", "p.next = s; s.next = p.next", "s.next = p; p.next = s", "p = s; s.next = p.next"],
            "correct_answer": "s.next = p.next; p.next = s",
            "explanation": "正确顺序：先将s的next指向p的后继（s.next = p.next），再将p的next指向s（p.next = s）。顺序不能颠倒，否则会丢失p的后继结点。"
        },
        {
            "id": 202,
            "question": "双向链表中，删除结点p的操作是？",
            "options": ["p.prev.next = p.next; p.next.prev = p.prev", "p.next = p.prev; p.prev = p.next", "p.prev = p.next; p.next = p.prev", "p.prev.next = p.next; p.next = p.prev"],
            "correct_answer": "p.prev.next = p.next; p.next.prev = p.prev",
            "explanation": "将p的前驱的next指向p的后继（p.prev.next = p.next），将p的后继的prev指向p的前驱（p.next.prev = p.prev）。"
        },
    ],
    "二叉树": [
        {
            "id": 301,
            "question": "二叉树的先序遍历顺序是？",
            "options": ["左-根-右", "根-左-右", "左-右-根", "根-右-左"],
            "correct_answer": "根-左-右",
            "explanation": "先序遍历（Preorder）：先访问根结点，再遍历左子树，最后遍历右子树（根-左-右）。"
        },
        {
            "id": 302,
            "question": "深度为k的二叉树最多有多少个结点？",
            "options": ["2^k-1", "2^k", "2^(k-1)", "2^k+1"],
            "correct_answer": "2^k-1",
            "explanation": "满二叉树时结点数最多：第1层1个，第2层2个，...，第k层2^(k-1)个。总和 = 2^k - 1。"
        },
    ],
    "顺序表": [
        {
            "id": 401,
            "question": "顺序表的主要特点是？",
            "options": ["支持随机存取", "插入删除不需要移动元素", "存储空间不连续", "不支持动态扩容"],
            "correct_answer": "支持随机存取",
            "explanation": "顺序表用数组实现，可以通过下标直接访问任意元素，时间复杂度O(1)。但插入删除需要移动大量元素。"
        },
    ],
}

_DEFAULT_KNOWLEDGE = [
    ("ch05_binary_tree", "二叉树"),
    ("ch03_queue_basic", "队列"),
    ("ch03_stack_basic", "栈"),
    ("ch02_linked_list", "链表"),
    ("ch02_seq_list", "顺序表"),
]


# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════

def _get_today_str() -> str:
    return date.today().isoformat()


def _get_questions_for_node(node_name: str) -> list:
    """获取与知识点相关的练习题"""
    # 精确匹配
    if node_name in _QUESTIONS_POOL:
        return _QUESTIONS_POOL[node_name]
    # 模糊匹配
    for key, questions in _QUESTIONS_POOL.items():
        if key in node_name or node_name in key:
            return questions
    # 默认返回队列练习题
    return _QUESTIONS_POOL.get("队列", [])


def _pick_today_node() -> tuple:
    """随机选取今日知识点"""
    # 基于日期确定今天学习的知识点（确保一天内不变）
    import hashlib
    today = _get_today_str()
    idx = int(hashlib.md5(today.encode()).hexdigest(), 16) % len(_DEFAULT_KNOWLEDGE)
    return _DEFAULT_KNOWLEDGE[idx]


async def _get_or_create_progress(db: AsyncSession, user_id: int) -> DailyLearningProgress:
    """获取或创建今日学习进度"""
    today = date.today()
    result = await db.execute(
        select(DailyLearningProgress).where(
            DailyLearningProgress.user_id == user_id,
            DailyLearningProgress.task_date == today
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        node_id, node_name = _pick_today_node()
        questions = _get_questions_for_node(node_name)
        progress = DailyLearningProgress(
            user_id=user_id,
            task_date=today,
            node_id=node_id,
            node_name=node_name,
            total_questions=len(questions),
            task1_status='pending',
            task2_status='pending',
            task3_status='pending',
        )
        db.add(progress)
        await db.commit()
        await db.refresh(progress)
    return progress


def _build_task_status(progress: DailyLearningProgress) -> TaskStatusResponse:
    """构建任务状态响应"""
    all_completed = (
        progress.task1_status == 'completed' and
        progress.task2_status == 'completed' and
        progress.task3_status == 'completed'
    )
    return TaskStatusResponse(
        task_date=progress.task_date.isoformat(),
        node_id=progress.node_id,
        node_name=progress.node_name,
        task1_status=progress.task1_status,
        task2_status=progress.task2_status,
        current_question_index=progress.current_question_index,
        total_questions=progress.total_questions,
        correct_count=progress.correct_count,
        task3_status=progress.task3_status,
        total_review=progress.total_review,
        reviewed_count=progress.reviewed_count,
        all_completed=all_completed,
    )


# ═══════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════

@router.get("/today", response_model=TaskStatusResponse)
async def get_today_task(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """获取今日学习任务状态"""
    print(f"[DailyLearning] 获取今日任务: user={current_user.id}")
    progress = await _get_or_create_progress(db, current_user.id)
    return _build_task_status(progress)


@router.get("/questions")
async def get_practice_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """获取今日练习题"""
    print(f"[DailyLearning] 获取练习题: user={current_user.id}")
    progress = await _get_or_create_progress(db, current_user.id)
    questions = _get_questions_for_node(progress.node_name or "队列")

    # 更新任务二状态为 in_progress
    if progress.task2_status == 'pending':
        progress.task2_status = 'in_progress'
        progress.total_questions = len(questions)
        progress.current_question_index = 0
        await db.commit()

    # 返回所有题目（不含答案）
    result = []
    for q in questions:
        result.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "knowledge": progress.node_name or "队列",
        })
    return {
        "questions": result,
        "current_index": progress.current_question_index,
        "total": len(questions),
        "node_name": progress.node_name or "队列",
    }


@router.post("/answer")
async def submit_answer(
    req: AnswerSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """提交练习题答案"""
    print(f"[DailyLearning] 提交答案: user={current_user.id}, question_id={req.question_id}")

    progress = await _get_or_create_progress(db, current_user.id)
    questions = _get_questions_for_node(progress.node_name or "队列")

    # 查找题目
    question = None
    for q in questions:
        if q["id"] == req.question_id:
            question = q
            break
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    correct = req.user_answer.strip() == question["correct_answer"].strip()

    if correct:
        progress.correct_count = (progress.correct_count or 0) + 1
        progress.current_question_index = (progress.current_question_index or 0) + 1
        all_completed = progress.current_question_index >= len(questions)

        if all_completed:
            progress.task2_status = 'completed'
            progress.task2_completed_at = datetime.now(timezone.utc)

        await db.commit()

        # 返回下一题或完成状态
        next_question = None
        if not all_completed and progress.current_question_index < len(questions):
            nq = questions[progress.current_question_index]
            next_question = PracticeQuestion(
                id=nq["id"],
                question=nq["question"],
                options=nq["options"],
                correct_answer="",  # 不暴露答案
                explanation="",
                knowledge=progress.node_name or "队列",
            )

        return AnswerResultResponse(
            correct=True,
            correct_answer=question["correct_answer"],
            explanation=question["explanation"],
            next_question=next_question,
            all_completed=all_completed,
            task_completed=all_completed,
        )
    else:
        # 答错：记录到错题库
        wrong = WrongQuestion(
            user_id=current_user.id,
            node_id=progress.node_id or "",
            question_text=question["question"],
            options=json.dumps(question["options"], ensure_ascii=False),
            correct_answer=question["correct_answer"],
            user_answer=req.user_answer,
            explanation=question["explanation"],
            source="quiz",
            error_count=1,
            mastered=False,
            question_type="choice",
        )
        db.add(wrong)
        await db.commit()

        return AnswerResultResponse(
            correct=False,
            correct_answer=question["correct_answer"],
            explanation=question["explanation"],
            all_completed=False,
            task_completed=False,
        )


@router.get("/review")
async def get_review_questions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """获取今日温故知新（错题复习）"""
    print(f"[DailyLearning] 获取错题复习: user={current_user.id}")

    progress = await _get_or_create_progress(db, current_user.id)

    # 获取该用户所有未掌握的错题
    result = await db.execute(
        select(WrongQuestion).where(
            WrongQuestion.user_id == current_user.id,
            WrongQuestion.mastered == False,
        )
    )
    wrong_questions = result.scalars().all()

    if not wrong_questions:
        # 没有错题，任务三自动完成
        progress.task3_status = 'completed'
        progress.task3_completed_at = datetime.now(timezone.utc)
        progress.total_review = 0
        await db.commit()
        return {
            "questions": [],
            "total": 0,
            "message": "暂无错题需要复习 🎉",
            "task_completed": True,
        }

    # 随机打乱
    random.shuffle(wrong_questions)

    progress.task3_status = 'in_progress'
    progress.total_review = len(wrong_questions)
    progress.current_review_index = 0
    progress.review_question_ids = json.dumps([w.id for w in wrong_questions])
    await db.commit()

    questions = []
    for wq in wrong_questions:
        opts = json.loads(wq.options) if wq.options else None
        questions.append(ReviewQuestion(
            id=wq.id,
            question_text=wq.question_text,
            options=opts,
            correct_answer=wq.correct_answer,
            explanation=wq.explanation,
            knowledge=progress.node_name or "数据结构",
        ))

    return {
        "questions": questions,
        "total": len(questions),
        "node_name": progress.node_name or "数据结构",
    }


@router.post("/answer-review")
async def submit_review_answer(
    req: ReviewSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """提交错题复习答案"""
    print(f"[DailyLearning] 提交复习答案: user={current_user.id}, wrong_q_id={req.wrong_question_id}")

    progress = await _get_or_create_progress(db, current_user.id)

    result = await db.execute(
        select(WrongQuestion).where(
            WrongQuestion.id == req.wrong_question_id,
            WrongQuestion.user_id == current_user.id,
        )
    )
    wq = result.scalar_one_or_none()
    if not wq:
        raise HTTPException(status_code=404, detail="错题记录不存在")

    correct = req.user_answer.strip() == wq.correct_answer.strip()

    if correct:
        wq.mastered = True
        wq.reviewed_count = (wq.reviewed_count or 0) + 1
        progress.reviewed_count = (progress.reviewed_count or 0) + 1
        progress.current_review_index = (progress.current_review_index or 0) + 1

        # 检查所有错题是否已掌握
        remaining = await db.execute(
            select(sa_func.count(WrongQuestion.id)).where(
                WrongQuestion.user_id == current_user.id,
                WrongQuestion.mastered == False,
            )
        )
        remaining_count = remaining.scalar() or 0

        all_completed = remaining_count == 0
        if all_completed:
            progress.task3_status = 'completed'
            progress.task3_completed_at = datetime.now(timezone.utc)

        await db.commit()

        return ReviewResultResponse(
            correct=True,
            correct_answer=wq.correct_answer,
            explanation=wq.explanation,
            mastered=True,
            all_completed=all_completed,
        )
    else:
        wq.error_count = (wq.error_count or 0) + 1
        wq.user_answer = req.user_answer
        await db.commit()

        return ReviewResultResponse(
            correct=False,
            correct_answer=wq.correct_answer,
            explanation=wq.explanation,
            mastered=False,
            all_completed=False,
        )


@router.post("/update-task")
async def update_task_status(
    req: TaskUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """AI 主动更新任务状态（例如检测到知识点名称后调用）"""
    print(f"[DailyLearning] 更新任务状态: user={current_user.id}, task={req.task_type}, status={req.status}")

    progress = await _get_or_create_progress(db, current_user.id)
    now = datetime.now(timezone.utc)

    if req.task_type == "task1":
        progress.task1_status = req.status
        if req.status == "completed":
            progress.task1_completed_at = now
    elif req.task_type == "task2":
        progress.task2_status = req.status
        if req.status == "completed":
            progress.task2_completed_at = now
    elif req.task_type == "task3":
        progress.task3_status = req.status
        if req.status == "completed":
            progress.task3_completed_at = now
    else:
        raise HTTPException(status_code=400, detail="无效的任务类型")

    await db.commit()
    return _build_task_status(progress)


@router.get("/prompt")
async def get_daily_learning_prompt():
    """获取每日学习任务系统提示（用于 LLM system prompt）"""
    prompt_path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))), 'prompts', 'daily_learning_task.md')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"prompt": content}
    except FileNotFoundError:
        print(f"[DailyLearning] 提示文件不存在: {prompt_path}")
        return {"prompt": ""}


@router.get("/full-status")
async def get_full_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_required_user),
):
    """获取完整进度（含前三题预览、错题数）"""
    progress = await _get_or_create_progress(db, current_user.id)
    questions = _get_questions_for_node(progress.node_name or "队列")

    # 错题数
    wrong_count = await db.execute(
        select(sa_func.count(WrongQuestion.id)).where(
            WrongQuestion.user_id == current_user.id,
            WrongQuestion.mastered == False,
        )
    )
    wrong_total = wrong_count.scalar() or 0

    return {
        "task": _build_task_status(progress).dict(),
        "preview_questions": [{
            "id": q["id"],
            "question": q["question"],
        } for q in questions[:3]],
        "wrong_question_count": wrong_total,
        "today_knowledge": progress.node_name or "队列",
    }
