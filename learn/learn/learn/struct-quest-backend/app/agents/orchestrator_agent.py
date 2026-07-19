"""
Orchestrator Agent（总控Agent）— 系统的流程大脑
==============================================

定位：导演，不是演员。
职责：判断下一步应该让谁工作。不负责回答问题。

输入：所有用户事件（注册/登录/开始学习/完成测试/提问/完成学习/点击推荐/生成资源）
输出：调度决策（下一个 Agent 是谁，或者等待用户）

设计原则：
- Agent 不直接互相调用，全部通过 Orchestrator 调度
- 两级决策：规则派发表（快速免费）+ LLM 动态路由（兜底）
- 每次 Agent 执行完都回到 Orchestrator 重新评估

工作流示例：
  用户注册 → Orchestrator → ProfileAgent → 返回 Orchestrator
  Orchestrator → PlannerAgent → ResourceAgent → 返回 Orchestrator
  等待用户完成测试...

  用户提问 → Orchestrator → 判断是问答 → TutorAgent → 返回 Orchestrator
"""

import json
from typing import Dict, Any, List, Optional

from app.agents.base import BaseAgent
from app.agents.state import LearningState, EventType
from app.utils.logger import get_logger

logger = get_logger("orchestrator")


# ══════════════════════════════════════════════════
#  事件 → 工作流映射表（规则引擎）
# ══════════════════════════════════════════════════

WORKFLOW_MAP: Dict[str, List[str]] = {
    # ── 首次注册：建立画像 + 生成初始测试 ──
    EventType.USER_REGISTERED: [
        "profile_agent",         # ① 建立初始画像
        "assessment_agent",      # ② 生成初始测试
    ],

    # ★ 诊断测试完成 → 全面分析 + 画像 + 规划 + 推荐 ──
    "diagnostic_completed": [
        "learning_analytics_agent",   # ① 分析诊断数据
        "profile_agent",              # ② 更新画像（含诊断掌握度）
        "planner_agent",              # ③ 规划学习路径
        "resource_agent",             # ④ 准备首次资源
        "recommendation_agent",       # ⑤ 生成首页推荐
    ],

    # ★ 引导完成（初始画像已生成）→ 规划 + 资源 + 推荐 ──
    "onboarding_completed": [
        "planner_agent",              # ① 基于初始画像规划路径
        "resource_agent",             # ② 生成首批学习资源
        "recommendation_agent",       # ③ 首页推荐
    ],

    # ★ 资源被查看 → 记录行为 ──
    "resource_viewed": [
        "learning_analytics_agent",   # ① 更新行为分析
    ],

    # ★ 练习完成 → 测评 + 分析 + 画像更新 ──
    "practice_completed": [
        "assessment_agent",           # ① 评估答题结果
        "learning_analytics_agent",   # ② 分析学习指标变化
        "profile_agent",              # ③ 更新画像
        "recommendation_agent",       # ④ 刷新推荐
    ],

    # ── 登录：快速分析 + 刷新推荐 ──
    EventType.USER_LOGIN: [
        "learning_analytics_agent",   # ① 分析学习数据
        "recommendation_agent",       # ② 刷新首页推荐
    ],

    # ── 开始学习（完整流程）──
    EventType.START_LEARNING: [
        "learning_analytics_agent",   # ① 分析当前状态
        "profile_agent",              # ② 更新画像
        "planner_agent",              # ③ 规划路径
        "resource_agent",             # ④ 准备资源
        "recommendation_agent",       # ⑤ 生成推荐
    ],

    # ── 完成测试：评估 → 更新画像 → 调整路径 ──
    EventType.COMPLETE_TEST: [
        "assessment_agent",           # ① 评估测试结果
        "learning_analytics_agent",   # ② 分析学习指标变化
        "profile_agent",              # ③ 更新画像
        "planner_agent",              # ④ 调整学习路径
        "recommendation_agent",       # ⑤ 刷新推荐
    ],

    # ── 提交答案：单次评估 ──
    EventType.SUBMIT_ANSWER: [
        "assessment_agent",           # ① 评估答案
    ],

    # ── 提问：先获取画像→再辅导回答（v4 多模态）──
    EventType.ASK_QUESTION: [
        "profile_agent",              # ① 获取/更新最新画像（供格式决策使用）
        "tutor_agent",                # ② 辅导回答（含格式决策+多模态资源生成）
    ],

    # ── 完成学习：全面分析 + 更新 ──
    EventType.COMPLETE_LEARNING: [
        "learning_analytics_agent",   # ① 分析学习数据
        "profile_agent",              # ② 更新画像
        "recommendation_agent",       # ③ 刷新推荐
    ],

    # ── 点击推荐：刷新推荐 ──
    EventType.CLICK_RECOMMENDATION: [
        "recommendation_agent",       # ① 基于点击行为调整推荐
    ],

    # ── 生成资源（通用）──
    EventType.GENERATE_RESOURCE: [
        "resource_agent",             # ① 根据 payload 生成资源
    ],

    # ── 按需生成特定资源 ──
    EventType.REQUEST_MINDMAP: [
        "resource_agent",             # ① 仅生成思维导图
    ],
    EventType.REQUEST_CODE: [
        "resource_agent",             # ① 仅生成代码案例
    ],
    EventType.REQUEST_ANIMATION: [
        "resource_agent",             # ① 仅生成动画
    ],
    EventType.REQUEST_EXERCISE: [
        "resource_agent",             # ① 仅生成练习题
    ],

    # ── 每日打卡 ──
    EventType.DAILY_CHECKIN: [
        "learning_analytics_agent",   # ① 分析每日数据
        "recommendation_agent",       # ② 每日推荐
    ],

    # ── 继续会话（LLM 动态决策）──
    EventType.CONTINUE_SESSION: [],    # 由 LLM 动态决定
}


# ══════════════════════════════════════════════════
#  调度后处理：根据上一个 Agent 产出决定后续
# ══════════════════════════════════════════════════

# 如果某个 Agent 执行完后需要根据结果动态调整，在这里处理
POST_AGENT_ADJUSTMENTS = {
    "assessment_agent": {
        "score_below_40": ["planner_agent", "resource_agent"],   # 严重不及格 → 重规划
        "score_40_to_80": ["resource_agent"],                    # 及格 → 准备下一步资源
        "score_above_80": ["recommendation_agent"],              # 优秀 → 刷新推荐，等待用户
    },
}


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator（总控Agent）— 系统的流程大脑

    不回答问题、不分析数据、不生成资源。
    只做一件事：判断下一步应该让谁工作。
    """

    @property
    def name(self) -> str:
        return "orchestrator"

    @property
    def description(self) -> str:
        return "多智能体系统总控 — 根据用户事件判断下一步调度哪个 Agent"

    # ═══════════════════════════════════════════
    #  核心 run 方法
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        event_type = state.get("event_type", EventType.START_LEARNING)
        event_payload = state.get("event_payload", {})
        pending = list(state.get("pending_agents", []))

        logger.info("[Orchestrator] 事件: %s | 待执行: %s | 阶段: %s",
                     event_type, pending, state.get("session_phase", "?"))

        # ── 判断是否为重入（Agent 已完成返回）──
        is_reentry = self._is_reentry(state)

        # ── 情况1：有待执行的 Agent 队列（Agent 刚执行完回来）──
        if pending:
            return self._handle_pending_queue(state, pending, event_type)

        # ── 情况2：重入（无 pending，已执行过）──
        if is_reentry:
            logger.info("[Orchestrator] 工作流已全部执行，进入后处理")
            return self._decide_post_workflow(state, event_type)

        # ── 情况3：全新事件 ──
        return self._handle_new_event(state, event_type, event_payload)

    def _is_reentry(self, state: LearningState) -> bool:
        """检测是否为重入（已有 Agent 执行过）"""
        messages = state.get("messages", [])
        for msg in reversed(messages):
            agent = msg.get("agent", "")
            if agent and agent != "orchestrator":
                return True
        # 也检查各 Agent 产出是否非空（但不检查从 DB 加载的画像和聊天回复）
        if state.get("learning_analytics"):
            return True
        return False

    # ═══════════════════════════════════════════
    #  处理待执行队列
    # ═══════════════════════════════════════════

    def _handle_pending_queue(
        self, state: LearningState, pending: List[str], event_type: str
    ) -> Dict[str, Any]:
        """Agent 执行完回到 Orchestrator，从队列中取出下一个"""
        # 检查是否需要根据上一个 Agent 的产出调整队列
        last_agent = self._detect_last_agent(state, pending)

        if last_agent and last_agent in POST_AGENT_ADJUSTMENTS:
            adjusted = self._apply_post_adjustment(state, last_agent)
            if adjusted is not None:
                pending = adjusted
                logger.info("[Orchestrator] 根据 %s 产出调整队列: %s", last_agent, pending)

        # 队列已空 → 工作流完成
        if not pending:
            return self._decide_post_workflow(state, event_type)

        # 取出下一个 Agent
        next_agent = pending[0]
        remaining = pending[1:] if len(pending) > 1 else []

        return self._dispatch_agent(next_agent, remaining, state,
                                     f"执行工作流: {' → '.join([next_agent] + remaining[:2])}")

    def _detect_last_agent(self, state: LearningState, pending: List[str]) -> Optional[str]:
        """推断上一个执行的 Agent（通过检查哪个产出最近更新了）"""
        # 简单策略：检查 messages 中最近的 agent 日志
        messages = state.get("messages", [])
        for msg in reversed(messages):
            agent_name = msg.get("agent", "")
            if agent_name and agent_name != "orchestrator":
                return agent_name
        return None

    def _apply_post_adjustment(
        self, state: LearningState, last_agent: str
    ) -> Optional[List[str]]:
        """根据 Agent 产出动态调整后续队列 + 写入调整记录"""
        if last_agent == "assessment_agent":
            assessment = state.get("assessment", {})
            # 兼容新旧格式
            score = assessment.get("overall_score", 0)
            if isinstance(score, dict):
                score = score.get("overall_score", 0)
            score = float(score) if score else 0

            adjustments = POST_AGENT_ADJUSTMENTS["assessment_agent"]
            iteration = state.get("iteration_count", 0)
            max_iter = state.get("max_iterations", 5)

            result = None
            adjust_type = None
            adjust_reason = None

            if score < 40 and iteration < max_iter:
                result = adjustments["score_below_40"]
                adjust_type = "path_reroute"
                adjust_reason = f"测评得分 {score} 分（<40），严重不及格，触发路径重规划"
            elif score < 80:
                result = adjustments["score_40_to_80"]
                adjust_type = "resource_type_change"
                adjust_reason = f"测评得分 {score} 分（40-80），调整后续资源以适应水平"
            else:
                result = adjustments["score_above_80"]
                adjust_type = None  # 不需要记录

            # ★ v5: 写入资源调整记录（异步，不阻塞主流程）
            if adjust_type:
                self._log_adjustment(state, adjust_type, adjust_reason, score)

            return result

        return None

    def _log_adjustment(
        self, state: LearningState, adjust_type: str, reason: str, score: float
    ):
        """异步写入调整记录到数据库（失败不影响主流程）"""
        try:
            import asyncio
            from app.db.session import AsyncSessionLocal
            from app.models.resource_adjustment import ResourceAdjustment
            from datetime import datetime, timezone

            user_id_str = state.get("user_id", "0")
            try:
                user_id = int(user_id_str)
            except (ValueError, TypeError):
                return

            # 获取当前路径信息
            learning_path = state.get("learning_path", [])
            current_step = learning_path[0] if learning_path else {}

            from_value = {
                "topic": current_step.get("topic", ""),
                "score": score,
            }
            to_value = {
                "adjustment": adjust_type,
            }

            async def _write():
                async with AsyncSessionLocal() as db:
                    adj = ResourceAdjustment(
                        user_id=user_id,
                        adjustment_type=adjust_type,
                        from_value=from_value,
                        to_value=to_value,
                        trigger_event="assessment_score",
                        reason=reason,
                        metric_name="score",
                        metric_before=score,
                    )
                    db.add(adj)
                    await db.commit()

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_write())
                else:
                    loop.run_until_complete(_write())
            except RuntimeError:
                # 没有事件循环，尝试同步
                try:
                    asyncio.run(_write())
                except Exception:
                    pass

        except Exception as e:
            logger.debug(f"[Orchestrator] 调整记录写入失败（非关键）: {e}")

    # ═══════════════════════════════════════════
    #  处理新事件
    # ═══════════════════════════════════════════

    def _handle_new_event(
        self, state: LearningState, event_type: str, event_payload: Dict
    ) -> Dict[str, Any]:
        """新事件到达，查表派发工作流"""

        # 已有画像 → 跳过 onboarding 阶段
        profile = state.get("student_profile", {})
        if profile and profile.get("ability_level"):
            phase = "learning_active"
        else:
            phase = "onboarding"

        # 查表
        workflow = WORKFLOW_MAP.get(event_type)

        if workflow is None:
            # 未知事件 → LLM 动态决策
            logger.info("[Orchestrator] 未知事件类型 '%s'，使用 LLM 决策", event_type)
            return self._llm_decide(state, event_type, event_payload)

        if not workflow:
            # 空工作流（如 continue_session）→ LLM 决策
            return self._llm_decide(state, event_type, event_payload)

        # 派发工作流中的第一个 Agent
        first_agent = workflow[0]
        remaining = workflow[1:] if len(workflow) > 1 else []

        logger.info("[Orchestrator] 事件 '%s' → 派发链: %s", event_type,
                     " → ".join(workflow))

        return self._dispatch_agent(first_agent, remaining, state,
                                     f"事件 {event_type} 触发工作流",
                                     phase=phase)

    # ═══════════════════════════════════════════
    #  工作流完成后决策
    # ═══════════════════════════════════════════

    def _decide_post_workflow(self, state: LearningState, event_type: str) -> Dict[str, Any]:
        """工作流执行完毕，决定：等待用户 / 结束 / 继续循环"""
        assessment = state.get("assessment", {})
        should_adjust = assessment.get("should_adjust_path", False)
        iteration = state.get("iteration_count", 0)
        max_iter = state.get("max_iterations", 5)

        # 迭代上限
        if iteration >= max_iter:
            return self._set_end(state, f"达到最大迭代次数 ({max_iter})")

        # 需要重规划 → 启动重规划子工作流
        if should_adjust and event_type in (EventType.COMPLETE_TEST, EventType.SUBMIT_ANSWER):
            logger.info("[Orchestrator] 需要重规划，启动调整流程")
            return self._dispatch_agent(
                "planner_agent",
                ["resource_agent", "recommendation_agent"],
                state,
                "测评发现薄弱点，重新规划路径"
            )

        # 提问类事件 → 直接结束（返回给用户）
        if event_type == EventType.ASK_QUESTION:
            return self._set_end(state, "问答完成")

        # 资源请求 → 生成完就结束
        if event_type in (EventType.REQUEST_MINDMAP, EventType.REQUEST_CODE,
                          EventType.REQUEST_ANIMATION, EventType.REQUEST_EXERCISE,
                          EventType.GENERATE_RESOURCE):
            return self._set_end(state, "资源生成完成")

        # 默认：等待用户下一步操作
        return self._set_wait(state, "工作流完成，等待用户下一步操作")

    # ═══════════════════════════════════════════
    #  派发与状态设置
    # ═══════════════════════════════════════════

    def _dispatch_agent(
        self, agent_name: str, remaining: List[str], state: LearningState,
        reason: str, phase: str = "learning_active"
    ) -> Dict[str, Any]:
        """派发下一个 Agent"""
        decision = {
            "next_agent": agent_name,
            "reason": reason,
            "wait_for_user": False,
            "remaining_queue": remaining,
        }

        log = self._log(state, f"🎯 派发 → {agent_name} | 原因: {reason}")

        return {
            **log,
            "orchestrator_decision": decision,
            "pending_agents": remaining,
            "next_action": agent_name,
            "session_phase": phase,
        }

    def _set_wait(self, state: LearningState, reason: str) -> Dict[str, Any]:
        """设置等待用户状态"""
        decision = {
            "next_agent": None,
            "reason": reason,
            "wait_for_user": True,
        }

        log = self._log(state, f"⏸️ 等待用户 | {reason}")

        return {
            **log,
            "orchestrator_decision": decision,
            "pending_agents": [],
            "next_action": "wait_for_user",
            "session_phase": "awaiting_user",
        }

    def _set_end(self, state: LearningState, reason: str) -> Dict[str, Any]:
        """设置会话结束"""
        decision = {
            "next_agent": None,
            "reason": reason,
            "wait_for_user": False,
        }

        log = self._log(state, f"✅ 会话结束 | {reason}")

        return {
            **log,
            "orchestrator_decision": decision,
            "pending_agents": [],
            "next_action": "end",
            "session_status": "completed",
            "session_phase": "completed",
        }

    # ═══════════════════════════════════════════
    #  LLM 动态路由（兜底策略）
    # ═══════════════════════════════════════════

    def _llm_decide(
        self, state: LearningState, event_type: str, event_payload: Dict
    ) -> Dict[str, Any]:
        """当规则表无法覆盖时，使用 LLM 决策下一步"""
        available_agents = [
            "profile_agent", "learning_analytics_agent", "planner_agent",
            "resource_agent", "recommendation_agent", "tutor_agent",
            "assessment_agent",
        ]

        # 构建紧凑的状态摘要
        profile = state.get("student_profile", {})
        analytics = state.get("learning_analytics", {})
        path = state.get("learning_path", [])

        summary_parts = [
            f"事件: {event_type}",
            f"会话阶段: {state.get('session_phase', 'unknown')}",
            f"有画像: {bool(profile and profile.get('ability_level'))}",
            f"有分析数据: {bool(analytics)}",
            f"学习路径: {len(path)} 步",
            f"已完成步骤: {sum(1 for s in path if s.get('status') == 'completed')}",
            f"迭代次数: {state.get('iteration_count', 0)}",
        ]

        prompt = f"""你是 StructQuest 多智能体学习系统的总控调度器。

## 当前状态
{chr(10).join(summary_parts)}

## 可用 Agent
{chr(10).join(f'- {a}' for a in available_agents)}

## 事件数据
{json.dumps(event_payload, ensure_ascii=False)[:500]}

请决定下一步应该调度哪个 Agent。返回 JSON:
{{"next_agent": "<agent_name>", "reason": "...", "wait_for_user": false}}
如果应该等待用户输入，设置 wait_for_user 为 true 且 next_agent 为 null。"""

        try:
            response = self._call_llm(
                [{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=300,
            )
            decision = self._parse_json(response)
            agent_name = decision.get("next_agent")
            wait = decision.get("wait_for_user", False)

            if wait or not agent_name:
                return self._set_wait(state, decision.get("reason", "LLM 判断应等待用户"))

            return self._dispatch_agent(
                agent_name, [], state,
                decision.get("reason", "LLM 动态决策")
            )
        except Exception as e:
            logger.warning("[Orchestrator] LLM 决策失败: %s，默认等待用户", e)
            return self._set_wait(state, f"LLM 决策失败 ({e})，默认等待用户")

    # ═══════════════════════════════════════════
    #  降级策略
    # ═══════════════════════════════════════════

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        super().fallback(state, error)
        return self._set_wait(state, f"Orchestrator 降级 ({error})")
