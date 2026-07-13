"""
学习路径规划 Agent（增强版）
============================

核心职责：
  1. 根据学生画像和学习目标，规划个性化学习路线
  2. 将大目标拆解为可执行的学习步骤（3~8个）
  3. 构建知识点依赖图谱（前置关系链）
  4. 自适应难度螺旋（根据认知画像调整难度分布）
  5. 动态时间分配（注意力时长/学习节奏/短板权重）
  6. 支持动态调整（根据测评反馈回退/重规划）

增强点（v2）：
- 知识点依赖图谱：每步明确前置依赖，形成 DAG
- 布鲁姆层级标注：每个步骤对应认知层级
- 难度螺旋策略：S型曲线分布，避免疲劳
- 认知适配时间分配：慢节奏+高例子需求 → 更多时间
- 调整模式：微调(slight) / 重构(rebuild) / 补漏(remedial)
"""
import json
from typing import Dict, Any, List, Optional

from app.agents.base import BaseAgent
from app.agents.state import LearningState, PathStep
from app.utils.logger import get_logger

logger = get_logger("path_agent")


# ════════════════════════════════════════════
#  Prompt 模板
# ════════════════════════════════════════════

PATH_PLANNING_PROMPT = """你是一位资深的教学设计专家和课程架构师。
请根据学生画像和学习目标，制定一份详细的个性化学习路径。

## 学习目标
{goal}

## 学科领域
{subject}

## 学生画像（深度分析结果）
{profile}

## 已完成的历史步骤
{completed_steps}

## 测评调整需求（如果有）
{adjustment_request}

## 知识点领域参考图谱（RAG检索到的结构化知识）
{knowledge_graph}

请以 JSON 格式输出完整的学习路径：

```json
{{
    "steps": [
        {{
            "step_id": 1,
            "topic": "步骤名称",
            "description": "详细说明这一步学什么、为什么重要",
            "difficulty": "easy|medium|hard",
            "bloom_level": "remember|understand|apply|analyze|evaluate|create",
            "estimated_minutes": 预计耗时(数字),
            "prerequisites": ["前置知识点1", "前置知识点2"],
            "status": "pending",
            "resources_generated": false,
            "teaching_hint": "针对该学生的教学建议"
        }}
    ],
    "planning_rationale": "整体路径设计思路说明(100字以内)",
    "difficulty_distribution": "描述难度如何分布(如: 先易后难, S型曲线等)"
}}
```

### 规划核心原则

**数量控制**：3~8 个步骤，根据目标复杂度灵活调整

**认知规律**：
- 从基础到进阶，遵循布鲁姆认知层次（先 remember→understand，再 apply→analyze，最后 evaluate→create）
- 每个步骤是可独立完成的单元

**难度螺旋**：
- 采用(波浪式)难度分布：easy → medium → hard → medium → hard
- 避免连续 hard 步骤导致认知过载
- 在 medium 步骤中安排巩固环节

**时间分配策略**：
- 总计不超过 {total_time_limit} 分钟
- 根据学生节奏调整：slow=增加30%, fast=压缩20%
- 高 concrete_example_need 的学生，实践类步骤多分配时间
- 短板相关步骤额外增加20%的时间

**依赖关系**：
- prerequisites 必须形成有效的前置链（DAG，无环）
- 如果调整路径，标注 [调整] 并说明原因

**布鲁姆层级**：
- 初学者多用 remember / understand / apply
- 中高级加入 analyze / evaluate / create
- 与 cognitive.preferred_depth 对齐

**只输出 JSON，不要其他内容。"""


class PathPlanningAgent(BaseAgent):
    """学习路径规划 Agent v2 — 个性化路线 + 依赖图谱 + 动态调整"""

    @property
    def name(self) -> str:
        return "path_agent"

    @property
    def description(self) -> str:
        return "根据学生画像规划学习路线，构建知识依赖图谱，支持动态调整"

    # ═══════════════════════════════════════════
    #  核心 run 方法
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        logger.info("开始规划学习路径...")

        goal = state.get("current_goal", "")
        subject = state.get("subject", "通用")
        profile: Dict = state.get("student_profile", {})
        existing_path: List[PathStep] = state.get("learning_path", [])
        assessment: Dict = state.get("assessment", {})

        # 提取已完成步骤
        completed_steps = self._extract_completed_steps(existing_path)

        # 判断是否需要调整 + 计算时间预算
        adjustment_request, total_time_limit = self._build_adjustment_request(
            assessment, profile
        )

        # 构建 RAG 知识图谱上下文
        knowledge_graph = self._build_knowledge_graph_context(state)

        prompt = self._build_system_prompt(
            PATH_PLANNING_PROMPT,
            goal=goal,
            subject=subject,
            profile=json.dumps(profile, ensure_ascii=False, indent=2),
            completed_steps=completed_steps or "无（首次规划）",
            adjustment_request=adjustment_request or "无（首次规划）",
            knowledge_graph=knowledge_graph or "无可用知识图谱",
            total_time_limit=int(total_time_limit),
        )

        messages = [
            {"role": "system", "content": (
                "你是一位经验丰富的课程设计师和教育心理学家。\n"
                "你的专长包括：\n"
                "- 布鲁姆认知分类学应用\n"
                "- 认知负荷理论\n"
                "- 知识图谱与依赖关系建模\n"
                "- 自适应学习路径设计\n\n"
                "路径需要科学、合理、个性化，符合教育学原理。"
            )},
            {"role": "user", "content": prompt},
        ]

        try:
            response_text = self._call_llm(messages, temperature=0.7, max_tokens=3500)
            path_data = self._parse_json(response_text)
            steps = self._normalize_steps(path_data.get("steps", []), offset=len(completed_steps))
        except Exception as e:
            logger.warning("LLM 调用失败: %s，使用模板路径", e)
            steps = self._fallback_path(goal, subject, len(existing_path))

        is_adjustment = bool(adjustment_request)
        action_type = "🔄 调整学习路径" if is_adjustment else "📋 制定学习路径"

        log_entry = self._log(
            state,
            f"{action_type}: 共 {len(steps)} 步 | "
            f"{' → '.join([s['topic'][:8] for s in steps[:5]])}"
            + ("..." if len(steps) > 5 else "")
            + f" | 分布: {path_data.get('difficulty_distribution', 'N/A') if 'path_data' in dir() else ''}",
        )

        iteration = state.get("iteration_count", 0) + (1 if is_adjustment else 0)

        return {
            **log_entry,
            "learning_path": steps,
            "next_action": "generate_resources",
            "iteration_count": iteration,
        }

    # ═══════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════

    def _extract_completed_steps(self, existing_path: List[PathStep]) -> str:
        """提取已完成步骤的摘要"""
        lines = []
        for step in existing_path:
            if step.get("status") == "completed":
                score_info = f"(得分: {step.get('score', 'N/A')})" if step.get("score") else ""
                lines.append(f"- 步骤{step['step_id']}: {step['topic']} {score_info}")
        return "\n".join(lines)

    def _build_adjustment_request(
        self,
        assessment: Dict,
        profile: Dict,
    ) -> tuple[str, int]:
        """
        构建调整请求文本 + 计算动态时间预算
        
        Returns:
            (adjustment_request文本, total_time_limit分钟数)
        """
        adjustment_request = ""
        base_time = 120

        if assessment and assessment.get("should_adjust_path"):
            gaps = assessment.get("gaps_found", [])
            gap_details = assessment.get("gap_details", [])
            
            detail_lines = []
            for gd in gap_details[:3]:
                severity = gd.get("severity", "?")
                cause = gd.get("possible_cause", "")
                detail_lines.append(f"  - {gd.get('gap', gd.get('topic', '?'))} [{severity}] 原因: {cause}")

            adjustment_request = (
                f"⚠️ 上次测评得分: {assessment.get('overall_score')}/100\n"
                f"发现的问题:\n" + "\n".join(detail_lines or [f"  - {g}" for g in gaps]) +
                f"\n系统建议: {assessment.get('recommendation', '')}\n"
                f"下一步重点: {assessment.get('next_focus', '')}\n"
                f"错误模式: {json.dumps(assessment.get('error_analysis', {}), ensure_ascii=False)[:300]}"
            )
            base_time = 180  # 调整时给更多时间

        # 根据认知画像调整时间
        pace = profile.get("pace", "moderate")
        attention = profile.get("attention_span", 25)
        cognitive = profile.get("cognitive", {})
        example_need = cognitive.get("concrete_example_need", 0.5)
        depth_pref = cognitive.get("preferred_depth", "moderate")

        time_multiplier = 1.0

        if pace == "slow":
            time_multiplier *= 1.5
        elif pace == "fast":
            time_multiplier *= 0.8

        # 高例子需求 → 实践步骤多花时间
        if example_need > 0.7:
            time_multiplier *= 1.2

        # 深度学习者需要更多时间
        if depth_pref == "deep":
            time_multiplier *= 1.15

        # 注意力时长限制
        max_by_attention = attention * 4  # 大约能专注4个注意力块
        total_time = min(int(base_time * time_multiplier), max(60, max_by_attention), 360)

        return adjustment_request, total_time

    def _build_knowledge_graph_context(self, state: LearningState) -> str:
        """从 RAG 上下文或状态中提取知识图谱信息"""
        rag_ctx = state.get("rag_context")
        if rag_ctx and len(rag_ctx) > 50:
            return f"[RAG知识背景]\n{rag_ctx[:1200]}"
        
        # 尝试用 RAG 检索
        subject = state.get("subject", "")
        goal = state.get("current_goal", "")
        query = f"{subject} {goal} 知识点体系 结构 关系"
        retrieved = self._retrieve_knowledge(query, top_k=2)
        if retrieved:
            return f"[RAG检索到的知识结构]\n{retrieved[:1000]}"
        
        return ""

    def _normalize_steps(
        self,
        raw_steps: List[Dict],
        offset: int = 0,
    ) -> List[Dict]:
        """标准化步骤数据，确保所有必要字段存在"""
        bloom_levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
        valid_difficulties = {"easy", "medium", "hard"}

        normalized = []
        for i, step in enumerate(raw_steps):
            s = dict(step)  # 浅拷贝避免修改原始数据
            
            s["step_id"] = s.get("step_id", offset + i + 1)
            s.setdefault("status", "pending")
            s.setdefault("resources_generated", False)
            s.setdefault("score", None)
            
            # 校验 difficulty
            if s.get("difficulty") not in valid_difficulties:
                s["difficulty"] = "medium"
            
            # 校验 bloom_level
            bloom = s.get("bloom_level", "understand").lower()
            if bloom not in bloom_levels:
                # 根据 difficulty 推断
                diff_map = {"easy": "remember", "medium": "apply", "hard": "analyze"}
                bloom = diff_map.get(s["difficulty"], "understand")
            s["bloom_level"] = bloom

            # 确保 list 字段
            s.setdefault("prerequisites", [])

            normalized.append(s)

        return normalized

    # ═══════════════════════════════════════════
    #  规则兜底
    # ═══════════════════════════════════════════

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        super().fallback(state, error)
        goal = state.get("current_goal", "")
        subject = state.get("subject", "通用")
        offset = len(state.get("learning_path", []))
        return {
            "learning_path": self._fallback_path(goal, subject, offset),
        }

    def _fallback_path(
        self,
        goal: str,
        subject: str,
        offset: int = 0,
    ) -> List[Dict]:
        """LLM 不可用时的模板路径"""
        base_id = offset + 1
        return [
            {
                "step_id": base_id,
                "topic": f"{subject}基础概念与术语",
                "description": f"建立{subject}的核心概念框架，理解基本定义和原理",
                "difficulty": "easy",
                "bloom_level": "remember",
                "estimated_minutes": 15,
                "prerequisites": [],
                "status": "pending",
                "resources_generated": False,
                "score": None,
                "teaching_hint": "使用类比和图示帮助理解抽象概念",
            },
            {
                "step_id": base_id + 1,
                "topic": f"{subject}核心方法与操作",
                "description": f"掌握{subject}的主要方法、算法流程和常用技巧",
                "difficulty": "medium",
                "bloom_level": "understand",
                "estimated_minutes": 20,
                "prerequisites": [f"{subject}基础概念与术语"],
                "status": "pending",
                "resources_generated": False,
                "score": None,
                "teaching_hint": "配合代码示例逐步讲解",
            },
            {
                "step_id": base_id + 2,
                "topic": f"{subject}动手实践练习",
                "description": f"通过编程练习巩固所学知识，解决实际问题",
                "difficulty": "medium",
                "bloom_level": "apply",
                "estimated_minutes": 25,
                "prerequisites": [f"{subject}核心方法与操作"],
                "status": "pending",
                "resources_generated": False,
                "score": None,
                "teaching_hint": "由简到繁，逐步增加复杂度",
            },
            {
                "step_id": base_id + 3,
                "topic": f"{subject}进阶分析与优化",
                "description": f"深入分析{subject}的性能特点，学会评估和优化方案",
                "difficulty": "hard",
                "bloom_level": "analyze",
                "estimated_minutes": 20,
                "prerequisites": [f"{subject}动手实践练习"],
                "status": "pending",
                "resources_generated": False,
                "score": None,
                "teaching_hint": "引入真实案例进行对比分析",
            },
            {
                "step_id": base_id + 4,
                "topic": "综合项目实战与总结",
                "description": f"将所学知识整合完成目标: {goal}",
                "difficulty": "hard",
                "bloom_level": "create",
                "estimated_minutes": 25,
                "prerequisites": [f"{subject}进阶分析与优化"],
                "status": "pending",
                "resources_generated": False,
                "score": None,
                "teaching_hint": "鼓励自主设计和实现",
            },
        ]
