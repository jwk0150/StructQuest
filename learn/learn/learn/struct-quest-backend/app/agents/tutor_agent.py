"""
Tutor Agent（学习老师）— v3
==========================

定位：学习老师。不是百科问答，而是结合学生画像、知识库、聊天历史、错题本
给出个性化的教学回答。

输入：
  - 学生问题
  - 学生画像（能力水平、学习风格、薄弱点）
  - 知识库（RAG 检索）
  - 聊天历史（判断是否反复问同一问题）
  - 错题本（针对性指出错误原因）

回答策略：
  - 不是百科答案，而是个性化教学
  - 如果学生已问多次 → 变换教学方式
  - 结合错题指出具体问题
  - 可生成图示、代码辅助理解
"""

from typing import Dict, Any, List, Optional

from app.agents.base import BaseAgent
from app.agents.state import LearningState, TutorResponse
from app.utils.logger import get_logger

logger = get_logger("tutor_agent")


# ══════════════════════════════════════════════════
#  Prompt 模板
# ══════════════════════════════════════════════════

TUTOR_SYSTEM_PROMPT = """你是一位耐心、博学的数据结构辅导老师。你的回答不是百科式的，而是针对性的教学。

## 学生画像
- 能力水平: {ability_level}
- 学习风格: {learning_style}
- 薄弱点: {weaknesses}
- 费曼适配度: {feynman_score}（高=多用类比讲故事，低=严谨定义+推导）
- 错误模式: {error_patterns}

## 知识库参考
{rag_context}

## 学生错题本
{error_book}

## 历史对话（检查是否已反复问过）
{chat_history}

## 教学原则
1. **个性化**：根据学生画像调整解释方式
   - 如果费曼适配度高 → 先用人话类比，再给专业术语
   - 如果薄弱点正好相关 → 重点展开这部分
2. **查重**：如果学生已经问了3次以上类似问题 → 变换教学方式
3. **结合错题**：如果错题本中有相关错误 → 直接指出"你之前主要错在..."
4. **循序渐进**：先确认理解基础概念，再深入
5. **启发性**：不直接给答案，引导学生思考

## 回答格式
- 使用 Markdown 格式
- 代码块标注语言
- 重要概念用 **加粗**
- 可在最后给出1-2个后续建议问题"""


class TutorAgent(BaseAgent):
    """
    学习老师 Agent v3

    结合知识库 + 画像 + 聊天历史 + 错题给出个性化教学回答。
    """

    @property
    def name(self) -> str:
        return "tutor_agent"

    @property
    def description(self) -> str:
        return "学习老师 — 结合画像/知识库/错题本给出个性化教学回答"

    # ═══════════════════════════════════════════
    #  核心 run 方法
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        logger.info("👨‍🏫 Tutor Agent 开始辅导...")

        # 获取问题
        event_payload = state.get("event_payload", {})
        question = (
            event_payload.get("question", "")
            or state.get("user_answer", "")
            or (state.get("user_messages", [])[-1] if state.get("user_messages") else "")
        )

        if not question:
            log = self._log(state, "❓ 无有效问题")
            return {
                **log,
                "chat_response": "请问你有什么学习上的问题？",
                "next_action": "orchestrate",
            }

        # 收集上下文
        profile = state.get("student_profile", {})
        cognitive = profile.get("cognitive", {})
        analytics = state.get("learning_analytics", {})

        # RAG 知识库检索
        subject = state.get("subject", "数据结构")
        rag_context = self._retrieve_knowledge(
            f"{subject} {question}", top_k=3
        )

        # 错题本（从画像的错误模式和分析数据中提取）
        error_book = self._build_error_book(profile, analytics)

        # 聊天历史（检测是否重复提问）
        chat_history = self._summarize_chat_history(state)

        # 构建 prompt
        system_content = self._build_system_prompt(
            TUTOR_SYSTEM_PROMPT,
            ability_level=profile.get("ability_level", "intermediate"),
            learning_style=profile.get("learning_style", "reading"),
            weaknesses=", ".join(profile.get("weaknesses", [])) or "无",
            feynman_score=str(cognitive.get("feynman_adaptation", 0.5)),
            error_patterns=", ".join(profile.get("error_patterns", [])) or "无",
            rag_context=rag_context[:2000] if rag_context else "无相关知识库参考资料",
            error_book=error_book,
            chat_history=chat_history,
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": question},
        ]

        try:
            response = self._call_llm(messages, temperature=0.7, max_tokens=1500)
        except Exception as e:
            logger.warning("LLM 辅导回答失败: %s", e)
            response = (
                f"关于「{question}」，让我来为你解释。\n\n"
                f"这个问题的核心在于理解基本概念。建议先回顾相关讲义，"
                f"然后通过练习来巩固理解。\n\n"
                f"如果还有疑问，可以换个方式再问我。"
            )

        # 构建 TutorResponse
        tutor_response: Dict[str, Any] = {
            "answer_text": response,
            "referenced_knowledge": self._extract_topics(response, question),
            "used_context": self._describe_used_context(rag_context, error_book),
            "follow_up_suggestions": self._suggest_follow_ups(question, profile),
            "generated_visual": None,
        }

        # 日志
        log = self._log(
            state,
            f"👨‍🏫 辅导完成 | 问题: {question[:30]}... | "
            f"回答长度: {len(response)} 字 | "
            f"引用了: {tutor_response['used_context']}"
        )

        return {
            **log,
            "tutor_response": tutor_response,
            "chat_response": response,
            "next_action": "orchestrate",
        }

    # ═══════════════════════════════════════════
    #  错题本构建
    # ═══════════════════════════════════════════

    def _build_error_book(self, profile: Dict, analytics: Dict) -> str:
        """从画像和分析数据中构建错题摘要"""
        parts = []

        error_patterns = (
            analytics.get("error_patterns")
            or profile.get("error_patterns", [])
        )
        primary_error = (
            analytics.get("primary_error_type")
            or profile.get("primary_error_type", "")
        )

        if primary_error:
            parts.append(f"主要错误类型: {primary_error}")

        if error_patterns:
            parts.append(f"常见错误: {', '.join(error_patterns[:5])}")

        weaknesses = profile.get("weaknesses", [])
        if weaknesses:
            parts.append(f"薄弱知识点: {', '.join(weaknesses[:5])}")

        # 低掌握度知识点
        mastery = profile.get("knowledge_mastery", {})
        low_mastery = [f"{t}({s:.0f})" for t, s in mastery.items() if float(s) < 50]
        if low_mastery:
            parts.append(f"低掌握度: {', '.join(low_mastery[:5])}")

        return "\n".join(parts) if parts else "暂无错题记录"

    # ═══════════════════════════════════════════
    #  聊天历史摘要
    # ═══════════════════════════════════════════

    def _summarize_chat_history(self, state: LearningState) -> str:
        """提取最近的对话历史，检测重复提问"""
        user_messages = state.get("user_messages", [])
        if not user_messages:
            return "无历史对话"

        recent = user_messages[-8:] if len(user_messages) > 8 else user_messages
        return "\n".join(f"- {m[:100]}" for m in recent)

    # ═══════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════

    @staticmethod
    def _extract_topics(response: str, question: str) -> List[str]:
        """从回答中提取引用的知识点"""
        # 简单关键词提取
        keywords = ["链表", "树", "图", "栈", "队列", "排序", "查找",
                    "递归", "动态规划", "哈希", "DFS", "BFS", "二叉树",
                    "Dijkstra", "堆", "数组", "指针"]
        found = []
        for kw in keywords:
            if kw in response or kw in question:
                found.append(kw)
        return found[:5] if found else [question[:20]]

    @staticmethod
    def _describe_used_context(rag_context: str, error_book: str) -> str:
        """描述回答使用了哪些上下文来源"""
        sources = []
        if rag_context and len(rag_context) > 20:
            sources.append("知识库")
        if error_book and "暂无" not in error_book:
            sources.append("错题本")
        if not sources:
            sources.append("基础知识")
        return " + ".join(sources)

    @staticmethod
    def _suggest_follow_ups(question: str, profile: Dict) -> List[str]:
        """生成后续建议问题"""
        weaknesses = profile.get("weaknesses", [])
        suggestions = []

        # 基于薄弱点建议
        if weaknesses:
            suggestions.append(f"想了解一下「{weaknesses[0]}」的详细内容吗？")

        # 通用建议
        suggestions.append("需要我出一个练习题来检验你的理解吗？")
        suggestions.append("要不要看一下相关的代码示例？")

        return suggestions[:2]

    # ═══════════════════════════════════════════
    #  降级策略
    # ═══════════════════════════════════════════

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        super().fallback(state, error)
        question = (
            state.get("event_payload", {}).get("question", "")
            or (state.get("user_messages", [])[-1] if state.get("user_messages") else "")
            or "你的问题"
        )
        return {
            "next_action": "orchestrate",
            "chat_response": (
                f"关于「{question[:30]}」，这是一个很好的问题。\n\n"
                f"建议你先回顾相关的基础概念，然后我们可以逐步深入讨论。\n"
                f"如果方便的话，可以换个方式重新提问，我会尽力帮你解答。"
            ),
            "tutor_response": {
                "answer_text": f"关于「{question[:30]}」的基础回答（降级模式）",
                "referenced_knowledge": [question[:20]],
                "used_context": "基础知识（服务暂不可用）",
                "follow_up_suggestions": ["需要我出个练习题吗？"],
            },
        }
