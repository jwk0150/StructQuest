"""
StructQuest 多智能体学习系统 v3 — Orchestrator 中心化架构
==========================================================

Agent 体系（8 个）：

  🧠 Orchestrator           — 流程大脑（事件分类 + Agent 调度）
  📊 ProfileAgent           — 学生画像（维护 student_profile 表）
  📈 LearningAnalyticsAgent — 数据分析中心（活跃度/专注度/知识掌握/错误模式）
  📋 PlannerAgent           — 学习规划师（基于画像+知识图谱规划路径）
  📦 ResourceAgent          — 资源工厂（先检索后生成，保存到资源库）
  🎯 RecommendationAgent    — 首页推荐（个性化排序与推荐）
  👨‍🏫 TutorAgent             — 学习老师（结合画像/知识库/错题辅导）
  📝 AssessmentAgent        — 测评反馈（布鲁姆六维评估）

核心原则：
  - Agent 不直接互相调用，全部通过 Orchestrator 调度
  - 数据驱动闭环：行为 → Analytics → Profile → Planner → Resource → Recommendation → Tutor

模块说明：
  - state.py                   全局共享状态定义
  - base.py                    Agent 基类
  - orchestrator_agent.py      总控调度 Agent
  - profile_agent.py           学生画像 Agent
  - learning_analytics_agent.py 数据分析 Agent
  - planner_agent.py           学习规划 Agent
  - resource_agent.py          资源生成 Agent
  - recommendation_agent.py    推荐 Agent
  - tutor_agent.py             辅导 Agent
  - assessment_agent.py        测评 Agent
  - graph.py                   LangGraph 编排引擎（星型拓扑）
"""

from app.agents.graph import MultiAgentGraph, build_graph, run_learning_session
from app.agents.state import (
    LearningState, EventType,
    StudentProfile, LearningAnalytics, PathStep,
    ResourceItem, ResourceBundle,
    RecommendationItem, RecommendationResult,
    TutorResponse, CognitiveProfile,
    create_initial_state,
)
from app.agents.orchestrator_agent import OrchestratorAgent
from app.agents.profile_agent import ProfileAgent
from app.agents.learning_analytics_agent import LearningAnalyticsAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.resource_agent import ResourceGenerationAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.tutor_agent import TutorAgent
from app.agents.assessment_agent import AssessmentAgent

__all__ = [
    # 图编排
    "MultiAgentGraph",
    "build_graph",
    "run_learning_session",

    # 状态
    "LearningState",
    "EventType",
    "StudentProfile",
    "LearningAnalytics",
    "PathStep",
    "ResourceItem",
    "ResourceBundle",
    "RecommendationItem",
    "RecommendationResult",
    "TutorResponse",
    "CognitiveProfile",
    "create_initial_state",

    # Agent 类
    "OrchestratorAgent",
    "ProfileAgent",
    "LearningAnalyticsAgent",
    "PlannerAgent",
    "ResourceGenerationAgent",
    "RecommendationAgent",
    "TutorAgent",
    "AssessmentAgent",
]
