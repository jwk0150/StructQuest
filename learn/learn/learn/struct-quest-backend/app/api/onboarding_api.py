"""
冷启动画像引导 API
==================

四阶段冷启动流程中的第二阶段（学习目标问卷）和第三阶段（诊断测试）的 API 端点。

端点：
- POST /api/onboarding/questionnaire    — 保存学习目标问卷
- GET  /api/onboarding/diagnostic/questions — 获取诊断测试题目
- POST /api/onboarding/diagnostic/submit    — 提交诊断测试结果（含行为数据）
"""
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth import get_required_user
from app.models.user import User
from app.agents.profile_agent import ProfileAgent
from app.agents.state import LearningState
from app.services.learning_record_service import learning_record_service
from app.utils.logger import get_logger

logger = get_logger("api.onboarding")

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


# ════════════════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════════════════

class QuestionnaireRequest(BaseModel):
    """学习目标问卷"""
    learning_purpose: str          # 学习目的：course_preview/daily_study/final_exam/postgraduate/project_practice/algorithm_contest
    preferred_styles: List[str]    # 学习方式偏好（多选）：video/diagram/reading/coding/practice
    daily_study_time: str          # 每天学习时间：15min/30min/1hour/2hours

    @field_validator("learning_purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        allowed = ["course_preview", "daily_study", "final_exam", "postgraduate", "project_practice", "algorithm_contest"]
        if v not in allowed:
            raise ValueError(f"无效的学习目的: {v}，可选值: {allowed}")
        return v

    @field_validator("preferred_styles")
    @classmethod
    def validate_styles(cls, v: List[str]) -> List[str]:
        allowed = ["video", "diagram", "reading", "coding", "practice"]
        for s in v:
            if s not in allowed:
                raise ValueError(f"无效的学习方式: {s}，可选值: {allowed}")
        if len(v) < 1:
            raise ValueError("请至少选择一种学习方式")
        return v

    @field_validator("daily_study_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        allowed = ["15min", "30min", "1hour", "2hours"]
        if v not in allowed:
            raise ValueError(f"无效的学习时间: {v}，可选值: {allowed}")
        return v


class DiagnosticAnswerItem(BaseModel):
    """单道诊断题的答题记录（含行为数据）"""
    question_id: str
    module: str                    # 知识模块：array/linked_list/stack/queue/tree/graph/sorting/searching
    difficulty: int = 1            # 题目难度 1-3
    user_answer: int               # 用户选择的选项索引（0-based）
    correct_answer: int            # 正确答案索引
    is_correct: bool               # 是否答对
    answer_time_ms: int            # 答题耗时（毫秒）
    skip_count: int = 0            # 跳题次数
    modify_count: int = 0          # 修改答案次数


class DiagnosticSubmitRequest(BaseModel):
    """诊断测试提交"""
    answers: List[DiagnosticAnswerItem]
    total_time_ms: int             # 总耗时（毫秒）


class GenerateProfileRequest(BaseModel):
    """请求 AI 生成初始画像"""
    pass  # 所有数据从 User 表和 diagnostic_results 中读取


# ════════════════════════════════════════════════════════
# 诊断测试题库（8 个核心模块 × 3 题 = 24 题）
# ════════════════════════════════════════════════════════

DIAGNOSTIC_QUESTIONS = {
    "array": [
        {
            "id": "diag_arr_1", "difficulty": 1,
            "question": "数组在内存中的存储方式是？",
            "options": ["连续存储", "链式存储", "树形存储", "散列存储"],
            "correct": 0,
            "explanation": "数组元素在内存中连续存放，通过首地址+偏移量可实现 O(1) 随机访问。",
            "knowledge_point": "数组的存储结构"
        },
        {
            "id": "diag_arr_2", "difficulty": 2,
            "question": "在一个长度为 n 的数组中，按下标访问第 i 个元素的时间复杂度是？",
            "options": ["O(1)", "O(log n)", "O(n)", "O(i)"],
            "correct": 0,
            "explanation": "数组支持随机存取，通过基地址+i×元素大小直接计算地址，时间复杂度为 O(1)。",
            "knowledge_point": "数组的随机访问特性"
        },
        {
            "id": "diag_arr_3", "difficulty": 2,
            "question": "在有序数组中插入一个元素并保持有序，时间复杂度是？",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            "correct": 2,
            "explanation": "虽然可以用二分查找 O(log n) 找到插入位置，但插入时需要移动后续元素，整体为 O(n)。",
            "knowledge_point": "数组插入操作的时间复杂度"
        },
    ],
    "linked_list": [
        {
            "id": "diag_ll_1", "difficulty": 1,
            "question": "链表相比数组的主要优势是？",
            "options": ["随机访问快", "内存连续", "插入删除效率高", "占用内存少"],
            "correct": 2,
            "explanation": "链表插入和删除不需要移动元素，只需修改指针，时间复杂度为 O(1)（已知位置时）。",
            "knowledge_point": "链表的优势"
        },
        {
            "id": "diag_ll_2", "difficulty": 2,
            "question": "在单链表中，已知指针 p 指向某节点，删除该节点的后继节点的时间复杂度是？",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n^2)"],
            "correct": 0,
            "explanation": "已知 p，只需修改 p.next = p.next.next，时间复杂度 O(1)。",
            "knowledge_point": "链表的删除操作"
        },
        {
            "id": "diag_ll_3", "difficulty": 3,
            "question": "判断一个单链表是否有环，最优的方法是？",
            "options": ["遍历时记录访问过的节点", "快慢指针（Floyd 判圈）", "反转链表看是否回到起点", "计算链表长度"],
            "correct": 1,
            "explanation": "快慢指针（Floyd 判圈算法）空间复杂度 O(1)，是最优解。快指针每次走两步，慢指针每次走一步，若相遇则有环。",
            "knowledge_point": "链表环检测"
        },
    ],
    "stack": [
        {
            "id": "diag_stk_1", "difficulty": 1,
            "question": "栈的工作原理是？",
            "options": ["先进先出（FIFO）", "后进先出（LIFO）", "按优先级出", "随机出"],
            "correct": 1,
            "explanation": "栈遵循后进先出（LIFO）原则，最后入栈的元素最先出栈。",
            "knowledge_point": "栈的基本原理"
        },
        {
            "id": "diag_stk_2", "difficulty": 2,
            "question": "以下哪个场景最适合使用栈？",
            "options": ["打印队列管理", "函数调用和递归", "搜索引擎索引", "社交网络好友推荐"],
            "correct": 1,
            "explanation": "函数调用使用调用栈（Call Stack）保存返回地址和局部变量，递归也依赖栈实现。",
            "knowledge_point": "栈的应用场景"
        },
        {
            "id": "diag_stk_3", "difficulty": 3,
            "question": "给定入栈序列 1,2,3，以下哪个不可能是出栈序列？",
            "options": ["3,2,1", "1,2,3", "3,1,2", "2,1,3"],
            "correct": 2,
            "explanation": "3,1,2 不可能：3 最先出栈说明 1,2,3 都已入栈，此时栈内从上到下为 3,2,1，3 出栈后栈顶是 2 而不是 1。",
            "knowledge_point": "栈的入栈出栈序列"
        },
    ],
    "queue": [
        {
            "id": "diag_que_1", "difficulty": 1,
            "question": "队列的工作原理是？",
            "options": ["先进先出（FIFO）", "后进先出（LIFO）", "按优先级出", "随机出"],
            "correct": 0,
            "explanation": "队列遵循先进先出（FIFO）原则，最先入队的元素最先出队。",
            "knowledge_point": "队列的基本原理"
        },
        {
            "id": "diag_que_2", "difficulty": 2,
            "question": "广度优先搜索（BFS）使用什么数据结构实现？",
            "options": ["栈", "队列", "堆", "二叉树"],
            "correct": 1,
            "explanation": "BFS 需要按层遍历，先访问的节点其邻接点应该先被处理，使用队列实现。",
            "knowledge_point": "队列在BFS中的应用"
        },
        {
            "id": "diag_que_3", "difficulty": 2,
            "question": "循环队列解决的主要问题是？",
            "options": ["队列速度慢", "假溢出（空间浪费）", "入队出队顺序混乱", "无法存储大量数据"],
            "correct": 1,
            "explanation": "普通顺序队列出队后，front 指针后移，前面空间无法再利用（假溢出）。循环队列通过取模运算让队列空间循环使用。",
            "knowledge_point": "循环队列"
        },
    ],
    "tree": [
        {
            "id": "diag_tree_1", "difficulty": 1,
            "question": "二叉树的第 k 层最多有多少个节点？",
            "options": ["k", "2k", "2^(k-1)", "k^2"],
            "correct": 2,
            "explanation": "二叉树第 i 层最多有 2^(i-1) 个节点，第 k 层即 2^(k-1) 个。",
            "knowledge_point": "二叉树的性质"
        },
        {
            "id": "diag_tree_2", "difficulty": 2,
            "question": "二叉树的中序遍历序列是？",
            "options": ["根→左→右", "左→根→右", "左→右→根", "根→右→左"],
            "correct": 1,
            "explanation": "中序遍历顺序为「左子树 → 根节点 → 右子树」，对于二叉搜索树，中序遍历得到有序序列。",
            "knowledge_point": "二叉树的遍历"
        },
        {
            "id": "diag_tree_3", "difficulty": 3,
            "question": "一棵完全二叉树有 100 个节点，其深度（高度）是？",
            "options": ["6", "7", "8", "10"],
            "correct": 1,
            "explanation": "深度为 k 的完全二叉树节点数在 2^(k-1) 到 2^k-1 之间。2^6=64，2^7-1=127，100 在 [64,127] 之间，深度为 7。",
            "knowledge_point": "完全二叉树的深度计算"
        },
    ],
    "graph": [
        {
            "id": "diag_graph_1", "difficulty": 1,
            "question": "图的广度优先遍历（BFS）使用什么辅助数据结构？",
            "options": ["栈", "队列", "优先队列", "集合"],
            "correct": 1,
            "explanation": "BFS 按距离逐层遍历，先访问的节点的邻接点应先被处理，因此使用队列实现。",
            "knowledge_point": "图的BFS遍历"
        },
        {
            "id": "diag_graph_2", "difficulty": 2,
            "question": "Dijkstra 算法解决什么问题？",
            "options": ["最小生成树", "单源最短路径", "拓扑排序", "最大流"],
            "correct": 1,
            "explanation": "Dijkstra 算法用于解决非负权图中从单个源点到其他所有顶点的最短路径问题。",
            "knowledge_point": "最短路径算法"
        },
        {
            "id": "diag_graph_3", "difficulty": 3,
            "question": "一个有 n 个顶点的连通无向图，最少有多少条边？",
            "options": ["n", "n-1", "n+1", "n(n-1)/2"],
            "correct": 1,
            "explanation": "连通无向图的最少边数 = n-1（即一棵生成树）。再多删一条边图就不再连通。",
            "knowledge_point": "图的连通性"
        },
    ],
    "sorting": [
        {
            "id": "diag_sort_1", "difficulty": 1,
            "question": "以下哪种排序算法是稳定的？",
            "options": ["快速排序", "堆排序", "归并排序", "选择排序"],
            "correct": 2,
            "explanation": "归并排序在合并时保持相等元素的原有顺序，是稳定的 O(n log n) 排序算法。",
            "knowledge_point": "排序的稳定性"
        },
        {
            "id": "diag_sort_2", "difficulty": 2,
            "question": "快速排序的平均时间复杂度是？",
            "options": ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"],
            "correct": 1,
            "explanation": "快速排序平均时间复杂度为 O(n log n)，但在最坏情况下（如已有序数组且选第一个元素为基准）退化为 O(n^2)。",
            "knowledge_point": "快速排序的时间复杂度"
        },
        {
            "id": "diag_sort_3", "difficulty": 3,
            "question": "对 10 万个整数排序，要求稳定且时间复杂度 O(n log n)，最佳选择是？",
            "options": ["快速排序", "堆排序", "归并排序", "插入排序"],
            "correct": 2,
            "explanation": "快速排序不稳定，堆排序不稳定且常数因子大，插入排序是 O(n^2)。归并排序稳定且保证 O(n log n)。",
            "knowledge_point": "排序算法的选择"
        },
    ],
    "searching": [
        {
            "id": "diag_search_1", "difficulty": 1,
            "question": "二分查找的前提条件是？",
            "options": ["数据必须存储在链表中", "数据必须有序", "数据必须是整数", "数据量必须很大"],
            "correct": 1,
            "explanation": "二分查找要求数据有序（通常是升序），并且需要支持随机访问（顺序存储）。",
            "knowledge_point": "二分查找的前提"
        },
        {
            "id": "diag_search_2", "difficulty": 2,
            "question": "哈希表查找的平均时间复杂度是？",
            "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            "correct": 0,
            "explanation": "理想情况下，哈希表通过哈希函数直接定位，平均查找时间复杂度为 O(1)。",
            "knowledge_point": "哈希表的查找效率"
        },
        {
            "id": "diag_search_3", "difficulty": 3,
            "question": "哈希表中「冲突」指的是什么？处理冲突的常用方法不包括？",
            "options": [
                "不同的 key 映射到相同的位置 — 不包括「二分法」",
                "哈希函数计算太慢 — 不包括「链地址法」",
                "数据量太大 — 不包括「开放定址法」",
                "查找失败 — 不包括「再哈希法」"
            ],
            "correct": 0,
            "explanation": "冲突指不同关键字通过哈希函数映射到同一地址。常用解决方法包括链地址法和开放定址法，二分法不是处理冲突的方法。",
            "knowledge_point": "哈希冲突及解决方法"
        },
    ],
}


# ════════════════════════════════════════════════════════
# API 端点
# ════════════════════════════════════════════════════════

@router.post("/questionnaire")
async def save_questionnaire(
    req: QuestionnaireRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """保存学习目标问卷（冷启动第二阶段）"""
    user.learning_purpose = req.learning_purpose
    user.preferred_styles = req.preferred_styles
    user.daily_study_time = req.daily_study_time
    await db.commit()
    await db.refresh(user)

    logger.info(f"用户 {user.username} 完成学习目标问卷: purpose={req.learning_purpose}, styles={req.preferred_styles}")

    return {
        "message": "问卷已保存",
        "learning_purpose": req.learning_purpose,
        "preferred_styles": req.preferred_styles,
        "daily_study_time": req.daily_study_time,
    }


@router.get("/diagnostic/questions")
async def get_diagnostic_questions(
    user: User = Depends(get_required_user),
):
    """获取诊断测试题目（8 个知识模块 × 3 题 = 24 题）

    返回所有题目但不包含正确答案，前端在用户提交后由后端评分。
    """
    questions_for_frontend = {}
    total_count = 0

    for module, qs in DIAGNOSTIC_QUESTIONS.items():
        module_questions = []
        for q in qs:
            total_count += 1
            module_questions.append({
                "id": q["id"],
                "module": module,
                "difficulty": q["difficulty"],
                "question": q["question"],
                "options": q["options"],
                "knowledge_point": q["knowledge_point"],
                # 不返回 correct 和 explanation，前端提交后后端评分
            })
        questions_for_frontend[module] = module_questions

    module_names = {
        "array": "数组", "linked_list": "链表", "stack": "栈",
        "queue": "队列", "tree": "树", "graph": "图",
        "sorting": "排序", "searching": "查找",
    }

    return {
        "modules": [{"key": k, "name": module_names.get(k, k)} for k in DIAGNOSTIC_QUESTIONS.keys()],
        "questions": questions_for_frontend,
        "total_questions": total_count,
        "total_modules": len(DIAGNOSTIC_QUESTIONS),
    }


@router.post("/diagnostic/submit")
async def submit_diagnostic(
    req: DiagnosticSubmitRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """提交诊断测试结果（冷启动第三阶段）

    后端根据题目 ID 查找正确答案并评分，同时记录行为数据。
    """
    # 构建正确答案映射
    correct_map = {}
    for module_qs in DIAGNOSTIC_QUESTIONS.values():
        for q in module_qs:
            correct_map[q["id"]] = {
                "correct": q["correct"],
                "module": q.get("module", ""),
                "difficulty": q.get("difficulty", 1),
                "knowledge_point": q.get("knowledge_point", ""),
            }

    # 评分 + 按模块聚合
    module_stats = {}  # {module: {correct, total, total_time_ms, questions: [...]}}
    total_correct = 0
    total_questions = 0

    for item in req.answers:
        total_questions += 1
        ref = correct_map.get(item.question_id, {})
        actual_correct = ref.get("correct", item.correct_answer)
        module = ref.get("module", item.module)
        is_correct = (item.user_answer == actual_correct)

        if is_correct:
            total_correct += 1

        if module not in module_stats:
            module_stats[module] = {
                "correct": 0, "total": 0, "total_time_ms": 0,
                "questions": [],
            }

        ms = module_stats[module]
        ms["correct"] += 1 if is_correct else 0
        ms["total"] += 1
        ms["total_time_ms"] += item.answer_time_ms
        ms["questions"].append({
            "question_id": item.question_id,
            "knowledge_point": ref.get("knowledge_point", ""),
            "difficulty": ref.get("difficulty", 1),
            "is_correct": is_correct,
            "user_answer": item.user_answer,
            "correct_answer": actual_correct,
            "answer_time_ms": item.answer_time_ms,
            "skip_count": item.skip_count,
            "modify_count": item.modify_count,
        })

    # 计算每个模块的掌握度（正确率 + 时间因素）
    knowledge_mastery = {}
    for module, stats in module_stats.items():
        accuracy = stats["correct"] / max(stats["total"], 1)
        avg_time = stats["total_time_ms"] / max(stats["total"], 1) / 1000  # 转为秒
        # 时间因素：回答快且正确 → 掌握度高；回答慢但正确 → 可能是理解慢
        # 简单公式：accuracy 权重 70%，时间因素 30%
        time_factor = max(0, 1 - (avg_time / 120))  # 假设 120 秒为基准
        mastery_score = round((accuracy * 0.7 + max(0, time_factor) * 0.3) * 100)
        knowledge_mastery[module] = max(0, min(100, mastery_score))

    # 构建诊断结果
    diagnostic_results = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": total_questions,
        "total_correct": total_correct,
        "overall_accuracy": round(total_correct / max(total_questions, 1) * 100, 1),
        "total_time_ms": req.total_time_ms,
        "total_time_seconds": round(req.total_time_ms / 1000, 1),
        "module_stats": module_stats,
        "knowledge_mastery": knowledge_mastery,
        "behavior_summary": {
            "total_skips": sum(a.skip_count for a in req.answers),
            "total_modifies": sum(a.modify_count for a in req.answers),
            "avg_time_per_question_ms": round(req.total_time_ms / max(total_questions, 1)),
        },
    }

    # 保存到用户
    user.diagnostic_results = diagnostic_results
    await db.commit()
    await db.refresh(user)

    module_names = {
        "array": "数组", "linked_list": "链表", "stack": "栈",
        "queue": "队列", "tree": "树", "graph": "图",
        "sorting": "排序", "searching": "查找",
    }
    mastery_display = {module_names.get(k, k): v for k, v in knowledge_mastery.items()}

    logger.info(
        f"用户 {user.username} 完成诊断测试: "
        f"正确率 {diagnostic_results['overall_accuracy']}%, "
        f"掌握度: {mastery_display}"
    )

    return {
        "message": "诊断测试已提交",
        "overall_accuracy": diagnostic_results["overall_accuracy"],
        "total_correct": total_correct,
        "total_questions": total_questions,
        "total_time_seconds": diagnostic_results["total_time_seconds"],
        "knowledge_mastery": mastery_display,
        "module_stats": {
            module_names.get(k, k): {
                "accuracy": round(stats["correct"] / max(stats["total"], 1) * 100),
                "avg_time_seconds": round(stats["total_time_ms"] / max(stats["total"], 1) / 1000, 1),
            }
            for k, stats in module_stats.items()
        },
    }


@router.post("/generate-profile")
async def generate_initial_profile(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """调用 Profile Agent 综合四阶段数据生成初始画像（冷启动第四阶段）

    综合：注册基础信息 + 学习目标问卷 + 诊断测试结果
    """
    # 构建传给 Profile Agent 的状态
    diagnostic = user.diagnostic_results or {}
    preferred_styles = user.preferred_styles or []

    # 学习目的中文映射
    purpose_map = {
        "course_preview": "课程预习",
        "daily_study": "日常学习",
        "final_exam": "期末考试",
        "postgraduate": "考研",
        "project_practice": "项目实践",
        "algorithm_contest": "算法竞赛",
    }
    learning_purpose_cn = purpose_map.get(user.learning_purpose or "", "日常学习")

    # 学习方式中文映射
    style_map = {
        "video": "视频讲解", "diagram": "图解", "reading": "阅读讲义",
        "coding": "动手写代码", "practice": "刷题",
    }
    preferred_cn = [style_map.get(s, s) for s in preferred_styles]

    state: LearningState = {
        "subject": user.course or "数据结构",
        "current_goal": user.learning_goal or learning_purpose_cn,
        "event_type": "initial_profile",
        "event_payload": {
            "major": user.major or "",
            "grade": user.grade or "",
            "course": user.course or "数据结构",
            "learning_goal": user.learning_goal or "",
            "target_score": user.target_score or "",
            "daily_study_time": user.daily_study_time or "",
            "exam_date": user.exam_date or "",
            "learning_purpose": learning_purpose_cn,
            "preferred_styles": preferred_cn,
        },
        "student_profile": {},
    }

    # 如果已有诊断结果，注入掌握度数据
    if diagnostic.get("knowledge_mastery"):
        module_names = {
            "array": "数组", "linked_list": "链表", "stack": "栈",
            "queue": "队列", "tree": "树", "graph": "图",
            "sorting": "排序", "searching": "查找",
        }
        mastery_cn = {module_names.get(k, k): v for k, v in diagnostic["knowledge_mastery"].items()}
        state["diagnostic_mastery"] = mastery_cn
        state["diagnostic_accuracy"] = diagnostic.get("overall_accuracy", 0)
        state["diagnostic_behavior"] = diagnostic.get("behavior_summary", {})

    try:
        agent = ProfileAgent()
        result = agent.run(state)

        profile_data = result.get("student_profile", {})
        if not profile_data:
            profile_data = agent._default_profile(user.course or "数据结构", user.learning_goal or "")

        # 保存到用户
        user.profile_data = profile_data
        user.has_completed_onboarding = True
        await db.commit()
        await db.refresh(user)

        # 创建画像快照
        try:
            await learning_record_service.create_profile_snapshot(
                db=db,
                user_id=user.id,
                profile_data=profile_data,
                source="agent",
                summary=profile_data.get("summary", ""),
            )
        except Exception as e:
            logger.warning("创建画像快照失败: %s", e)

        # ★ 启动 Orchestrator 管线：规划路径 + 生成资源 + 推荐
        orchestrator_result = {}
        try:
            from app.agents.graph import run_learning_session
            orchestrator_result = run_learning_session(
                subject=user.course or "数据结构",
                goal=user.learning_goal or learning_purpose_cn,
                user_id=str(user.id),
                event_type="onboarding_completed",
                event_payload={
                    "major": user.major or "",
                    "grade": user.grade or "",
                    "course": user.course or "数据结构",
                    "learning_purpose": learning_purpose_cn,
                    "daily_study_time": user.daily_study_time or "",
                },
                max_iterations=3,
            )
            logger.info(f"Orchestrator 管线完成: {orchestrator_result.get('_summary', {})}")
        except Exception as e:
            logger.warning("Orchestrator 管线执行失败（非致命）: %s", e)

        logger.info(f"用户 {user.username} 初始画像生成完成: level={profile_data.get('ability_level')}")

        return {
            "message": "初始画像已生成",
            "profile": profile_data,
            "has_completed_onboarding": True,
            "learning_path": orchestrator_result.get("learning_path", []),
            "resources": orchestrator_result.get("resources", []),
            "recommendation": orchestrator_result.get("recommendation", {}),
        }

    except Exception as e:
        logger.error("Profile Agent 调用失败: %s", e)
        # 降级：使用默认画像
        agent = ProfileAgent()
        profile_data = agent._default_profile(user.course or "数据结构", user.learning_goal or "")

        # 注入诊断数据
        if diagnostic.get("knowledge_mastery"):
            module_names = {
                "array": "数组", "linked_list": "链表", "stack": "栈",
                "queue": "队列", "tree": "树", "graph": "图",
                "sorting": "排序", "searching": "查找",
            }
            mastery_cn = {module_names.get(k, k): v for k, v in diagnostic["knowledge_mastery"].items()}
            profile_data["knowledge_mastery"] = mastery_cn

        user.profile_data = profile_data
        user.has_completed_onboarding = True
        await db.commit()

        return {
            "message": "初始画像已生成（降级模式）",
            "profile": profile_data,
            "has_completed_onboarding": True,
        }
