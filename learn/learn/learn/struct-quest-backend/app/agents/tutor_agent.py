"""
Tutor Agent（学习老师）— v4 多模态增强版
========================================

定位：学习老师。不是百科问答，而是结合学生画像、知识库、聊天历史、错题本
给出个性化的多模态教学回答。

v4 新增特性：
  - 格式决策引擎：根据用户画像自动选择最佳回复格式
  - 多模态资源生成：思维导图 / 动画 / PPT大纲 / 代码案例 / 练习题
  - 资源附件支持：回复可携带多种类型的学习资源
  - 可解释性：告知用户为什么选择该格式

输入：
  - 学生问题
  - 学生画像（能力水平、学习风格、薄弱点、资源偏好、认知特征）
  - 知识库（RAG 检索）
  - 聊天历史（判断是否反复问同一问题）
  - 错题本（针对性指出错误原因）

回答策略：
  - 不是百科答案，而是个性化教学 + 多模态资源
  - 如果学生已问多次 → 变换教学方式
  - 结合错题指出具体问题
  - 根据资源偏好生成思维导图/动画/PPT/代码/练习题
"""

from typing import Dict, Any, List, Optional
import time as _time
import json as _json

from app.agents.base import BaseAgent
from app.agents.state import LearningState, TutorResponse, TutorResourceAttachment
from app.agents.question_router import QuestionRouter
from app.agents.rich_response_builder import RichResponseBuilder
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
- 资源偏好: {resource_prefs}
- 回复格式: {primary_format}（{format_reason}）

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
- 可在最后给出1-2个后续建议问题

## ⚠️ 重要：你不需要自己生成资源，系统会自动处理
- 当用户要求思维导图/PPT/动画/代码/练习题时，**后端系统会自动生成对应的资源附件**并展示给用户
- 你的回复只需做：**简短引入 → 补充讲解 → 后续建议**
- 严禁说"我无法生成XX""我只能文字回复"等！系统会处理资源，你只负责文字引导
- 示例：用户说"做二叉树动画" → 你说"好的，请查看下方的动画演示 👇" + 简要补充

## ⚠️ 注意
- 学生已附带多种形式的资源（思维导图/动画/代码等），你在回答中要自然地提及这些资源
- 不要重复写学生已经在附带的资源中能看到的内容，而是做补充讲解"""


# ══════════════════════════════════════════════════
#  格式决策权重配置
# ══════════════════════════════════════════════════

# 资源偏好 → 格式得分加成（权重 40%）
RESOURCE_PREF_TO_FORMAT = {
    "视频":      {"mindmap_enhanced": 0.4, "ppt_enhanced": 0.1},
    "PPT":       {"ppt_enhanced": 0.4, "mindmap_enhanced": 0.1},
    "思维导图":   {"mindmap_enhanced": 0.4, "ppt_enhanced": 0.1},
    "代码":      {"code_enhanced": 0.4, "exercise_enhanced": 0.1},
    "讲义":      {"text_only": 0.3, "ppt_enhanced": 0.2},
    "练习题":    {"exercise_enhanced": 0.4, "code_enhanced": 0.1},
    "文档":      {"text_only": 0.3, "ppt_enhanced": 0.2},
}

# 学习风格 → 格式得分加成（权重 25%）
LEARNING_STYLE_BONUS = {
    "visual":    {"mindmap_enhanced": 30, "ppt_enhanced": 15},
    "auditory":  {"mindmap_enhanced": 20, "ppt_enhanced": 20},
    "reading":   {"text_only": 25, "ppt_enhanced": 15, "mindmap_enhanced": 10},
    "hands_on":  {"code_enhanced": 25, "exercise_enhanced": 20, "mindmap_enhanced": 10},
}

# 格式中文标签
FORMAT_LABELS = {
    "text_only":          "纯文本讲解",
    "mindmap_enhanced":   "思维导图辅助",
    "animation_enhanced": "动画演示辅助",
    "code_enhanced":      "代码案例辅助",
    "ppt_enhanced":       "PPT大纲辅助",
    "exercise_enhanced":  "练习题巩固",
}

# 格式→应生成的资源类型
FORMAT_TO_RESOURCES = {
    "text_only":          [],
    "mindmap_enhanced":   ["mindmap"],
    "animation_enhanced": ["animation"],
    "code_enhanced":      ["code_example"],
    "ppt_enhanced":       ["notes", "mindmap"],  # PPT需要讲义+导图联合
    "exercise_enhanced":  ["quiz"],
}

# 复杂主题关键词（触发可视化）
COMPLEX_TOPICS = [
    "动态规划", "递归", "图", "树", "Dijkstra", "最短路径",
    "红黑树", "AVL", "B树", "KMP", "哈夫曼", "拓扑排序",
    "最小生成树", "关键路径", "并查集", "平衡树", "哈希冲突",
    "BFS", "DFS", "排序算法", "堆排序", "快速排序", "归并排序",
]


class TutorAgent(BaseAgent):
    """
    学习老师 Agent v4（多模态增强版）

    结合知识库 + 画像 + 聊天历史 + 错题给出个性化教学回答，
    并根据用户偏好自动附带思维导图/动画/代码等多模态资源。
    """

    @property
    def name(self) -> str:
        return "tutor_agent"

    @property
    def description(self) -> str:
        return "学习老师 — 结合画像/知识库/错题本给出个性化多模态教学回答"

    # ═══════════════════════════════════════════
    #  核心 run 方法（v4 增强版）
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        logger.info("👨‍🏫 Tutor Agent v4 开始辅导（多模态模式）...")

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

        # ★ 检测用户是否显式请求了特定资源类型（如"做PPT"/"生成导图"/"动画演示"）
        explicit_request = self._detect_explicit_request(question)
        topic_from_explicit = self._extract_topic_from_explicit_request(question, explicit_request)
        logger.info("🔍 显式请求检测: explicit_request=%s, topic_from_explicit=%s, question=%s",
                    explicit_request, topic_from_explicit, question[:50])

        # ★ v4.1 格式决策（支持手动覆盖 + 混合模式）
        format_override = event_payload.get("format_override", "")
        if format_override and format_override in FORMAT_TO_RESOURCES:
            primary_format = format_override
            format_reason = "你手动选择了此格式"
        elif explicit_request and topic_from_explicit:
            # 用户显式说"用思维导图讲讲树"→ 强制选择对应格式
            primary_format = explicit_request
            format_reason = f"你要求使用{FORMAT_LABELS.get(primary_format, primary_format)}（主题: {topic_from_explicit}）"
        else:
            primary_format, format_reason = self._decide_response_format(profile, analytics, question)

        # ★ 如果用户显式要求了资源但没有给具体主题 → 让 AI 追问，不生成资源
        skip_resources = False
        if explicit_request and not topic_from_explicit:
            skip_resources = True
            primary_format = "text_only"
            format_reason = f"用户要求{FORMAT_LABELS.get(explicit_request, '资源')}但未指定主题，先确认"

        # RAG 知识库检索
        subject = state.get("subject", "数据结构")
        rag_context = self._retrieve_knowledge(
            f"{subject} {question}", top_k=3
        )

        # 错题本
        error_book = self._build_error_book(profile, analytics)

        # 聊天历史
        chat_history = self._summarize_chat_history(state)

        # 资源偏好文本
        resource_prefs = profile.get("resource_preferences", {})
        resource_prefs_text = ", ".join(
            f"{k}={v:.0f}%" for k, v in sorted(resource_prefs.items(), key=lambda x: -x[1])[:4]
        ) if resource_prefs else "无偏好数据"

        # ★ 如果用户显式要求了资源但缺少主题，加入指导信息
        explicit_guide = ""
        if skip_resources:
            explicit_guide = (
                "\n⚠️ 用户要求生成 " + FORMAT_LABELS.get(explicit_request, '资源')
                + "，但未指定具体主题。"
                + "请在回复中友好地询问用户想了解哪个具体的数据结构概念，"
                + "例如'你想生成关于什么的导图？比如链表、二叉树、排序算法等'。"
                + "确认主题后下次我会自动生成对应资源。"
            )

        # 构建 prompt
        system_content = self._build_system_prompt(
            TUTOR_SYSTEM_PROMPT,
            ability_level=profile.get("ability_level", "intermediate"),
            learning_style=profile.get("learning_style", "reading"),
            weaknesses=", ".join(profile.get("weaknesses", [])) or "无",
            feynman_score=str(cognitive.get("feynman_adaptation", 0.5)),
            error_patterns=", ".join(profile.get("error_patterns", [])) or "无",
            resource_prefs=resource_prefs_text + explicit_guide,
            primary_format=FORMAT_LABELS.get(primary_format, "文本"),
            format_reason=format_reason,
            rag_context=rag_context[:2000] if rag_context else "无相关知识库参考资料",
            error_book=error_book,
            chat_history=chat_history,
        )

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": question},
        ]

        try:
            # ★ 显式资源请求：用模板回复，不让 LLM 自由发挥去描述资源
            if explicit_request and topic_from_explicit:
                format_label = FORMAT_LABELS.get(primary_format, "资源")
                response = (
                    f"好的，已为你生成**{format_label}**：{topic_from_explicit} 👇\n\n"
                    f"下方是系统自动生成的资源。如果你需要：\n"
                    f"- 补充讲解某个细节\n"
                    f"- 用其他形式呈现（动画/导图/代码）\n"
                    f"- 调整难度或深度\n\n"
                    f"随时告诉我！"
                )
                print(f"[Tutor] ✨ 显式资源请求模板回复: topic={topic_from_explicit}, format={primary_format}",
                      flush=True)
            else:
                response = self._call_llm(messages, temperature=0.7, max_tokens=1500)
        except Exception as e:
            logger.warning("LLM 辅导回答失败: %s", e)
            response = (
                f"关于「{question}」，让我来为你解释。\n\n"
                f"这个问题的核心在于理解基本概念。建议先回顾相关讲义，"
                f"然后通过练习来巩固理解。\n\n"
                f"如果还有疑问，可以换个方式再问我。"
            )

        # ★ v4 新增：生成多模态资源附件（如果用户没给主题则跳过）
        if skip_resources:
            resource_attachments = []
            logger.info("⏭️ 跳过资源生成: 用户未指定主题")
        else:
            resource_attachments = self._generate_resource_attachments(
                state, profile, question, primary_format, response,
                topic_hint=topic_from_explicit,
            )

        # ★ v5 新增：QuestionRouter 意图检测 + RichResponseBuilder 消息卡片
        router = QuestionRouter()
        route_result = router.route(question)
        logger.info("🔀 意图路由: intent=%s difficulty=%s topic=%s components=%s",
                    route_result["intent"], route_result["difficulty"],
                    route_result["topic"], route_result["suggested_components"])

        # 获取知识图谱节点数据（供 suggestion/knowledge_graph 卡片使用）
        knowledge_nodes = self._get_knowledge_nodes_for_cards(state)

        # 构建消息卡片
        message_cards = RichResponseBuilder.build(
            question=question,
            answer=response,
            route_result=route_result,
            profile=profile,
            rag_context=rag_context,
            resource_attachments=resource_attachments,
            knowledge_nodes=knowledge_nodes,
        )
        logger.info("📦 消息卡片: 生成 %d 个卡片 %s", len(message_cards),
                    [c["type"] for c in message_cards])

        # 构建 TutorResponse（v5 增强版：含消息卡片）
        tutor_response: Dict[str, Any] = {
            "answer_text": response,
            "referenced_knowledge": self._extract_topics(response, question),
            "used_context": self._describe_used_context(rag_context, error_book),
            "follow_up_suggestions": self._suggest_follow_ups(question, profile, primary_format),
            "generated_visual": None,
            # ★ v4 新增字段
            "resource_attachments": resource_attachments,
            "primary_format": primary_format,
            "format_reason": format_reason,
            # ★ v5 新增：消息卡片 + 路由信息
            "message_cards": message_cards,
            "route_result": route_result,
        }

        # 日志
        res_summary = ", ".join(a.get("type", "?") for a in resource_attachments) if resource_attachments else "无"
        log = self._log(
            state,
            f"👨‍🏫 v4 辅导完成 | 问题: {question[:30]}... | "
            f"格式: {FORMAT_LABELS.get(primary_format, primary_format)} | "
            f"附带资源: {res_summary} | "
            f"回答长度: {len(response)} 字"
        )

        return {
            **log,
            "tutor_response": tutor_response,
            "chat_response": response,
            "next_action": "orchestrate",
        }

    # ═══════════════════════════════════════════
    #  ★ v4 新增：格式决策引擎
    # ═══════════════════════════════════════════

    def _decide_response_format(
        self, profile: Dict, analytics: Dict, question: str
    ) -> tuple:
        """
        根据用户画像的多维度信息决定最佳回复格式组合

        决策权重：
        - resource_preferences: 40%（用户明确喜欢什么格式）
        - learning_style: 25%（学习风格）
        - feynman_adaptation: 15%（高→更需要可视化类比，低→文字更严谨）
        - topic_complexity: 20%（复杂概念更适合动画/导图）

        ★ 新用户兜底：无画像数据时，根据问题类型智能选择多模态格式，
           而不是默认 text_only。
        """
        resource_prefs = profile.get("resource_preferences", {}) or analytics.get("resource_preferences", {})
        learning_style = profile.get("learning_style", "reading")
        cognitive = profile.get("cognitive", {})

        # ── 新用户/无画像兜底：根据问题类型直接选格式 ──
        has_profile = bool(resource_prefs) or profile.get("learning_style") or cognitive.get("feynman_adaptation")
        if not has_profile:
            return self._decide_format_for_new_user(question)

        # 计算每种格式的得分
        format_scores = {
            "text_only": 10,           # 基础分，总有文字
            "mindmap_enhanced": 0,
            "animation_enhanced": 0,
            "code_enhanced": 0,
            "ppt_enhanced": 0,
            "exercise_enhanced": 0,
        }

        # 1. resource_preferences 加分（权重 40%）
        if resource_prefs:
            for pref_key, score in resource_prefs.items():
                mappings = RESOURCE_PREF_TO_FORMAT.get(pref_key, {})
                for fmt, weight in mappings.items():
                    format_scores[fmt] += (score / 100.0) * weight * 40

        # 2. learning_style 加分（权重 25%）
        style_bonus = LEARNING_STYLE_BONUS.get(learning_style, {})
        for fmt, bonus in style_bonus.items():
            format_scores[fmt] += bonus

        # 3. feynman_adaptation 调整
        feynman = float(cognitive.get("feynman_adaptation", 0.5))
        if feynman >= 0.7:
            format_scores["animation_enhanced"] += 10
            format_scores["mindmap_enhanced"] += 8
        elif feynman <= 0.3:
            format_scores["text_only"] += 15
            format_scores["code_enhanced"] += 5

        # 4. topic_complexity 加分（复杂主题优先用思维导图，动画仅当用户明确要求时触发）
        if self._is_complex_topic(question):
            format_scores["mindmap_enhanced"] += 20
            format_scores["code_enhanced"] += 5
            format_scores["text_only"] -= 5

        # 5. 动手型 + 高 exercise → 练习题
        if learning_style == "hands_on":
            format_scores["exercise_enhanced"] += 10

        # 选择得分最高的格式
        best_format = max(format_scores, key=format_scores.get)

        # 如果所有非文本格式得分都很低，回退到 text_only
        non_text_scores = {k: v for k, v in format_scores.items() if k != "text_only"}
        max_non_text = max(non_text_scores.values()) if non_text_scores else 0
        if max_non_text < 15:
            best_format = "text_only"

        # 生成可解释的原因
        reason = self._build_format_reason(best_format, profile, question, format_scores)

        return best_format, reason

    # ═══════════════════════════════════════════
    #  ★ 显式资源请求检测（用户说"做PPT""生成导图""演示动画"等）
    # ═══════════════════════════════════════════

    # 关键词 → 资源格式（精确匹配值高于话题推断）
    EXPLICIT_REQUEST_RULES = [
        (["ppt", "幻灯片", "课件"], "ppt_enhanced"),
        (["思维导图", "导图", "脑图", "知识图谱", "markmap"], "mindmap_enhanced"),
        (["动画", "视频", "演示过程", "可视化过程", "看看过程", "动态演示"], "animation_enhanced"),
        (["代码", "编程", "写一个", "实现", "源码", "python"], "code_enhanced"),
        (["练习", "题目", "考题", "试卷", "测验"], "exercise_enhanced"),
    ]

    # 结构主题关键词（用于从问题中提取真正的主题）
    DS_TOPIC_KEYWORDS = [
        # 复合遍历术语（必须先于单独的"遍历"匹配）
        "前序遍历", "中序遍历", "后序遍历", "层次遍历", "层序遍历",
        "深度优先遍历", "广度优先遍历", "先序遍历",
        # 数据结构
        "链表", "单向链表", "双向链表", "循环链表", "栈", "队列", "双端队列",
        "树", "二叉树", "二叉搜索树", "BST", "AVL", "红黑树", "B树", "B+树", "字典树",
        "堆", "大顶堆", "小顶堆", "优先队列",
        "图", "有向图", "无向图", "加权图", "哈希", "哈希表", "数组", "矩阵", "字符串",
        # 排序
        "排序", "冒泡排序", "快速排序", "快排", "归并排序", "堆排序", "选择排序", "插入排序",
        "希尔排序", "计数排序", "桶排序", "基数排序", "拓扑排序",
        # 查找/遍历
        "二分查找", "二分", "遍历", "DFS", "BFS", "深度优先", "广度优先", "顺序查找",
        # 算法范式
        "递归", "迭代", "动态规划", "DP", "贪心", "回溯", "分治",
        # 图算法
        "最短路径", "Dijkstra", "Floyd", "最小生成树", "Kruskal", "Prim",
        "并查集", "KMP", "Manacher",
        # 复杂度
        "时间复杂度", "空间复杂度", "指针", "引用",
    ]

    @classmethod
    def _detect_explicit_request(cls, question: str) -> Optional[str]:
        """检测用户是否显式请求了特定资源类型，返回对应的 format 名称"""
        q = question.lower()
        for keywords, fmt in cls.EXPLICIT_REQUEST_RULES:
            for kw in keywords:
                if kw.lower() in q:
                    return fmt
        return None

    @classmethod
    def _extract_topic_from_explicit_request(cls, question: str, explicit_request: Optional[str]) -> Optional[str]:
        """从显式资源请求中提取真正的主题（如"用导图讲讲链表"→"链表"）"""
        if not explicit_request:
            return None

        # 移除请求语部分，尝试提取主题关键字
        request_patterns = [
            "思维导图", "知识图谱", "markmap", "弄一个", "来一个",
            "生成", "创建", "演示", "展示", "给我", "帮我",
            "可以", "能不能", "能否", "能", "吗", "么", "一下",
            "ppt", "导图", "脑图", "动画", "视频", "代码", "练习题",
            "题目", "课件", "幻灯片", "形式", "方式", "关于",
            "做", "作", "画", "写", "用", "请",
        ]
        import re as _re
        cleaned = question
        for p in sorted(request_patterns, key=len, reverse=True):
            cleaned = cleaned.replace(p, " ")
        cleaned = _re.sub(r'[，。！？、,.!?：:；;（）()\[\]【】"“”’]', ' ', cleaned)
        cleaned = _re.sub(r'\s+', ' ', cleaned).strip()

        # 清理请求词后再匹配，避免把"思维导图"里的"图"误识别成图论主题
        for kw in sorted(cls.DS_TOPIC_KEYWORDS, key=len, reverse=True):
            if kw in cleaned:
                return kw

        # 如果清理后还有合理长度的词，取第一个
        words = cleaned.split()
        stop_words = {
            "的", "了", "一下", "可以", "比如", "关于", "想要", "我要",
            "请问", "能", "能否", "能不能", "吗", "么", "呢", "吧",
            "资源", "内容", "学习", "辅助",
        }
        for w in words:
            if len(w) >= 2 and not w.isdigit() and w not in stop_words:
                return w[:50]

        return None

    # ═══════════════════════════════════════════
    #  ★ 新用户格式决策（无画像时的智能兜底）
    # ═══════════════════════════════════════════

    # 问题关键词 → 适合的格式
    QUESTION_FORMAT_RULES = [
        # 代码/算法实现类 → 代码案例
        (["实现", "代码", "怎么写", "编程", "python", "示例", "写一个", "编写", "程序"], "code_enhanced",
         "你问的是编程实现类问题，配合代码案例更容易理解"),
        # 排序/搜索/遍历等算法过程 → 思维导图（动画成功率低，用导图替代）
        (["排序", "查找", "遍历", "过程", "步骤", "执行过程", "二分", "快速排序", "归并排序"], "mindmap_enhanced",
         "涉及算法过程，思维导图能帮你理清执行步骤"),
        # 概念/结构/关系类 → 思维导图
        (["是什么", "概念", "区别", "关系", "结构", "分类", "类型", "讲讲", "介绍", "解释",
          "对比", "总结", "梳理", "体系", "导图", "思维导图"], "mindmap_enhanced",
         "这是概念梳理类问题，思维导图能帮你建立知识结构"),
        # 练习/测试/考试类 → 练习题
        (["练习", "题目", "考试", "测验", "做题", "检验", "测试", "巩固"], "exercise_enhanced",
         "你想通过练习来巩固，直接为你生成练习题"),
        # 显式要求动画时才触发动画
        (["动画", "演示过程", "可视化过程", "视频演示", "看看过程", "动态"], "animation_enhanced",
         "你要求看动画演示，尝试生成视频（渲染可能较慢）"),
    ]

    def _decide_format_for_new_user(self, question: str) -> tuple:
        """新用户（无画像）根据问题类型智能选择格式"""
        q_lower = question.lower()

        for keywords, fmt, reason in self.QUESTION_FORMAT_RULES:
            for kw in keywords:
                if kw in q_lower:
                    return fmt, reason

        # 默认：复杂主题给思维导图，简单问题给纯文本
        if self._is_complex_topic(question):
            return "mindmap_enhanced", "这是个复杂概念，思维导图能帮你理清结构"
        return "text_only", "这个问题用文字讲解即可"

    @staticmethod
    def _is_complex_topic(question: str) -> bool:
        """判断问题是否涉及复杂概念"""
        return any(kw in question for kw in COMPLEX_TOPICS)

    @staticmethod
    def _extract_topic_from_response(ai_response: str, question: str) -> str:
        """
        从 AI 回答中提取真正的主题。
        避免把用户请求语（如"我要思维导图"）当作生成资源的主题。

        策略：
        1. 从回答中提取**加粗**的术语（通常是核心概念）
        2. 提取第一个 ## 标题下的内容
        3. 如果用户问题包含明显的数据结构关键词，直接使用
        4. 兜底用问题前50字
        """
        import re as _re

        # 策略0：用户问题本身就包含明确的数据结构关键词 → 直接用
        ds_keywords = [
            "链表", "树", "图", "栈", "队列", "堆", "二叉树", "哈希",
            "排序", "查找", "遍历", "递归", "动态规划", "贪心", "回溯",
            "数组", "字符串", "指针", "并查集", "拓扑", "最短路",
            "BFS", "DFS", "二叉树", "红黑树", "AVL", "堆排序",
            "冒泡", "快排", "归并", "迪杰斯特拉", "Dijkstra",
            "时间复杂度", "空间复杂度",
        ]
        for kw in sorted(ds_keywords, key=len, reverse=True):
            if kw in question:
                return kw

        # 策略1：从 AI 回答中提取**加粗**的关键词
        bold_matches = _re.findall(r'\*\*(.+?)\*\*', ai_response)
        if bold_matches:
            # 过滤掉太短或明显不是概念的词
            valid = [b for b in bold_matches if len(b) >= 2 and not b.isspace()
                     and b not in ("注意", "加粗", "提示", "示例", "参考")]
            if valid:
                return valid[0][:50]

        # 策略2：从AI回答提取第一个 ## 标题
        heading = _re.search(r'##\s+(.+?)(?:\n|$)', ai_response)
        if heading:
            title = heading.group(1).strip()
            # 去掉"一、""1." 等编号前缀
            title = _re.sub(r'^[\d一二三四五六七八九十]+[\.\、\s]*', '', title)
            if len(title) >= 2:
                return title[:50]

        # 策略3：问题中有明显关键词（非请求语）
        request_patterns = ["我要", "给我", "帮我", "生成", "画", "做一个", "来一个", "弄一个"]
        is_request = any(p in question for p in request_patterns)
        if not is_request and len(question) >= 4:
            # 尝试提取问题主题（去掉"是什么""讲讲"等前缀）
            cleaned = _re.sub(r'^(什么是|是|讲讲|讲讲看|解释一下|介绍一下|请问)\s*', '', question)
            return cleaned[:50]

        # 兜底：如果无法提取，用问题作为主题
        return question[:50]

    @staticmethod
    def _build_format_reason(
        best_format: str, profile: Dict, question: str, scores: Dict
    ) -> str:
        """构建格式决策的可解释原因"""
        reasons = []

        learning_style = profile.get("learning_style", "")
        style_cn = {"visual": "视觉偏好者", "auditory": "听觉偏好者",
                     "reading": "阅读偏好者", "hands_on": "动手实践偏好者"}
        if learning_style:
            reasons.append(f"你是{style_cn.get(learning_style, learning_style)}")

        resource_prefs = profile.get("resource_preferences", {})
        if resource_prefs:
            top_pref = sorted(resource_prefs.items(), key=lambda x: -x[1])[:2]
            pref_text = "、".join(f"{k}({v:.0f})" for k, v in top_pref)
            reasons.append(f"你偏好 {pref_text}")

        if TutorAgent._is_complex_topic(question):
            reasons.append("这是个复杂概念，可视化有助于理解")

        if best_format == "text_only":
            return "这个问题用文字讲解即可" if not reasons else "你偏好文字阅读，用纯文本方式讲解"
        elif best_format == "mindmap_enhanced":
            return f"{'; '.join(reasons)}，用思维导图辅助理解"
        elif best_format == "animation_enhanced":
            return f"{'; '.join(reasons)}，生成动画演示辅助理解"
        elif best_format == "code_enhanced":
            return f"{'; '.join(reasons)}，配合代码案例加深理解"
        elif best_format == "ppt_enhanced":
            return f"{'; '.join(reasons)}，用结构化讲义+导图辅助"
        elif best_format == "exercise_enhanced":
            return f"{'; '.join(reasons)}，用练习题来巩固理解"

        return f"{'; '.join(reasons)}，选择此格式辅助教学"

    # ═══════════════════════════════════════════
    #  ★ v4 新增：多模态资源生成
    # ═══════════════════════════════════════════

    def _generate_resource_attachments(
        self, state: LearningState, profile: Dict, question: str, primary_format: str,
        ai_response: str = "", topic_hint: str = None,
    ) -> List[TutorResourceAttachment]:
        """
        根据格式决策生成对应的多模态资源附件

        调用 ResourceGenerationAgent 为每种需要的类型生成资源
        """
        resource_types = list(FORMAT_TO_RESOURCES.get(primary_format, []))
        if not resource_types:
            return []

        # ★ v4.1 混合模式：复杂主题额外追加思维导图/代码/练习
        if self._is_complex_topic(question) and primary_format != "text_only":
            # 复杂主题总是追加思维导图（如果还没生成）
            if "mindmap" not in resource_types:
                resource_types.append("mindmap")
            # 动手型用户追加练习题
            learning_style = profile.get("learning_style", "")
            if learning_style == "hands_on" and "quiz" not in resource_types:
                resource_types.append("quiz")
            # 代码类追加代码案例
            if primary_format in ("code_enhanced", "exercise_enhanced") and "code_example" not in resource_types:
                resource_types.append("code_example")
            logger.info("📦 复杂主题混合模式: 将生成 %d 种资源 %s", len(resource_types), resource_types)

        attachments = []
        start_time = _time.time()

        try:
            from app.agents.resource_agent import ResourceGenerationAgent

            # ★ 从 AI 回答或显式请求中提取真正的主题
            real_topic = topic_hint or self._extract_topic_from_response(ai_response, question)
            logger.info("📦 资源主题: %s (来源: %s)", real_topic, "显式请求" if topic_hint else "AI回答提取")

            # 准备一个临时 state 供 ResourceAgent 使用
            # description 按资源类型定制，让 LLM 生成更精准的内容
            type_descriptions = {
                "animation":   f"用动画可视化展示「{real_topic}」的完整执行过程（从初始状态到最终结果）",
                "mindmap":     f"梳理「{real_topic}」的核心概念、定义、特性和应用场景的层级关系",
                "code_example": f"用 Python 代码演示「{real_topic}」，由浅入深 3 个递进示例",
                "quiz":        f"针对「{real_topic}」设计 6~8 道覆盖布鲁姆六层的练习题",
                "notes":       f"系统讲解「{real_topic}」的核心概念、原理、常见误区和实战案例",
                "ppt_outline": f"梳理「{real_topic}」的 PPT 大纲（每页一个章节）",
            }
            description = type_descriptions.get(
                resource_types[0] if resource_types else "notes",
                f"深度学习{real_topic}的核心概念"
            )

            temp_state = dict(state)
            temp_state["event_payload"] = {
                "topic": real_topic,
                "question": question,
                "description": description,
            }
            temp_state["student_profile"] = profile

            resource_agent = ResourceGenerationAgent()

            for res_type in resource_types:
                try:
                    logger.info("📦 Tutor 触发资源生成: %s", res_type)
                    gen_start = _time.time()

                    # 使用 ResourceAgent 的流式生成
                    bundle = resource_agent.generate_resource_bundle(
                        temp_state, only_types=[res_type]
                    )

                    content = bundle.get(res_type, "")
                    if not content:
                        continue

                    gen_elapsed = round(_time.time() - gen_start, 2)

                    # 构建附件
                    attachment = self._build_attachment(
                        res_type, question, content, profile, primary_format, gen_elapsed
                    )
                    if attachment:
                        attachments.append(attachment)
                        logger.info("✅ 资源生成完成: %s (%.1fs)", res_type, gen_elapsed)

                except Exception as e:
                    logger.warning("⚠️ 资源 %s 生成失败: %s", res_type, e)

        except Exception as e:
            logger.warning("⚠️ 资源生成系统初始化失败: %s", e)

        total_elapsed = round(_time.time() - start_time, 2)
        if attachments:
            logger.info("📦 Tutor 资源包完成: %d 项 (总耗时 %.1fs)", len(attachments), total_elapsed)

        return attachments

    def _build_attachment(
        self, res_type: str, question: str, content: Any,
        profile: Dict, primary_format: str, gen_elapsed: float
    ) -> Optional[TutorResourceAttachment]:
        """根据资源类型构建附件对象"""
        type_meta = {
            "mindmap":      {"format": "markmap", "title_suffix": "思维导图", "reason": "用户偏好视觉化学习"},
            "animation":    {"format": "video", "title_suffix": "动画演示", "reason": "动画辅助理解复杂概念"},
            "code_example": {"format": "python", "title_suffix": "代码案例", "reason": "代码实例加深理解"},
            "quiz":         {"format": "json", "title_suffix": "练习题", "reason": "练习巩固知识"},
            "notes":        {"format": "markdown", "title_suffix": "学习讲义", "reason": "结构化知识梳理"},
        }

        meta = type_meta.get(res_type, {"format": "text", "title_suffix": "学习资源", "reason": "辅助理解"})

        # 根据内容类型构建
        if isinstance(content, str):
            att: TutorResourceAttachment = {
                "type": res_type,
                "title": f"{question[:20]} - {meta['title_suffix']}",
                "content_text": content,
                "content_json": None,
                "format": meta["format"],
                "preview_url": None,
                "file_url": None,
                "thumbnail_url": None,
                "generated_for": meta["reason"],
                "quality_score": None,
                "generation_time_seconds": gen_elapsed,
                "metadata": {},
            }
            return att

        elif isinstance(content, dict):
            # 动画资源（dict 类型，可能渲染成功或只有代码 fallback）
            video_url = content.get("video_url", "")
            fallback_text = content.get("fallback_text", "")
            source_code = content.get("source_code", "")
            # 当视频渲染失败时，用 fallback_text（含说明+代码）代替裸源码
            display_text = fallback_text if not video_url and fallback_text else source_code
            att: TutorResourceAttachment = {
                "type": res_type,
                "title": f"{question[:20]} - {meta['title_suffix']}",
                "content_text": display_text,
                "content_json": content if res_type == "animation" else None,
                "format": "markdown" if (not video_url and fallback_text) else meta["format"],
                "preview_url": video_url,
                "file_url": video_url,
                "thumbnail_url": content.get("thumbnail_url", ""),
                "generated_for": meta["reason"],
                "quality_score": None,
                "generation_time_seconds": gen_elapsed,
                "metadata": {"render_error": content.get("error", ""), "format": content.get("format", "unknown")} if res_type == "animation" else {},
            }
            return att

        elif isinstance(content, list):
            # 练习题
            att: TutorResourceAttachment = {
                "type": res_type,
                "title": f"{question[:20]} - {meta['title_suffix']}",
                "content_text": _json.dumps(content, ensure_ascii=False, indent=2),
                "content_json": {"quiz_items": content},
                "format": meta["format"],
                "preview_url": None,
                "file_url": None,
                "thumbnail_url": None,
                "generated_for": meta["reason"],
                "quality_score": None,
                "generation_time_seconds": gen_elapsed,
                "metadata": {},
            }
            return att

        return None

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
    def _get_knowledge_nodes_for_cards(state: LearningState) -> list:
        """从 state 中获取知识图谱节点数据（供消息卡片使用）"""
        try:
            import asyncio
            from app.db.session import AsyncSessionLocal
            from sqlalchemy.future import select
            from app.models.knowledge_graph import KnowledgeNode

            async def fetch():
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(KnowledgeNode).order_by(KnowledgeNode.order_index)
                    )
                    nodes = result.scalars().all()
                    return [
                        {
                            "id": n.id,
                            "title": n.title,
                            "description": n.description,
                            "category": n.category,
                            "difficulty": n.difficulty,
                            "parent_id": n.parent_id,
                            "prerequisites": n.prerequisites or [],
                            "icon": n.icon,
                            "points": n.points or [],
                            "ai_suggestion": n.ai_suggestion,
                        }
                        for n in nodes
                    ]

            # 尝试在已有事件循环中运行
            try:
                loop = asyncio.get_running_loop()
                # 已有循环 → 在新线程中运行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(lambda: asyncio.run(fetch()))
                    return future.result(timeout=5)
            except RuntimeError:
                # 没有运行中的循环 → 直接 run
                return asyncio.run(fetch())

        except Exception as e:
            logger.warning("获取知识图谱节点失败: %s", e)
            return []

    @staticmethod
    def _extract_topics(response: str, question: str) -> List[str]:
        """从回答中提取引用的知识点"""
        keywords = ["链表", "树", "图", "栈", "队列", "排序", "查找",
                    "递归", "动态规划", "哈希", "DFS", "BFS", "二叉树",
                    "Dijkstra", "堆", "数组", "指针", "红黑树", "AVL",
                    "拓扑", "并查集", "KMP", "最短路径", "最小生成树"]
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
    def _suggest_follow_ups(question: str, profile: Dict, primary_format: str = "text_only") -> List[str]:
        """生成后续建议问题（v4：根据格式调整建议）"""
        weaknesses = profile.get("weaknesses", [])
        suggestions = []

        # 基于薄弱点建议
        if weaknesses:
            suggestions.append(f"想了解一下「{weaknesses[0]}」的详细内容吗？")

        # 根据当前格式给出不同建议
        if primary_format == "mindmap_enhanced":
            suggestions.append("需要我根据这个导图出一份对应练习题吗？")
        elif primary_format == "code_enhanced":
            suggestions.append("想看这个算法的动画演示吗？")
        elif primary_format == "animation_enhanced":
            suggestions.append("需要我再解释一下动画中的关键步骤吗？")
        else:
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
                "resource_attachments": [],
                "primary_format": "text_only",
                "format_reason": "降级模式，仅提供文字回答",
            },
        }
