"""
测评 Agent（增强版）
==================

核心职责：
  1. 根据学生的学习表现进行多维度测评
  2. 布鲁姆分类学六维度评分（remember/understand/apply/analyze/evaluate/create）
  3. 识别已掌握的知识点和未掌握的部分
  4. 错误模式识别（概念混淆/计算错误/逻辑漏洞/方法误用）
  5. 知识追踪（每个知识点的掌握度趋势）
  6. 决定是否需要调整学习路径

增强点（v2）：
- 布鲁姆分类学六维度评分
- 错误模式自动识别与分类
- 知识掌握度追踪（KnowledgeMastery）
- gap_details: 每个缺口附带 severity + cause
- error_analysis: 结构化错误分析报告
- 自适应阈值（根据学生 error_tolerance 动态调整）
"""
from typing import Dict, Any, List, Optional

from app.agents.base import BaseAgent
from app.agents.state import LearningState, AssessmentResult, KnowledgeMastery
from app.utils.logger import get_logger

logger = get_logger("assessment_agent")


# ════════════════════════════════════════════
#  Prompt 模板 — 布鲁姆分类学版
# ════════════════════════════════════════════

ASSESSMENT_PROMPT = """你是一位严谨的学习评估专家和教育测量学家。
请对以下学习情况进行全面的、多维度的评估。

## 当前学习步骤
- **主题**: {topic}
- **描述**: {description}
- **难度**: {difficulty}
- **目标布鲁姆层级**: {bloom_level}

## 学生回答/提交的内容
{submission}

## 参考答案（来自练习题资源）
{reference_answer}

## 学生画像
- 能力水平: {ability_level}
- 薄弱点: {weaknesses}
- 学习节奏: {pace}
- 认知特征:
  - 错误容忍度: {error_tolerance}
  - 抽象推理能力: {abstract_reasoning}
  - 费曼适配度: {feynman_adaptation}
  - MBTI风格: {mbti_style}

## 历史测评记录
{history}

## 知识库参考标准答案/评分标准
{rag_context}

请以 JSON 格式输出完整的测评报告：

```json
{{
    "overall_score": 得分(0~100整数),
    
    "step_scores": {{
        "概念理解": 0~100,
        "应用能力": 0~100,
        "问题解决": 0~100
    }},
    
    "bloom_scores": {{
        "remember": 0~100,
        "understand": 0~100,
        "apply": 0~100,
        "analyze": 0~100,
        "evaluate": 0~100,
        "create": 0~100
    }},
    
    "strengths_identified": ["掌握好的方面1", "方面2", "..."],
    
    "gaps_found": ["未掌握的知识点1", "..."],
    
    "gap_details": [
        {{
            "gap": "具体知识点",
            "severity": "high|medium|low",
            "cause": "根本原因分析",
            "remediation": "补救建议"
        }}
    ],
    
    "recommendation": "针对性的改进建议（50~150字）",
    
    "error_analysis": {{
        "primary_error_type": "概念混淆|计算错误|逻辑漏洞|方法误用|理解偏差|无错误",
        "error_patterns": ["具体错误模式1", "错误模式2"],
        "common_mistakes": ["典型错误描述"],
        "suggested_fix": "如何纠正这些错误的建议"
    }},
    
    "should_adjust_path": true/false,
    "adjustment_reason": "如果需要调整说明原因，否则写\"保持当前路径\"",
    "next_focus": "建议接下来重点学习的内容"
}}
```

### 评分标准（布鲁姆分类学）

| 层级 | 描述 | 评分要点 |
|------|------|----------|
| remember | 记忆/回忆 | 能否准确复述定义、公式 |
| understand | 理解/解释 | 能否用自己的话解释概念 |
| apply | 应用/使用 | 能否在类似场景中正确使用方法 |
| analyze | 分析/拆解 | 能否分解问题、识别关系 |
| evaluate | 评价/判断 | 能否评判方案的优劣 |
| create | 创造/设计 | 能否综合所学解决新问题 |

### 综合评分档位
- **90~100** 🌟 优秀：完全掌握，可以进入下一步
- **75~89** ✅ 良好：基本掌握，可前进但需复习薄弱点
- **60~74** ⚠️ 及格：部分掌握，建议补充练习后再前进
- **40~59** ❌ 不及格：需回退重学或换方式讲解
- **0~39** 💥 严重不足：需要从基础重新开始

### 特殊要求
- 如果 submission 为空或学生尚未提交，则进行"初始能力预估"（给出保守分数）
- 考虑学生的 error_tolerance 来调整反馈语气
- 只输出 JSON，不要其他内容"""


class AssessmentAgent(BaseAgent):
    """测评 Agent v2 — 布鲁姆维度 + 错误模式 + 知识追踪"""

    PASS_THRESHOLD = 60       # 通过阈值
    EXCELLENT_THRESHOLD = 80  # 优秀阈值

    @property
    def name(self) -> str:
        return "assessment_agent"

    @property
    def description(self) -> str:
        return "多维度评估学习效果（布鲁姆六维），识别错误模式，动态调整路径"

    # ═══════════════════════════════════════════
    #  核心 run 方法
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        logger.info("开始多维度测评...")

        learning_path: List[Dict] = state.get("learning_path", [])
        profile: Dict = state.get("student_profile", {})
        cognitive = profile.get("cognitive", {})
        current_index = state.get("current_step_index", 0)

        # 获取用户最新提交的答案
        user_answer = (
            state.get("user_answer")
            or (state.get("user_messages", [])[-1] if state.get("user_messages") else "")
        )
        
        previous_assessment = state.get("assessment", {})

        # 找到当前正在学习的步骤
        current_step = self._find_current_step(learning_path)
        if not current_step:
            log = self._log(state, "❓ 无有效学习步骤，结束会话")
            return {
                **log,
                "session_status": "completed",
                "next_action": "end",
            }

        topic = current_step.get("topic", "未知主题")
        difficulty = current_step.get("difficulty", "medium")
        bloom_level = current_step.get("bloom_level", "understand")

        # 获取参考答案
        reference_answer = self._extract_reference_answer(
            state.get("resources", []), topic
        )

        # 构建历史记录摘要
        history_summary = self._build_history(previous_assessment)

        # RAG 检索评分标准
        rag_context = self._retrieve_rubric(topic, difficulty)

        prompt = self._build_system_prompt(
            ASSESSMENT_PROMPT,
            topic=topic,
            description=current_step.get("description", ""),
            difficulty=difficulty,
            bloom_level=bloom_level,
            submission=user_answer or "（学生尚未提交答案，进行初始能力预估）",
            reference_answer=reference_answer or "无",
            ability_level=profile.get("ability_level", "intermediate"),
            weaknesses=", ".join(profile.get("weaknesses", [])) or "无",
            pace=profile.get("pace", "moderate"),
            error_tolerance=str(cognitive.get("error_tolerance", 0.6)),
            abstract_reasoning=str(cognitive.get("abstract_reasoning", 0.5)),
            feynman_adaptation=str(cognitive.get("feynman_adaptation", 0.5)),
            mbti_style=cognitive.get("mbti_style", "sentinel"),
            history=history_summary or "无历史记录",
            rag_context=rag_context or "无",
        )

        messages = [
            {"role": "system", "content": (
                "你是一位公正的教育测评专家和认知心理学家。\n\n"
                "你的专长包括：\n"
                "- 布鲁姆认知分类学框架的应用\n"
                "- 错误模式分析与诊断\n"
                "- 形成性评估与总结性评估\n"
                "- 个性化的改进建议生成\n\n"
                "请客观评估，避免过于宽松或苛刻。关注学习过程而非仅仅结果。"
            )},
            {"role": "user", "content": prompt},
        ]

        try:
            response_text = self._call_llm(messages, temperature=0.3, max_tokens=2500)
            assessment_data = self._parse_json(response_text)
            assessment_data = self._validate_assessment(assessment_data, topic, current_step, profile)
        except Exception as e:
            logger.warning("LLM 评估失败: %s，使用规则评估", e)
            assessment_data = self._rule_based_assessment(user_answer, current_step, profile)

        overall_score = assessment_data.get("overall_score", 0)
        should_adjust = assessment_data.get("should_adjust_path", False)

        # 自适应阈值（根据学生错误容忍度微调）
        effective_threshold = self._adaptive_threshold(cognitive)

        # 更新当前步骤状态
        updated_path = list(learning_path)
        for step in updated_path:
            if step.get("step_id") == current_step.get("step_id"):
                step["score"] = overall_score
                if overall_score >= effective_threshold:
                    step["status"] = "completed"
                else:
                    step["status"] = "in_progress"
                break

        # 决定下一步动作
        next_action = self._determine_next_action(
            overall_score=overall_score,
            should_adjust=should_adjust,
            current_step=current_step,
            learning_path=updated_path,
            iteration_count=state.get("iteration_count", 0),
            max_iterations=state.get("max_iterations", 5),
            threshold=effective_threshold,
        )

        # 构建知识追踪数据
        knowledge_tracking = self._update_knowledge_tracking(
            previous_assessment.get("knowledge_tracking", {}),
            assessment_data,
            topic,
            overall_score,
        )

        # 更新 assessment 数据加入知识追踪
        assessment_data["knowledge_tracking"] = knowledge_tracking

        # 标记是否通过（前端依赖此字段判断是否完结节点）
        assessment_data["passed"] = overall_score >= effective_threshold

        # 日志
        status_icon = "✅ PASS" if overall_score >= effective_threshold else "❌ FAIL"
        log_entry = self._log(
            state,
            f"{status_icon} 测评完成 | 主题: {topic} | "
            f"总分: {overall_score}/100 | "
            f"主要错误: {assessment_data.get('error_analysis', {}).get('primary_error_type', 'N/A')} | "
            f"下一步: {next_action}"
        )

        result: Dict[str, Any] = {
            **log_entry,
            "assessment": assessment_data,
            "learning_path": updated_path,
            "next_action": next_action,
        }

        # 会话结束检查
        if next_action == "end" or self._is_session_complete(updated_path, state):
            result["session_status"] = "completed"

        return result

    # ═══════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════

    def _find_current_step(self, path: List[Dict]) -> Optional[Dict]:
        """找到当前正在学习的步骤"""
        for step in path:
            if step.get("status") == "in_progress":
                return step
        for step in path:
            if step.get("status") == "pending":
                return step
        return path[-1] if path else None

    def _extract_reference_answer(self, resources: List[Dict], topic: str) -> str:
        """从资源中提取参考答案"""
        for res in resources:
            if res.get("type") == "exercise" and res.get("topic") == topic:
                return res.get("content", "")[:800]
        return ""

    def _build_history(self, prev: Dict) -> str:
        """构建历史测评记录摘要"""
        if not prev:
            return ""
        lines = []
        if prev.get("overall_score") is not None:
            lines.append(f"上次测评总分: {prev['overall_score']}/100")
        gaps = prev.get("gaps_found", [])
        if gaps:
            lines.append(f"上次发现的不足: {', '.join(gaps[:3])}")
        errors = prev.get("error_analysis", {})
        if errors.get("error_patterns"):
            lines.append(f"上次错误模式: {', '.join(errors['error_patterns'][:2])}")
        if prev.get("recommendation"):
            lines.append(f"上次建议: {prev['recommendation'][:100]}")
        return "\n".join(lines)

    def _retrieve_rubric(self, topic: str, difficulty: str) -> str:
        """RAG 检索评分标准/参考答案"""
        query = f"{topic} 评分标准 参考答案 {difficulty}"
        return self._retrieve_knowledge(query, top_k=2)

    def _adaptive_threshold(self, cognitive: Dict) -> int:
        """
        根据学生特征动态调整通过阈值
        
        - 高错误容忍度的学生 → 鼓励为主，略降低阈值
        - 低抽象推理能力的 → 给更多机会，略降阈值
        - 低费曼适配度的 → 需要更扎实的基础，不降
        """
        threshold = self.PASS_THRESHOLD
        err_tol = float(cognitive.get("error_tolerance", 0.5))
        abstract = float(cognitive.get("abstract_reasoning", 0.5))
        feynman = float(cognitive.get("feynman_adaptation", 0.5))

        # 错误容忍度高 → 降低5分（鼓励导向）
        if err_tol > 0.7:
            threshold -= 5
        
        # 抽象推理能力低 → 降低5分（给更多尝试空间）
        if abstract < 0.4:
            threshold -= 5

        # 但费曼适配度低时需要更高门槛（需要扎实基础）
        if feynman < 0.35:
            threshold += 5

        return max(45, min(threshold, 70))  # 限制在 45~70 范围内

    def _validate_assessment(
        self,
        data: Dict,
        topic: str,
        current_step: Dict,
        profile: Dict,
    ) -> Dict:
        """确保返回数据完整且符合 schema"""
        # 默认值填充
        data.setdefault("overall_score", 0)
        data.setdefault("step_scores", {"概念理解": 0, "应用能力": 0, "问题解决": 0})
        data.setdefault("bloom_scores", {
            "remember": 0, "understand": 0, "apply": 0,
            "analyze": 0, "evaluate": 0, "create": 0,
        })
        data.setdefault("strengths_identified", [])
        data.setdefault("gaps_found", [topic])
        data.setdefault("gap_details", [{
            "gap": topic,
            "severity": "medium",
            "cause": "待进一步分析",
            "remediation": "建议复习相关讲义和代码示例",
        }])
        data.setdefault("recommendation", "建议仔细学习提供的资料后再次练习。")
        data.setdefault("should_adjust_path", False)
        data.setdefault("adjustment_reason", "")
        data.setdefault("next_focus", topic)
        data.setdefault("passed", False)
        data.setdefault("error_analysis", {
            "primary_error_type": "理解偏差",
            "error_patterns": [],
            "common_mistakes": [],
            "suggested_fix": "",
        })

        # 分数范围约束
        score_key = "overall_score"
        data[score_key] = max(0, min(100, int(data[score_key])))

        for dict_field in ("step_scores", "bloom_scores"):
            for k, v in data[dict_field].items():
                data[dict_field][k] = max(0, min(100, int(v)))

        return data

    def _update_knowledge_tracking(
        self,
        existing: Dict[str, KnowledgeMastery],
        new_assessment: Dict,
        topic: str,
        score: int,
    ) -> Dict[str, KnowledgeMastery]:
        """更新知识点掌握追踪"""
        from datetime import datetime

        entry: Dict[str, Any] = dict(existing.get(topic, {}))
        was_error = score < self.PASS_THRESHOLD

        entry["topic"] = topic
        entry["mastery_level"] = max(entry.get("mastery_level", 0), score * 0.7 + entry.get("mastery_level", 0) * 0.3)
        entry["last_assessed_at"] = datetime.now().isoformat()
        entry["error_count"] = entry.get("error_count", 0) + (1 if was_error else 0)
        entry["success_count"] = entry.get("success_count", 0) + (0 if was_error else 1)

        # 追踪错误模式
        patterns = new_assessment.get("error_analysis", {}).get("error_patterns", [])
        existing_patterns = set(entry.get("error_patterns", []))
        entry["error_patterns"] = list(existing_patterns.union(patterns))[:8]

        # 趋势判断
        hist_scores = [entry.get("last_score", score), score]
        if len(hist_scores) >= 2 and hist_scores[-1] > hist_scores[-2] + 10:
            entry["confidence_trend"] = "improving"
        elif len(hist_scores) >= 2 and hist_scores[-1] < hist_scores[-2] - 10:
            entry["confidence_trend"] = "declining"
        else:
            entry["confidence_trend"] = "stable"

        entry["last_score"] = score
        entry["recommended_action"] = new_assessment.get("recommendation", "")[:200]

        result = dict(existing)
        result[topic] = entry
        return result

    # ═══════════════════════════════════════════
    #  路由决策
    # ═══════════════════════════════════════════

    def _determine_next_action(
        self,
        overall_score: float,
        should_adjust: bool,
        current_step: Dict,
        learning_path: List[Dict],
        iteration_count: int,
        max_iterations: int,
        threshold: int,
    ) -> str:
        """
        核心路由逻辑（v3 — 返回描述性标记，由 Orchestrator 解读）

        返回值含义：
        - "orchestrate"       → 回到 Orchestrator 由它决定
        - "end"               → 会话结束
        """
        # 上限检查
        if iteration_count >= max_iterations:
            return "end"

        # 优秀 → 标记完成，回到 Orchestrator
        if overall_score >= self.EXCELLENT_THRESHOLD:
            remaining = any(s.get("status") in ("pending", "in_progress") for s in learning_path)
            if not remaining:
                return "end"
            # 还有下一步 → 回到 Orchestrator，让它决定是否继续
            return "orchestrate"

        # 及格线以上
        if overall_score >= threshold:
            if should_adjust and iteration_count < max_iterations:
                return "orchestrate"  # Orchestrator 会检测到需要重规划
            remaining = any(s.get("status") in ("pending", "in_progress") for s in learning_path)
            return "orchestrate" if remaining else "end"

        # 不及格
        if overall_score < 40 and iteration_count < max_iterations:
            return "orchestrate"  # Orchestrator 检测到低分 → 会启动重规划

        return "orchestrate"

    def _is_session_complete(self, learning_path: List[Dict], state: LearningState) -> bool:
        all_completed = all(s.get("status") == "completed" for s in learning_path)
        return all_completed or state.get("iteration_count", 0) >= 5

    # ═══════════════════════════════════════════
    #  规则兜底
    # ═══════════════════════════════════════════

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        super().fallback(state, error)
        user_answer = state.get("user_answer") or ""
        current_step = self._find_current_step(state.get("learning_path", []))
        profile = state.get("student_profile", {})
        assessment = self._rule_based_assessment(user_answer, current_step or {}, profile)
        return {
            "assessment": assessment,
            "learning_path": state.get("learning_path", []),
            "next_action": "orchestrate",
        }

    def _rule_based_assessment(
        self,
        submission: str,
        current_step: Dict,
        profile: Dict,
    ) -> Dict:
        """LLM 不可用时的规则评估"""
        has_submission = bool(
            submission and submission.strip()
            and "尚未提交" not in submission
        )
        topic = current_step.get("topic", "未知主题")

        if not has_submission:
            return {
                "overall_score": 0,
                "step_scores": {"概念理解": 0, "应用能力": 0, "问题解决": 0},
                "bloom_scores": {
                    "remember": 0, "understand": 0, "apply": 0,
                    "analyze": 0, "evaluate": 0, "create": 0,
                },
                "strengths_identified": [],
                "gaps_found": [topic],
                "gap_details": [{
                    "gap": topic,
                    "severity": "high",
                    "cause": "尚未开始学习",
                    "remediation": "请先学习提供的讲义资料",
                }],
                "recommendation": "请先学习提供的资料，然后完成练习题。",
                "should_adjust_path": False,
                "adjustment_reason": "首次学习，无需调整",
                "next_focus": topic,
                "error_analysis": {
                    "primary_error_type": "无错误",
                    "error_patterns": [],
                    "common_mistakes": [],
                    "suggested_fix": "",
                },
                "knowledge_tracking": {},
                "passed": False,
            }

        # 基于提交长度的简单规则
        sub_len = len(submission)
        if sub_len < 20:
            score = 35
        elif sub_len < 80:
            score = 55
        elif sub_len < 200:
            score = 72
        else:
            score = 82

        is_fail = score < self.PASS_THRESHOLD
        return {
            "overall_score": score,
            "step_scores": {"概念理解": score, "应用_ability": score - 8, "problem_solving": score - 12},
            "bloom_scores": {
                "remember": min(score + 10, 100),
                "understand": score,
                "apply": score - 10,
                "analyze": max(score - 25, 0),
                "evaluate": max(score - 30, 0),
                "create": max(score - 35, 0),
            },
            "strengths_identified": ["能够作答并表达想法"] if score > 55 else [],
            "gaps_found": [topic] if is_fail else [],
            "gap_details": ([{
                "gap": topic,
                "severity": "medium",
                "cause": "练习不够充分",
                "remediation": "多做类似题目巩固理解",
            }] if is_fail else []),
            "recommendation": (
                "建议仔细复习讲义中的关键概念后再尝试。"
                if is_fail else "做得不错！继续下一步。"
            ),
            "should_adjust_path": score < 45,
            "adjustment_reason": "需要加强基础训练" if score < 45 else "",
            "next_focus": topic,
            "error_analysis": {
                "primary_error_type": "理解偏差" if score < 65 else "轻微不足",
                "error_patterns": ["答案不够详细"] if score < 60 else [],
                "common_mistakes": [],
                "suggested_fix": "提供更详细的解题过程" if score < 60 else "",
            },
            "knowledge_tracking": {},
            "passed": not is_fail,
        }
