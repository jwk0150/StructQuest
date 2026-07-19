"""
RichResponse Builder（富文本响应构建器）
============================================

根据 QuestionRouter 的路由结果 + LLM 回答，将原始响应拆解为结构化的消息卡片数组。
每个卡片包含 type、title、icon、collapsed、data、actions 字段，前端直接渲染。

消息卡片类型:
  - knowledge       📘 知识讲解卡
  - code            💻 代码卡
  - complexity      📊 复杂度/数据分析卡
  - quiz            📝 互动练习卡
  - suggestion      🎯 AI 学习建议卡
  - knowledge_graph 🗺 知识图谱卡
  - comparison      ⚖️ 对比卡
  - debug           🔧 调试卡
  - mermaid         📐 Mermaid 图表
"""

import re
import json as _json
from typing import Dict, List, Any, Optional


class RichResponseBuilder:
    """将 LLM 文本回答 + 路由信息 转换为结构化消息卡片"""

    # ══════════════════════════════════════════════════
    #  公共入口
    # ══════════════════════════════════════════════════

    @classmethod
    def build(
        cls,
        question: str,
        answer: str,
        route_result: dict,
        profile: dict = None,
        rag_context: str = "",
        resource_attachments: list = None,
        knowledge_nodes: list = None,
    ) -> List[dict]:
        """
        根据回答内容生成消息卡片列表

        Args:
            question: 用户问题
            answer: LLM 原始回答文本
            route_result: QuestionRouter.route() 的输出
            profile: 学生画像
            rag_context: RAG 检索上下文
            resource_attachments: 已有的资源附件（避免重复）
            knowledge_nodes: 知识图谱节点列表（用于 suggestion/knowledge_graph 卡片）

        Returns:
            消息卡片列表
        """
        cards = []
        intent = route_result.get("intent", "concept_explain")
        difficulty = route_result.get("difficulty", 2)
        topic = route_result.get("topic", "")
        components = route_result.get("suggested_components", ["knowledge", "suggestion"])
        profile = profile or {}

        resource_types = {att.get("type") for att in (resource_attachments or []) if isinstance(att, dict)}
        is_resource_ack = bool(resource_types) and ("已为你生成" in answer or "下方是系统自动生成" in answer)
        if is_resource_ack and not resource_types.intersection({"quiz"}):
            return []

        # 按顺序生成各类型卡片
        for comp_type in components:
            card = None
            if comp_type == "knowledge":
                card = cls._build_knowledge_card(answer, topic, difficulty)
            elif comp_type == "code":
                card = cls._build_code_card(answer, topic)
            elif comp_type == "complexity":
                card = cls._build_complexity_card(answer, topic)
            elif comp_type == "quiz":
                card = cls._build_quiz_card(answer, resource_attachments)
            elif comp_type == "suggestion":
                card = cls._build_suggestion_card(profile, topic, knowledge_nodes)
            elif comp_type == "knowledge_graph":
                card = cls._build_knowledge_graph_card(topic, knowledge_nodes)
            elif comp_type == "comparison":
                card = cls._build_comparison_card(answer, topic)
            elif comp_type == "debug":
                card = cls._build_debug_card(answer)

            if card:
                cards.append(card)

        # 提取 Mermaid 图表（如果有）
        mermaid_card = cls._extract_mermaid_card(answer)
        if mermaid_card:
            cards.append(mermaid_card)

        return cards

    # ══════════════════════════════════════════════════
    #  各卡片构建方法
    # ══════════════════════════════════════════════════

    @classmethod
    def _build_knowledge_card(cls, answer: str, topic: str, difficulty: int) -> dict:
        """📘 知识讲解卡：提取概念、摘要、要点"""
        # 提取一句话摘要（第一个句子）
        summary = ""
        first_line = answer.strip().split("\n")[0]
        # 移除 markdown 标记
        first_line = re.sub(r'^#{1,4}\s+', '', first_line)
        first_line = re.sub(r'\*\*(.+?)\*\*', r'\1', first_line)
        if len(first_line) > 2 and len(first_line) < 120:
            summary = first_line

        # 提取要点列表（以 - 或 * 开头的行）
        key_points = []
        lines = answer.split("\n")
        for line in lines:
            stripped = line.strip()
            if re.match(r'^[-*]\s+', stripped):
                point = re.sub(r'^[-*]\s+', '', stripped)
                point = re.sub(r'\*\*(.+?)\*\*', r'\1', point)
                if 2 < len(point) < 80:
                    key_points.append(point)
            if len(key_points) >= 5:
                break

        # 提取分段内容（## 开头的章节）
        sections = []
        current_heading = ""
        current_content = []

        for line in lines:
            heading_match = re.match(r'^#{2,4}\s+(.+)', line)
            if heading_match:
                if current_heading and current_content:
                    sections.append({
                        "heading": current_heading,
                        "content": " ".join(current_content)[:500],
                    })
                current_heading = heading_match.group(1).strip()
                current_content = []
            elif current_heading:
                clean = re.sub(r'\*\*(.+?)\*\*', r'\1', line.strip())
                if clean:
                    current_content.append(clean)

        if current_heading and current_content:
            sections.append({
                "heading": current_heading,
                "content": " ".join(current_content)[:500],
            })

        # 难度星级
        difficulty_stars = "★" * difficulty + "☆" * (5 - difficulty)

        return {
            "type": "knowledge",
            "title": topic or "知识点讲解",
            "icon": "📘",
            "collapsed": False,
            "difficulty": difficulty_stars,
            "summary": summary,
            "sections": sections[:5],  # 最多5个分段
            "key_points": key_points[:5],
            "data": {
                "difficulty": difficulty,
                "topic": topic,
                "sections": sections[:5],
                "key_points": key_points[:5],
                "summary": summary,
            },
            "actions": [],
        }

    @classmethod
    def _build_code_card(cls, answer: str, topic: str) -> dict:
        """💻 代码卡：提取代码块 + 逐行解释"""
        # 提取代码块
        code_blocks = cls._extract_code_blocks(answer)
        if not code_blocks:
            return None

        main_code = code_blocks[0]
        language = main_code.get("language", "python")
        code_text = main_code.get("code", "")

        # 尝试提取逐行解释（代码块附近的注释/说明）
        line_explanations = cls._extract_line_explanations(answer, code_text)

        return {
            "type": "code",
            "title": f"{topic} - 代码示例" if topic else "代码示例",
            "icon": "💻",
            "collapsed": False,
            "data": {
                "language": language,
                "code": code_text,
                "line_explanations": line_explanations,
                "all_blocks": code_blocks[:3],
            },
            "actions": [
                {"label": "复制代码", "action": "copy", "target": code_text},
                {"label": "逐行解释", "action": "toggle_explain"},
            ],
        }

    @classmethod
    def _build_complexity_card(cls, answer: str, topic: str) -> dict:
        """📊 复杂度卡：提取时间复杂度/空间复杂度/对比数据"""
        # 提取复杂度信息
        time_complexity = cls._extract_complexity(answer, r"时间复杂度[：:]\s*(.+?)(?:\n|$)")
        space_complexity = cls._extract_complexity(answer, r"空间复杂度[：:]\s*(.+?)(?:\n|$)")

        # 提取表格数据（如果回答中包含复杂度表格）
        table_data = cls._extract_table_data(answer)

        return {
            "type": "complexity",
            "title": f"{topic} - 复杂度分析" if topic else "复杂度分析",
            "icon": "📊",
            "collapsed": False,
            "data": {
                "time_complexity": time_complexity,
                "space_complexity": space_complexity,
                "table_data": table_data,
                "chart_data": cls._build_chart_data(table_data),
            },
            "actions": [],
        }

    @classmethod
    def _build_quiz_card(cls, answer: str, resource_attachments: list = None) -> dict:
        """📝 练习卡：提取或使用已有练习题"""
        # 优先使用 resource_attachments 中的练习题
        if resource_attachments:
            for att in resource_attachments:
                if att.get("type") == "quiz" or att.get("format") == "json":
                    quiz_data = att.get("content_json", {})
                    if isinstance(quiz_data, dict) and "quiz_items" in quiz_data:
                        quiz_items = quiz_data["quiz_items"]
                    else:
                        quiz_items = quiz_data if isinstance(quiz_data, list) else []

                    return {
                        "type": "quiz",
                        "title": "练习题",
                        "icon": "📝",
                        "collapsed": False,
                        "data": {
                            "questions": quiz_items[:5],
                            "total": len(quiz_items) if isinstance(quiz_items, list) else 0,
                        },
                        "actions": [
                            {"label": "提交答案", "action": "submit_quiz"},
                        ],
                    }

        # 如果回答中包含题目格式，尝试解析
        quiz_items = cls._parse_quiz_from_answer(answer)
        if quiz_items:
            return {
                "type": "quiz",
                "title": "练习题",
                "icon": "📝",
                "collapsed": False,
                "data": {
                    "questions": quiz_items[:5],
                    "total": len(quiz_items),
                },
                "actions": [
                    {"label": "提交答案", "action": "submit_quiz"},
                ],
            }

        return None

    @classmethod
    def _build_suggestion_card(
        cls, profile: dict, topic: str, knowledge_nodes: list = None
    ) -> dict:
        """🎯 学习建议卡：基于画像推荐下一步"""
        weaknesses = profile.get("weaknesses", [])
        knowledge_mastery = profile.get("knowledge_mastery", {})

        # 已掌握的知识点（掌握度 > 70%）
        mastered = [t for t, s in knowledge_mastery.items() if float(s) > 70][:5]

        # 下一步建议
        next_steps = []
        if weaknesses:
            next_steps.append({
                "topic": weaknesses[0],
                "reason": "这是你当前的薄弱点，建议优先巩固",
                "action": "start_learn",
            })

        # 从知识节点中找与当前主题相关的后续节点
        if knowledge_nodes and topic:
            for node in knowledge_nodes:
                prereqs = node.get("prerequisites", []) or []
                if isinstance(prereqs, list):
                    for p in prereqs:
                        if topic.lower() in str(p).lower() and node.get("title") not in [s.get("topic") for s in next_steps]:
                            next_steps.append({
                                "topic": node.get("title", ""),
                                "reason": f"学完{topic}后推荐学习",
                                "action": "start_learn",
                                "node_id": node.get("id", ""),
                            })
                            break
                if len(next_steps) >= 3:
                    break

        # 知识图谱局部快照
        kg_snippet = None
        if knowledge_nodes and topic:
            kg_snippet = cls._build_kg_snippet(topic, knowledge_nodes)

        return {
            "type": "suggestion",
            "title": "AI 学习建议",
            "icon": "🎯",
            "collapsed": False,
            "data": {
                "mastered": mastered,
                "weak_points": weaknesses[:3],
                "next_steps": next_steps[:3],
                "knowledge_graph_snippet": kg_snippet,
            },
            "actions": [],
        }

    @classmethod
    def _build_knowledge_graph_card(cls, topic: str, knowledge_nodes: list = None) -> dict:
        """🗺 知识图谱卡：当前节点 + 邻居节点"""
        if not knowledge_nodes:
            return None

        kg_snippet = cls._build_kg_snippet(topic, knowledge_nodes)
        if not kg_snippet:
            return None

        return {
            "type": "knowledge_graph",
            "title": "知识图谱",
            "icon": "🗺",
            "collapsed": True,
            "data": {
                "current": kg_snippet.get("current", topic),
                "neighbors": kg_snippet.get("neighbors", []),
                "parent": kg_snippet.get("parent", ""),
                "children": kg_snippet.get("children", []),
            },
            "actions": [],
        }

    @classmethod
    def _build_comparison_card(cls, answer: str, topic: str) -> dict:
        """⚖️ 对比卡：提取对比项和差异"""
        items = cls._extract_comparison_items(answer)

        return {
            "type": "comparison",
            "title": f"{topic} 对比分析" if topic else "对比分析",
            "icon": "⚖️",
            "collapsed": False,
            "data": {
                "items": items,
                "raw_answer": answer,
            },
            "actions": [],
        }

    @classmethod
    def _build_debug_card(cls, answer: str) -> dict:
        """🔧 调试卡：错误定位 + 修复方案"""
        # 提取错误信息
        error_match = re.search(r'(?:错误|报错|bug|Error)[：:]\s*(.+?)(?:\n|$)', answer, re.IGNORECASE)
        error_desc = error_match.group(1) if error_match else ""

        # 提取修复代码（通常在第2个或最后一个代码块）
        code_blocks = cls._extract_code_blocks(answer)
        fix_code = code_blocks[1].get("code", "") if len(code_blocks) > 1 else (
            code_blocks[0].get("code", "") if code_blocks else ""
        )

        return {
            "type": "debug",
            "title": "错误分析",
            "icon": "🔧",
            "collapsed": False,
            "data": {
                "error_description": error_desc,
                "root_cause": cls._extract_section(answer, "原因"),
                "fix_code": fix_code,
                "original_code": code_blocks[0].get("code", "") if code_blocks else "",
            },
            "actions": [
                {"label": "复制修复代码", "action": "copy", "target": fix_code},
            ],
        }

    @classmethod
    def _extract_mermaid_card(cls, answer: str) -> Optional[dict]:
        """📐 从回答中提取 Mermaid 代码块"""
        mermaid_match = re.search(
            r'```mermaid\s*\n(.*?)```', answer, re.DOTALL | re.IGNORECASE
        )
        if not mermaid_match:
            return None

        return {
            "type": "mermaid",
            "title": "关系图解",
            "icon": "📐",
            "collapsed": False,
            "data": {
                "code": mermaid_match.group(1).strip(),
            },
            "actions": [],
        }

    # ══════════════════════════════════════════════════
    #  辅助提取方法
    # ══════════════════════════════════════════════════

    @staticmethod
    def _extract_code_blocks(text: str) -> List[dict]:
        """提取所有代码块"""
        # 匹配 ```language\ncode\n```
        pattern = r'```(\w*)\s*\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        blocks = []
        for lang, code in matches:
            blocks.append({
                "language": lang.strip() or "plaintext",
                "code": code.strip(),
            })
        return blocks

    @staticmethod
    def _extract_line_explanations(answer: str, code: str) -> dict:
        """尝试从回答中提取代码的逐行解释"""
        explanations = {}
        code_lines = code.strip().split("\n")

        # 查找 "第X行" 或 "line X" 模式的解释
        for i, line in enumerate(code_lines):
            line_num = i + 1
            # 在回答中搜索对应行号的解释
            patterns = [
                rf"第\s*{line_num}\s*行[：:]\s*(.+?)(?:\n|$)",
                rf"line\s*{line_num}[：:]\s*(.+?)(?:\n|$)",
            ]
            for pat in patterns:
                match = re.search(pat, answer, re.IGNORECASE)
                if match:
                    explanations[str(line_num)] = match.group(1).strip()[:120]
                    break

        return explanations

    @staticmethod
    def _extract_complexity(text: str, pattern: str) -> Optional[str]:
        """从文本中提取复杂度信息"""
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()[:100]
        return None

    @staticmethod
    def _extract_table_data(text: str) -> List[dict]:
        """提取 Markdown 表格数据"""
        # 匹配表格行
        lines = text.split("\n")
        table_rows = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                if re.match(r'^\|[\s\-:]+\|', stripped):
                    # 分隔行，跳过
                    in_table = True
                    continue
                if in_table or stripped.startswith("|"):
                    cells = [c.strip() for c in stripped.split("|")[1:-1]]
                    if cells:
                        table_rows.append(cells)
                        in_table = True
            else:
                if in_table:
                    break

        # 转换为字典列表
        if len(table_rows) < 2:
            return []

        headers = table_rows[0]
        result = []
        for row in table_rows[1:]:
            # 确保行长度匹配（用空填充）
            while len(row) < len(headers):
                row.append("")
            row_dict = {}
            for i, h in enumerate(headers):
                if i < len(row):
                    row_dict[h] = row[i]
            result.append(row_dict)

        return result

    @staticmethod
    def _build_chart_data(table_data: List[dict]) -> dict:
        """将表格数据转换为 ECharts 柱状图数据"""
        if not table_data:
            return {}

        # 尝试识别包含"算法"或复杂度数据的列
        labels = []
        values = []
        value_key = None

        # 找第一个看起来像算法名称的列作为 labels
        first_row = table_data[0] if table_data else {}
        for key in first_row:
            if "算法" in key or "结构" in key or "方法" in key or "名称" in key:
                value_key = key
                break
        if not value_key:
            value_key = list(first_row.keys())[0] if first_row else ""

        labels = [row.get(value_key, "") for row in table_data]

        # 找时间复杂度列
        time_keys = [k for k in first_row if "时间" in k or "Time" in k]
        data = {}
        for tk in time_keys[:2]:  # 最多取2列
            data[tk] = [row.get(tk, "") for row in table_data]

        return {
            "labels": labels,
            "series": data,
        }

    @staticmethod
    def _parse_quiz_from_answer(answer: str) -> List[dict]:
        """从纯文本回答中解析练习题"""
        items = []
        # 匹配 "1. 题目内容\n A. 选项A\n B. 选项B" 等格式
        question_pattern = re.compile(
            r'(\d+)[\.、]\s*(.+?)(?=\n\s*(?:[A-D][\.、]|\d+[\.、]|$))',
            re.DOTALL
        )
        # 简化版：按数字编号分割
        parts = re.split(r'\n\s*(?=\d+[\.、])', answer)
        for part in parts:
            # 检查是否包含选项
            if re.search(r'[A-D][\.、]', part):
                lines = [l.strip() for l in part.split("\n") if l.strip()]
                if len(lines) >= 3:
                    question_text = re.sub(r'^\d+[\.、]\s*', '', lines[0])
                    options = []
                    for opt_line in lines[1:]:
                        opt_match = re.match(r'([A-D])[\.、]\s*(.+)', opt_line)
                        if opt_match:
                            options.append({
                                "label": opt_match.group(1),
                                "text": opt_match.group(2).strip(),
                            })
                    if options:
                        items.append({
                            "type": "single_choice",
                            "question": question_text,
                            "options": options,
                        })
            if len(items) >= 3:
                break

        return items

    @staticmethod
    def _extract_section(answer: str, keyword: str) -> str:
        """提取回答中某个关键词对应的段落"""
        pattern = rf'(?:{keyword})[：:]\s*(.+?)(?:\n\n|\n(?:#{1,4}\s|$))'
        match = re.search(pattern, answer, re.DOTALL)
        if match:
            return match.group(1).strip()[:500]
        return ""

    @staticmethod
    def _extract_comparison_items(answer: str) -> List[dict]:
        """提取对比项"""
        items = []
        # 查找 "1. A: ... \n B: ..." 格式
        comparison_pattern = re.compile(
            r'(?:^|\n)\s*(?:[1-9][\.、]|[-*])\s*(.+?)[：:]\s*(.+?)(?=\n\s*(?:[2-9][\.、]|[-*]|$))',
            re.DOTALL
        )
        matches = comparison_pattern.findall(answer)
        for title, desc in matches[:5]:
            items.append({
                "name": title.strip()[:50],
                "description": desc.strip()[:200],
            })
        return items

    @staticmethod
    def _build_kg_snippet(topic: str, knowledge_nodes: list) -> Optional[dict]:
        """从知识节点列表中构建局部知识图谱"""
        if not knowledge_nodes or not topic:
            return None

        current_node = None
        for node in knowledge_nodes:
            if topic.lower() in node.get("title", "").lower() or topic.lower() in node.get("id", "").lower():
                current_node = node
                break

        if not current_node:
            return None

        parent_id = current_node.get("parent_id", "")
        node_id = current_node.get("id", "")

        # 找到父节点
        parent = None
        for node in knowledge_nodes:
            if node.get("id") == parent_id:
                parent = node
                break

        # 找到子节点（parent_id == 当前节点id）
        children = []
        for node in knowledge_nodes:
            if node.get("parent_id") == node_id:
                children.append({
                    "id": node.get("id", ""),
                    "title": node.get("title", ""),
                    "difficulty": node.get("difficulty", 1),
                })

        # 找到兄弟节点 / 前置依赖节点
        neighbors = []
        prereqs = current_node.get("prerequisites", []) or []
        if isinstance(prereqs, list):
            for pid in prereqs:
                for node in knowledge_nodes:
                    if node.get("id") == pid:
                        neighbors.append({
                            "id": node.get("id", ""),
                            "title": node.get("title", ""),
                            "relation": "前置",
                            "difficulty": node.get("difficulty", 1),
                        })
                        break

        # 添加同父节点
        for node in knowledge_nodes:
            if node.get("parent_id") == parent_id and node.get("id") != node_id:
                neighbors.append({
                    "id": node.get("id", ""),
                    "title": node.get("title", ""),
                    "relation": "兄弟",
                    "difficulty": node.get("difficulty", 1),
                })

        return {
            "current": current_node.get("title", topic),
            "current_id": node_id,
            "parent": parent.get("title", "") if parent else "",
            "children": children[:5],
            "neighbors": neighbors[:5],
        }
