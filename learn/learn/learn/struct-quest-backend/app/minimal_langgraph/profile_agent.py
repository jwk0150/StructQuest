"""
ProfileAgent — 分析学生画像

职责：根据学科和目标，生成学生学习画像
策略：优先调用 LLM，失败时使用规则兜底（确保无 API Key 也可运行）
"""
import json
import os
import time
from typing import Dict, Any

from app.minimal_langgraph.state import MinimalState


# ── Prompt 模板 ──

PROFILE_PROMPT = """你是一位专业的教育心理学家，请根据以下信息生成学生学习画像。

学科：{subject}
学习目标：{goal}

请以 JSON 格式输出：
```json
{{
    "ability_level": "beginner|intermediate|advanced",
    "learning_style": "visual|auditory|reading|hands_on",
    "strengths": ["擅长1", "擅长2"],
    "weaknesses": ["短板1", "短板2"],
    "pace": "fast|moderate|slow",
    "summary": "一句话总结画像"
}}
```
只输出 JSON，不要其他内容。"""


class ProfileAgent:
    """学习画像 Agent — 分析学生能力、偏好、短板"""

    def __call__(self, state: MinimalState) -> Dict[str, Any]:
        """
        LangGraph 节点函数：接收 state，返回需要更新的字段
        """
        print("[ProfileAgent] 开始分析学生画像...")

        subject = state.get("subject", "通用")
        goal = state.get("goal", "提升学习能力")

        # 尝试调用 LLM
        try:
            profile_data = self._analyze_with_llm(subject, goal)
        except Exception as e:
            print(f"[ProfileAgent] LLM 不可用 ({e})，使用规则兜底")
            profile_data = self._fallback_profile(subject, goal)

        # 记录日志
        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent": "ProfileAgent",
            "message": f"画像完成: {profile_data.get('ability_level', 'N/A')} | {profile_data.get('summary', '')}",
        }

        print(f"[ProfileAgent] 完成: {profile_data.get('ability_level')} | {profile_data.get('summary', '')}")

        return {
            "profile": profile_data,
            "messages": state.get("messages", []) + [log_entry],
        }

    # ── LLM 调用 ──

    def _analyze_with_llm(self, subject: str, goal: str) -> Dict:
        """使用 LLM 分析画像"""
        prompt = PROFILE_PROMPT.format(subject=subject, goal=goal)

        messages = [
            {"role": "system", "content": "你是教育心理学专家，擅长分析学习画像。"},
            {"role": "user", "content": prompt},
        ]

        response_text = self._call_openai(messages)
        return self._parse_json(response_text)

    def _call_openai(self, messages: list, temperature: float = 0.7) -> str:
        """同步调用 OpenAI 兼容 API"""
        from dotenv import load_dotenv
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        if not api_key:
            raise RuntimeError("未配置 OPENAI_API_KEY")

        import openai
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=messages,
            temperature=temperature,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()

    # ── JSON 解析 ──

    @staticmethod
    def _parse_json(text: str) -> Dict:
        """从 LLM 响应中提取 JSON"""
        import re

        # 尝试提取 ```json ... ```
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 找最外层 { ... }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法解析 JSON: {text[:200]}")

    # ── 规则兜底（确保无 LLM 也可运行）──

    @staticmethod
    def _fallback_profile(subject: str, goal: str) -> Dict:
        """LLM 不可用时的规则兜底"""
        return {
            "ability_level": "beginner",
            "learning_style": "reading",
            "strengths": [f"{subject}基础知识学习意愿强", "逻辑思维能力"],
            "weaknesses": [f"{subject}实践经验不足", "系统性知识框架待建立"],
            "pace": "moderate",
            "summary": f"初学者，正在学习{subject}，目标为{goal}。建议从基础概念入手，循序渐进。",
        }
