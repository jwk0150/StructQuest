"""
最小 LangGraph 示例 — 状态定义

流程：ProfileAgent → PlannerAgent → END
"""
from typing import TypedDict, List, Dict, Any, Optional


class StudentProfile(TypedDict, total=False):
    """ProfileAgent 的输出：学生画像"""
    ability_level: str          # beginner / intermediate / advanced
    learning_style: str         # visual / auditory / reading / hands_on
    strengths: List[str]        # 擅长领域
    weaknesses: List[str]       # 知识短板
    pace: str                   # fast / moderate / slow
    summary: str                # 画像总结


class LearningStep(TypedDict, total=False):
    """PlannerAgent 的输出：单个学习步骤"""
    step_id: int
    topic: str
    description: str
    difficulty: str             # easy / medium / hard
    estimated_minutes: int
    prerequisites: List[str]


class MinimalState(TypedDict, total=False):
    """
    最小全局状态 — ProfileAgent 和 PlannerAgent 共享

    LangGraph 要求：
    - 所有节点函数接收此 State，返回需要更新的字段
    - 返回的 dict 会自动 merge 到 State 中
    """
    # ── 输入 ──
    subject: str                # 学科
    goal: str                   # 学习目标

    # ── Agent 产出 ──
    profile: StudentProfile     # ProfileAgent → 填充
    plan: List[LearningStep]    # PlannerAgent → 填充

    # ── 控制字段 ──
    messages: List[Dict[str, Any]]  # Agent 日志


def create_initial_state(subject: str, goal: str) -> MinimalState:
    """创建初始状态"""
    return {
        "subject": subject,
        "goal": goal,
        "profile": {},
        "plan": [],
        "messages": [],
    }
