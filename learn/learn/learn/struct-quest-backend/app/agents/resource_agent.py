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
import asyncio

from app.agents.base import BaseAgent
from app.agents.state import LearningState, ResourceItem
from app.utils.logger import get_logger

logger = get_logger("resource_agent")

# 延迟导入避免循环依赖
_content_cache = None


def _get_cache():
    global _content_cache
    if _content_cache is None:
        from app.services.content_cache import cache_service
        _content_cache = cache_service
    return _content_cache


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

ANIMATION_TEMPLATE = """你是一位算法可视化专家。请用 Manim Community Edition 编写**有真实动画的**教学视频。

## 主题
{topic}

## 步骤描述
{description}

## 难度等级
{difficulty}

## 🎯 目标：生成真正的算法可视化动画（不是纯文字！）

观众要看到**真实的算法执行过程**——节点、连线、数组元素位置变化、颜色高亮等。文字只是辅助标注。

---

## ✅ 允许使用的对象（按算法类型选用）

| 类别 | 可用对象 |
|------|---------|
| 文本 | `Text`(中文字符串, font=CHINESE_FONT, font_size=20~36) |
| 节点 | `Circle`, `Square`, `RoundedRectangle`(radius=0.1) |
| 数组元素 | `Square(side_length=0.8)` + `Text(数值)` 组合成 `VGroup` |
| 指针/连线 | `Arrow`, `Line`, `DashedLine` |
| 树节点 | `Circle(radius=0.35)` + `Text(数值)` 放在 `VGroup` 里 |
| 树边 | `Line(节点1.get_center(), 节点2.get_center(), stroke_width=3)` |
| 容器 | `VGroup(...)` 把多个对象编组 |
| 布局 | `.move_to()`, `.next_to()`, `.shift()`, `.to_edge()` |
| 动画 | `Create`, `Write`, `FadeIn`, `FadeOut`, `Transform`, `Indicate`, `Flash`, `Circumscribe` |
| 数学 | `numpy as np`(用于坐标计算) |
| 控制流 | `for` 循环、`if` 条件、`def` 辅助函数(放在 construct 内部或作为方法) |

---

## 📋 通用模板：二叉树遍历（后序/前序/中序、层序、BFS/DFS）

```python
from manim import *
import os

if os.name == "nt":
    CHINESE_FONT = "C:/Windows/Fonts/msyh.ttc"
else:
    CHINESE_FONT = "Noto Sans CJK SC"

def make_node(value, color=BLUE):
    \"\"\"创建一个树节点：圆 + 文字\"\"\"
    circle = Circle(radius=0.35, color=color, fill_opacity=0.3)
    text = Text(str(value), font_size=24, color=WHITE, font=CHINESE_FONT)
    return VGroup(circle, text)

def make_edge(p1, p2):
    \"\"\"创建一条树边\"\"\"
    return Line(p1.get_center(), p2.get_center(), color=GREY, stroke_width=3)

class AlgorithmScene(Scene):
    def construct(self):
        # ===== 标题 =====
        title = Text("二叉树后序遍历", font_size=36, color=YELLOW, font=CHINESE_FONT)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.5)

        # ===== 构建树 =====
        #       1
        #      / \\
        #     2   3
        #    / \\
        #   4   5
        n1 = make_node(1, BLUE).move_to([0, 1.5, 0])
        n2 = make_node(2, BLUE).move_to([-1.5, 0.3, 0])
        n3 = make_node(3, BLUE).move_to([1.5, 0.3, 0])
        n4 = make_node(4, BLUE).move_to([-2.2, -0.9, 0])
        n5 = make_node(5, BLUE).move_to([-0.8, -0.9, 0])

        edges = VGroup(
            make_edge(n1, n2), make_edge(n1, n3),
            make_edge(n2, n4), make_edge(n2, n5),
        )
        nodes = VGroup(n1, n2, n3, n4, n5)

        self.play(LaggedStart(*[Create(c) for c in edges], lag_ratio=0.2))
        self.play(LaggedStart(*[FadeIn(n, scale=0.5) for n in nodes], lag_ratio=0.2))
        self.wait(0.5)

        # ===== 遍历过程：依次高亮 + 记录访问顺序 =====
        visit_order = [4, 5, 2, 3, 1]  # 后序：左、右、根
        output_text = Text("输出: ", font_size=24, color=GREEN, font=CHINESE_FONT)
        output_text.to_edge(DOWN).shift(LEFT * 3)
        self.play(Write(output_text))

        output_str = ""
        node_map = {1: n1, 2: n2, 3: n3, 4: n4, 5: n5}

        for v in visit_order:
            node = node_map[v]
            # 高亮当前节点
            self.play(
                node[0].animate.set_fill(YELLOW, opacity=0.8),
                Indicate(node, color=YELLOW),
                run_time=0.6
            )
            # 追加到输出文字
            new_output = Text(f"输出: {' → '.join(map(str, visit_order[:visit_order.index(v)+1]))}",
                            font_size=24, color=GREEN, font=CHINESE_FONT)
            new_output.move_to(output_text.get_center())
            self.play(Transform(output_text, new_output), run_time=0.4)
            # 标记为已访问
            self.play(node[0].animate.set_fill(GREEN, opacity=0.5), run_time=0.3)

        self.wait(2)
        self.play(FadeOut(VGroup(title, nodes, edges, output_text)))
```

---

## 📋 数组算法模板（排序/查找/双指针等）

```python
from manim import *
import os

if os.name == "nt":
    CHINESE_FONT = "C:/Windows/Fonts/msyh.ttc"
else:
    CHINESE_FONT = "Noto Sans CJK SC"

def make_array(values, box_size=0.7):
    \"\"\"把列表转成 VGroup(方块+数字)\"\"\"
    cells = VGroup()
    for v in values:
        square = Square(side_length=box_size, color=BLUE, fill_opacity=0.2)
        text = Text(str(v), font_size=22, color=WHITE, font=CHINESE_FONT)
        cell = VGroup(square, text)
        # 文字居中叠在方块上
        text.move_to(square.get_center())
        cells.add(cell)
    cells.arrange(RIGHT, buff=0.05)
    return cells

class AlgorithmScene(Scene):
    def construct(self):
        # ===== 标题 =====
        title = Text("数组演示", font_size=36, color=YELLOW, font=CHINESE_FONT)
        title.to_edge(UP)
        self.play(Write(title))

        # ===== 数组 =====
        arr = [5, 2, 8, 1, 9, 3]
        cells = make_array(arr).shift(DOWN * 0.5)
        self.play(LaggedStart(*[FadeIn(c, shift=UP*0.3) for c in cells], lag_ratio=0.1))
        self.wait(0.5)

        # ===== 高亮某个元素（比如最大值） =====
        max_idx = arr.index(max(arr))
        max_cell = cells[max_idx]
        self.play(max_cell[0].animate.set_fill(YELLOW, opacity=0.8))
        self.play(Indicate(max_cell, color=YELLOW))
        self.wait(0.5)

        # ===== 交换两个元素的位置 =====
        i, j = 0, 3
        cell_i, cell_j = cells[i], cells[j]
        # 记录原始位置
        pos_i, pos_j = cell_i.get_center(), cell_j.get_center()
        self.play(
            cell_i.animate.move_to(pos_j),
            cell_j.animate.move_to(pos_i),
            run_time=1.2
        )
        self.wait(0.5)

        # ===== 标注指针 =====
        arrow = Arrow(UP, DOWN, color=RED).next_to(cells[1], UP, buff=0.2)
        label = Text("i", font_size=22, color=RED, font=CHINESE_FONT).next_to(arrow, UP, buff=0.1)
        self.play(Create(arrow), Write(label))
        self.wait(1)

        self.play(FadeOut(VGroup(title, cells, arrow, label)))
```

---

## 📝 填写规则

1. **根据「主题」选择最合适的模板**：
   - 树相关（遍历/搜索/构建/删除）→ 用**二叉树模板**
   - 数组/链表/排序/查找 → 用**数组模板**
   - 图算法 → 用二叉树模板的思路（节点+边）
   - 其他概念（递归/DP/栈）→ 自由发挥
2. **可以修改节点数量、位置、值、颜色**
3. **可以增删步骤**，但要保持动画连贯
4. **必须用 `font=CHINESE_FONT`** 渲染中文
5. **运行时间控制在 5~25 秒**（总帧数 150~750）

## ⚠️ 极其重要
- 主题是「**{topic}**」——必须围绕这个主题生成对应的可视化！
- 不要照搬模板里的变量名（如"5 2 8 1 9 3"）——要根据主题换成合适的数据
- 必须**真正画出算法执行过程**，而不是只写文字说明
- 节点位置可以用 `move_to([x, y, 0])` 直接给坐标，方便控制布局

请直接输出完整 Python 代码（不要 markdown 包裹，不要 ```）："""





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
    FULL_RESOURCE_TYPES = [
        "notes",
        "mindmap",
        "quiz",
        "code_example",
        "animation",      # 🎬 动画视频 (Manim)
        "ppt_outline",    # ★ v4 新增：PPT大纲 (Markdown)
    ]

    # 类型元信息（供前端展示用）
    TYPE_META = {
        "notes":        {"icon": "📖", "label": "学习讲义", "format": "markdown", "color": "#4F46E5"},
        "mindmap":      {"icon": "🧠", "label": "思维导图", "format": "markmap", "color": "#8B5CF6"},
        "quiz":         {"icon": "✏️", "label": "练习题", "format": "json", "color": "#EF4444"},
        "code_example": {"icon": "💻", "label": "代码案例", "format": "python", "color": "#10B981"},
        "animation":    {"icon": "🎬", "label": "动画演示", "format": "video", "color": "#EC4899"},
        "ppt_outline":  {"icon": "📊", "label": "PPT大纲", "format": "markdown", "color": "#F59E0B"},
    }

    # 模板映射
    TEMPLATE_MAP = {
        "notes": NOTES_TEMPLATE,
        "mindmap": MINDMAP_TEMPLATE,
        "quiz": QUIZ_TEMPLATE,
        "code_example": CODE_EXAMPLE_TEMPLATE,
        "animation": ANIMATION_TEMPLATE,
        "ppt_outline": NOTES_TEMPLATE,  # ★ v4：PPT大纲复用讲义模板（结构化输出）
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
            "ppt_outline": lambda: self._gen_ppt_outline(common, topic, subject),
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
                # ★ 步骤1：三层缓存检索（Redis → SQLite → ChromaDB）
                cached = self._search_resource_cache(res_type, topic, subject)
                if cached:
                    logger.info("📋 %s 从缓存命中，复用 (%d 字符)", res_type, len(str(cached)))
                    bundle[res_type] = cached
                    continue

                # ★ 步骤2：未命中则 AI 生成
                logger.info("🔄 正在 AI 生成 %s...", res_type)
                generated = RESOURCE_GENERATORS[res_type]()
                bundle[res_type] = generated
                logger.info("✅ %s 生成完成 (%d 字符)", res_type, len(str(generated)))

                # ★ 步骤3：写入三层缓存（asyncio.run 独立事件循环，线程池安全）
                try:
                    asyncio.run(_get_cache().save_cache(
                        res_type, topic, subject, str(generated)))
                    logger.info("✅ 缓存已写入: %s/%s (%d 字符)", res_type, topic, len(str(generated)))
                except Exception as e:
                    logger.debug("缓存写入跳过: %s", e)
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

    # ── 📊 PPT 大纲生成 ──

    def _gen_ppt_outline(self, common, topic, subject):
        """生成 PPT 大纲（Markdown 格式，可直接送入 PPT 生成器）"""
        rag_ctx = self._retrieve_for_resource(topic, "notes", subject)
        params = {**common, "rag_context": rag_ctx, "style_guide": "PPT大纲格式，每页一个 ## 标题，下面用 - 列举要点"}
        raw = self._generate_single("ppt_outline", params)
        # 清洗为结构化大纲
        return self._clean_ppt_outline(raw, topic)

    @staticmethod
    def _clean_ppt_outline(raw: str, topic: str) -> str:
        """清洗 PPT 大纲输出，确保格式规范"""
        stripped = raw.strip()
        if not stripped.startswith("#"):
            stripped = f"# {topic} PPT大纲\n\n{stripped}"
        # 确保有基本结构
        lines = stripped.split("\n")
        has_h2 = any(l.startswith("## ") for l in lines)
        if not has_h2:
            stripped += f"\n\n## 核心概念\n- 定义\n- 特性\n\n## 原理详解\n- 要点1\n- 要点2\n\n## 应用场景\n- 场景1\n- 场景2\n\n## 总结\n- 关键点"
        return stripped

    # ── 🎬 动画视频生成 (Manim) ──

    def _gen_animation(self, common, topic, subject):
        """
        生成动画视频资源（v5 硬编码模板方案）。

        流程：
        1. LLM 生成步骤描述（JSON: title + steps + result）
        2. Python 硬编码模板拼出 Manim 代码
        3. 调用 ManimRenderer 沙箱渲染 MP4

        这样 LLM 不参与代码生成，100% 保证代码可渲染且内容正确。
        """
        import time as _time, json as _json
        start = _time.time()

        print("[v5-NEW] _gen_animation 使用硬编码模板方案 (topic=%s)" % topic, flush=True)

        try:
            from app.services.manim_renderer import get_renderer

            renderer = get_renderer()

            # ── 步骤1：LLM 只生成文字内容（JSON），不生成代码 ──
            steps_json = self._generate_animation_steps(common, topic)
            if not steps_json:
                return self._animation_fallback("", "无法生成步骤描述")

            title = steps_json.get("title", topic)
            steps = steps_json.get("steps", [f"了解{topic}的基本概念", f"掌握{topic}的核心操作", f"能够应用{topic}解决实际问题"])
            result_text = steps_json.get("result", f"掌握{topic}")

            logger.info("🎬 步骤描述: title=%s, steps=%d, result=%s", title, len(steps), result_text)

            # ── 步骤2：硬编码模板拼出 Manim 代码 ──
            try:
                manim_code = self._build_manim_code(title, steps, result_text)
                logger.info("🎬 Manim 代码已构建 (%d 字符)，前200字符: %s", len(manim_code), manim_code[:200])
            except Exception as e:
                logger.error("❌ Manim 代码构建失败: %s", e)
                return self._animation_fallback("", f"代码构建失败: {e}")

            # ── 步骤3：沙箱渲染 ──
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
    #  ★ v5：动画步骤生成 + 硬编码代码模板
    # ═══════════════════════════════════════════

    def _generate_animation_steps(self, common: Dict, topic: str) -> Optional[Dict]:
        """让 LLM 生成动画的步骤描述（JSON），不涉及代码生成"""
        import json as _json
        prompt = f"""你是数据结构教学专家。请为「{topic}」生成一个动画演示的步骤描述。

严格返回 JSON 格式（不要任何其他文字）：
{{
    "title": "中文标题（如：二叉树后序遍历）",
    "steps": [
        "步骤1的具体描述，一句话",
        "步骤2的具体描述，一句话",
        ...
    ],
    "result": "最终结果描述，一句话"
}}

要求：
- title：10-20字的简洁标题
- steps：4-6个步骤，每个步骤一句话（15-30字），按时间顺序描述核心操作
- result：一句话总结最终输出（10-20字）
- 所有文字必须是简体中文
- 只输出 JSON，不要包裹在 ``` 中
- 必须包含当前主题「{topic}」的具体内容，不得编造无关主题"""

        try:
            response = self._call_llm(
                [{"role": "user", "content": prompt}],
                temperature=0.5, max_tokens=800,
            )
            data = self._parse_json(response)
            if data and isinstance(data, dict) and "steps" in data:
                return data
        except Exception as e:
            logger.warning("⚠️ 动画步骤生成失败: %s", e)
        return None

    @staticmethod
    def _build_manim_code(title: str, steps: list, result_text: str) -> str:
        """用硬编码模板拼接 Manim 代码。LLM 不参与代码生成，100% 可渲染。

        v6：智能识别主题类型（树/数组/图），用对应的**真实图形模板**渲染。
        """
        import json as _json

        # 转义双引号（防注入到 f-string）
        title_escaped = title.replace('"', '\\"').replace("'", "\\'")
        steps_json = _json.dumps(steps, ensure_ascii=False)
        result_escaped = result_text.replace('"', '\\"').replace("'", "\\'")

        # ── 智能识别可视化类型 ──
        viz_type = _detect_viz_type(title, steps, result_text)
        steps_count = len(steps) if steps else 3

        if viz_type == "tree":
            return _render_tree_template(title_escaped, steps_json, result_escaped, steps_count)
        elif viz_type == "array":
            return _render_array_template(title_escaped, steps_json, result_escaped, steps_count)
        elif viz_type == "graph":
            return _render_graph_template(title_escaped, steps_json, result_escaped, steps_count)
        else:
            # 兜底：原文字版（确保不会崩）
            return _render_text_template(title_escaped, steps_json, result_escaped)


# ════════════════════════════════════════════

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
            "ppt_outline":  ["概念 定义 原理 大纲 要点"],
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
        ★ 检索资源库：三层缓存查询（Redis → SQLite → ChromaDB）
        线程安全 — 使用 asyncio.run() 创建独立事件循环
        """
        try:
            result = asyncio.run(_get_cache().get_cache(res_type, topic, subject))
            if result:
                logger.info("✅ 缓存命中(%s/%s): %d 字符", res_type, topic, len(result))
            return result
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

#  v6 智能可视化模板：树 / 数组 / 图 / 文字
# ════════════════════════════════════════════

def _detect_viz_type(title: str, steps: list, result_text: str) -> str:
    """根据标题/步骤/结果关键词判断可视化类型"""
    text = (title + " " + " ".join(steps or []) + " " + result_text).lower()

    # 树相关
    tree_kw = ["树", "二叉", "bst", "遍历", "前序", "中序", "后序", "层序", "bfs", "dfs", "heap", "堆", "哈夫曼", "avl", "红黑"]
    if any(kw in text for kw in tree_kw):
        return "tree"

    # 图相关
    graph_kw = ["图", "最短路", "dijkstra", "prim", "kruskal", "拓扑", "关键路径", "floyd"]
    if any(kw in text for kw in graph_kw):
        return "graph"

    # 数组/排序/搜索
    array_kw = ["数组", "排序", "搜索", "查找", "冒泡", "快速排序", "归并", "插入排序", "选择排序", "堆排序",
                "二分", "线性查找", "双指针", "滑动窗口", "链表", "栈", "队列", "stack", "queue", "list"]
    if any(kw in text for kw in array_kw):
        return "array"

    return "text"


def _render_text_template(title_escaped: str, steps_json: str, result_escaped: str) -> str:
    """兜底模板：流程卡片图（每步用方块+箭头连接，至少有图形元素）"""
    return f'''from manim import *
import os

if os.name == "nt":
    CHINESE_FONT = "C:/Windows/Fonts/msyh.ttc"
else:
    CHINESE_FONT = "Noto Sans CJK SC"

class AlgorithmScene(Scene):
    def construct(self):
        # ===== 标题 =====
        title = Text("{title_escaped}", font_size=36, color=YELLOW, font=CHINESE_FONT)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        # ===== 输入卡片 =====
        steps = {steps_json}
        result_str = "{result_escaped}"

        # 起始节点
        start_box = RoundedRectangle(width=2.0, height=0.7, corner_radius=0.1,
                                     color=GREEN, fill_opacity=0.25, stroke_width=3)
        start_text = Text("开始", font_size=22, color=WHITE, font=CHINESE_FONT)
        start_text.move_to(start_box.get_center())
        start_node = VGroup(start_box, start_text).move_to([-5, 1.5, 0])
        self.play(FadeIn(start_node, shift=RIGHT*0.3))
        self.wait(0.2)

        # 步骤卡片（沿 X 轴排列）
        step_nodes = VGroup()
        step_boxes = []
        n = len(steps)
        for i, s in enumerate(steps):
            # 卡片大小按文字长度自适应
            w = max(1.8, min(3.5, 0.15 * len(s) + 0.6))
            box = RoundedRectangle(width=w, height=0.7, corner_radius=0.1,
                                   color=BLUE, fill_opacity=0.2, stroke_width=2)
            txt = Text(f"{{i+1}}. {{s[:18]}}{{'…' if len(s) > 18 else ''}}",
                       font_size=18, color=WHITE, font=CHINESE_FONT)
            txt.move_to(box.get_center())
            node = VGroup(box, txt)
            step_boxes.append((box, txt, node))
            step_nodes.add(node)

        # 步骤均匀分布在右侧
        if n > 0:
            step_nodes.arrange(RIGHT, buff=0.4)
            step_nodes.move_to([0, 0, 0])
            # 第一个步骤接在 start 之后
            if step_nodes[0].get_left()[0] < -3:
                step_nodes.shift(RIGHT * (-3 - step_nodes[0].get_left()[0]))

        # 起点→第一步
        first_arrow = Arrow(start_node.get_right(), step_nodes[0].get_left(),
                           color=WHITE, stroke_width=3, buff=0.15)
        self.play(Create(first_arrow), run_time=0.4)
        # 步骤依次弹出
        self.play(FadeIn(step_nodes[0], shift=UP*0.2), run_time=0.4)
        self.wait(0.2)

        # 步骤间用箭头连接
        for i in range(1, n):
            arr = Arrow(step_nodes[i-1].get_right(), step_nodes[i].get_left(),
                       color=WHITE, stroke_width=3, buff=0.15)
            self.play(FadeIn(step_nodes[i], shift=UP*0.2), Create(arr), run_time=0.5)
            self.wait(0.15)

        # 最后一个步骤 → 结果
        end_box = RoundedRectangle(width=2.2, height=0.7, corner_radius=0.1,
                                   color=YELLOW, fill_opacity=0.3, stroke_width=3)
        end_text = Text(f"→ {{result_str[:10]}}", font_size=20, color=WHITE, font=CHINESE_FONT)
        end_text.move_to(end_box.get_center())
        end_node = VGroup(end_box, end_text)
        if n > 0:
            end_node.next_to(step_nodes[-1], RIGHT, buff=0.6)
        else:
            end_node.next_to(start_node, RIGHT, buff=0.6)
        end_arrow = Arrow(step_nodes[-1].get_right() if n > 0 else start_node.get_right(),
                         end_node.get_left(), color=WHITE, stroke_width=3, buff=0.15)
        self.play(Create(end_arrow), FadeIn(end_node, shift=LEFT*0.2), run_time=0.5)
        self.wait(1.5)

        # 全部高亮闪烁（强调流程走完）
        for node in step_nodes:
            self.play(node[0].animate.set_fill(YELLOW, opacity=0.5), run_time=0.15)
        self.play(end_node[0].animate.set_fill(GREEN, opacity=0.6), run_time=0.3)
        self.wait(1.5)

        # 收尾
        self.play(*[FadeOut(m) for m in [title, start_node, step_nodes, end_node, first_arrow, end_arrow]])
'''


def _render_tree_template(title_escaped: str, steps_json: str, result_escaped: str, steps_count: int) -> str:
    """二叉树遍历模板：绘制5节点二叉树，按访问顺序依次高亮"""
    # 树结构（硬编码示例）：
    #         1
    #        / \\
    #       2   3
    #      / \\
    #     4   5
    return f'''from manim import *
import os

if os.name == "nt":
    CHINESE_FONT = "C:/Windows/Fonts/msyh.ttc"
else:
    CHINESE_FONT = "Noto Sans CJK SC"

class AlgorithmScene(Scene):
    def construct(self):
        # ===== 标题 =====
        title = Text("{title_escaped}", font_size=36, color=YELLOW, font=CHINESE_FONT)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        # ===== 构建节点（位置硬编码） =====
        def make_node(value, x, y, color=BLUE):
            c = Circle(radius=0.35, color=color, fill_opacity=0.2, stroke_width=3)
            t = Text(str(value), font_size=24, color=WHITE, font=CHINESE_FONT)
            node = VGroup(c, t)
            node.move_to([x, y, 0])
            return node

        n1 = make_node(1,  0,    1.8)
        n2 = make_node(2, -1.8,  0.5)
        n3 = make_node(3,  1.8,  0.5)
        n4 = make_node(4, -2.6, -0.8)
        n5 = make_node(5, -1.0, -0.8)

        node_map = {{1: n1, 2: n2, 3: n3, 4: n4, 5: n5}}
        nodes = VGroup(n1, n2, n3, n4, n5)

        # ===== 构建边 =====
        def make_edge(n_a, n_b):
            return Line(n_a.get_center(), n_b.get_center(), color=GREY, stroke_width=3)

        edges = VGroup(
            make_edge(n1, n2), make_edge(n1, n3),
            make_edge(n2, n4), make_edge(n2, n5),
        )

        # ===== 绘制树 =====
        self.play(LaggedStart(*[Create(e) for e in edges], lag_ratio=0.15))
        self.play(LaggedStart(*[FadeIn(n, scale=0.6) for n in nodes], lag_ratio=0.15))
        self.wait(0.3)

        # ===== 步骤文字（左下角） =====
        steps = {steps_json}
        steps_text = Text("步骤 0/{0}".format(len(steps)), font_size=22, color=WHITE, font=CHINESE_FONT)
        steps_text.to_edge(DOWN).shift(LEFT * 3.5)
        self.play(Write(steps_text))

        # ===== 遍历顺序：按主题自适应（后序→4,5,2,3,1 / 前序→1,2,4,5,3 / 中序→4,2,5,1,3 / 层序→1,2,3,4,5） =====
        title_lower = "{title_escaped}".lower()
        if "后序" in "{title_escaped}":
            order = [4, 5, 2, 3, 1]
        elif "前序" in "{title_escaped}":
            order = [1, 2, 4, 5, 3]
        elif "中序" in "{title_escaped}":
            order = [4, 2, 5, 1, 3]
        elif "层序" in "{title_escaped}" or "bfs" in title_lower:
            order = [1, 2, 3, 4, 5]
        else:
            # 默认：层序
            order = [1, 2, 3, 4, 5]

        # ===== 依次访问高亮 =====
        output_label = Text("输出: ", font_size=24, color=GREEN, font=CHINESE_FONT)
        output_label.to_edge(DOWN).shift(RIGHT * 1.5)
        self.play(Write(output_label))

        collected = []
        for idx, val in enumerate(order):
            node = node_map[val]
            # 高亮节点
            self.play(
                node[0].animate.set_fill(YELLOW, opacity=0.9),
                Indicate(node, color=YELLOW, scale_factor=1.2),
                run_time=0.6
            )
            # 收集到输出
            collected.append(str(val))
            new_output = Text("→ ".join(collected), font_size=24, color=GREEN, font=CHINESE_FONT)
            new_output.move_to(output_label.get_center()).shift(RIGHT * 0.8)
            self.play(Transform(output_label, new_output), run_time=0.3)
            # 标记为已访问
            self.play(node[0].animate.set_fill(GREEN, opacity=0.5), run_time=0.2)
            # 更新步骤计数
            new_steps = Text("步骤 {{}}/{0}".format(len(order)), font_size=22, color=WHITE, font=CHINESE_FONT)
            new_steps.move_to(steps_text.get_center())
            self.play(Transform(steps_text, new_steps), run_time=0.2)

        self.wait(1.5)

        # ===== 结果 =====
        result = Text("结果: {result_escaped}", font_size=28, color=YELLOW, font=CHINESE_FONT)
        result.to_edge(DOWN).shift(UP * 0.8)
        self.play(Write(result))
        self.wait(2)

        self.play(*[FadeOut(m) for m in [title, nodes, edges, steps_text, output_label, result]])
'''


def _render_array_template(title_escaped: str, steps_json: str, result_escaped: str, steps_count: int) -> str:
    """数组算法模板：方格+数字，高亮+交换+指针"""
    # 默认演示数组
    return f'''from manim import *
import os

if os.name == "nt":
    CHINESE_FONT = "C:/Windows/Fonts/msyh.ttc"
else:
    CHINESE_FONT = "Noto Sans CJK SC"

class AlgorithmScene(Scene):
    def construct(self):
        # ===== 标题 =====
        title = Text("{title_escaped}", font_size=36, color=YELLOW, font=CHINESE_FONT)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        # ===== 数组（硬编码示例，可适配多种场景） =====
        values = [5, 2, 8, 1, 9, 3]
        cells = VGroup()
        for v in values:
            square = Square(side_length=0.7, color=BLUE, fill_opacity=0.15, stroke_width=2)
            text = Text(str(v), font_size=24, color=WHITE, font=CHINESE_FONT)
            text.move_to(square.get_center())
            cell = VGroup(square, text)
            cells.add(cell)
        cells.arrange(RIGHT, buff=0.1)
        cells.shift(DOWN * 0.3)
        self.play(LaggedStart(*[FadeIn(c, shift=UP*0.4) for c in cells], lag_ratio=0.1))
        self.wait(0.3)

        # ===== 索引标签 =====
        index_labels = VGroup()
        for i in range(len(values)):
            lbl = Text(str(i), font_size=18, color=GREY, font=CHINESE_FONT)
            lbl.next_to(cells[i], DOWN, buff=0.15)
            index_labels.add(lbl)
        self.play(Write(index_labels))

        # ===== 指针 i 初始化在 index 0 =====
        ptr_i = Arrow(UP, DOWN, color=RED, stroke_width=4).scale(0.6)
        ptr_i.next_to(cells[0], UP, buff=0.25)
        label_i = Text("i", font_size=22, color=RED, font=CHINESE_FONT).next_to(ptr_i, UP, buff=0.05)
        self.play(Create(ptr_i), Write(label_i))
        self.wait(0.3)

        # ===== 遍历高亮 =====
        steps = {steps_json}
        for i in range(min(len(steps), len(values))):
            target = cells[i]
            # 高亮当前格
            self.play(
                target[0].animate.set_fill(YELLOW, opacity=0.7),
                Indicate(target, color=YELLOW),
                run_time=0.6
            )
            # 移动指针到下一个
            if i < len(values) - 1:
                self.play(
                    ptr_i.animate.next_to(cells[i+1], UP, buff=0.25),
                    label_i.animate.next_to(cells[i+1], UP * 1.1, buff=0.4),
                    run_time=0.4
                )
            # 标记为已访问
            self.play(target[0].animate.set_fill(GREEN, opacity=0.3), run_time=0.2)
            self.wait(0.3)

        # ===== 结果 =====
        result = Text("结果: {result_escaped}", font_size=28, color=YELLOW, font=CHINESE_FONT)
        result.next_to(cells, DOWN, buff=0.8)
        self.play(Write(result))
        self.wait(2)

        self.play(*[FadeOut(m) for m in [title, cells, index_labels, ptr_i, label_i, result]])
'''


def _render_graph_template(title_escaped: str, steps_json: str, result_escaped: str, steps_count: int) -> str:
    """图算法模板：节点+边的网络图（5节点示例）"""
    return f'''from manim import *
import os

if os.name == "nt":
    CHINESE_FONT = "C:/Windows/Fonts/msyh.ttc"
else:
    CHINESE_FONT = "Noto Sans CJK SC"

class AlgorithmScene(Scene):
    def construct(self):
        # ===== 标题 =====
        title = Text("{title_escaped}", font_size=36, color=YELLOW, font=CHINESE_FONT)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(0.3)

        # ===== 5节点图（环形示例） =====
        #     A(顶)
        #    /  \\
        #   B    C
        #   |    |
        #   D----E
        positions = {{
            "A": [ 0,    1.6, 0],
            "B": [-1.8,  0.3, 0],
            "C": [ 1.8,  0.3, 0],
            "D": [-1.2, -1.2, 0],
            "E": [ 1.2, -1.2, 0],
        }}
        edges_list = [("A","B"), ("A","C"), ("B","D"), ("C","E"), ("D","E")]

        # 创建节点
        node_map = {{}}
        for name, pos in positions.items():
            c = Circle(radius=0.35, color=BLUE, fill_opacity=0.2, stroke_width=3)
            t = Text(name, font_size=22, color=WHITE, font=CHINESE_FONT)
            node = VGroup(c, t).move_to(pos)
            node_map[name] = node

        nodes = VGroup(*node_map.values())

        # 创建边
        edges = VGroup()
        for a, b in edges_list:
            edges.add(Line(node_map[a].get_center(), node_map[b].get_center(),
                          color=GREY, stroke_width=3))

        # 绘制图
        self.play(LaggedStart(*[Create(e) for e in edges], lag_ratio=0.1))
        self.play(LaggedStart(*[FadeIn(n, scale=0.6) for n in nodes], lag_ratio=0.1))
        self.wait(0.3)

        # ===== BFS 遍历：依次高亮 A→B→C→D→E =====
        steps = {steps_json}
        visit_order = ["A", "B", "C", "D", "E"]
        output_label = Text("队列: ", font_size=22, color=GREEN, font=CHINESE_FONT)
        output_label.to_edge(DOWN).shift(LEFT * 2.5)
        self.play(Write(output_label))

        collected = []
        for idx, name in enumerate(visit_order):
            node = node_map[name]
            self.play(
                node[0].animate.set_fill(YELLOW, opacity=0.9),
                Indicate(node, color=YELLOW, scale_factor=1.2),
                run_time=0.6
            )
            collected.append(name)
            new_out = Text(" → ".join(collected), font_size=24, color=GREEN, font=CHINESE_FONT)
            new_out.move_to(output_label.get_center()).shift(RIGHT * 0.9)
            self.play(Transform(output_label, new_out), run_time=0.3)
            self.play(node[0].animate.set_fill(GREEN, opacity=0.5), run_time=0.2)

        self.wait(1.5)
        result = Text("结果: {result_escaped}", font_size=28, color=YELLOW, font=CHINESE_FONT)
        result.next_to(output_label, UP, buff=0.4)
        self.play(Write(result))
        self.wait(2)

        self.play(*[FadeOut(m) for m in [title, nodes, edges, output_label, result]])
'''
