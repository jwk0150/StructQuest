"""
Planner Agent（学习规划师）— v3
============================

定位：学习规划师。根据学生画像、知识图谱、课程和考试时间规划个性化学习路径。

输入：
  - 学生画像（掌握度、薄弱点、学习节奏）
  - 知识图谱（章节结构、前置依赖）
  - 考试时间 / 学习目标

核心功能：
  - 自适应难度螺旋
  - 知识点依赖图谱（前置关系链）
  - 如果学习进度快 → 跳过基础，进入强化
  - 如果掌握度低 → 回退重规划

输出：learning_path（学习路径步骤列表）
"""

import json
from typing import Dict, Any, List, Optional

from app.agents.base import BaseAgent
from app.agents.state import LearningState, PathStep
from app.utils.logger import get_logger

logger = get_logger("planner_agent")


# ══════════════════════════════════════════════════
#  Prompt 模板
# ══════════════════════════════════════════════════

PLANNING_PROMPT = """你是一位资深的教学设计专家和课程架构师。
请根据学生画像和学习目标，制定个性化的学习路径。

## 学习目标
{goal}

## 学科领域
{subject}

## 学生画像
{profile}

## 知识掌握度
{knowledge_mastery}

## 已完成的步骤
{completed_steps}

## 考试时间约束
{exam_constraint}

## 知识图谱参考
{knowledge_graph}

## 规划要求

### 数量控制
- 3~8 个步骤，根据目标复杂度灵活调整
- 如果学生已掌握某知识点（掌握度 > 80），跳过对应步骤

### 认知规律
- 从基础到进阶，遵循布鲁姆认知层次
- 每个步骤是可独立完成的学习单元

### 难度螺旋（S型曲线）
- easy → medium → hard → medium → hard
- 避免连续 hard 步骤导致认知过载
- 在 medium 步骤中安排巩固环节

### 时间分配
- 总计不超过 {total_time} 分钟
- 短板相关步骤额外增加20%的时间
- 根据学习节奏调整：突击型=压缩15%，持续型=标准，碎片型=每步不超过20分钟

### 依赖关系
- prerequisites 必须形成有效的前置链（DAG，无环）
- 如果调整路径，标注 [调整] 并说明原因

### 动态调整
- 如果学生快于预期 → 跳过基础，进入强化
- 如果测评分数 < 40 → 回退重学前置知识

返回 JSON：
```json
{{
    "steps": [
        {{
            "step_id": 1,
            "topic": "步骤名称",
            "description": "详细说明",
            "difficulty": "easy|medium|hard",
            "bloom_level": "remember|understand|apply|analyze|evaluate|create",
            "estimated_minutes": 预计耗时(数字),
            "prerequisites": ["前置知识点"],
            "status": "pending",
            "resources_generated": false,
            "teaching_hint": "针对该学生的教学建议"
        }}
    ],
    "planning_rationale": "整体路径设计思路(100字以内)",
    "difficulty_distribution": "难度分布说明",
    "daily_schedule": "每日学习建议"
}}
```
只返回 JSON，不要其他内容。"""


class PlannerAgent(BaseAgent):
    """
    学习规划师 Agent v3

    替代旧版 PathPlanningAgent。新增：
    - 掌握度驱动的动态跳过
    - 学习节奏适配
    - 考试时间约束
    - 每日学习日程建议
    """

    @property
    def name(self) -> str:
        return "planner_agent"

    @property
    def description(self) -> str:
        return "学习规划师 — 基于画像和知识图谱规划个性化学习路径"

    # ═══════════════════════════════════════════
    #  核心 run 方法
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        logger.info("📋 开始规划学习路径...")

        goal = state.get("current_goal", "")
        subject = state.get("subject", "通用")
        profile = state.get("student_profile", {})
        analytics = state.get("learning_analytics", {})
        existing_path = state.get("learning_path", [])
        assessment = state.get("assessment", {})
        event_payload = state.get("event_payload", {})

        # ── 提取已完成步骤 ──
        completed_steps = self._extract_completed(existing_path)

        # ── 合并知识掌握度（画像 + 分析数据）──
        knowledge_mastery = self._merge_knowledge_mastery(profile, analytics)

        # ── 计算时间预算 ──
        total_time = self._calc_time_budget(profile, analytics, event_payload)

        # ── 检查是否需要调整（测评结果）──
        adjustment_request = self._build_adjustment(assessment, profile)

        # ── 构建知识图谱上下文 ──
        knowledge_graph = self._build_knowledge_context(state)

        # ── 考试约束 ──
        exam_constraint = event_payload.get("exam_days", "") or "无考试时间约束"

        prompt = self._build_system_prompt(
            PLANNING_PROMPT,
            goal=goal,
            subject=subject,
            profile=json.dumps(self._compact_profile(profile), ensure_ascii=False, indent=2),
            knowledge_mastery=json.dumps(knowledge_mastery, ensure_ascii=False),
            completed_steps=completed_steps or "无（首次规划）",
            exam_constraint=str(exam_constraint),
            knowledge_graph=knowledge_graph or "无可用知识图谱",
            total_time=int(total_time),
        )

        try:
            response = self._call_llm(
                [{"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=3500,
            )
            path_data = self._parse_json(response)
            steps = self._normalize_steps(
                path_data.get("steps", []),
                offset=len(completed_steps.split("\n")) if completed_steps else 0,
                knowledge_mastery=knowledge_mastery,
            )
            rationale = path_data.get("planning_rationale", "")
            daily_schedule = path_data.get("daily_schedule", "")
        except Exception as e:
            logger.warning("LLM 规划失败: %s，使用模板路径", e)
            steps = self._fallback_path(goal, subject, len(existing_path), knowledge_mastery)
            rationale = "使用默认模板路径（LLM 不可用）"
            daily_schedule = "每日完成1-2个学习步骤"

        # ── 判断是首次规划还是调整 ──
        is_adjustment = bool(adjustment_request)
        iteration = state.get("iteration_count", 0) + (1 if is_adjustment else 0)

        # ── 日志 ──
        action = "🔄 调整路径" if is_adjustment else "📋 制定路径"
        log = self._log(
            state,
            f"{action}: {len(steps)} 步 | "
            f"{' → '.join([s['topic'][:8] for s in steps[:4]])}"
            + ("..." if len(steps) > 4 else "")
            + f" | 总时长: {sum(s.get('estimated_minutes', 15) for s in steps)}分钟"
        )

        return {
            **log,
            "learning_path": steps,
            "next_action": "orchestrate",
            "iteration_count": iteration,
        }

    # ═══════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════

    def _extract_completed(self, path: List[Dict]) -> str:
        """提取已完成步骤摘要"""
        lines = []
        for step in path:
            if step.get("status") == "completed":
                score = step.get("score", "N/A")
                lines.append(f"- {step['topic']} (得分: {score})")
        return "\n".join(lines)

    def _merge_knowledge_mastery(
        self, profile: Dict, analytics: Dict
    ) -> Dict[str, float]:
        """合并画像和分析数据中的知识掌握度"""
        mastery = dict(profile.get("knowledge_mastery", {}))
        analytics_mastery = analytics.get("knowledge_mastery", {})
        mastery.update(analytics_mastery)
        return mastery

    def _calc_time_budget(
        self, profile: Dict, analytics: Dict, payload: Dict
    ) -> float:
        """计算动态时间预算"""
        base_time = 120  # 默认 120 分钟

        rhythm = profile.get("learning_rhythm",
                  analytics.get("learning_rhythm", "持续型"))

        if rhythm == "突击型":
            base_time = 90  # 高强度压缩
        elif rhythm == "碎片型":
            base_time = 150  # 分散学习需要更多总时间

        # 考试约束
        exam_days = payload.get("exam_days")
        if exam_days:
            try:
                days = int(exam_days)
                if days <= 7:
                    base_time = min(base_time, days * 20)  # 紧急备考
            except (ValueError, TypeError):
                pass

        # 注意力约束
        attention = profile.get("attention_span", 25)
        return min(base_time, max(60, attention * 5))

    def _build_adjustment(self, assessment: Dict, profile: Dict) -> str:
        """构建调整请求"""
        if not assessment or not assessment.get("should_adjust_path"):
            return ""

        score = assessment.get("overall_score", 0)
        if isinstance(score, dict):
            score = score.get("overall_score", 0)
        score = float(score) if score else 0

        gaps = assessment.get("gaps_found", [])
        gap_details = assessment.get("gap_details", [])

        lines = [f"⚠️ 上次测评得分: {score}/100"]

        for gd in gap_details[:3]:
            lines.append(
                f"- {gd.get('gap', gd.get('topic', '?'))} "
                f"[{gd.get('severity', '?')}] "
                f"原因: {gd.get('cause', gd.get('possible_cause', '?'))}"
            )

        if not gap_details and gaps:
            lines.extend(f"- {g}" for g in gaps[:3])

        if score < 40:
            lines.append("需要回退重学前置知识")
        elif score < 80:
            lines.append("需要微调难度和重点")

        return "\n".join(lines)

    def _build_knowledge_context(self, state: LearningState) -> str:
        """构建知识图谱上下文"""
        rag_ctx = state.get("rag_context")
        if rag_ctx and len(rag_ctx) > 50:
            return f"[RAG知识背景]\n{rag_ctx[:1200]}"

        subject = state.get("subject", "")
        goal = state.get("current_goal", "")
        query = f"{subject} {goal} 知识点体系 结构 依赖关系"
        retrieved = self._retrieve_knowledge(query, top_k=2)
        if retrieved:
            return f"[RAG检索]\n{retrieved[:1000]}"

        return ""

    @staticmethod
    def _compact_profile(profile: Dict) -> Dict:
        """压缩画像为 prompt 友好的格式"""
        return {
            "ability_level": profile.get("ability_level"),
            "learning_style": profile.get("learning_style"),
            "pace": profile.get("pace"),
            "learning_rhythm": profile.get("learning_rhythm"),
            "strengths": profile.get("strengths", [])[:5],
            "weaknesses": profile.get("weaknesses", [])[:5],
            "focus_score": profile.get("focus_score"),
            "error_patterns": profile.get("error_patterns", [])[:3],
        }

    def _normalize_steps(
        self, raw_steps: List[Dict], offset: int = 0,
        knowledge_mastery: Dict[str, float] = None,
    ) -> List[Dict]:
        """标准化步骤数据"""
        knowledge_mastery = knowledge_mastery or {}
        bloom_levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        valid_difficulties = {"easy", "medium", "hard"}

        normalized = []
        for i, step in enumerate(raw_steps):
            s = dict(step)
            s["step_id"] = s.get("step_id", offset + i + 1)
            s.setdefault("status", "pending")
            s.setdefault("resources_generated", False)
            s.setdefault("score", None)
            s.setdefault("teaching_hint", "")

            # 检查是否已掌握 → 标记跳过
            topic = s.get("topic", "")
            if topic in knowledge_mastery and knowledge_mastery[topic] >= 80:
                s["status"] = "skipped"
                s["score"] = knowledge_mastery[topic]

            # 校验 difficulty
            if s.get("difficulty") not in valid_difficulties:
                s["difficulty"] = "medium"

            # 校验 bloom_level
            bloom = s.get("bloom_level", "understand").lower()
            if bloom not in bloom_levels:
                diff_map = {"easy": "remember", "medium": "apply", "hard": "analyze"}
                bloom = diff_map.get(s["difficulty"], "understand")
            s["bloom_level"] = bloom

            s.setdefault("prerequisites", [])
            normalized.append(s)

        return normalized

    # ═══════════════════════════════════════════
    #  降级路径
    # ═══════════════════════════════════════════

    def _fallback_path(
        self, goal: str, subject: str, offset: int = 0,
        knowledge_mastery: Dict[str, float] = None,
    ) -> List[Dict]:
        """LLM 不可用时的模板路径（5步标准模板）"""
        knowledge_mastery = knowledge_mastery or {}
        base_id = offset + 1

        template_steps = [
            {
                "topic": f"{subject}基础概念与术语",
                "description": f"建立{subject}的核心概念框架",
                "difficulty": "easy",
                "bloom_level": "remember",
                "estimated_minutes": 15,
                "prerequisites": [],
                "teaching_hint": "使用类比和图示",
            },
            {
                "topic": f"{subject}核心方法与操作",
                "description": f"掌握{subject}的主要方法和算法流程",
                "difficulty": "medium",
                "bloom_level": "understand",
                "estimated_minutes": 20,
                "prerequisites": [f"{subject}基础概念与术语"],
                "teaching_hint": "配合代码示例逐步讲解",
            },
            {
                "topic": f"{subject}动手实践练习",
                "description": "通过编程练习巩固所学知识",
                "difficulty": "medium",
                "bloom_level": "apply",
                "estimated_minutes": 25,
                "prerequisites": [f"{subject}核心方法与操作"],
                "teaching_hint": "由简到繁，逐步增加复杂度",
            },
            {
                "topic": f"{subject}进阶分析与优化",
                "description": f"深入分析{subject}的性能特点",
                "difficulty": "hard",
                "bloom_level": "analyze",
                "estimated_minutes": 20,
                "prerequisites": [f"{subject}动手实践练习"],
                "teaching_hint": "引入真实案例对比分析",
            },
            {
                "topic": "综合项目实战",
                "description": f"综合所学完成: {goal}",
                "difficulty": "hard",
                "bloom_level": "create",
                "estimated_minutes": 25,
                "prerequisites": [f"{subject}进阶分析与优化"],
                "teaching_hint": "鼓励自主设计和实现",
            },
        ]

        normalized = []
        for i, step in enumerate(template_steps):
            s = dict(step)
            s["step_id"] = base_id + i
            s["status"] = "pending"
            s["resources_generated"] = False
            s["score"] = None

            # 跳过已掌握的
            topic = s.get("topic", "")
            if topic in knowledge_mastery and knowledge_mastery[topic] >= 80:
                s["status"] = "skipped"
                s["score"] = knowledge_mastery[topic]

            normalized.append(s)

        return normalized

    # ═══════════════════════════════════════════
    #  降级策略
    # ═══════════════════════════════════════════

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        super().fallback(state, error)
        goal = state.get("current_goal", "")
        subject = state.get("subject", "通用")
        offset = len(state.get("learning_path", []))
        knowledge_mastery = state.get("student_profile", {}).get("knowledge_mastery", {})
        return {
            "next_action": "orchestrate",
            "learning_path": self._fallback_path(goal, subject, offset, knowledge_mastery),
        }
