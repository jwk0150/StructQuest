"""
PlannerAgent — 生成学习路径

职责：根据学生画像和学习目标，规划个性化学习步骤
策略：优先调用 LLM，失败时使用规则兜底（确保无 API Key 也可运行）
"""
import json
import os
import time
from typing import Dict, Any, List

from app.minimal_langgraph.state import MinimalState


# ── Prompt 模板 ──

PLANNER_PROMPT = """你是一位资深课程设计师，请根据学生画像和学习目标，规划个性化学习路径。

学科：{subject}
学习目标：{goal}

学生画像：
{profile}

请以 JSON 格式输出：
```json
{{
    "steps": [
        {{
            "step_id": 1,
            "topic": "步骤名称",
            "description": "详细说明学什么",
            "difficulty": "easy|medium|hard",
            "estimated_minutes": 20,
            "prerequisites": []
        }}
    ]
}}
```

要求：
- 3~5 个步骤，从基础到进阶
- 难度先易后难
- 只输出 JSON，不要其他内容。"""


class PlannerAgent:
    """学习路径规划 Agent — 根据画像生成学习步骤"""

    def __call__(self, state: MinimalState) -> Dict[str, Any]:
        """
        LangGraph 节点函数：接收 state，返回需要更新的字段
        """
        print("[PlannerAgent] 开始规划学习路径...")

        subject = state.get("subject", "通用")
        goal = state.get("goal", "提升学习能力")
        profile = state.get("profile", {})

        # 尝试调用 LLM
        try:
            plan_data = self._plan_with_llm(subject, goal, profile)
        except Exception as e:
            print(f"[PlannerAgent] LLM 不可用 ({e})，使用规则兜底")
            plan_data = self._fallback_plan(subject, goal)

        # 记录日志
        topics = " → ".join(s.get("topic", "")[:10] for s in plan_data[:4])
        log_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "agent": "PlannerAgent",
            "message": f"路径规划完成: {len(plan_data)}步 | {topics}",
        }

        print(f"[PlannerAgent] 完成: {len(plan_data)}步 | {topics}")

        return {
            "plan": plan_data,
            "messages": state.get("messages", []) + [log_entry],
        }

    # ── LLM 调用 ──

    def _plan_with_llm(self, subject: str, goal: str, profile: Dict) -> List[Dict]:
        """使用 LLM 规划路径"""
        profile_str = json.dumps(profile, ensure_ascii=False, indent=2) if profile else "暂无画像数据"
        prompt = PLANNER_PROMPT.format(subject=subject, goal=goal, profile=profile_str)

        messages = [
            {"role": "system", "content": "你是课程设计专家，擅长规划个性化学习路径。"},
            {"role": "user", "content": prompt},
        ]

        response_text = self._call_openai(messages)
        data = self._parse_json(response_text)
        return data.get("steps", data if isinstance(data, list) else [])

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
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()

    # ── JSON 解析 ──

    @staticmethod
    def _parse_json(text: str) -> Dict:
        """从 LLM 响应中提取 JSON"""
        import re

        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法解析 JSON: {text[:200]}")

    # ── 规则兜底 ──

    @staticmethod
    def _fallback_plan(subject: str, goal: str) -> List[Dict]:
        """LLM 不可用时的模板路径"""
        return [
            {
                "step_id": 1,
                "topic": f"{subject}基础概念",
                "description": f"建立{subject}的核心概念框架，理解基本定义和原理",
                "difficulty": "easy",
                "estimated_minutes": 15,
                "prerequisites": [],
            },
            {
                "step_id": 2,
                "topic": f"{subject}核心方法",
                "description": f"掌握{subject}的主要方法和常用技巧",
                "difficulty": "medium",
                "estimated_minutes": 25,
                "prerequisites": [f"{subject}基础概念"],
            },
            {
                "step_id": 3,
                "topic": f"{subject}实践练习",
                "description": "通过动手练习巩固所学知识，解决实际问题",
                "difficulty": "medium",
                "estimated_minutes": 30,
                "prerequisites": [f"{subject}核心方法"],
            },
            {
                "step_id": 4,
                "topic": "综合应用与总结",
                "description": f"整合所学知识完成目标: {goal}",
                "difficulty": "hard",
                "estimated_minutes": 25,
                "prerequisites": [f"{subject}实践练习"],
            },
        ]
