"""
最小 LangGraph 示例 — 图编排

流程：START → ProfileAgent → PlannerAgent → END

使用最新 LangGraph 写法：
- StateGraph(StateSchema)
- add_node(name, func)
- add_edge(START, node) / add_edge(node, END)
- compile() → invoke()
"""
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from app.minimal_langgraph.state import MinimalState, create_initial_state
from app.minimal_langgraph.profile_agent import ProfileAgent
from app.minimal_langgraph.planner_agent import PlannerAgent


# ══════════════════════════════════════════
#  Agent 实例化
# ══════════════════════════════════════════

profile_agent = ProfileAgent()
planner_agent = PlannerAgent()


# ══════════════════════════════════════════
#  图构建
# ══════════════════════════════════════════

def build_minimal_graph():
    """
    构建最小 LangGraph：
    
    START → ProfileAgent → PlannerAgent → END
    
    Returns:
        CompiledGraph — 可调用 .invoke(state)
    """
    workflow = StateGraph(MinimalState)

    # 添加节点（每个节点是一个可调用对象，接收 state，返回更新字段）
    workflow.add_node("profile_agent", profile_agent)
    workflow.add_node("planner_agent", planner_agent)

    # 添加边
    workflow.add_edge(START, "profile_agent")         # 入口 → 画像
    workflow.add_edge("profile_agent", "planner_agent")  # 画像 → 规划
    workflow.add_edge("planner_agent", END)            # 规划 → 结束

    # 编译
    compiled = workflow.compile()
    return compiled


# ══════════════════════════════════════════
#  便捷运行函数
# ══════════════════════════════════════════

def run_minimal_session(subject: str, goal: str) -> Dict[str, Any]:
    """
    一站式运行最小示例
    
    用法:
        result = run_minimal_session("数据结构", "掌握链表和树")
        print(result["profile"]["ability_level"])
        for step in result["plan"]:
            print(f"  {step['step_id']}. {step['topic']}")
    """
    graph = build_minimal_graph()
    initial_state = create_initial_state(subject, goal)

    print(f"\n{'='*50}")
    print(f"  [START] 最小 LangGraph 示例")
    print(f"  学科: {subject}")
    print(f"  目标: {goal}")
    print(f"{'='*50}\n")

    final_state = graph.invoke(initial_state)

    print(f"\n{'='*50}")
    print(f"  [DONE] 执行完成")
    print(f"  画像: {final_state.get('profile', {}).get('ability_level', 'N/A')}")
    print(f"  路径: {len(final_state.get('plan', []))} 步")
    print(f"{'='*50}\n")

    return final_state
