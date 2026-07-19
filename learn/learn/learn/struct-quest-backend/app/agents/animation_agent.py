"""
AI 算法实验室 - 动画生成智能体

将自然语言请求转换为可视化动画步骤序列。
支持：
- 排序算法（冒泡、快速、归并、堆...）
- 树结构（BST/AVL/红黑树旋转）
- 图算法（BFS/DFS/Dijkstra...）
- 链表操作
- 其他常见数据结构算法

输出标准 AnimCommand JSON，可被前端渲染引擎直接消费。
"""

import json
import time
import re
import hashlib
from typing import Dict, List, Optional, Any
from app.services.llm import llm_service


# ═══════════════════════════════════════════════════════
#  动画指令校验器
# ═══════════════════════════════════════════════════════

VALID_OPS = {
    # 数组类
    "set_data", "swap", "compare", "mark", "mark_range",
    "pivot", "partition", "shift",
    # 树
    "tree_build", "tree_mark", "tree_rotate_left", "tree_rotate_right",
    "tree_insert", "tree_delete",
    # 图
    "graph_build", "graph_visit", "graph_edge_highlight", "graph_path_highlight",
    # 链表
    "list_build", "list_mark", "list_insert", "list_delete",
    # 控制
    "wait", "speed",
}

def validate_animation_steps(data: dict) -> dict:
    """
    校验 + 清洗 AI 生成的动画步骤，保证前端可安全渲染。

    检查项：
    1. steps 数组非空
    2. 每条 step 有 narration
    3. commands 中的 op 在合法集合内
    4. 去除不合法 command
    5. 步骤数上限 25 步（防过长）
    6. narration 长度上限 200 字
    """
    if not data or not isinstance(data, dict):
        raise ValueError("AI 返回了空数据")

    steps = data.get("steps", [])
    if not steps or not isinstance(steps, list):
        raise ValueError(f"缺少 steps 数组（{len(steps)} 步）")

    cleaned_steps = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        narration = str(step.get("narration", ""))[:200]
        if not narration.strip():
            narration = f"步骤 {i + 1}"

        commands = []
        for cmd in step.get("commands", []):
            if not isinstance(cmd, dict):
                continue
            op = cmd.get("op", "")
            if op in VALID_OPS:
                commands.append(cmd)

        cleaned_steps.append({
            "narration": narration,
            "commands": commands,
            "code_line": max(-1, int(step.get("code_line", -1))),
            "code_explanation": str(step.get("code_explanation", ""))[:150],
        })

    if len(cleaned_steps) > 25:
        cleaned_steps = cleaned_steps[:25]

    if len(cleaned_steps) == 0:
        raise ValueError("校验后无可执行步骤")

    data["steps"] = cleaned_steps
    return data


# ═══════════════════════════════════════════════════════
#  本地预设匹配器（无 LLM 调用，前端也有一份）
# ═══════════════════════════════════════════════════════

PRESET_KEYWORDS = {
    "bubble_sort":    ["冒泡", "bubble", "气泡"],
    "quick_sort":     ["快排", "快速排序", "quick", "partition", "分区"],
    "merge_sort":     ["归并", "merge", "合并排序"],
    "insertion_sort": ["插入排序", "insertion", "插排"],
    "selection_sort": ["选择排序", "selection"],
    "heap_sort":      ["堆排序", "heap", "堆"],
    "binary_search":  ["二分", "binary search", "折半"],
    "bst_insert":     ["BST", "二叉搜索树插入", "二叉查找树"],
    "avl_rotate_left":  ["AVL左旋", "左单旋", "LL旋转"],
    "avl_rotate_right": ["AVL右旋", "右单旋", "RR旋转"],
    "graph_bfs":      ["BFS", "广度优先", "广度"],
    "graph_dfs":      ["DFS", "深度优先", "深度"],
    "linked_list_reverse": ["链表反转", "反转链表"],
    "linked_list_insert":  ["链表插入"],
    "linked_list_delete":  ["链表删除"],
}

def match_preset(text: str) -> Optional[str]:
    """匹配预设算法，命中返回 algo_id，否则 None"""
    text_lower = text.lower().strip()
    for algo_id, keywords in PRESET_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return algo_id
    return None


# ═══════════════════════════════════════════════════════
#  生成结果缓存（内存 LRU，可选持久化到 DB）
# ═══════════════════════════════════════════════════════

_cache: Dict[str, dict] = {}
MAX_CACHE_SIZE = 100

def _cache_key(prompt: str, level: str) -> str:
    raw = f"{prompt}::{level}"
    return hashlib.md5(raw.encode()).hexdigest()

def cache_get(prompt: str, level: str) -> Optional[dict]:
    return _cache.get(_cache_key(prompt, level))

def cache_set(prompt: str, level: str, data: dict):
    key = _cache_key(prompt, level)
    if len(_cache) >= MAX_CACHE_SIZE:
        # 简单淘汰：删除最旧的
        oldest = next(iter(_cache))
        del _cache[oldest]
    _cache[key] = data

def cache_clear():
    """清空缓存（旧 prompt 生成的答案可能格式不兼容）"""
    _cache.clear()


# ═══════════════════════════════════════════════════════
#  AI 动画生成核心
# ═══════════════════════════════════════════════════════

SYSTEM_PROMPT = """你是一个算法动画生成器。根据用户请求，生成完整的算法可视化教学步骤。

输出必须是合法 JSON（不要用 Markdown 代码块包裹）：

{
  "algorithm": "算法名称",
  "category": "sorting|search|tree|graph|linked_list|other",
  "complexity": {"time": "时间复杂度", "space": "空间复杂度"},
  "code": "算法的伪代码或 JavaScript 代码（多行字符串）",
  "steps": [
    {
      "narration": "这一步的口播讲解（口语化，像老师在讲课，中文）",
      "commands": [
        {"op": "操作名", ...参数}
      ],
      "code_line": 对应代码行号(0-based, -1表示无关),
      "code_explanation": "这行代码的简短解释"
    }
  ],
  "summary": "学习总结建议"
}

支持的动画操作 op（sorting/array 类型）：
- {"op": "set_data", "data": [8,3,9,2,1]}     // 初始化数组
- {"op": "swap", "i": 0, "j": 3}               // 交换两个元素
- {"op": "compare", "i": 0, "j": 1}            // 比较两个元素
- {"op": "mark", "indices": [2,3], "color": "#ef4444"}  // 标记元素
- {"op": "pivot", "index": 4}                   // 标记为 pivot
- {"op": "partition", "low": 0, "high": 5}      // 分区操作

树类型（★ 必须先用 tree_build 输出完整树结构）：
- {"op": "tree_build", "structure": {"nodes": [{"value": 50}, {"value": 30}, {"value": 70}], "edges": [{"from": 50, "to": 30, "side": "left"}, {"from": 50, "to": 70, "side": "right"}]}}
- {"op": "tree_mark", "node": 30, "color": "#ef4444"}   // 标记节点，color: #ef4444红, #f59e0b橙, #22c55e绿, #6366f1紫
- {"op": "tree_rotate_left", "node": 30}
- {"op": "tree_rotate_right", "node": 30}

图类型（★ 必须先用 graph_build 给出邻接表）：
- {"op": "graph_build", "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}], "adjList": {"A": ["B","C"], "B": ["A"], "C": ["A","B"]}}
- {"op": "graph_visit", "node": "A"}                     // 访问/标记节点
- {"op": "graph_edge_highlight", "from": "A", "to": "B"} // 高亮边

链表类型（★ 必须先用 list_build 输出初始链表）：
- {"op": "list_build", "values": [1,2,3,4,5]}            // 初始化链表节点
- {"op": "list_insert", "values": [1,2,3,4,5], "position": 2}   // 插入后完整链表 + 位置
- {"op": "list_delete", "values": [1,2,4,5], "position": 2}     // 删除后完整链表 + 位置
- {"op": "list_mark", "position": 2, "color": "#ef4444"}

规则：
1. 每步 2-5 条 command
2. 步骤总数 8-15 步（过多会太慢）
3. narration 口语化，用中文，像老师在讲课
4. 数组数据 6-10 个元素（太多视觉乱）
5. 为每一步指定 code_line（0-based）和 code_explanation
6. code 字段写完整的可运行代码
7. 如果是排序，第一步用 set_data 初始化数组，最后标记所有元素为 sorted
8. ★★ 树/图/链表类必须第一步输出结构化命令（tree_build/graph_build/list_build），否则前端无法渲染
9. ★ 遍历类（DFS/BFS/前/中/后序）：第一步用结构化命令建结构，后续步骤用 mark/visit 标记访问过的节点

【示例：后序遍历二叉树】
{
  "algorithm": "后序遍历二叉树",
  "category": "tree",
  "complexity": {"time": "O(n)", "space": "O(h)"},
  "code": "function postOrder(node) {\n  if (node === null) return;\n  postOrder(node.left);\n  postOrder(node.right);\n  visit(node);\n}",
  "steps": [
    {"narration": "构建二叉树：根50，左30右70", "commands": [{"op": "tree_build", "structure": {"nodes": [{"value":50},{"value":30},{"value":70},{"value":20},{"value":40}], "edges": [{"from":50,"to":30,"side":"left"},{"from":50,"to":70,"side":"right"},{"from":30,"to":20,"side":"left"},{"from":30,"to":40,"side":"right"}]}}], "code_line": 0, "code_explanation": "构造二叉树"},
    {"narration": "后序遍历：先左子树，从根到左子30", "commands": [{"op": "tree_mark", "node": 50, "color": "#f59e0b"}, {"op": "tree_mark", "node": 30, "color": "#6366f1"}], "code_line": 2, "code_explanation": "先递归访问左子树"},
    {"narration": "继续深入30的左子20", "commands": [{"op": "tree_mark", "node": 30, "color": "#f59e0b"}, {"op": "tree_mark", "node": 20, "color": "#6366f1"}], "code_line": 2, "code_explanation": "递归到底"},
    {"narration": "20没有子树，访问20（后序：左右根）", "commands": [{"op": "tree_mark", "node": 20, "color": "#22c55e"}], "code_line": 4, "code_explanation": "visit(20)"},
    {"narration": "回到30，访问30的右子40", "commands": [{"op": "tree_mark", "node": 20, "color": "#f59e0b"}, {"op": "tree_mark", "node": 40, "color": "#6366f1"}], "code_line": 3, "code_explanation": "postOrder(right)"},
    {"narration": "40没有子树，访问40", "commands": [{"op": "tree_mark", "node": 40, "color": "#22c55e"}], "code_line": 4, "code_explanation": "visit(40)"},
    {"narration": "30的左右都访问了，访问30", "commands": [{"op": "tree_mark", "node": 30, "color": "#22c55e"}], "code_line": 4, "code_explanation": "visit(30)"},
    {"narration": "同样访问根的右子树70、最后访问根50", "commands": [{"op": "tree_mark", "node": 70, "color": "#22c55e"}, {"op": "tree_mark", "node": 50, "color": "#22c55e"}], "code_line": 4, "code_explanation": "完成遍历"}
  ],
  "summary": "后序遍历顺序：左→右→根"
}

【示例：BFS 遍历图】
{
  "algorithm": "BFS 广度优先",
  "category": "graph",
  "complexity": {"time": "O(V+E)", "space": "O(V)"},
  "code": "function bfs(graph, start) { ... }",
  "steps": [
    {"narration": "构建图：A-B-C-D 邻接关系", "commands": [{"op": "graph_build", "nodes": [{"id":"A"},{"id":"B"},{"id":"C"},{"id":"D"}], "adjList": {"A":["B","C"],"B":["A","D"],"C":["A"],"D":["B"]}}], "code_line": 0, "code_explanation": "建图"},
    {"narration": "从A开始，加入队列", "commands": [{"op": "graph_visit", "node": "A"}], "code_line": 3, "code_explanation": "queue.push(A)"},
    {"narration": "访问A的邻居B", "commands": [{"op": "graph_visit", "node": "B"}], "code_line": 6, "code_explanation": "遍历A的邻居"},
    {"narration": "访问A的邻居C", "commands": [{"op": "graph_visit", "node": "C"}], "code_line": 6, "code_explanation": "queue.push(C)"},
    {"narration": "BFS 完成", "commands": [], "code_line": -1, "code_explanation": "结束"}
  ]
}
"""

USER_PROMPT_TEMPLATE = """用户请求：{user_request}
用户水平：{user_level}

{level_hint}

请严格按照 system prompt 中的格式生成完整的动画教学 JSON。"""

LEVEL_HINTS = {
    "beginner": "用户是初学者。请使用 12-15 步，每步讲解非常详细，使用简单语言。",
    "intermediate": "用户有一定基础。请使用 10-12 步，讲解适中，重点讲核心逻辑。",
    "advanced": "用户水平较高。请使用 8-10 步，重点讲解算法精髓和技巧，可适当跳过基础。",
}


async def generate_animation(
    user_request: str,
    user_level: str = "beginner",
    use_cache: bool = True,
) -> dict:
    """
    AI 生成算法动画步骤。

    Returns:
        {
            "algorithm": str,
            "category": str,
            "complexity": {"time": str, "space": str},
            "code": str,
            "steps": [
                {"narration": str, "commands": [...], "code_line": int, "code_explanation": str}
            ],
            "summary": str,
            "source": "ai" | "preset",
        }
    """
    # 1. 检查缓存
    if use_cache:
        cached = cache_get(user_request, user_level)
        if cached:
            cached["source"] = "ai_cached"
            return cached

    # 2. 先尝试预设匹配（快速路径）
    preset_id = match_preset(user_request)
    if preset_id:
        return {
            "algorithm": preset_id,
            "category": "preset",
            "source": "preset",
            "matched_id": preset_id,
        }

    # 3. 调用 LLM 生成
    level_hint = LEVEL_HINTS.get(user_level, LEVEL_HINTS["beginner"])
    user_prompt = USER_PROMPT_TEMPLATE.format(
        user_request=user_request,
        user_level=user_level,
        level_hint=level_hint,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    result = await llm_service.chat_completion(
        messages=messages,
        temperature=0.5,   # 低温度提高一致性
        max_tokens=4096,
    )

    # 4. 解析 JSON
    from app.agents.base import BaseAgent
    data = BaseAgent._parse_json(result["content"])

    # 5. 校验
    data = validate_animation_steps(data)

    data["source"] = "ai"

    # 6. 缓存
    if use_cache:
        cache_set(user_request, user_level, data)

    return data
