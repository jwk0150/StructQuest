"""
LangGraph 图编排引擎（v3 — Orchestrator 星型拓扑）
==================================================

核心架构变更：
  旧：固定线性管道 profile → behavior → ... → assessment → loop
  新：Orchestrator 中心化星型拓扑

拓扑结构：
                          ┌──────────────────────┐
                          │   🧠 Orchestrator     │  ← 流程大脑
                          └──────────┬───────────┘
                                     │
     ┌──────────┬──────────┬──────────┼──────────┬──────────┬──────────┐
     ▼          ▼          ▼          ▼          ▼          ▼          ▼
  profile  learning    planner   resource  recommendation  tutor   assessment
  _agent   _analytics  _agent    _agent    _agent          _agent   _agent
     │          │          │          │          │          │          │
     └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
                                     │
                          (所有 Agent 返回 Orchestrator)

原则：Agent 不直接互相调用，全部通过 Orchestrator 调度。
"""

import time
from typing import Dict, Any, List, Optional

from app.agents.state import LearningState, create_initial_state, EventType
from app.agents.orchestrator_agent import OrchestratorAgent
from app.agents.profile_agent import ProfileAgent
from app.agents.learning_analytics_agent import LearningAnalyticsAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.resource_agent import ResourceGenerationAgent
from app.agents.recommendation_agent import RecommendationAgent
from app.agents.tutor_agent import TutorAgent
from app.agents.assessment_agent import AssessmentAgent
from app.agents.base import BaseAgent
from app.utils.logger import get_logger

logger = get_logger("graph")


# ================================================================
#                     Agent 实例化（单例）
# ================================================================

REGISTERED_AGENTS: Dict[str, BaseAgent] = {}


def _get_or_create_agents() -> Dict[str, BaseAgent]:
    """懒加载 Agent 实例（单例模式）"""
    if not REGISTERED_AGENTS:
        REGISTERED_AGENTS.update({
            "orchestrator": OrchestratorAgent(),
            "profile_agent": ProfileAgent(),
            "learning_analytics_agent": LearningAnalyticsAgent(),
            "planner_agent": PlannerAgent(),
            "resource_agent": ResourceGenerationAgent(),
            "recommendation_agent": RecommendationAgent(),
            "tutor_agent": TutorAgent(),
            "assessment_agent": AssessmentAgent(),
        })
    return REGISTERED_AGENTS


# ================================================================
#                   LangGraph 节点函数
# ================================================================

def node_orchestrator(state: LearningState) -> Dict[str, Any]:
    """总控节点 — 所有会话从这里开始"""
    agent = _get_or_create_agents()["orchestrator"]
    logger.info("🧠 [Orchestrator] 流程调度中...")
    decision = agent.run(state)
    return decision


def node_profile(state: LearningState) -> Dict[str, Any]:
    """画像分析节点"""
    agent = _get_or_create_agents()["profile_agent"]
    logger.info("📊 [Profile] 维护学生画像...")
    state = _preload_rag_context(state)
    return agent.run(state)


def node_learning_analytics(state: LearningState) -> Dict[str, Any]:
    """学习分析节点"""
    agent = _get_or_create_agents()["learning_analytics_agent"]
    logger.info("📈 [LearningAnalytics] 分析学习数据...")
    return agent.run(state)


def node_planner(state: LearningState) -> Dict[str, Any]:
    """路径规划节点"""
    agent = _get_or_create_agents()["planner_agent"]
    logger.info("📋 [Planner] 规划学习路径...")
    return agent.run(state)


def node_resource(state: LearningState) -> Dict[str, Any]:
    """资源生成节点"""
    agent = _get_or_create_agents()["resource_agent"]
    logger.info("📦 [Resource] 准备学习资源...")
    return agent.run(state)


def node_recommendation(state: LearningState) -> Dict[str, Any]:
    """推荐节点"""
    agent = _get_or_create_agents()["recommendation_agent"]
    logger.info("🎯 [Recommendation] 生成推荐...")
    return agent.run(state)


def node_tutor(state: LearningState) -> Dict[str, Any]:
    """辅导节点"""
    agent = _get_or_create_agents()["tutor_agent"]
    logger.info("👨‍🏫 [Tutor] 辅导问答中...")
    return agent.run(state)


def node_assessment(state: LearningState) -> Dict[str, Any]:
    """测评节点"""
    agent = _get_or_create_agents()["assessment_agent"]
    logger.info("📝 [Assessment] 评估学习效果...")
    return agent.run(state)


# ================================================================
#                   条件路由函数
# ================================================================

def route_from_orchestrator(state: LearningState) -> str:
    """
    Orchestrator 决策后的路由 — 核心路由函数

    读取 orchestrator_decision，决定：
    - 派发到哪个 Agent
    - 等待用户 (wait)
    - 结束会话 (end)
    """
    decision = state.get("orchestrator_decision", {})
    wait = decision.get("wait_for_user", False)

    if wait:
        logger.info("[路由] Orchestrator → 等待用户")
        return "wait"

    pending = state.get("pending_agents", [])
    next_agent = decision.get("next_agent")

    if next_agent and next_agent in _get_or_create_agents():
        logger.info("[路由] Orchestrator → %s", next_agent)
        return next_agent

    # 从 pending 队列取第一个
    if pending:
        first = pending[0]
        if first in _get_or_create_agents():
            logger.info("[路由] Orchestrator → %s (来自队列)", first)
            return first

    # 检查 session_status
    if state.get("session_status") == "completed":
        logger.info("[路由] Orchestrator → 会话结束")
        return "end"

    # 默认：结束
    logger.info("[路由] Orchestrator → 无可用路由，结束")
    return "end"


def route_after_agent(state: LearningState) -> str:
    """
    Agent 执行完后的路由

    所有 Agent 执行完后都回到 Orchestrator 重新评估。
    例外：会话完成 / 等待用户时直接结束。
    """
    session_status = state.get("session_status", "running")
    next_action = state.get("next_action", "")

    if session_status == "completed":
        return "end"

    if next_action == "wait_for_user":
        return "end"

    # ★ 默认：回到 Orchestrator
    return "continue"


# ================================================================
#                  辅助函数
# ================================================================

def _preload_rag_context(state: LearningState) -> LearningState:
    """在需要时预加载 RAG 上下文"""
    subject = state.get("subject", "")
    goal = state.get("current_goal", "")

    if not subject or state.get("rag_context"):
        return state

    try:
        # 简单的 RAG 预加载
        temp_agent = object.__new__(BaseAgent)
        query = f"{subject} {goal} 基础概念 知识点"
        context = temp_agent._retrieve_knowledge(query, top_k=3)

        if context:
            state["rag_context"] = context
            logger.info("RAG 上下文已预加载 (%d 字符)", len(context))
    except Exception as e:
        logger.debug("RAG 预加载跳过: %s", e)

    return state


# ================================================================
#                      图构建器（v3）
# ================================================================

class MultiAgentGraph:
    """
    多智能体学习系统图管理器（v3 — Orchestrator 星型拓扑）

    使用方式：
        graph = MultiAgentGraph()
        result = graph.run(
            subject="数据结构",
            goal="掌握链表操作",
            event_type="start_learning",
        )

    或使用便捷函数：
        result = run_learning_session(event_type="ask_question",
                                       event_payload={"question": "什么是DFS？"})
    """

    VALID_AGENTS = {
        "orchestrator", "profile_agent", "learning_analytics_agent",
        "planner_agent", "resource_agent", "recommendation_agent",
        "tutor_agent", "assessment_agent",
    }

    def __init__(self):
        self._graph = None
        self._compiled = None

    def build(self):
        """构建 LangGraph 有向图（v3 — 星型拓扑）"""
        try:
            from langgraph.graph import StateGraph, START, END
        except ImportError:
            raise ImportError(
                "请先安装 langgraph: pip install langgraph"
            )

        workflow = StateGraph(LearningState)

        # ====== 添加节点 ======
        workflow.add_node("orchestrator", node_orchestrator)
        workflow.add_node("profile_agent", node_profile)
        workflow.add_node("learning_analytics_agent", node_learning_analytics)
        workflow.add_node("planner_agent", node_planner)
        workflow.add_node("resource_agent", node_resource)
        workflow.add_node("recommendation_agent", node_recommendation)
        workflow.add_node("tutor_agent", node_tutor)
        workflow.add_node("assessment_agent", node_assessment)

        # ====== 入口：START → Orchestrator ======
        workflow.add_edge(START, "orchestrator")

        # ====== Orchestrator → 条件路由到任意 Agent ======
        route_targets = {name: name for name in self.VALID_AGENTS if name != "orchestrator"}
        route_targets["wait"] = END
        route_targets["end"] = END

        workflow.add_conditional_edges(
            "orchestrator",
            route_from_orchestrator,
            route_targets,
        )

        # ====== 所有 Agent 执行完后 → 回到 Orchestrator ======
        for agent_name in self.VALID_AGENTS:
            if agent_name == "orchestrator":
                continue
            workflow.add_conditional_edges(
                agent_name,
                route_after_agent,
                {
                    "continue": "orchestrator",
                    "end": END,
                },
            )

        # 编译图
        self._compiled = workflow.compile()
        self._graph = workflow

        logger.info("=" * 55)
        logger.info("StructQuest 多智能体系统 v3 — Orchestrator 星型拓扑")
        logger.info("=" * 55)
        self._print_agent_info()
        return self

    def _print_agent_info(self):
        """打印注册的 Agent 信息"""
        agents_info = [
            ("🧠 Orchestrator",    "流程大脑 — 事件分类 + Agent 调度"),
            ("📊 ProfileAgent",    "学生画像 — 维护 student_profile 表"),
            ("📈 LearningAnalytics","数据分析 — 活跃度/专注度/知识掌握/错误模式"),
            ("📋 PlannerAgent",    "学习规划 — 基于画像和知识图谱规划路径"),
            ("📦 ResourceAgent",   "资源工厂 — 先检索后生成，保存到资源库"),
            ("🎯 Recommendation",  "首页推荐 — 个性化排序与推荐"),
            ("👨‍🏫 TutorAgent",      "学习老师 — 结合画像/知识库/错题辅导"),
            ("📝 AssessmentAgent", "测评反馈 — 布鲁姆六维评估"),
        ]
        logger.info("注册 Agents (%d):", len(agents_info))
        for icon_name, desc in agents_info:
            logger.info("  %s: %s", icon_name, desc)

    def run(
        self,
        subject: str = "",
        goal: str = "",
        user_id: str = "default",
        user_messages: Optional[List[str]] = None,
        event_type: str = EventType.START_LEARNING,
        event_payload: Optional[Dict[str, Any]] = None,
        max_iterations: int = 5,
        existing_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        运行一次事件驱动的学习会话（v3）

        Args:
            subject: 学科主题
            goal: 学习目标
            user_id: 用户标识
            user_messages: 历史消息
            event_type: 事件类型（决定 Orchestrator 如何调度）
            event_payload: 事件携带数据
            max_iterations: 最大迭代次数
            existing_state: 已有会话状态（继续会话时传入）
        """
        if self._compiled is None:
            self.build()

        if existing_state:
            # 继续已有会话
            initial_state = {
                **existing_state,
                "event_type": event_type,
                "event_payload": event_payload or {},
                "session_status": "running",
                "next_action": "orchestrate",
            }
        else:
            initial_state = create_initial_state(
                user_id=user_id,
                subject=subject,
                goal=goal,
                event_type=event_type,
                event_payload=event_payload,
            )

        if user_messages:
            initial_state["user_messages"] = user_messages
        initial_state["max_iterations"] = max_iterations

        start_time = time.time()

        logger.info(
            "[START] 事件驱动会话 | 事件: %s | 学科: %s | 目标: %s | 用户: %s",
            event_type, subject, goal, user_id,
        )

        final_state = self._compiled.invoke(initial_state)

        elapsed = time.time() - start_time
        summary = self._build_summary(final_state, elapsed)

        logger.info(
            "[DONE] 会话完成 | 耗时: %.1fs | 阶段: %s | 路径步数: %d",
            elapsed,
            final_state.get("session_phase", "?"),
            len(final_state.get("learning_path", [])),
        )

        return {**final_state, "_summary": summary}

    @staticmethod
    def _build_summary(state: LearningState, elapsed_seconds: float = 0) -> Dict[str, Any]:
        """构建最终结果摘要"""
        profile = state.get("student_profile", {})
        path = state.get("learning_path", [])
        analytics = state.get("learning_analytics", {})
        recommendation = state.get("recommendation", {})
        decision = state.get("orchestrator_decision", {})

        completed_steps = sum(1 for s in path if s.get("status") == "completed")

        return {
            "user_id": state.get("user_id"),
            "subject": state.get("subject"),
            "goal": state.get("current_goal"),
            "event_type": state.get("event_type"),
            "session_phase": state.get("session_phase", "completed"),
            "session_status": state.get("session_status", "completed"),
            "iterations": state.get("iteration_count", 0),
            "elapsed_seconds": round(elapsed_seconds, 1),
            "orchestrator_reason": decision.get("reason", ""),
            "wait_for_user": decision.get("wait_for_user", False),
            "profile_summary": profile.get("summary", ""),
            "ability_level": profile.get("ability_level", ""),
            "activity_score": analytics.get("activity_score"),
            "focus_score": analytics.get("focus_score"),
            "total_steps": len(path),
            "completed_steps": completed_steps,
            "resource_count": len(state.get("resources", [])),
            "recommendation_count": len(recommendation.get("items", [])),
            "chat_response": state.get("chat_response"),
            "agent_logs": state.get("messages", []),
        }

    # ═══════════════════════════════════════════
    #  图可视化
    # ═══════════════════════════════════════════

    def get_graph_visualization(self) -> Optional[str]:
        """获取图的 Mermaid 可视化字符串（v3）"""
        return '''```mermaid
flowchart TD
    START((🎯 事件)) --> ORC[🧠 Orchestrator<br/>流程大脑]

    ORC -->|注册| PA[📊 Profile<br/>建立画像]
    ORC -->|分析| LA[📈 LearningAnalytics<br/>数据分析]
    ORC -->|规划| PL[📋 Planner<br/>学习路径]
    ORC -->|资源| RA[📦 Resource<br/>资源工厂]
    ORC -->|推荐| RC[🎯 Recommendation<br/>首页推荐]
    ORC -->|提问| TA[👨‍🏫 Tutor<br/>学习辅导]
    ORC -->|测试| AA[📝 Assessment<br/>测评反馈]

    PA --> ORC
    LA --> ORC
    PL --> ORC
    RA --> ORC
    RC --> ORC
    TA --> ORC
    AA --> ORC

    ORC -->|等待用户| WAIT((⏸️ 等待))
    ORC -->|完成| END((🏁 结束))

    style START fill:#4CAF50,color:#fff
    style END fill:#f44336,color:#fff
    style ORC fill:#FF9800,color:#fff
    style PA fill:#2196F3,color:#fff
    style LA fill:#9C27B0,color:#fff
    style PL fill:#00BCD4,color:#fff
    style RA fill:#FF5722,color:#fff
    style RC fill:#E91E63,color:#fff
    style TA fill:#4CAF50,color:#fff
    style AA fill:#607D8B,color:#fff
```'''


# ================================================================
#                    便捷入口函数
# ================================================================

def build_graph() -> MultiAgentGraph:
    """构建并返回图实例（可复用）"""
    return MultiAgentGraph().build()


def run_learning_session(
    subject: str = "",
    goal: str = "",
    user_id: str = "default",
    user_messages: Optional[List[str]] = None,
    max_iterations: int = 5,
    event_type: str = EventType.START_LEARNING,
    event_payload: Optional[Dict[str, Any]] = None,
    existing_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    一站式运行事件驱动学习会话（v3）

    用例:
        # 新用户注册
        result = run_learning_session(
            subject="数据结构", goal="掌握链表",
            event_type="user_registered",
        )

        # 提问
        result = run_learning_session(
            event_type="ask_question",
            event_payload={"question": "什么是DFS？"},
        )

        # 继续会话
        result = run_learning_session(
            event_type="submit_answer",
            event_payload={"answer": "..."},
            existing_state=previous_state,
        )
    """
    graph = MultiAgentGraph()
    return graph.run(
        subject=subject,
        goal=goal,
        user_id=user_id,
        user_messages=user_messages,
        event_type=event_type,
        event_payload=event_payload,
        max_iterations=max_iterations,
        existing_state=existing_state,
    )
