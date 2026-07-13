"""
AI 学习资源生成系统 v4
=======================

根据学习路径生成学习资源，输出统一结构：

  {
    "notes": "",        # 学习讲义 (Markdown)
    "mindmap": "",      # 思维导图 (Mermaid 格式)
    "quiz": [],         # 练习题 (结构化数组)
    "code_example": "",  # 代码案例 (Python，可运行)
    "animation": {},     # 动画视频 (Manim)
  }

注：PPT 大纲已迁移至独立的 PPT 智能生成器（三阶段流程：
思维导图 → 大纲编辑 → 渲染），通过 /api/ppt 接口提供。

核心特性：
- 思维导图使用 Mermaid mindmap 语法
- 代码案例支持 Python，保证可运行
- 练习题为结构化 JSON 数组，便于前端交互
- 根据学生画像动态调整难度/风格/深度
- RAG 检索增强
- 支持流式逐个推送（WebSocket）
- 降级策略保证可用性
"""
from typing import Dict, Any, List, Optional, Generator
import json
import re

from app.agents.base import BaseAgent
from app.agents.state import LearningState, ResourceItem
from app.utils.logger import get_logger

logger = get_logger("resource_agent")


# ════════════════════════════════════════════
#  Prompt 模板 — 5 种资源类型
# ════════════════════════════════════════════

NOTES_TEMPLATE = """为以下主题编写一份高质量学习讲义。

## 主题
{topic}

## 步骤描述
{description}

## 目标布鲁姆层级
{bloom_level}

## 难度等级
{difficulty}

## 目标学生画像
- 能力水平: {ability_level}
- 学习偏好: {learning_style}
- 知识短板: {weaknesses}
- 兴趣方向: {interests}
- 认知特征:
  - 费曼适配度: {feynman_score} (高=多用类比/故事; 低=严谨定义+推导)
  - 抽象推理能力: {abstract_reasoning} (低=多给具体例子)
  - 对例子的依赖度: {example_need} (高=每个概念配实例)
  - 偏好深度: {preferred_depth}
  - MBTI认知风格: {mbti_style}

## 参考知识库内容
{rag_context}

## 要求

严格按以下章节输出 Markdown 讲义（不要输出 JSON 或其他格式）：

```markdown
# {topic} 讲义

## 一、引言与动机
> 用生活化的场景引入，说明为什么学这个、有什么用

## 二、核心概念解析
### 2.1 基本定义
（正式定义 + 直观解释）

### 2.2 类比理解
（用日常事物做比喻，帮助建立直觉）

### 2.3 图示说明
（用文字描述直观的示意图或流程）

## 三、深入讲解
### 3.1 原理详解
（分小节逐步深入讲解核心原理）

### 3.2 关键要点
（列出 3~5 个必须记住的核心要点）

### 3.3 与前置知识的联系
（如何从已学知识过渡到本主题）

## 四、常见误区与陷阱
（针对学生薄弱点重点提醒，至少 3 个常见错误）

## 五、实战示例
（结合 interests 的完整应用场景例子）

## 六、思考与延伸
（2~3 道引导性思考题 + 1 个拓展方向）
```

### 语言风格适配
{style_guide}

### 其他要求
- 结合 interests 举例说明
- 讲义长度适中（1500~3000 字）
- 使用标准 Markdown 格式
- 重要概念加粗
- 公式用 $...$ 包裹
- 代码块标注语言"""


MINDMAP_TEMPLATE = """你是一个极高水平的 Markmap 知识图谱架构师。你的任务是将复杂的知识点转化为完美的 Markmap 渲染结构。

# Rules (绝对强制执行)

1. **结构化强制**：必须使用 Markdown 标题层级 (`#`, `##`, `###`, `####`) 来定义节点的逻辑从属关系。
   - `#` 为中心节点（主题: {topic}）
   - `##` 为第一层分支（核心维度）
   - `###` 为第二层分支（概念/定义）
   - `-` (列表) 为叶子节点（具体的详细解释、参数、优缺点）

2. **严禁废话**：不要输出任何开场白（如"好的，这是你要的思维导图"），也不要输出任何总结性文字。直接从 `#` 根节点开始输出。

3. **高密度逻辑**：
   - 尽量使用短语，不要使用完整的长句子。
   - 确保每个分支的逻辑严谨，按照：定义 → 特性 → 原理 → 应用 → 复杂度/评价 的逻辑排序。

4. **视觉优化**：对于代码、公式等，直接放在列表项中。

# Context
- 学科领域: {subject}
- 前置知识: {prerequisites}
- 后续关联: {next_steps}
- 目标布鲁姆层级: {bloom_level}
- 薄弱点（在相关节点后加 ❗ 标记）: {weaknesses}
- 知识库参考 (仅作补充): {rag_context}

# Example (主题: 数组)
# 数组 (Array)
## 基础定义
- 连续内存空间
- 相同数据类型
- 索引从 0 开始
## 核心操作
### 访问
- 随机访问 O(1)
- 越界检查
### 插入
- 末尾 O(1)
- 中间 O(n) ❗
### 删除
- 末尾 O(1)
- 中间 O(n)
### 查找
- 线性扫描 O(n)
- 二分查找 O(log n)
## 常见分类
### 按维度
- 一维数组
- 二维矩阵
- 多维张量
### 按大小
- 静态数组
- 动态数组 (ArrayList)
## 应用场景
- 哈希表底层结构
- 矩阵运算/图像处理
- DP 备忘录存储
- 排序算法载体

直接输出 Markdown："""


QUIZ_TEMPLATE = """为主题"{topic}"设计一组结构化练习题。

## 步骤描述
{description}

## 目标布鲁姆层级
{bloom_level}

## 难度等级
{difficulty}

## 学生情况
- 能力水平: {ability_level}
- 薄弱点: {weaknesses}
- 认知特征:
  - 错误容忍度: {error_tolerance}
  - 抽象推理能力: {abstract_reasoning}

## 参考知识库内容
{rag_context}

## 要求

设计 6~8 道题目，仅输出纯 JSON 数组。

每道题目格式如下：
{{
    "id": 1,
    "question": "题目文本",
    "type": "choice",
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
    "answer": "A",
    "explanation": "详细解析...",
    "difficulty": "easy",
    "bloom_level": "remember",
    "knowledge_point": "考查的知识点",
    "weakness_related": false
}}

### 题目分布
- **记忆层 (remember)**: 2 题 — type 为 choice
- **理解层 (understand)**: 1~2 题 — type 为 choice 或 fill_blank
- **应用层 (apply)**: 2 题 — type 为 short_answer 或 choice
- **分析层 (analyze)**: 1 题 — type 为 short_answer
- **评价/创造层**: 0~1 题 — type 为 short_answer

### type 字段说明
| type | 说明 | options |
|------|------|---------|
| choice | 选择题 | 必须有 4 个选项 |
| fill_blank | 填空题 | 空数组 [] |
| short_answer | 简答/编程题 | 空数组 [] |

### 特别要求
- 至少有 2 题直接针对 weaknesses 设计（weakness_related 为 true）
- 编程题的 answer 字段提供完整的 Python 参考答案

### ⚠️ 输出格式强制要求 ⚠️
- **禁止**输出任何开场白、问候语、解释说明
- **禁止**输出"好的，这是...""以下是...""为您生成..."等任何引导文字
- **禁止**将 JSON 包裹在 ```json ... ``` 代码块中
- **禁止**在 JSON 数组前后添加任何文字，包括换行说明
- **你的回答必须以 [ 开头，以 ] 结尾，中间内容仅为合法 JSON 数组**
- 如果违反以上规则，系统将无法解析你的输出"""


CODE_EXAMPLE_TEMPLATE = """为主题"{topic}"编写递进式 Python 代码案例。

## 步骤描述
{description}

## 目标布鲁姆层级
{bloom_level}

## 难度等级
{difficulty}

## 学生情况
- 能力水平: {ability_level}
- 学习偏好: {learning_style}
- 认知特征:
  - 抽象推理能力: {abstract_reasoning}
  - 对例子依赖度: {example_need}

## 参考知识库中的代码片段
{rag_context}

## 要求

提供 3 个由浅入深的递进 Python 代码示例，所有代码必须可直接运行。

输出格式：纯 Python 代码（不要输出 Markdown 格式），用注释分隔不同示例。

严格遵循以下结构：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
{topic} — 递进式代码案例
难度: {difficulty}
\"\"\"

# ══════════════════════════════════════════════════════
# 示例 1: {topic} 基础用法
# 难度: easy | 知识点: xxx
# ══════════════════════════════════════════════════════

def example_1_basic():
    \"\"\"最基础用法，建立直觉\"\"\"
    # TODO: 实现基础功能
    pass

if __name__ == "__main__":
    print("=" * 50)
    print("示例 1: 基础用法")
    print("=" * 50)
    example_1_basic()

# ══════════════════════════════════════════════════════
# 示例 2: {topic} 实际应用
# 难度: medium | 知识点: xxx
# ══════════════════════════════════════════════════════

def example_2_application():
    \"\"\"真实场景中的应用，处理边界情况\"\"\"
    # TODO: 实现应用场景
    pass

if __name__ == "__main__":
    print()
    print("=" * 50)
    print("示例 2: 实际应用")
    print("=" * 50)
    example_2_application()

# ══════════════════════════════════════════════════════
# 示例 3: {topic} 进阶优化
# 难度: hard | 知识点: xxx
# ══════════════════════════════════════════════════════

def example_3_advanced():
    \"\"\"性能优化、错误处理、高级用法\"\"\"
    # TODO: 实现高级用法
    pass

if __name__ == "__main__":
    print()
    print("=" * 50)
    print("示例 3: 进阶优化")
    print("=" * 50)
    example_3_advanced()
```

### 代码要求
- **必须使用 Python 3 语法**
- **所有代码必须可直接运行**（python xxx.py 即可执行）
- 每个示例有完整的 if __name__ == "__main__" 入口和打印输出
- 示例 1：Hello World 级别，最基础用法
- 示例 2：实际应用级，处理真实场景和边界
- 示例 3：进阶/优化级，性能优化或高级用法
- 关键行必须加注释说明
- 针对薄弱点设计"错误示范"（❌ 错误 → ✅ 正确）
- 如果 topic 不涉及编程，输出伪代码/算法流程的 Python 版本
- 不要包裹在 ``` 代码块中，直接输出 Python 代码"""



# ════════════════════════════════════════════
#  费曼教学风格指南
# ════════════════════════════════════════════

STYLE_GUIDES = {
    "high_feynman": (
        "**费曼式教学风格（高适配度 >= 0.7）：**\n"
        "- 用生活化类比解释抽象概念（如\"链表像火车车厢一样一节节连起来\"）\n"
        "- 用对话式的、友好的语气\n"
        "- 先说(人话)再说(专业术语)\n"
        "- 多问\"你想想看...\"引导思考\n"
        "- 每个抽象概念都配一个具体的生活实例\n"
    ),
    "low_feynman": (
        "**严谨学术风格（低适配度 <= 0.3）：**\n"
        "- 使用精确的数学/形式化定义\n"
        "- 强调逻辑推导和证明过程\n"
        "- 使用标准术语和专业表达\n"
        "- 结构清晰、层次分明\n"
        "- 公式定理优先，辅以简短说明\n"
    ),
    "medium_feynman": (
        "**平衡教学风格（0.3 < 适配度 < 0.7）：**\n"
        "- 先给出直觉性解释，再补充严格定义\n"
        "- 类比与公式并重\n"
        "- 适当使用图示描述\n"
        "- 关键概念用两种方式表达（直觉 + 严谨）\n"
    ),
}


# ════════════════════════════════════════════
#  动画视频模板 (Manim)
# ════════════════════════════════════════════

ANIMATION_TEMPLATE = """你是一位算法可视化专家和 Manim 动画大师。

## 任务
为以下算法/数据结构概念编写一段 Manim (Community Edition) Python 代码，生成教学动画。

## 主题
{topic}

## 步骤描述
{description}

## 难度等级
{difficulty}
## 布鲁姆层级
{bloom_level}

## 学生画像
- 能力水平: {ability_level}
- 学习偏好: {learning_style}
- 费曼适配度: {feynman_score}

## 代码要求：

### 必须的结构：
```python
class AlgorithmScene(Scene):
    def construct(self):
        # 你的动画代码
        pass
```

### 动画设计原则：
1. **渐进式展示**：逐步呈现每个步骤，不要一次性显示所有内容
2. **颜色编码**：比较元素用红色/蓝色区分，已处理用绿色/灰色
3. **文字标注**：关键步骤用 Text/Tex 添加说明（中文）
4. **时间节奏**：适当使用 wait(0.5~1) 让观众消化信息
5. **视觉清晰**：字号 >= 24，对比度足够

### 根据主题类型选择动画策略：
- **搜索算法**（二分查找、线性搜索）：展示数组+左右指针、高亮比较、标明 mid、FadeOut 排除区域
- **排序算法**（快排、归并）：展示数组初始状态、高亮 pivot、分区过程可视化
- **树/图遍历**（DFS/BFS）：绘制树形结构、移动点表示路径、已访问节点变色
- **链表操作**（反转、合并）：绘制节点和指针动画、指针重定向
- **数学概念**（递归、DP）：图形辅助理解、递归调用栈可视化

### 技术约束：
- 使用 manim Community Edition 语法（兼容 v0.18+）
- ⚠️ 不要设置 config.media_width / config.media_height（系统会自动注入字符串值）
- 场景类名必须是 `AlgorithmScene`
- 只使用 manim + numpy
- 控制总帧数在 300~800 帧
- 不要使用 ShowPassingFlash 等闪烁效果

请直接输出完整 Python 代码（不要 markdown 包裹）：
"""




# ════════════════════════════════════════════
#  Manim 辅助函数
# ════════════════════════════════════════════

def _clean_manim_output(raw: str) -> str:
    """清理 LLM 输出的 Manim 代码，移除 markdown 包裹"""
    import re
    code = raw.strip()

    # 移除 markdown 代码块标记 (```python, ```manim, ```)
    code = re.sub(r"^```(?:python|manim)?\s*\n?", "", code, flags=re.MULTILINE)
    code = re.sub(r"```\s*$", "", code, flags=re.MULTILINE)

    # 确保有 import 但不重复添加
    if "from manim import" not in code and "class " in code:
        header = (
            "from manim import *\n"
            "import numpy as np\n\n"
            'config.background_color = "#1a1a2e"\n\n'
        )
        code = header + code

    return code.strip()


# ════════════════════════════════════════════
#  资源输出结构
# ════════════════════════════════════════════

class ResourceBundle(dict):
    """
    资源包 — 学习资源的统一输出结构

    {
        "notes": str,          # 学习讲义 (Markdown)
        "mindmap": str,        # 思维导图 (Mermaid)
        "quiz": List[Dict],    # 练习题 (结构化数组)
        "code_example": str,   # 代码案例 (Python)
        "animation": dict,     # 动画视频 ({video_url, source_code})
    }

    注：PPT 大纲已迁移至独立的智能生成器流程。
    """
    pass


# ════════════════════════════════════════════
#  Resource Generation Agent v4
# ════════════════════════════════════════════

class ResourceGenerationAgent(BaseAgent):
    """
    AI 资源生成 Agent v4

    输出统一的 ResourceBundle 结构：
    {
        "notes": "",          # 学习讲义 (Markdown)
        "mindmap": "",        # 思维导图 (Mermaid 格式)
        "quiz": [],           # 练习题 (结构化数组)
        "code_example": "",   # 代码案例 (Python，可运行)
        "animation": {},      # 动画视频 (Manim: {video_url, source_code})
    }

    注：PPT 生成已迁移至独立的 PPT 智能生成器（三阶段流程），
    通过 /api/ppt/parse-mindmap 和 /api/ppt/render 接口提供。
    """

    RESOURCE_TYPES = [
        "notes",         # 📖 学习讲义
        "quiz",          # ✏️ 练习题
        # "mindmap",       # 🧠 思维导图 (onboarding 时跳过，按需生成)
        # "code_example",  # 💻 代码案例 (onboarding 时跳过，按需生成)
    ]

    # 完整资源类型（按需生成时使用）
    # 注：ppt_outline 已迁移至独立的 PPT 智能生成器（三阶段流程：思维导图→大纲→渲染）
    FULL_RESOURCE_TYPES = [
        "notes",
        "mindmap",
        "quiz",
        "code_example",
        "animation",      # 🎬 动画视频 (Manim)
    ]

    # 类型元信息（供前端展示用）
    TYPE_META = {
        "notes":        {"icon": "📖", "label": "学习讲义", "format": "markdown", "color": "#4F46E5"},
        "mindmap":      {"icon": "🧠", "label": "思维导图", "format": "mermaid", "color": "#8B5CF6"},
        "quiz":         {"icon": "✏️", "label": "练习题", "format": "json", "color": "#EF4444"},
        "code_example": {"icon": "💻", "label": "代码案例", "format": "python", "color": "#10B981"},
        "animation":     {"icon": "🎬", "label": "动画演示", "format": "video", "color": "#EC4899"},
    }

    # 模板映射
    TEMPLATE_MAP = {
        "notes": NOTES_TEMPLATE,
        "mindmap": MINDMAP_TEMPLATE,
        "quiz": QUIZ_TEMPLATE,
        "code_example": CODE_EXAMPLE_TEMPLATE,
        "animation": ANIMATION_TEMPLATE,
    }

    @property
    def name(self) -> str:
        return "resource_agent"

    @property
    def description(self) -> str:
        return "资源工厂 — 先检索资源库，无则 AI 生成，保存到资源库供复用"

    # ═══════════════════════════════════════════
    #  核心 run 方法（v3 — 事件驱动 + 先检索后生成）
    # ═══════════════════════════════════════════

    # 事件类型 → 只生成的资源类型映射
    EVENT_TYPE_MAP = {
        "request_mindmap": ["mindmap"],
        "request_code_example": ["code_example"],
        "request_animation": ["animation"],
        "request_exercise": ["quiz"],
        "generate_resource": None,  # None = 从 payload 中读取
    }

    def run(self, state: LearningState) -> Dict[str, Any]:
        """
        v3 — 事件驱动的资源生成

        策略：先检索资源库，命中则复用，未命中则 AI 生成。
        """
        event_type = state.get("event_type", "")
        event_payload = state.get("event_payload", {})

        # 根据事件类型决定生成哪些资源
        only_types = self._resolve_types(event_type, event_payload)

        if only_types:
            logger.info("🚀 按需生成资源: %s", only_types)
        else:
            logger.info("🚀 开始生成学习资源（完整资源包）...")

        # 生成资源包（先检索后生成）
        bundle = self.generate_resource_bundle(state, only_types=only_types)

        # 转换为 ResourceItem 列表
        resource_items = self._bundle_to_items(bundle, state)

        # 更新路径状态
        learning_path = state.get("learning_path", [])
        updated_path = list(learning_path)
        current_index = state.get("current_step_index", 0)

        for step in updated_path:
            if step.get("step_id") == current_index + 1 or (
                current_index < len(updated_path) and
                step == updated_path[current_index]
            ):
                step["resources_generated"] = True
                step["status"] = "in_progress"
                break

        # 日志
        source_summary = self._summarize_sources(resource_items)
        log_entry = self._log(
            state,
            f"📦 资源包完成: {len(resource_items)} 项 | 来源: {source_summary}"
        )

        return {
            **log_entry,
            "resources": resource_items,
            "resource_bundle": bundle,
            "learning_path": updated_path,
            "next_action": "orchestrate",
        }

    def _resolve_types(self, event_type: str, payload: Dict) -> Optional[List[str]]:
        """根据事件类型决定生成哪些资源类型"""
        mapped = self.EVENT_TYPE_MAP.get(event_type)
        if mapped is not None:
            return mapped
        # 从 payload 读取
        requested = payload.get("resource_type") or payload.get("resource_types")
        if requested:
            if isinstance(requested, list):
                return requested
            return [requested]
        # 默认：生成 RESOURCE_TYPES 中定义的全部类型
        return None

    @staticmethod
    def _summarize_sources(items: List[Dict]) -> str:
        """统计资源来源"""
        cached = sum(1 for item in items if item.get("source") == "cached")
        generated = len(items) - cached
        return f"缓存复用 {cached} + AI生成 {generated}"

    # ═══════════════════════════════════════════
    #  资源包生成（核心方法）
    # ═══════════════════════════════════════════

    def generate_resource_bundle(
        self, state: LearningState, only_types: Optional[List[str]] = None
    ) -> ResourceBundle:
        """
        生成资源包（v3：先检索后生成）

        Args:
            only_types: 如果指定，只生成这些类型（如 ["mindmap"]）
        """
        learning_path: List[Dict] = state.get("learning_path", [])
        profile: Dict = state.get("student_profile", {})
        assessment: Dict = state.get("assessment", {})
        subject = state.get("subject", "通用")
        event_payload = state.get("event_payload", {})

        # ★ 如果没有学习路径，从 event_payload 构造虚拟步骤
        if not learning_path:
            topic = event_payload.get("topic") or event_payload.get("question") or subject
            if not topic or topic == "通用":
                logger.warning("⚠️ 无学习路径且无指定主题，使用降级资源")
                return self._fallback_bundle(state, RuntimeError("无学习路径"))

            logger.info("📋 从事件数据构造虚拟学习步骤: %s", topic)
            current_step = {
                "topic": topic,
                "description": event_payload.get("description", f"学习{topic}"),
                "difficulty": event_payload.get("difficulty", "medium"),
                "bloom_level": event_payload.get("bloom_level", "understand"),
                "prerequisites": event_payload.get("prerequisites", []),
                "status": "in_progress",
                "resources_generated": False,
                "step_id": 0,
                "estimated_minutes": 20,
            }
        else:
            # 找到当前步骤
            current_step, _ = self._find_current_step(
                learning_path, state.get("current_step_index", 0)
            )

            if not current_step:
                logger.info("✅ 所有步骤已完成")
                return self._fallback_bundle(state, RuntimeError("所有步骤已完成"))

        topic = current_step["topic"]
        difficulty = current_step.get("difficulty", "medium")
        bloom_level = current_step.get("bloom_level", "understand")
        description = current_step.get("description", "")
        cognitive = profile.get("cognitive", {})
        gaps_found = assessment.get("gaps_found", [])
        gap_details = assessment.get("gap_details", [])

        weakness_descriptions = self._extract_gap_details(gap_details, gaps_found)
        next_steps = [s["topic"] for s in learning_path
                      if s.get("step_id", 0) > current_step.get("step_id", 0)]

        common = self._build_common_params(
            topic=topic, description=description, difficulty=difficulty,
            bloom_level=bloom_level, profile=profile, cognitive=cognitive,
            subject=subject, prerequisites=current_step.get("prerequisites", []),
            next_steps=next_steps, weakness_descriptions=weakness_descriptions,
            gaps_found=gaps_found,
        )

        bundle = ResourceBundle()

        RESOURCE_GENERATORS = {
            "notes": lambda: self._gen_notes(common, cognitive, topic, subject),
            "mindmap": lambda: self._gen_mindmap(common, topic, subject),
            "quiz": lambda: self._gen_quiz(common, topic, subject),
            "code_example": lambda: self._gen_code(common, topic, subject),
            "animation": lambda: self._gen_animation(common, topic, subject),
        }

        # ★ 先检索资源库，有则复用
        # 兼容单字符串传入（generate_resources 传入 only_type 为 str，而非 List[str]）
        if isinstance(only_types, str):
            only_types = [only_types]
        types_to_generate = only_types if only_types is not None else self.RESOURCE_TYPES

        for res_type in types_to_generate:
            if res_type not in RESOURCE_GENERATORS:
                continue
            try:
                # ★ 步骤1：检索资源库
                cached = self._search_resource_cache(res_type, topic, subject)
                if cached:
                    logger.info("📋 %s 从缓存命中，复用", res_type)
                    bundle[res_type] = cached
                    continue

                # ★ 步骤2：未命中则 AI 生成
                logger.info("🔄 正在 AI 生成 %s...", res_type)
                bundle[res_type] = RESOURCE_GENERATORS[res_type]()
                logger.info("✅ %s 生成完成", res_type)
            except Exception as e:
                logger.warning("⚠️ %s 生成失败: %s", res_type, e)
                bundle[res_type] = self._fallback_content(res_type, topic)

        return bundle

    # ═══════════════════════════════════════════
    #  流式生成器（兼容 WebSocket 逐个推送）
    # ═══════════════════════════════════════════

    def generate_resources(
        self, state: LearningState, only_type: str = None
    ) -> Generator[ResourceItem, None, None]:
        """
        逐个生成资源的生成器（用于流式推送到前端）

        生成 ResourceBundle 后拆分为 ResourceItem 列表，
        保持与旧版 WebSocket 接口的兼容性。
        """
        bundle = self.generate_resource_bundle(state, only_types=[only_type] if only_type else None)

        # 使用 FULL_RESOURCE_TYPES 遍历（而非 RESOURCE_TYPES，后者只有 notes+quiz）
        for res_type in self.FULL_RESOURCE_TYPES:
            if only_type and res_type != only_type:
                continue

            content = bundle.get(res_type, "")
            if not content:
                continue

            topic = self._get_current_topic(state)

            meta = self.TYPE_META.get(res_type, {})

            # quiz 特殊处理：保留结构化数据供前端交互渲染，同时转 Markdown 作为文本兜底
            quiz_items = None
            if res_type == "quiz" and isinstance(content, list):
                quiz_items = content  # 保留结构化数据
                content = self._format_quiz_to_markdown(content)
            elif isinstance(content, (list, dict)):
                # animation 等 dict 直接转 JSON 字符串
                content = json.dumps(content, ensure_ascii=False, indent=2)

            resource_item: ResourceItem = {
                "type": res_type,
                "topic": topic,
                "title": f"{meta.get('icon', '')} {meta.get('label', res_type)}：{topic}",
                "content": content,
                "format": meta.get("format", "text"),
                "difficulty": self._get_current_difficulty(state),
                "estimated_minutes": 15,
                "rag_sources": [],
                "tags": [res_type],
                "meta": meta,
            }
            if quiz_items is not None:
                resource_item["quiz_items"] = quiz_items

            yield resource_item

    # ═══════════════════════════════════════════
    #  单个资源生成
    # ═══════════════════════════════════════════

    def _generate_single(self, res_type: str, params: Dict[str, Any]) -> str:
        """调用 LLM 生成单个资源内容"""

        template = self.TEMPLATE_MAP.get(res_type)
        if not template:
            raise ValueError(f"未知的资源类型: {res_type}")

        prompt = self._build_system_prompt(template, **params)

        messages = [
            {"role": "system", "content": (
                "你是一位顶级教育资源创作者和教育专家。\n"
                "你的任务是根据教学需求生成高质量、针对性强的学习资源。\n"
                "\n核心原则：\n"
                "- 内容准确无误，符合学术规范\n"
                "- 严格遵守用户指定的格式要求\n"
                "- 参考提供的知识库内容进行扩展\n"
                "- 针对学生薄弱点提供额外关注\n"
            )},
            {"role": "user", "content": prompt},
        ]

        # 不同资源类型的参数调优
        temp_map = {
            "notes": 0.75,
            "mindmap": 0.55,
            "quiz": 0.65,
            "code_example": 0.8,
        }
        max_tok_map = {
            "notes": 4096,
            "mindmap": 2048,
            "quiz": 4096,
            "code_example": 4096,
        }

        return self._call_llm(
            messages,
            temperature=temp_map.get(res_type, 0.7),
            max_tokens=max_tok_map.get(res_type, 3000),
        )

    # ═══════════════════════════════════════════
    #  单个资源生成辅助方法
    # ═══════════════════════════════════════════

    def _gen_notes(self, common, cognitive, topic, subject):
        rag_ctx = self._retrieve_for_resource(topic, "notes", subject)
        params = {**common, "rag_context": rag_ctx, "style_guide": self._get_style_guide(cognitive)}
        return self._generate_single("notes", params)

    def _gen_mindmap(self, common, topic, subject):
        rag_ctx = self._retrieve_for_resource(topic, "mindmap", subject)
        params = {**common, "rag_context": rag_ctx}
        return self._clean_mindmap(self._generate_single("mindmap", params))

    def _gen_quiz(self, common, topic, subject):
        rag_ctx = self._retrieve_for_resource(topic, "quiz", subject)
        params = {**common, "rag_context": rag_ctx}
        return self._parse_quiz(self._generate_single("quiz", params))

    def _gen_code(self, common, topic, subject):
        rag_ctx = self._retrieve_for_resource(topic, "code_example", subject)
        params = {**common, "rag_context": rag_ctx}
        return self._clean_python_code(self._generate_single("code_example", params))

    # ── 🎬 动画视频生成 (Manim) ──

    def _gen_animation(self, common, topic, subject):
        """
        生成动画视频资源。

        流程：
        1. LLM 生成 Manim Python 代码
        2. 调用 ManimRenderer 沙箱渲染 MP4
        3. 返回包含 video_url + source_code 的字典

        Returns:
            dict: {"video_url": str, "source_code": str, "render_time": float}
                 或 {"error": str} 如果失败时降级为文本说明
        """
        import time as _time
        start = _time.time()

        try:
            from app.services.manim_renderer import get_renderer, build_animation_prompt

            renderer = get_renderer()

            # 步骤1：LLM 生成 Manim 代码
            prompt_params = {**common}
            prompt_params.setdefault("description", f"可视化展示 {topic} 的执行过程")
            prompt_params.setdefault("difficulty", common.get("difficulty", "medium"))

            raw_code = self._generate_single("animation", prompt_params)

            # 清理 LLM 输出中的 markdown 包裹
            manim_code = _clean_manim_output(raw_code)
            logger.info("🎬 Manim 代码已生成 (%d 字符)", len(manim_code))

            # 步骤2：沙箱渲染（如果可用）
            if renderer.available:
                logger.info("🎬 开始 Manim 渲染...")
                render_result = renderer.render(
                    code=manim_code,
                    scene_name="AlgorithmScene",
                    timeout=120,
                )

                if render_result.get("success"):
                    elapsed = round(_time.time() - start, 2)
                    logger.info("✅ 动画渲染成功 (%.1fs)", elapsed)

                    return {
                        "video_url": render_result.get("video_url", ""),
                        "source_code": manim_code,
                        "render_time": render_result.get("render_time", elapsed),
                        "thumbnail_url": render_result.get("thumbnail_url", ""),
                        "scene_name": "AlgorithmScene",
                        "format": "manim",
                    }
                else:
                    warn_msg = render_result.get("error", "未知错误")
                    logger.warning("⚠️ Manim 渲染失败: %s，返回代码供用户查看", warn_msg)
                    return self._animation_fallback(manim_code, warn_msg)
            else:
                # Manim 不可用时返回代码供用户自行运行
                logger.info("ℹ️ Manim 渲染器不可用，返回源代码")
                return self._animation_fallback(
                    manim_code,
                    "当前环境未安装 Manim，以下是可运行的动画代码"
                )

        except Exception as e:
            logger.error("❌ 动画生成异常: %s", e, exc_info=True)
            return self._animation_fallback("", str(e))

    def _animation_fallback(self, code: str, reason: str) -> Dict[str, Any]:
        """动画渲染失败时的降级响应 — 返回代码 + 说明文本"""
        fallback_text = f"""## 🎬 动画演示: 可视化代码

> ⚠️ **注意**: {reason}

### 可执行的 Manim 源码

```python
{code or '# (代码生成失败，请重试)'}
```

### 使用方法

1. 安装 Manim: `pip install manim`
2. 保存上方代码为 `algorithm.py`
3. 运行: `manim -pql algorithm.py AlgorithmScene`
"""
        return {
            "video_url": "",
            "source_code": code,
            "render_time": 0,
            "fallback_text": fallback_text,
            "format": "code_only",
            "error": reason,
        }

    # ═══════════════════════════════════════════
    #  Prompt 参数构建
    # ═══════════════════════════════════════════

    def _build_common_params(self, **kwargs) -> Dict[str, Any]:
        """构建所有资源类型共享的 prompt 参数"""
        profile = kwargs.get("profile", {})
        cognitive = kwargs.get("cognitive", {})
        weakness_descriptions = kwargs.get("weakness_descriptions", [])
        gaps_found = kwargs.get("gaps_found", [])

        return {
            "topic": kwargs.get("topic", ""),
            "description": kwargs.get("description", ""),
            "difficulty": kwargs.get("difficulty", "medium"),
            "bloom_level": kwargs.get("bloom_level", "understand"),
            "ability_level": profile.get("ability_level", "intermediate"),
            "learning_style": profile.get("learning_style", "reading"),
            "weaknesses": self._format_weaknesses_for_prompt(weakness_descriptions, gaps_found),
            "interests": ", ".join(profile.get("interests", [])) or "通用",
            "subject": kwargs.get("subject", ""),
            "prerequisites": ", ".join(kwargs.get("prerequisites", [])) or "无",
            "next_steps": " → ".join(kwargs.get("next_steps", [])[:3]) or "本主题最后一步",
            "feynman_score": str(cognitive.get("feynman_adaptation", 0.5)),
            "abstract_reasoning": str(cognitive.get("abstract_reasoning", 0.5)),
            "example_need": str(cognitive.get("concrete_example_need", 0.6)),
            "error_tolerance": str(cognitive.get("error_tolerance", 0.6)),
            "preferred_depth": cognitive.get("preferred_depth", "moderate"),
            "mbti_style": cognitive.get("mbti_style", "sentinel"),
        }

    def _format_weaknesses_for_prompt(
        self, gap_details: List[Dict], gaps_found: List[str]
    ) -> str:
        """将薄弱点格式化为 prompt 可用的文本"""
        if gap_details:
            parts = []
            for g in gap_details[:5]:
                severity = g.get("severity", "")
                cause = g.get("cause", "")
                remediation = g.get("remediation", g.get("suggested_remediation", ""))
                topic = g.get("gap", g.get("topic", ""))
                parts.append(f"- {topic}（严重程度:{severity}, 原因:{cause}, 建议:{remediation})")
            return "\n".join(parts) if parts else "暂无"
        elif gaps_found:
            return "\n".join(f"- {g}" for g in gaps_found[:5])
        return "暂无特定薄弱点"

    def _extract_gap_details(
        self, gap_details: List[Dict], gaps_found: List[str]
    ) -> List[Dict]:
        """提取薄弱点详细信息"""
        if gap_details:
            return gap_details
        return [{"gap": g, "severity": "medium"} for g in gaps_found[:5]]

    # ═══════════════════════════════════════════
    #  内容清洗与解析
    # ═══════════════════════════════════════════

    @staticmethod
    def _clean_mindmap(raw: str) -> str:
        """
        清洗思维导图输出（兼容 Mermaid 旧格式 + Markmap 新格式）

        优先检测 Markmap 格式（# 开头），否则按 Mermaid 清洗。
        """
        stripped = raw.strip()

        # 移除 ```markdown ... ``` 或 ``` ... ``` 包裹
        for prefix in ("```markdown", "```mermaid", "```"):
            if stripped.startswith(prefix):
                end = stripped.find("```", 3)
                if end > 0:
                    stripped = stripped[len(prefix):end].strip()
                break

        # 移除尾部 ```
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()

        # Markmap 格式（以 # 开头）→ 直接返回
        if stripped.startswith("#"):
            # 确保第一行是 # 标题
            lines = stripped.split("\n")
            if any(l.startswith("# ") or l.startswith("## ") for l in lines):
                return stripped

        # 兼容旧 Mermaid 格式
        if stripped.startswith("mindmap"):
            return stripped

        idx = stripped.find("mindmap")
        if idx >= 0:
            return stripped[idx:].strip()

        # 兜底：尝试提取 Markdown-like 内容
        return stripped

    @staticmethod
    def _clean_python_code(raw: str) -> str:
        """清洗 Python 代码输出：移除代码块包裹"""
        # 移除 ```python ... ``` 包裹
        match = re.search(r'```python\s*\n([\s\S]*?)\n```', raw)
        if match:
            return match.group(1).strip()

        # 移除 ``` ... ``` 包裹
        match = re.search(r'```\s*\n([\s\S]*?)\n```', raw)
        if match:
            content = match.group(1).strip()
            # 判断是否是 Python 代码
            if any(kw in content for kw in ["def ", "import ", "class ", "#!", "if __name__"]):
                return content

        stripped = raw.strip()
        # 如果以 Python 标识开头
        if stripped.startswith("#!") or stripped.startswith("# -*-") or stripped.startswith("import "):
            return stripped

        return stripped

    def _parse_quiz(self, raw: str) -> List[Dict]:
        """
        解析练习题为结构化数组

        策略（从强到弱）：
        1. 直接 JSON 数组解析
        2. 剥离代码块后解析
        3. 提取 [...] 片段后解析
        4. Markdown 降级解析
        5. 最终降级兜底
        """
        if not raw or not raw.strip():
            logger.warning("⚠️ Quiz 内容为空，使用降级内容")
            return self._fallback_quiz("未知主题")

        cleaned = raw.strip()

        # ── 第一步：剥离可能的 Markdown 代码块 ──
        # 匹配 ```json ... ``` 或 ``` ... ```
        code_block_patterns = [
            r'```json\s*\n([\s\S]*?)\n```',
            r'```\s*\n([\s\S]*?)\n```',
        ]
        for pattern in code_block_patterns:
            m = re.search(pattern, cleaned)
            if m:
                cleaned = m.group(1).strip()
                logger.debug("剥离代码块包裹，内容长度: %d", len(cleaned))
                break

        # ── 第二步：尝试直接解析 JSON ──
        try:
            data = self._parse_json(cleaned)
            if isinstance(data, list):
                return self._validate_quiz_items(data)
            elif isinstance(data, dict) and "questions" in data:
                return self._validate_quiz_items(data["questions"])
        except (ValueError, json.JSONDecodeError):
            pass

        # ── 第三步：查找 [ ... ] 并提取纯 JSON 片段 ──
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end > start:
            json_str = cleaned[start:end + 1]
            # 多轮尝试修复 JSON
            for attempt in range(3):
                try:
                    sanitized = self._sanitize_json_text(json_str)
                    data = json.loads(sanitized)
                    if isinstance(data, list):
                        return self._validate_quiz_items(data)
                except (json.JSONDecodeError, ValueError) as e:
                    if attempt == 0:
                        # 第一次失败：尝试修复常见问题（尾部多余逗号等）
                        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                    elif attempt == 1:
                        # 第二次失败：尝试移除最后一条不完整的记录
                        last_brace = json_str.rfind("{")
                        last_comma_before = json_str.rfind(",", 0, last_brace)
                        if last_comma_before > 0:
                            json_str = json_str[:last_comma_before] + "]"
                    logger.debug("JSON 修复第 %d 次失败: %s", attempt + 1, e)

        # ── 第四步：降级 Markdown 解析 ──
        logger.warning("⚠️ JSON 解析失败，尝试 Markdown 解析")
        try:
            return self._parse_quiz_from_markdown(raw)
        except Exception as e:
            logger.error("❌ Markdown 解析也失败: %s，使用降级内容", e)
            return self._fallback_quiz("未知主题")

    def _validate_quiz_items(self, items: List[Dict]) -> List[Dict]:
        """验证并标准化每个 quiz 项，确保所有值都是 JSON 可序列化的"""
        validated = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            try:
                validated.append({
                    "id": int(item.get("id", i + 1)),
                    "question": self._safe_str(item.get("question", "")),
                    "type": self._safe_str(item.get("type", "choice")),
                    "options": [self._safe_str(o) for o in (item.get("options") or [])],
                    "answer": self._safe_str(item.get("answer", "")),
                    "explanation": self._safe_str(item.get("explanation", "")),
                    "difficulty": self._safe_str(item.get("difficulty", "medium")),
                    "bloom_level": self._safe_str(item.get("bloom_level", "understand")),
                    "knowledge_point": self._safe_str(item.get("knowledge_point", "")),
                    "weakness_related": bool(item.get("weakness_related", False)),
                })
            except Exception as e:
                logger.warning("⚠️ Quiz 第%d项验证失败: %s，跳过", i + 1, e)
        # 确保至少有一道题
        if not validated:
            logger.warning("⚠️ 所有 Quiz 项验证失败，使用降级内容")
            return self._fallback_quiz("未知主题")
        return validated

    @staticmethod
    def _safe_str(value) -> str:
        """安全地将值转换为字符串（确保 JSON 可序列化）"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return str(value)
        except Exception:
            return ""

    def _parse_quiz_from_markdown(self, raw: str) -> List[Dict]:
        """从 Markdown 格式解析练习题（降级方案）"""
        items = []
        # 简单的正则匹配题目
        pattern = r'###\s*第(\d+)题.*?\*\*题型\*\*:\s*(.+?)[\n\r].*?\*\*题目\*\*:\s*(.+?)[\n\r]'
        matches = re.findall(pattern, raw, re.DOTALL)

        for i, (num, qtype, question) in enumerate(matches):
            items.append({
                "id": int(num) if num.isdigit() else i + 1,
                "question": question.strip(),
                "type": self._map_question_type(qtype.strip()),
                "options": [],
                "answer": "",
                "explanation": "",
                "difficulty": "medium",
                "bloom_level": "understand",
                "knowledge_point": "",
                "weakness_related": False,
            })

        if not items:
            # 最终降级：至少返回一道题
            items = [{
                "id": 1,
                "question": f"请简述核心概念",
                "type": "short_answer",
                "options": [],
                "answer": "",
                "explanation": "",
                "difficulty": "medium",
                "bloom_level": "understand",
                "knowledge_point": "",
                "weakness_related": False,
            }]

        return items

    @staticmethod
    def _map_question_type(qtype: str) -> str:
        """映射中文题型到标准 type"""
        if "选择" in qtype:
            return "choice"
        elif "填空" in qtype:
            return "fill_blank"
        elif "简答" in qtype or "编程" in qtype or "代码" in qtype:
            return "short_answer"
        elif "判断" in qtype:
            return "choice"  # 判断题用选择题格式
        return "short_answer"

    # ═══════════════════════════════════════════
    #  辅助方法
    # ═══════════════════════════════════════════

    def _find_current_step(
        self, path: List[Dict], start_index: int
    ) -> tuple:
        """找到当前待处理的学习步骤"""
        for i, step in enumerate(path[start_index:], start=start_index):
            if step.get("status") in ("pending", "in_progress") and not step.get("resources_generated"):
                return step, i
        return None, start_index

    def _retrieve_for_resource(
        self, topic: str, res_type: str, subject: str
    ) -> str:
        """为特定资源类型执行 RAG 检索"""
        type_keywords = {
            "notes":        ["概念 定义 原理 讲解"],
            "mindmap":      ["结构 体系 分类 关系 框架 知识图谱"],
            "quiz":         ["题目 练习 测验 例题 考点"],
            "code_example": ["代码 示例 实现 编程 算法"],
        }
        kw = type_keywords.get(res_type, [])
        query = f"{subject} {topic} {' '.join(kw)}"
        return self._retrieve_knowledge(query, top_k=3)

    def _get_style_guide(self, cognitive: Dict) -> str:
        """根据认知画像选择教学风格指南"""
        feynman = float(cognitive.get("feynman_adaptation", 0.5))
        mbti = cognitive.get("mbti_style", "sentinel")

        if feynman >= 0.7:
            guide = STYLE_GUIDES["high_feynman"]
        elif feynman <= 0.3:
            guide = STYLE_GUIDES["low_feynman"]
        else:
            guide = STYLE_GUIDES["medium_feynman"]

        mbti_hints = {
            "explorer":   "\n- 增加(试试看)(动手实验)类的引导语",
            "negotiator": "\n- 增加讨论问题和互动思考点",
            "analyst":    "\n- 增加数据对比和逻辑分析环节",
            "sentinel":   "\n- 保持系统性结构，增加检查清单",
        }
        guide += mbti_hints.get(mbti, "")
        return guide

    @staticmethod
    def _get_current_topic(state: LearningState) -> str:
        """获取当前学习步骤的主题"""
        path = state.get("learning_path", [])
        idx = state.get("current_step_index", 0)
        if path and idx < len(path):
            return path[idx].get("topic", "")
        # 从 event_payload 获取
        payload = state.get("event_payload", {})
        return payload.get("topic") or payload.get("question") or state.get("subject", "")

    @staticmethod
    def _get_current_difficulty(state: LearningState) -> str:
        """获取当前学习步骤的难度"""
        path = state.get("learning_path", [])
        idx = state.get("current_step_index", 0)
        if path and idx < len(path):
            return path[idx].get("difficulty", "medium")
        return "medium"

    def _search_resource_cache(
        self, res_type: str, topic: str, subject: str
    ) -> Optional[str]:
        """
        ★ 检索资源库：先找有没有已生成的资源可以复用

        策略：
        1. 查询数据库 resource_assets 表（同主题 + 同类型）
        2. 如果命中且质量分 > 60，直接复用
        3. 未命中返回 None，触发 AI 生成
        """
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import select
            from app.models.learning_ecosystem import ResourceAsset
            import asyncio

            async def _query():
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(ResourceAsset)
                        .where(
                            ResourceAsset.asset_type == res_type,
                            ResourceAsset.topic == topic,
                            ResourceAsset.review_status == "approved",
                            ResourceAsset.quality_score > 60,
                        )
                        .order_by(ResourceAsset.quality_score.desc())
                        .limit(1)
                    )
                    asset = result.scalar_one_or_none()
                    if asset and asset.content_text:
                        return asset.content_text
                    return None

            try:
                loop = asyncio.get_running_loop()
                # 在已有事件循环中，创建新的事件循环会出问题，直接返回 None
                logger.debug("跳过缓存查询（事件循环已运行）")
                return None
            except RuntimeError:
                return asyncio.run(_query())

        except Exception as e:
            logger.debug("资源缓存查询跳过: %s", e)
            return None

    def _bundle_to_items(self, bundle: ResourceBundle, state: LearningState) -> List[ResourceItem]:
        """将 ResourceBundle 转换为 ResourceItem 列表（v3：含来源标注）"""
        topic = self._get_current_topic(state)
        difficulty = self._get_current_difficulty(state)
        items = []

        # 使用完整资源类型遍历（包括按需生成的）
        all_types = list(bundle.keys()) if bundle else self.RESOURCE_TYPES

        for res_type in all_types:
            content = bundle.get(res_type, "")
            if not content:
                continue

            meta = self.TYPE_META.get(res_type, {})

            # quiz 特殊处理
            quiz_items = None
            if res_type == "quiz" and isinstance(content, list):
                quiz_items = content
                content = self._format_quiz_to_markdown(content)

            # 判断来源
            source = "generated"  # 默认 AI 生成
            # 如果是降级内容，标记为 fallback
            if "AI 生成暂时不可用" in str(content) or "生成失败" in str(content):
                source = "fallback"

            item = {
                "type": res_type,
                "topic": topic,
                "title": f"{meta.get('icon', '')} {meta.get('label', res_type)}：{topic}",
                "content": content,
                "format": meta.get("format", "text"),
                "difficulty": difficulty,
                "estimated_minutes": 15,
                "source": source,
                "rag_sources": [],
                "tags": [res_type, difficulty],
                "meta": meta,
            }
            if quiz_items is not None:
                item["quiz_items"] = quiz_items
            items.append(item)

        return items

    # ═══════════════════════════════════════════
    #  降级策略
    # ═══════════════════════════════════════════

    @staticmethod
    def _fallback_content(res_type: str, topic: str) -> str:
        """当 LLM 调用失败时返回降级内容"""
        fallbacks = {
            "notes": (
                f"# {topic} 学习讲义\n\n"
                f"> ⚠️ AI 生成暂时不可用，以下是基础模板。\n\n"
                f"## 核心概念\n\n{topic} 是本学科中的重要概念。\n\n"
                f"## 基本要点\n\n1. 理解定义\n2. 掌握操作\n3. 能够应用\n\n"
                f"## 常见误区\n\n- 混淆基本概念\n- 忽略边界条件\n\n"
                f"请稍后尝试重新生成。"
            ),
            "mindmap": (
                f"mindmap\n"
                f"  root(({topic}))\n"
                f"    核心概念\n"
                f"      定义\n"
                f"      特性\n"
                f"    基本操作\n"
                f"      创建\n"
                f"      查询\n"
                f"    应用场景\n"
                f"      实际案例\n"
                f"      拓展方向"
            ),
            "code_example": (
                f'#!/usr/bin/env python3\n'
                f'# -*- coding: utf-8 -*-\n'
                f'"""\n'
                f'{topic} — 代码案例\n'
                f'TODO: AI 生成暂时不可用，请稍后重试\n'
                f'"""\n\n'
                f'def example_basic():\n'
                f'    """基础示例"""\n'
                f'    print("Hello, {topic}!")\n\n'
                f'if __name__ == "__main__":\n'
                f'    example_basic()'
            ),
        }
        return fallbacks.get(res_type, f"⚠️ {res_type} 生成失败，请稍后重试")

    @staticmethod
    def _fallback_quiz(topic: str) -> List[Dict]:
        """quiz 降级内容"""
        return [
            {
                "id": 1,
                "question": f"请简述 {topic} 的核心概念",
                "type": "short_answer",
                "options": [],
                "answer": "",
                "explanation": "",
                "difficulty": "easy",
                "bloom_level": "remember",
                "knowledge_point": topic,
                "weakness_related": False,
            },
            {
                "id": 2,
                "question": f"列举 {topic} 的三个关键特性",
                "type": "short_answer",
                "options": [],
                "answer": "",
                "explanation": "",
                "difficulty": "medium",
                "bloom_level": "understand",
                "knowledge_point": topic,
                "weakness_related": False,
            },
        ]

    @staticmethod
    def _format_quiz_to_markdown(quiz_items: List[Dict]) -> str:
        """将 quiz JSON 数组转为纯内容 Markdown 文本（只显示值，不显示 JSON 键名）"""
        if not quiz_items:
            return "暂无练习题"
        lines = []
        bloom_cn = {
            "remember": "记忆", "understand": "理解", "apply": "应用",
            "analyze": "分析", "evaluate": "评价", "create": "创造",
        }
        diff_cn = {"easy": "简单", "medium": "中等", "hard": "困难"}
        type_cn = {"choice": "选择题", "fill_blank": "填空题", "short_answer": "简答题"}

        for item in quiz_items:
            qid = item.get("id", len(lines) + 1)
            qtype = item.get("type", "choice")
            question = item.get("question", "")
            options = item.get("options", [])
            answer = item.get("answer", "")
            explanation = item.get("explanation", "")
            difficulty = item.get("difficulty", "")
            bloom = item.get("bloom_level", "")
            knowledge = item.get("knowledge_point", "")
            weakness = item.get("weakness_related", False)

            # 题目头部标签
            tags = []
            if difficulty:
                tags.append(diff_cn.get(difficulty, difficulty))
            if bloom:
                tags.append(bloom_cn.get(bloom, bloom))
            tags.append(type_cn.get(qtype, qtype))
            if weakness:
                tags.append("薄弱点针对性")
            tag_str = " · ".join(tags)

            lines.append(f"### 第{qid}题")
            lines.append(f"*{tag_str}*")
            if knowledge:
                lines.append(f"**知识点**: {knowledge}")
            lines.append("")
            lines.append(f"**题目**：{question}")
            lines.append("")

            if qtype == "choice" and options:
                for opt in options:
                    lines.append(f"- {opt}")
                lines.append("")

            if answer:
                lines.append(f"**答案**：{answer}")
            lines.append("")

            if explanation:
                lines.append(f"**解析**：{explanation}")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _fallback_bundle(self, state: LearningState, error: Exception = None) -> ResourceBundle:
        """整体降级：当资源包生成失败时返回降级内容"""
        topic = self._get_current_topic(state) or state.get("subject", "通用")
        return ResourceBundle(
            notes=self._fallback_content("notes", topic),
            mindmap=self._fallback_content("mindmap", topic),
            quiz=self._fallback_quiz(topic),
            code_example=self._fallback_content("code_example", topic),
        )

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        """Agent 级别降级"""
        super().fallback(state, error)
        bundle = self._fallback_bundle(state, error)
        return {
            "next_action": "orchestrate",
            "resources": self._bundle_to_items(bundle, state),
            "resource_bundle": bundle,
        }
