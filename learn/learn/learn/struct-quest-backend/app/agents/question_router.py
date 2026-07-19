"""
Question Router（问题路由器）— 意图检测 + 难度评估 + 组件建议
=============================================================

在 TutorAgent 之前运行，检测用户问题的意图类型，为 RichResponseBuilder
提供决策依据：该用哪些消息卡片、以什么风格回答。

输出：
  - intent: 问题意图类型
  - difficulty: 难度 1-5
  - topic: 识别到的核心主题
  - suggested_components: 建议的消息卡片类型列表
  - style_hint: 回答风格提示
"""

from typing import Dict, List, Optional, Tuple
import re

# ══════════════════════════════════════════════════
#  意图规则表（优先级从上到下）
# ══════════════════════════════════════════════════

INTENT_RULES: List[Tuple[List[str], str, int]] = [
    # (触发关键词, 意图类型, 优先级)
    # --- 路径规划（最高优先级，避免与其他规则冲突）---
    (["学习路径", "下一步", "之后学什么", "路线", "规划", "先学什么", "怎么开始",
      "从哪里开始", "推荐学习"], "path_planning", 10),

    # --- 练习 ---
    (["出题", "练习题", "题库", "考试", "测验", "做题", "题目", "检验",
      "来几道", "刷题", "考考我", "测一测"], "practice", 10),

    # --- 调试 ---
    (["报错", "错误", "bug", "不对", "为什么错", "不工作", "调试",
      "debug", "出错", "异常", "改错", "修正"], "debug", 10),

    # --- 算法可视化 ---
    (["动画", "演示", "过程", "步骤", "可视化", "动态", "看看",
      "画出来", "展示", "看看过程", "演示一下", "执行过程"], "algorithm_viz", 10),

    # --- 代码编写 ---
    (["实现", "代码", "写一个", "编写", "编程", "示例", "源码",
      "怎么实现", "怎么写", "写代码", "python实现", "用python"], "code_write", 10),

    # --- 对比 ---
    (["区别", "对比", "比较", "不同", "差异", "哪个好", "优缺点",
      "vs", "和.*比", "优劣"], "compare", 9),

    # --- 复杂度分析 ---
    (["复杂度", "时间复杂度", "空间复杂度", "性能", "效率",
      "大O", "big o", "big-o"], "complexity_analysis", 9),

    # --- 概念解释 ---
    (["是什么", "什么是", "概念", "定义", "解释一下", "讲讲",
      "介绍", "意思", "含义", "讲讲看", "了解", "怎么理解"], "concept_explain", 8),

    # --- 关系分析 ---
    (["关系", "联系", "关联", "和.*什么关系", "区别.*联系"], "relation_analysis", 7),
]

# ══════════════════════════════════════════════════
#  主题关键词 → 难度映射
# ══════════════════════════════════════════════════

TOPIC_DIFFICULTY = {
    # 基础概念 (难度 1-2)
    "数组": 1, "时间复杂度": 2, "空间复杂度": 2, "大O": 2,
    "变量": 1, "指针": 2, "引用": 2, "内存": 2,
    # 线性结构 (难度 2-3)
    "链表": 2, "单链表": 2, "双向链表": 3, "循环链表": 3,
    "栈": 2, "队列": 2, "循环队列": 3, "双端队列": 3,
    # 排序 (难度 2-4)
    "冒泡排序": 2, "选择排序": 2, "插入排序": 2,
    "快速排序": 3, "归并排序": 3, "堆排序": 3,
    "希尔排序": 4, "计数排序": 3, "桶排序": 4, "基数排序": 4,
    # 树 (难度 3-5)
    "二叉树": 3, "二叉搜索树": 3, "遍历": 3,
    "前序遍历": 3, "中序遍历": 3, "后序遍历": 3, "层序遍历": 3,
    "BST": 3, "AVL": 4, "红黑树": 5, "B树": 5, "B+树": 5,
    "堆": 3, "大顶堆": 3, "小顶堆": 3, "优先队列": 3,
    "哈夫曼": 4, "字典树": 4, "线段树": 5,
    # 图 (难度 4-5)
    "图": 4, "BFS": 4, "DFS": 4, "深度优先": 4, "广度优先": 4,
    "最短路径": 4, "Dijkstra": 4, "Floyd": 4, "Bellman": 5,
    "最小生成树": 4, "Kruskal": 4, "Prim": 4,
    "拓扑排序": 4, "关键路径": 5,
    # 算法范式 (难度 3-5)
    "递归": 3, "分治": 3, "动态规划": 5, "DP": 5,
    "贪心": 4, "回溯": 4, "双指针": 3, "滑动窗口": 3,
    # 查找 (难度 2-3)
    "二分查找": 2, "二分": 2, "哈希": 3, "哈希表": 3,
    "哈希冲突": 3, "布隆过滤器": 4,
    # 字符串 (难度 3-5)
    "KMP": 5, "字符串": 3, "模式匹配": 4, "Manacher": 5,
    # 进阶 (难度 4-5)
    "并查集": 4, "LRU": 4, "跳表": 5,
    "排序": 3, "查找": 3, "遍历": 3,
}

# ══════════════════════════════════════════════════
#  意图 → 建议的消息卡片组件
# ══════════════════════════════════════════════════

INTENT_COMPONENTS: Dict[str, List[str]] = {
    "concept_explain":      ["knowledge", "complexity", "code", "suggestion"],
    "code_write":           ["code", "complexity", "knowledge", "suggestion"],
    "debug":                ["debug", "code", "suggestion"],
    "algorithm_viz":        ["knowledge", "complexity", "code", "suggestion"],
    "practice":             ["quiz", "knowledge", "suggestion"],
    "compare":              ["comparison", "complexity", "knowledge_graph", "suggestion"],
    "complexity_analysis":  ["complexity", "knowledge", "comparison", "suggestion"],
    "path_planning":        ["knowledge_graph", "suggestion"],
    "relation_analysis":    ["knowledge_graph", "knowledge", "suggestion"],
}

# ══════════════════════════════════════════════════
#  难度 → 风格提示
# ══════════════════════════════════════════════════

DIFFICULTY_STYLE = {
    1: "用生活类比讲解，大量具体例子，避免专业术语",
    2: "从具体例子入手，逐步引入术语，图文并茂",
    3: "先讲原理再举例，适当使用图表和代码",
    4: "可直接使用专业术语，结合代码和复杂度分析",
    5: "默认对方有基础，聚焦核心难点和优化思路",
}

# 数据结构关键词（用于主题提取）
DS_KEYWORDS = [
    "链表", "单链表", "双向链表", "循环链表", "栈", "队列", "双端队列",
    "二叉树", "二叉搜索树", "AVL", "红黑树", "B树", "B+树", "字典树",
    "堆", "大顶堆", "小顶堆", "优先队列", "哈夫曼",
    "图", "有向图", "无向图", "加权图", "哈希", "哈希表",
    "数组", "矩阵", "字符串", "并查集", "线段树", "跳表",
    "冒泡排序", "快速排序", "快排", "归并排序", "堆排序", "选择排序", "插入排序",
    "希尔排序", "计数排序", "桶排序", "基数排序", "拓扑排序",
    "二分查找", "二分", "BFS", "DFS", "深度优先", "广度优先",
    "最短路径", "Dijkstra", "Floyd", "最小生成树", "Kruskal", "Prim",
    "递归", "动态规划", "DP", "贪心", "回溯", "分治", "KMP",
    "时间复杂度", "空间复杂度", "遍历", "排序", "查找",
]


class QuestionRouter:
    """问题路由器：检测意图、评估难度、建议组件"""

    @staticmethod
    def route(question: str) -> dict:
        """
        分析用户问题，返回路由结果

        Returns:
            {
                "intent": str,                  # 意图类型
                "difficulty": int,               # 1-5
                "topic": str,                    # 核心主题
                "suggested_components": [str],   # 建议卡片列表
                "style_hint": str,               # 风格提示
                "is_complex": bool,              # 是否复杂主题
            }
        """
        intent = QuestionRouter._detect_intent(question)
        topic = QuestionRouter._extract_topic(question, intent)
        difficulty = QuestionRouter._assess_difficulty(question, topic)
        components = INTENT_COMPONENTS.get(intent, ["knowledge", "suggestion"])
        is_complex = difficulty >= 4

        return {
            "intent": intent,
            "difficulty": difficulty,
            "topic": topic or question[:30],
            "suggested_components": components,
            "style_hint": DIFFICULTY_STYLE.get(difficulty, DIFFICULTY_STYLE[2]),
            "is_complex": is_complex,
        }

    @staticmethod
    def _detect_intent(question: str) -> str:
        """按优先级匹配意图规则"""
        q = question.lower()

        # 先检测关键词匹配
        for keywords, intent, priority in sorted(INTENT_RULES, key=lambda x: -x[2]):
            for kw in keywords:
                if kw.lower() in q:
                    return intent

        # 默认返回概念解释
        return "concept_explain"

    @staticmethod
    def _extract_topic(question: str, intent: str = "") -> str:
        """从问题中提取核心主题"""
        # 优先匹配数据结构关键词
        for kw in sorted(DS_KEYWORDS, key=len, reverse=True):
            if kw in question:
                return kw

        # 如果没匹配到，尝试提取问题中的核心名词
        # 移除常见问句前缀
        cleaned = re.sub(
            r'^(什么是|什么|是|讲讲|讲一下|解释一下|介绍一下|请问|帮我|我想知道|'
            r'怎么实现|怎么写|如何|怎样|怎么做|如何做)\s*',
            '', question
        )
        # 移除标点取前15字
        cleaned = re.sub(r'[?？。！!，,、\s]+', '', cleaned)
        if len(cleaned) >= 2 and len(cleaned) <= 15:
            return cleaned

        return ""

    @staticmethod
    def _assess_difficulty(question: str, topic: str) -> int:
        """评估问题难度 1-5"""
        # 如果提取到了主题，直接用主题难度
        if topic and topic in TOPIC_DIFFICULTY:
            return TOPIC_DIFFICULTY[topic]

        # 否则遍历所有关键词匹配
        max_difficulty = 1
        for kw, diff in TOPIC_DIFFICULTY.items():
            if kw in question:
                max_difficulty = max(max_difficulty, diff)

        return max(1, min(5, max_difficulty))
