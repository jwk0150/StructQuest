"""每日任务 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel
import random

from app.db.session import get_db
from app.auth import get_required_user
from app.models.user import User
from app.models.daily_task import DailyTask
from app.models.wrong_question import WrongQuestion
from app.models.knowledge_graph import KnowledgeNode
from app.services.ability_service import ability_service

router = APIRouter(prefix="/api/daily-tasks", tags=["daily-tasks"])

class UpdateTaskStatusRequest(BaseModel):
    task_id: int
    status: str
    progress: Optional[int] = None

class SubmitPracticeRequest(BaseModel):
    answers: List[dict]  # [{question_id, answer, is_correct, question_text, options, correct_answer, explanation, question_type}]

# ═══ 知识节点ID列表，用于随机抽取每日学习主题 ═══
_ALL_NODE_IDS = [
    'ch01_data_concept', 'ch01_data_type', 'ch01_adt', 'ch01_algorithm',
    'ch02_seq_list', 'ch02_linked_list', 'ch02_doubly_list', 'ch02_circular_list', 'ch02_static_list',
    'ch03_stack_basic', 'ch03_seq_stack', 'ch03_chain_stack', 'ch03_queue_basic', 'ch03_circular_queue', 'ch03_chain_queue',
    'ch04_string', 'ch04_pattern_match', 'ch04_array', 'ch04_sparse_matrix', 'ch04_generalized_list',
    'ch05_tree_basic', 'ch05_binary_tree', 'ch05_tree_traversal', 'ch05_threaded_tree', 'ch05_huffman',
    'ch06_graph_concept', 'ch06_graph_storage', 'ch06_dfs', 'ch06_bfs', 'ch06_mst', 'ch06_shortest_path', 'ch06_topo_sort',
    'ch07_seq_search', 'ch07_binary_search', 'ch07_block_search', 'ch07_bst_search', 'ch07_hash_search',
    'ch08_insert_sort', 'ch08_shell_sort', 'ch08_bubble_sort', 'ch08_quick_sort', 'ch08_selection_sort', 'ch08_heap_sort', 'ch08_merge_sort', 'ch08_radix_sort',
]

# ═══ 简单任务的AI提示模板 ═══
_AI_PROMPTS = {
    'ch01_data_concept': '请详细讲解数据结构的基本概念，包括逻辑结构、存储结构、数据运算三要素，并举生活实例说明。',
    'ch01_data_type': '请详细讲解数据类型的概念，包括基本数据类型和构造数据类型的区别，以及typedef的用法。',
    'ch01_adt': '请详细讲解抽象数据类型ADT的概念、三元组表示法，以及封装和信息隐蔽的思想。',
    'ch01_algorithm': '请详细讲解算法的五大特性，以及时间复杂度和空间复杂度的分析方法。',
    'ch02_seq_list': '请详细讲解顺序表的存储结构、随机存取特性、插入删除操作的时间复杂度分析。',
    'ch02_linked_list': '请详细讲解单链表的定义、头插法和尾插法的实现、以及指针操作的关键点。',
    'ch02_doubly_list': '请详细讲解双向链表的结构、前驱后继指针、双向遍历的优势。',
    'ch02_circular_list': '请详细讲解循环链表的结构特点、与单链表的区别、约瑟夫问题的解法。',
    'ch02_static_list': '请详细讲解静态链表的概念、游标实现原理、备用链表的管理方式。',
    'ch03_stack_basic': '请详细讲解栈的基本概念、LIFO特性、栈顶栈底、进栈出栈操作。',
    'ch03_seq_stack': '请详细讲解顺序栈的实现、栈顶指针操作、栈满栈空判断。',
    'ch03_chain_stack': '请详细讲解链栈的实现、头插法与入栈出栈的关系。',
    'ch03_queue_basic': '请详细讲解队列的基本概念、FIFO特性、队头队尾、入队出队操作。',
    'ch03_circular_queue': '请详细讲解循环队列的设计思想、假溢出问题、取模运算、队空队满判断条件。',
    'ch03_chain_queue': '请详细讲解链队列的实现、队头队尾指针的维护。',
    'ch04_string': '请详细讲解串（字符串）的基本概念、定长顺序存储和堆分配存储的区别。',
    'ch04_pattern_match': '请详细讲解KMP算法的核心思想、next数组的推导过程、时间复杂度分析。',
    'ch04_array': '请详细讲解多维数组的存储方式、行优先和列优先的地址计算公式。',
    'ch04_sparse_matrix': '请详细讲解稀疏矩阵的三元组存储、十字链表、快速转置算法。',
    'ch04_generalized_list': '请详细讲解广义表的定义、表头表尾运算、递归特性、深度计算。',
    'ch05_tree_basic': '请详细讲解树的基本概念、结点的度、树的深度、树与森林的转换规则。',
    'ch05_binary_tree': '请详细讲解二叉树的性质、满二叉树、完全二叉树、顺序存储和链式存储。',
    'ch05_tree_traversal': '请详细讲解二叉树的前序、中序、后序、层序四种遍历方式，并给出递归和迭代实现。',
    'ch05_threaded_tree': '请详细讲解线索二叉树的概念、ltag/rtag标志位、中序线索化过程。',
    'ch05_huffman': '请详细讲解哈夫曼树的构造算法、WPL计算、哈夫曼编码的前缀特性。',
    'ch06_graph_concept': '请详细讲解图的基本概念、有向图和无向图、顶点的度、连通分量。',
    'ch06_graph_storage': '请详细讲解邻接矩阵和邻接表两种存储结构、空间复杂度对比、适用场景。',
    'ch06_dfs': '请详细讲解DFS深度优先搜索的原理、递归和栈实现、连通分量检测。',
    'ch06_bfs': '请详细讲解BFS广度优先搜索的原理、队列实现、最短路径应用。',
    'ch06_mst': '请详细讲解最小生成树的概念、Prim算法和Kruskal算法的原理与对比。',
    'ch06_shortest_path': '请详细讲解Dijkstra算法和Floyd算法的原理、贪心与动态规划思想。',
    'ch06_topo_sort': '请详细讲解拓扑排序的概念、Kahn算法、DFS实现、环检测原理。',
    'ch07_seq_search': '请详细讲解顺序查找的原理、ASL计算、哨兵优化技巧。',
    'ch07_binary_search': '请详细讲解折半查找的原理、判定树、平均查找长度计算。',
    'ch07_block_search': '请详细讲解分块查找的原理、索引表设计、ASL分析。',
    'ch07_bst_search': '请详细讲解二叉排序树的定义、查找插入删除操作、中序有序特性。',
    'ch07_hash_search': '请详细讲解哈希查找的原理、哈希函数设计、冲突处理方法、装填因子。',
    'ch08_insert_sort': '请详细讲解直接插入排序的原理、稳定性分析、最好最坏时间复杂度。',
    'ch08_shell_sort': '请详细讲解希尔排序的原理、增量序列选择、不稳定性的原因。',
    'ch08_bubble_sort': '请详细讲解冒泡排序的原理、优化标志位、稳定性分析。',
    'ch08_quick_sort': '请详细讲解快速排序的分治思想、基准选择、划分算法、最坏情况优化。',
    'ch08_selection_sort': '请详细讲解简单选择排序的原理、交换次数最少的特点。',
    'ch08_heap_sort': '请详细讲解堆排序的原理、建堆过程、堆调整、时间复杂度分析。',
    'ch08_merge_sort': '请详细讲解归并排序的分治合并思想、稳定性、空间复杂度。',
    'ch08_radix_sort': '请详细讲解基数排序的LSD和MSD方式、非比较排序的优势、时间复杂度。',
}

def _get_default_prompt(node_id, node_title):
    return f'请详细讲解{node_title}的核心概念、原理和应用，并给出代码示例。'

@router.get("/today")
async def get_today_tasks(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日任务列表，如果今天还没有任务则自动生成"""
    today = date.today()
    
    # 查询今天已有的任务
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.user_id == user.id,
            DailyTask.task_date == today,
        ).order_by(DailyTask.id)
    )
    existing_tasks = result.scalars().all()
    
    if existing_tasks:
        return {"tasks": [_task_to_dict(t) for t in existing_tasks], "generated": False}
    
    # 没有任务 → 自动生成
    tasks = await _generate_tasks(db, user.id, today)
    return {"tasks": tasks, "generated": True}


@router.post("/refresh")
async def refresh_tasks(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """刷新今日任务（删除旧任务，重新生成）"""
    today = date.today()
    
    # 删除今天已有的未完成任务
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.user_id == user.id,
            DailyTask.task_date == today,
        )
    )
    old_tasks = result.scalars().all()
    for t in old_tasks:
        await db.delete(t)
    await db.commit()
    
    # 重新生成
    tasks = await _generate_tasks(db, user.id, today)
    return {"tasks": tasks, "refreshed": True}


@router.post("/{task_id}/status")
async def update_task_status(
    task_id: int,
    req: UpdateTaskStatusRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """更新任务状态"""
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.id == task_id,
            DailyTask.user_id == user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task.status = req.status
    if req.progress is not None:
        task.progress = req.progress
    if req.status == 'completed':
        task.completed_at = datetime.utcnow()
        task.progress = 100
    
    await db.commit()
    
    # 任务完成后更新能力值
    if req.status == 'completed':
        await ability_service.on_event(db, user.id, 'task_completed', {
            'task_type': task.task_type,
            'task_title': task.task_title,
        })
    
    return _task_to_dict(task)


@router.get("/practice-questions")
async def get_practice_questions(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日练习题目（3道针对当天学习主题的题目）"""
    today = date.today()
    
    # 找到今天的 simple 任务确定知识点
    result = await db.execute(
        select(DailyTask).where(
            DailyTask.user_id == user.id,
            DailyTask.task_date == today,
            DailyTask.task_type == 'simple',
        )
    )
    simple_task = result.scalar_one_or_none()
    node_id = simple_task.target_node_id if simple_task else None
    
    # 从 NODE_EXAMS 取题
    from app.api.exam_api import NODE_EXAMS, DEFAULT_EXAM
    node_exam = NODE_EXAMS.get(node_id) if node_id else None
    if node_exam:
        all_questions = node_exam.get("questions", [])
        questions = random.sample(all_questions, min(3, len(all_questions)))
    else:
        # fallback 随机取
        all_exam_keys = list(NODE_EXAMS.keys())
        random.shuffle(all_exam_keys)
        questions = []
        for key in all_exam_keys:
            qs = NODE_EXAMS[key].get("questions", [])
            for q in qs:
                questions.append(q)
                if len(questions) >= 3:
                    break
            if len(questions) >= 3:
                break
    
    # 返回给前端时不包含正确答案
    result_questions = []
    for q in questions[:3]:
        result_questions.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
        })
    
    return {"questions": result_questions, "total": len(result_questions)}


@router.post("/practice-submit")
async def submit_practice(
    req: SubmitPracticeRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """提交今日练习答案"""
    correct_count = 0
    total = len(req.answers)
    wrong_items = []
    
    for answer in req.answers:
        if answer.get("is_correct"):
            correct_count += 1
        else:
            # 记录错题到 WrongQuestion 表
            wrong_items.append({
                "question": answer.get("question_text", ""),
                "answer": str(answer.get("correct_answer", "")),
                "user_answer": str(answer.get("answer", "")),
                "explanation": answer.get("explanation", ""),
                "options": answer.get("options", []),
                "question_type": answer.get("question_type", "choice"),
            })
    
    # 保存错题
    for item in wrong_items:
        result = await db.execute(
            select(WrongQuestion).where(
                WrongQuestion.user_id == user.id,
                WrongQuestion.question_text == item["question"],
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.error_count = (existing.error_count or 0) + 1
            existing.last_reviewed_at = datetime.utcnow()
            existing.mastered = False
        else:
            wq = WrongQuestion(
                user_id=user.id,
                node_id="daily_practice",
                question_text=item["question"],
                correct_answer=item["answer"],
                user_answer=item["user_answer"],
                explanation=item.get("explanation", ""),
                options=str(item.get("options", [])),
                source="quiz",
                error_count=1,
                mastered=False,
                question_type=item.get("question_type", "choice"),
            )
            db.add(wq)
    
    # 更新能力值
    if correct_count > 0:
        await ability_service.on_event(db, user.id, 'exam_passed', {
            'score': correct_count / max(total, 1) * 100,
        })
    
    await db.commit()
    
    return {
        "score": round(correct_count / max(total, 1) * 100, 1),
        "correct_count": correct_count,
        "total": total,
        "wrong_items_count": len(wrong_items),
    }


@router.get("/review-questions")
async def get_review_questions(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日重温任务的错题（随机取3题）"""
    result = await db.execute(
        select(WrongQuestion).where(
            WrongQuestion.user_id == user.id,
            WrongQuestion.mastered == False,
        ).order_by(WrongQuestion.last_reviewed_at.asc().nullsfirst())
    )
    all_wrong = result.scalars().all()
    
    total = len(all_wrong)
    if total == 0:
        return {"questions": [], "total": 0, "message": "没有需要复习的错题"}
    
    # 随机选最多3题
    selected = random.sample(all_wrong, min(3, total))
    questions = []
    for wq in selected:
        questions.append({
            "id": wq.id,
            "question": wq.question_text,
            "options": wq.options,
            "correct_answer": wq.correct_answer,
            "explanation": wq.explanation,
            "question_type": wq.question_type,
            "source": wq.source,
        })
    
    return {"questions": questions, "total": len(questions)}


@router.post("/review-submit")
async def submit_review(
    req: SubmitPracticeRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """提交重温任务的答案"""
    for answer in req.answers:
        qid = answer.get("question_id")
        if not qid:
            continue
        is_correct = answer.get("is_correct", False)
        
        result = await db.execute(
            select(WrongQuestion).where(
                WrongQuestion.id == qid,
                WrongQuestion.user_id == user.id,
            )
        )
        wq = result.scalar_one_or_none()
        if not wq:
            continue
        
        if is_correct:
            # 答对：降低错误次数
            wq.error_count = max(0, (wq.error_count or 0) - 1)
            wq.reviewed_count = (wq.reviewed_count or 0) + 1
            wq.last_reviewed_at = datetime.utcnow()
            # 连续答对2次或错误次数降至0 → 标记已掌握
            if wq.error_count <= 0 or wq.reviewed_count >= 2:
                wq.mastered = True
        else:
            wq.error_count = (wq.error_count or 0) + 1
            wq.last_reviewed_at = datetime.utcnow()
    
    await db.commit()
    return {"message": "复习记录已保存"}


async def _generate_tasks(db, user_id: int, task_date: date) -> List[dict]:
    """生成今日3个任务并保存到数据库"""
    import random
    tasks = []
    
    # 1. 简单任务：随机选一个未学习的知识点
    result = await db.execute(
        select(KnowledgeNode).order_by(KnowledgeNode.order_index)
    )
    all_nodes = result.scalars().all()
    
    if all_nodes:
        node = random.choice(all_nodes)
    else:
        node = None
    
    node_id = node.id if node else 'ch01_data_concept'
    node_title = node.title if node else '数据结构基本概念'
    prompt = _AI_PROMPTS.get(node_id, _get_default_prompt(node_id, node_title))
    
    # 创建简单任务
    simple = DailyTask(
        user_id=user_id,
        task_date=task_date,
        task_type='simple',
        task_title=f'学习 {node_title}',
        task_description='向AI提问并学习指定知识点，完成学习后即可完成任务。',
        estimated_time='10分钟',
        status='pending',
        progress=0,
        target_node_id=node_id,
        ai_prompt=prompt,
    )
    db.add(simple)
    tasks.append(simple)
    
    # 2. 拔高任务
    advanced = DailyTask(
        user_id=user_id,
        task_date=task_date,
        task_type='advanced',
        task_title=f'{node_title} 练习',
        task_description='完成3道关于该知识点的练习题，检测掌握程度。',
        estimated_time='10分钟',
        status='pending',
        progress=0,
        target_node_id=node_id,
    )
    db.add(advanced)
    tasks.append(advanced)
    
    # 3. 重温任务：检查错题库
    wrong_count = 0
    try:
        wrong_result = await db.execute(
            select(WrongQuestion).where(
                WrongQuestion.user_id == user_id,
                WrongQuestion.mastered == False,
            )
        )
        wrong_count = len(wrong_result.scalars().all())
    except Exception:
        pass
    
    if wrong_count > 0:
        review_title = f'错题复习（{wrong_count}题待复习）'
        review_desc = f'你还有 {wrong_count} 道错题需要复习，随机抽取题目进行巩固。'
    else:
        review_title = '错题复习'
        review_desc = '当前没有需要复习的错题，任务自动完成。'
    
    review = DailyTask(
        user_id=user_id,
        task_date=task_date,
        task_type='review',
        task_title=review_title,
        task_description=review_desc,
        estimated_time='5分钟',
        status='completed' if wrong_count == 0 else 'pending',
        progress=100 if wrong_count == 0 else 0,
    )
    db.add(review)
    tasks.append(review)
    
    await db.commit()
    
    # 刷新获取完整数据
    result = []
    for t in tasks:
        await db.refresh(t)
        result.append(_task_to_dict(t))
    
    return result


def _task_to_dict(task: DailyTask) -> dict:
    return {
        "id": task.id,
        "task_type": task.task_type,
        "task_title": task.task_title,
        "task_description": task.task_description,
        "estimated_time": task.estimated_time,
        "status": task.status,
        "progress": task.progress,
        "target_node_id": task.target_node_id,
        "ai_prompt": task.ai_prompt,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
