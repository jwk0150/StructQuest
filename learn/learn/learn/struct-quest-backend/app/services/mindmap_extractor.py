"""
导图提取器 (Mindmap Extractor / Parser)
========================================

功能：
1. 解析多种格式的思维导图输入（JSON、Markdown、Markmap格式）
2. 将思维导图压缩为轻量级文本（减少LLM Token消耗）
3. 调用AI生成结构化PPT大纲JSON

支持的输入格式：
  - mindmap_json: 标准树形JSON结构
  - markmap: Markmap/Mermaid语法
  - markdown: 层级Markdown文本
  - raw_text: 纯文本（自动构建扁平结构）

输出：
  - 标准大纲JSON (Outline JSON)
"""

import json
import re
import logging
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger("mindmap_extractor")


class MindmapExtractor:
    """
    导图提取器 — 从思维导图数据生成PPT大纲
    
    核心流程:
        输入 → 解析 → 压缩 → AI生成 → 输出大纲JSON
    """
    
    # 大纲生成的System Prompt
    OUTLINE_GENERATION_PROMPT = """你是一名专业的 PPT 内容创作者。请根据提供的主题/思维导图内容，自动生成一份完整的、内容丰富的 PPT 大纲。

## 核心任务
你不仅仅是提取结构，而是要为每一页 PPT 生成 **完整、专业、可直接使用的内容**。
用户会在你生成的基础上进行微调，所以请确保内容质量足够高。

---

## 内容质量要求（最重要！）

### bullet_points 写作标准
- 每个条目必须是 **完整的详细描述**（建议 40-120 字），而非简短关键词
- 包含三个层次：
  1. **概念定义**：清晰解释这是什么
  2. **核心要点**：关键细节、特性或机制
  3. **实际应用**：例子、场景、数据或案例

### 好的示例
```json
{
  "bullet_points": [
    "监督学习（Supervised Learning）：通过已标注的数据集训练模型，输入特征 X 与标签 Y 成对出现。模型学习从输入到输出的映射关系，常见算法包括线性回归（连续值预测）、决策树（分类与回归）、神经网络（复杂模式识别）等。典型应用：垃圾邮件分类、房价预测、图像识别。",
    "无监督学习（Unsupervised Learning）：从未标注的数据集中自主发现隐藏模式和内在结构，无需人工标注标签。主要技术包括 K-Means 聚类（客户分群）、PCA 降维（数据压缩）、关联规则挖掘（购物篮分析）。适用场景：数据探索、异常检测、用户行为分析。"
  ]
}
```

### 不好的示例（禁止！）
```json
{
  "bullet_points": [
    "监督学习",
    "无监督学习", 
    "强化学习"
  ]
}
```

---

## 结构规划

### ⚠️ 思维导图 → PPT 映射规则（必须遵守！）

输入的文本使用 Markdown 标题层级表示思维导图结构，请严格按以下规则映射：

```
# 根主题           → PPT 的 topic（封面标题）
## 一级分支        → section 页（章节分隔）或重要 content 页标题
### 二级分支       → content 页的标题，其下的 - 列表项展开为 bullet_points
#### 三级分支      → 可合并到上级 content 页的 bullet_points 中
- 叶子要点        → 展开为 bullet_points 的详细描述（40-120字）
```

**核心原则**：
- 思维导图的每个 `##` 一级分支至少对应 1-2 页 PPT 内容
- 思维导图的每个 `###` 二级分支尽量独立成页（信息量够的话）
- `-` 叶子节点必须展开为完整的详细描述，**禁止直接复制短关键词**
- **不要编造思维导图中没有的大标题**，内容要忠于原始结构

### 页数规划
- 目标页数：{target_pages} 页（包含封面和结尾）
- 优先保证思维导图的每个 `##` 一级分支都有对应的内容页
- 如果一级分支<=3个，则把 `###` 二级分支也独立成页
- 每页 3-5 个详细要点（宁少勿滥，保证每个要点都有实质内容）

---

## 页面类型系统（10种 layout，请灵活搭配使用！）

请根据内容特点选择最合适的 layout，**不要全部用同一种类型**：

| layout | 适用场景 | 特征 |
|--------|----------|------|
| **title** | 封面页（仅第1页） | 大标题+副标题，无bullet_points |
| **section** | 章节分隔页 | 大章节标题，简洁有力 |
| **content** | 内容主体页（最常用） | 标题+3-5条详细bullet_points |
| **summary** | 总结页（最后1-2页） | 回顾+展望，有bullet_points |
| **chart** | 数据展示页 | 标题+描述数据的bullet_points，visual_suggestion应说明图表类型 |
| **comparison** | 对比分析页 | 标题+对比维度bullet_points，适合"方案A vs B"、"优缺点对比"等 |
| **timeline** | 流程/时间线页 | 标题+按顺序排列的阶段/步骤bullet_points |
| **quote** | 金句/引用页 | 标题+1-2条核心引用bullet_points，视觉上突出文字 |
| **two_column** | 双栏图文页 | 标题+左右分栏的bullet_points，适合"理论+实践"、"概念+案例" |
| **cards_grid** | 卡片网格页 | 标题+多个并列短要点，每点独立成块（如"4大特点""6个步骤"） |

### layout 分配建议（按 target_pages 比例）
- title: 第1页（必须）
- section: 每3-5页内容插入1个章节页
- content: 主体，占总页数的50-60%
- summary: 最后1页（必须）
- chart/comparison/timeline/quote/two_column/cards_grid: 根据内容自然穿插，总共占比20-30%
- **重要：相邻页面不要使用相同layout，保持视觉节奏变化**

---

## 输出格式（严格 JSON）

```json
{{
  "total_pages": {target_pages},
  "topic": "{{主题名称}}",
  "slides": [
    {{
      "page": 1,
      "layout": "title",
      "title": "{{主标题}}",
      "subtitle": "{{副标题：一句话概括核心价值}}",
      "bullet_points": [],
      "speaker_notes": "开场白：介绍演讲背景、目的和预期收获",
      "visual_suggestion": "封面设计建议"
    }},
    {{
      "page": 2,
      "layout": "section",
      "title": "{{第一章节名}}",
      "subtitle": "",
      "bullet_points": [],
      "speaker_notes": "章节过渡语",
      "visual_suggestion": "章节页视觉建议：全屏色块+大标题"
    }},
    {{
      "page": 3,
      "layout": "content",
      "title": "{{页面标题}}",
      "bullet_points": [
        "{{详细描述1：概念+要点+例子，40-120字}}",
        "{{详细描述2：概念+要点+例子，40-120字}}",
        "{{详细描述3：概念+要点+例子，40-120字}}"
      ],
      "speaker_notes": "演讲者备注",
      "visual_suggestion": "布局建议：如'左侧文字右侧图示'或'三列卡片布局'"
    }},
    {{
      "page": 4,
      "layout": "comparison",
      "title": "{{方案对比标题}}",
      "bullet_points": [
        "{{方案A的详细描述，包含优缺点}}",
        "{{方案B的详细描述，包含优缺点}}",
        "{{两者的关键差异和适用场景}}"
      ],
      "speaker_notes": "对比讲解思路",
      "visual_suggestion": "左右双栏对比布局，中间分隔线+高亮差异点"
    }}
  ]
}}
```

## 新增字段说明
- **speaker_notes**（必填）：每页的演讲者备注，帮助演讲者知道如何展开讲解
- **visual_suggestion**（必填）：用一句话推荐该页的可视化呈现方式，**不同layout要给不同的具体建议**

---

## 注意事项
1. **内容为王**：每个 bullet_point 都必须有实质内容，禁止输出空洞关键词
2. **忠于原始结构**：PPT 的内容必须来源于思维导图，不要凭空编造不存在的主题
3. **层层覆盖**：确保思维导图的每个 `##` 一级分支都在 PPT 中有对应的页面
4. **layout 多样化**：合理使用10种layout类型，避免单调重复（相邻页禁止同layout）
5. **专业但易懂**：使用专业术语时给出通俗解释
6. **逻辑连贯**：从概述到细节再到总结，层层递进
7. **因地制宜**：根据实际内容调整深度
8. **只返回 JSON**：不要输出任何其他文字、解释或 markdown 标记"""
    
    def __init__(self, llm_service=None):
        """
        初始化导图提取器
        
        Args:
            llm_service: LLM服务实例（用于调用大模型生成大纲）。
                        如果为None，则使用规则引擎做简单转换。
        """
        self.llm_service = llm_service
    
    async def extract(
        self,
        source_type: str,           # "mindmap" | "markmap" | "markdown" | "raw_text"
        content: str,               # 原始内容
        target_pages: int = 10,     # 目标页数
        existing_mindmap: Optional[str] = None,  # 已有的思维导图数据
    ) -> Dict[str, Any]:
        """
        主入口：解析输入并生成大纲
        
        Args:
            source_type: 输入源类型
            content: 原始内容字符串
            target_pages: 目标PPT页数
            existing_mindmap: 已有的思维导图JSON（当source_type='existing'时使用）
        
        Returns:
            标准大纲JSON字典
        """
        logger.info(
            f"开始提取思维导图: type={source_type}, target_pages={target_pages}"
        )
        
        tree = None
        compressed_text = ""

        try:
            # Step 1: 解析原始数据为统一树形结构
            if source_type == "existing" and existing_mindmap:
                tree = self._parse_existing_mindmap(existing_mindmap)
            elif source_type == "mindmap":
                tree = self._parse_mindmap_json(content)
            elif source_type == "markmap":
                tree = self._parse_markmap(content)
            elif source_type == "markdown":
                tree = self._parse_markdown(content)
            elif source_type == "raw_text":
                tree = self._build_flat_structure(content)
            else:
                raise ValueError(f"不支持的输入类型: {source_type}")

            node_count = self._count_nodes(tree)
            logger.info(f"解析完成，共 {node_count} 个节点")

            # Step 2: 压缩成轻量级文本
            compressed_text = self._compress_to_lightweight_text(tree)
            logger.info(f"压缩后文本长度: {len(compressed_text)} 字符")

            # Step 3: 生成大纲（优先 LLM，失败时回退到规则引擎）
            if self.llm_service:
                try:
                    outline = await self._call_llm_generate_outline(
                        compressed_text, target_pages
                    )
                    logger.info("LLM 大纲生成成功")
                except Exception as llm_err:
                    logger.warning(f"LLM调用失败，回退到规则引擎: {llm_err}")
                    outline = self._rule_based_outline(
                        tree, compressed_text, target_pages
                    )
            else:
                logger.info("无LLM服务，使用规则引擎生成大纲")
                outline = self._rule_based_outline(
                    tree, compressed_text, target_pages
                )

            # 验证并标准化大纲
            outline = self._normalize_outline(outline, target_pages)

            logger.info(f"大纲生成完成: {outline.get('total_pages', 0)} 页")
            return outline

        except Exception as e:
            logger.error(f"导图提取失败: {e}", exc_info=True)
            # 使用已解析的树结构作为 fallback（比纯文本 fallback 更好）
            if tree is not None and self._count_nodes(tree) > 1:
                logger.info("使用已解析的树结构生成降级大纲")
                try:
                    fallback = self._rule_based_outline(tree, compressed_text, target_pages)
                    return self._normalize_outline(fallback, target_pages)
                except Exception:
                    pass
            return self._fallback_outline(compressed_text or content, target_pages)
    
    # ══════════════════════════════════
    #   解析器（各格式专用）
    # ══════════════════════════════════
    
    def _parse_existing_mindmap(self, mindmap_data: str) -> Dict:
        """解析已存在的思维导图数据（来自NodeLearning）"""
        if isinstance(mindmap_data, str):
            # 尝试 JSON 解析
            try:
                data = json.loads(mindmap_data)
            except json.JSONDecodeError:
                # 不是JSON → 尝试作为 Markdown/Markmap 文本处理
                return self._parse_markdown(mindmap_data)

            # json.loads 成功了，但结果可能仍然是字符串（如 markdown 被 JSON 序列化过）
            if isinstance(data, str):
                # 如果是 JSON 字符串，尝试再次解析（双重序列化），否则作为 Markdown
                try:
                    data = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    return self._parse_markdown(data)
        else:
            data = mindmap_data

        # 如果最终解析结果仍是字符串/非标准结构，回退到 Markdown 解析
        if isinstance(data, str):
            return self._parse_markdown(data)

        # 标准化树形结构
        return self._normalize_tree(data)
    
    def _parse_mindmap_json(self, content: str) -> Dict:
        """解析标准思维导图JSON"""
        data = json.loads(content)
        return self._normalize_tree(data)
    
    def _parse_markmap(self, content: str) -> Dict:
        """
        解析 Markmap / Markdown 层级文本

        支持的格式（自动检测）：

        【格式A — # 标题层级】（优先，AI 生成的思维导图使用此格式）:
        # 根主题
        ## 一级分支
        ### 二级细节
        - 叶子要点1
        - 叶子要点2
        ## 另一个一级分支

        【格式B — 缩进层级】（兼容旧格式）:
        根主题
          子标题1
            要点1.1
            要点1.2
          子标题2
        """
        lines = content.strip().split("\n")
        root = {"name": "根节点", "children": []}
        stack = [(root, 0)]  # (node, header_level)

        # ── 自动检测格式 ──
        has_headers = any(
            re.match(r'^#{1,6}\s+\S', line.strip())
            for line in lines
        )

        for line in lines:
            line = line.rstrip()
            if not line or line.startswith("```"):
                continue

            stripped = line.lstrip()

            if has_headers:
                # ── 格式A: 基于 # 数量的层级 ──
                header_match = re.match(r'^(#{1,6})\s+(.+)', stripped)
                list_match = re.match(r'^[-*]\s+(.+)', stripped)

                if header_match:
                    level = len(header_match.group(1))
                    text = header_match.group(2).strip()
                elif list_match:
                    # 列表项：作为当前最深父节点的叶子子节点
                    text = list_match.group(1).strip()
                    node = {"name": text, "children": []}
                    stack[-1][0]["children"].append(node)
                    continue  # 叶子节点不入栈
                else:
                    # 普通文本行：作为叶子节点
                    text = stripped[:80] + ("..." if len(stripped) > 80 else "")
                    node = {"name": text, "children": []}
                    stack[-1][0]["children"].append(node)
                    continue

                if not text:
                    continue

                node = {"name": text, "children": []}

                # 弹栈到层级比当前低的父节点
                while len(stack) > 1 and stack[-1][1] >= level:
                    stack.pop()

                stack[-1][0]["children"].append(node)
                stack.append((node, level))

            else:
                # ── 格式B: 基于缩进的层级（兼容旧逻辑）──
                level = len(line) - len(stripped)

                # 清理Markdown标记
                text = re.sub(r'^#{1,6}\s*', '', stripped).strip()
                if not text:
                    continue

                node = {"name": text, "children": []}

                while stack and stack[-1][1] >= level:
                    stack.pop()

                if stack:
                    parent = stack[-1][0]
                    parent["children"].append(node)

                stack.append((node, level))

        # 如果根节点只有一个子节点，提升它
        if len(root["children"]) == 1:
            root = root["children"][0]

        return root
    
    def _parse_markdown(self, content: str) -> Dict:
        """解析层级Markdown文本（类似Markmap但更宽松）"""
        return self._parse_markmap(content)
    
    def _build_flat_structure(self, text: str) -> Dict:
        """将纯文本构建为扁平的树形结构"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            return {"name": "内容", "children": []}
        
        root_name = paragraphs[0][:50] + ("..." if len(paragraphs[0]) > 50 else "")
        root = {
            "name": root_name,
            "children": [
                {"name": p[:80] + ("..." if len(p) > 80 else ""), "children": []}
                for p in paragraphs[1:20]
            ]
        }
        return root
    
    # ══════════════════════════════════
    #   树形工具方法
    # ══════════════════════════════════
    
    @staticmethod
    def _normalize_tree(data: Any) -> Dict:
        """将各种可能的JSON结构标准化为 {name, children[]} 格式"""
        if isinstance(data, dict):
            # 已经是标准格式
            if "name" in data and "children" in data:
                return {
                    "name": data["name"],
                    "children": [
                        MindmapExtractor._normalize_tree(c)
                        for c in (data.get("children") or [])
                    ]
                }
            # 可能是 {root: {...}} 或 {data: {...}}
            for key in ["root", "data", "mindmap", "topic"]:
                if key in data:
                    return MindmapExtractor._normalize_tree(data[key])
            # 尝试用第一个有子节点的key
            for val in data.values():
                if isinstance(val, (dict, list)):
                    return MindmapExtractor._normalize_tree(val)
        
        if isinstance(data, list) and len(data) > 0:
            # 数组形式 [{name, children[]}, ...]
            return {
                "name": "主题",
                "children": [
                    MindmapExtractor._normalize_tree(item) for item in data
                ]
            }
        
        return {"name": str(data), "children": []}
    
    @staticmethod
    def _count_nodes(node: Dict) -> int:
        """递归统计节点数"""
        count = 1
        for child in node.get("children", []):
            count += MindmapExtractor._count_nodes(child)
        return count
    
    # ══════════════════════════════════
    #   文本压缩（减少Token消耗）
    # ══════════════════════════════════
    
    def _compress_to_lightweight_text(self, tree: Dict) -> str:
        """
        将树形结构压缩为轻量级文本（保留层级信息，用于 LLM 输入）

        改进：
        - 更深层级（6层 vs 原来4层）
        - 更大的字符预算（8000 vs 原来4000）
        - 用 Markdown # 标记层级，LLM 更容易理解结构
        """
        lines = []
        self._tree_to_lines(tree, lines, depth=0, max_depth=6)

        # 合并为段落
        result = "\n".join(lines)

        # 后处理：截断总长度
        max_chars = 8000  # 增加 Token 预算，保留更多细节
        if len(result) > max_chars:
            result = result[:max_chars] + "\n... (内容已按长度截断)"

        return result

    def _tree_to_lines(
        self,
        node: Dict,
        lines: List[str],
        depth: int = 0,
        max_depth: int = 6
    ):
        """递归将树转为文本行（用 Markdown # 标记层级）"""
        if depth > max_depth:
            return

        name = node.get("name", "")
        if not name:
            return

        # 截断过长文本（放宽限制）
        max_name_len = 100 - depth * 6
        if len(name) > max_name_len:
            name = name[:max_name_len] + "..."

        # 用 Markdown 标题层级标记，LLM 更容易理解
        if depth == 0:
            # 根节点：用 # 标题
            lines.append(f"# {name}")
        else:
            # 子节点：用 ##/###/#### 等
            header_prefix = "#" * min(depth + 1, 6)
            child_count = len(node.get("children", []))
            if child_count > 0:
                lines.append(f"{header_prefix} {name}  ({child_count}个子主题)")
            else:
                lines.append(f"{header_prefix} {name}")

        # 处理子节点
        children = node.get("children", [])
        for i, child in enumerate(children):
            self._tree_to_lines(child, lines, depth + 1, max_depth)
    
    # ══════════════════════════════════
    #   大纲生成
    # ══════════════════════════════════
    
    async def _call_llm_generate_outline(
        self, 
        compressed_text: str, 
        target_pages: int
    ) -> Dict:
        """调用LLM生成大纲"""
        prompt = self.OUTLINE_GENERATION_PROMPT.format(
            target_pages=target_pages
        ) + f"\n\n## 待转换内容\n{compressed_text}"
        
        try:
            response = await self.llm_service.chat_completion(
                messages=[
                    {"role": "system", "content": (
                        "你是专业的PPT内容创作者。严格遵守以下规则：\n"
                        "1. 只输出有效JSON，不要任何额外文字\n"
                        "2. 每个bullet_point必须是40-120字的详细描述（概念+要点+例子）\n"
                        "3. 必须严格基于输入的思维导图结构生成内容，不要凭空编造\n"
                        "4. 思维导图的每个##一级分支至少对应1-2页PPT\n"
                        "5. 合理使用10种layout类型（title/section/content/summary/chart/comparison/timeline/quote/two_column/cards_grid）\n"
                        "6. 相邻页面不可使用相同layout"
                    )},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=8000,
            )
            
            # 提取JSON响应
            response_text = response.get("content", response) if isinstance(response, dict) else str(response)
            
            # 清理可能的markdown代码块包裹
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
            if json_match:
                response_text = json_match.group(1).strip()
            
            outline = json.loads(response_text)
            logger.info("LLM大纲生成成功")
            return outline
            
        except Exception as e:
            logger.warning(f"LLM调用失败，回退到规则引擎: {e}")
            raise e  # 让外层捕获并使用fallback
    
    # Layout 类型定义与元数据
    LAYOUT_META = {
        "title": {"label": "封面", "icon": "📄", "color": "#e6a23c", "needs_bullets": False},
        "section": {"label": "章节", "icon": "📑", "color": "#f56c6c", "needs_bullets": False},
        "content": {"label": "内容", "icon": "📋", "color": "#409eff", "needs_bullets": True},
        "summary": {"label": "总结", "icon": "✅", "color": "#67c23a", "needs_bullets": True},
        "chart": {"label": "图表", "icon": "📊", "color": "#9b59b6", "needs_bullets": True},
        "comparison": {"label": "对比", "icon": "⚖️", "color": "#e67e22", "needs_bullets": True},
        "timeline": {"label": "时间线", "icon": "⏱️", "color": "#1abc9c", "needs_bullets": True},
        "quote": {"label": "引用", "icon": "💬", "color": "#34495e", "needs_bullets": True},
        "two_column": {"label": "双栏", "icon": "📑", "color": "#2980b9", "needs_bullets": True},
        "cards_grid": {"label": "卡片网格", "icon": "🃏", "color": "#8e44ad", "needs_bullets": True},
    }

    # 视觉建议模板库（按 layout 类型）
    VISUAL_TEMPLATES = {
        "title": [
            "居中大标题+副标题，渐变背景（蓝紫渐变），底部装饰线条",
            "全屏背景图+半透明遮罩层+白色大标题，现代感强",
            "左侧几何图形装饰+右侧大标题，简约商务风格",
        ],
        "section": [
            "全屏色块展示章节标题，超大字号加粗，左下角页码",
            "左侧竖条色块+右侧大标题，简洁专业",
            "中心放射状装饰+环绕文字的章节名，创意感强",
        ],
        "content": [
            "左侧大标题区(30%)+右侧要点列表区(70%)，每行配小图标",
            "顶部醒目标题+下方三列卡片式要点，每卡独立底色",
            "左侧图标导航+右侧详细内容区，适合信息量大的页面",
            "顶部标题+中部大图/示意图+底部3个精炼要点",
        ],
        "summary": [
            "三列总结卡片布局，每列对应一个要点，底部感谢语",
            "左侧核心回顾列表+右侧Q&A区域+底部联系方式",
            "时间轴形式回顾各章节，每个节点一句话总结",
        ],
        "chart": [
            "左侧标题+说明文字(35%)+右侧柱状图/饼图区域(65%)，底部数据来源注释",
            "顶部标题+中间大型数据可视化图表+底部3个关键数据指标卡",
            "左侧多组数据对比表格(40%)+右侧趋势折线图(60%)",
        ],
        "comparison": [
            "左右双栏50:50对比布局，中间分隔线+差异点高亮标注",
            "顶部评价维度表头+下方矩阵式对比格，优势绿色/劣势红色标记",
            "左右两栏方案卡片+底部结论性总结横幅",
        ],
        "timeline": [
            "垂直时间轴布局，左侧时间节点连线+右侧每个阶段配图标和2-3行描述",
            "水平步骤条+下方每个步骤展开详情卡片，适合流程讲解",
            "S形曲线时间轴+沿途节点事件卡片，体现演进过程",
        ],
        "quote": [
            "居中大字引用文本(深色背景)+右下角来源署名+淡色装饰元素",
            "全屏引言图+半透明层上的大号引用文字，视觉冲击力强",
            "左侧大引号装饰+右侧引用正文+底部作者信息卡片",
        ],
        "two_column": [
            "左图右文50:50分栏，图片带圆角阴影，文字区含3个要点",
            "左概念解释区(45%)+右案例分析区(55%)，中间细分隔线",
            "左理论框架+右实践应用，双栏使用不同底色区分",
        ],
        "cards_grid": [
            "2x2或3x2等大卡片网格，每卡包含图标+标题+一句话描述",
            "上方大标题+下方横向滑动卡片组，每卡独立主题色",
            "六边形蜂窝卡片排列，每格一个关键词+简述，创意感强",
        ],
    }

    def _pick_visual_suggestion(self, layout: str) -> str:
        """根据 layout 类型随机选择一个视觉建议"""
        import random
        templates = self.VISUAL_TEMPLATES.get(layout, self.VISUAL_TEMPLATES["content"])
        return random.choice(templates)

    def _expand_node_to_bullets(self, node: Dict, parent_name: str = "", max_bullets: int = 5) -> List[str]:
        """将节点及其子节点扩展为详细的 bullet_points 列表（使用树中的实际内容）"""
        name = node.get("name", "")
        children = node.get("children", [])
        bullets = []

        if not name:
            return bullets

        if children:
            # 有子节点：每个子节点展开为一段完整描述
            for child in children[:max_bullets]:
                child_name = child.get("name", "")
                grandkids = child.get("children", [])
                if grandkids:
                    # 有孙节点：根据孙节点名称生成具体描述
                    gk_names = [g.get("name", "") for g in grandkids[:4] if g.get("name")]
                    if not gk_names:
                        gk_names = ["相关细节"]
                    detail = "、".join(gk_names)
                    bullets.append(
                        f"【{child_name}】：涵盖 {detail} 等方面。"
                        f"这些要素共同构成了「{child_name}」的完整知识体系，"
                        f"每个方面都有其特定的应用场景和注意事项。"
                    )
                else:
                    # 无孙节点但名字本身包含信息（如 "头插 O(1)"）
                    # 生成更有针对性的描述
                    bullets.append(
                        f"【{child_name}】：这是「{parent_name or name}」的关键知识点。"
                        f"掌握「{child_name}」需要理解其定义、适用条件以及与其他概念的关联。"
                        f"建议结合实际案例加深理解并注意常见误区。"
                    )
        else:
            # 叶子节点：基于节点名称生成内容
            bullets = [
                f"【{name} — 概念定义】：「{name}」是数据结构与算法体系中的重要概念，"
                f"理解其核心定义和基本原理是后续深入学习的基础。"
                f"建议从直观含义入手，逐步形式化理解。",
                f"【{name} — 核心机制】：「{name}」的关键在于理解其内部运作方式，"
                f"包括数据组织形态、操作执行流程以及性能特点（时间/空间复杂度）。"
                f"掌握这些内容有助于在实际场景中做出正确的技术选型。",
                f"【{name} — 实践要点】：在实际编程中运用「{name}」时，"
                f"重点关注边界条件处理、常见错误模式以及优化技巧。"
                f"建议通过动手编码和调试来巩固理论理解。",
            ]

        return [b for b in bullets if b]

    def _smart_select_layout(self, index: int, total: int, node: Dict, sibling_count: int) -> str:
        """
        根据上下文智能选择 layout 类型

        规则：
        - 第1页 → title
        - 每4-5页插入 section（当有多个兄弟节点时）
        - 最后一页 → summary
        - 节点名含"对比/比较/vs"→ comparison
        - 节点名含"流程/步骤/阶段/时间"→ timeline
        - 节点名含"数据/统计/分析/趋势"→ chart
        - 子节点数≥4且并列 → cards_grid
        - 子节点数=2 → two_column 或 comparison
        - 偶数页穿插 timeline/chart/comparison/quote 避免单调
        """
        name = (node.get("name") or "").lower()
        children = node.get("children", [])
        child_count = len(children)

        # 关键词匹配
        if any(k in name for k in ["对比", "比较", "vs ", "区别", "异同"]):
            return "comparison"
        if any(k in name for k in ["流程", "步骤", "阶段", "历程", "演进", "发展"]):
            return "timeline"
        if any(k in name for k in ["数据", "统计", "分析", "趋势", "占比", "分布"]):
            return "chart"
        if any(k in name for k in ["引用", "名言", "金句", "观点", "精髓"]):
            return "quote"

        # 结构判断
        if child_count >= 5:
            return "cards_grid"
        if child_count == 2 and sibling_count <= 3:
            return "two_column"

        # 位置轮换：避免连续相同layout
        cycle_layouts = ["content", "two_column", "cards_grid", "timeline", "chart"]
        pos = (index - 1) % len(cycle_layouts)
        if index > 2 and index < total - 1:
            return cycle_layouts[pos]

        return "content"

    def _rule_based_outline(
        self,
        tree: Dict,
        compressed_text: str,
        target_pages: int
    ) -> Dict:
        """
        规则引擎：基于规则的增强大纲转换（无需LLM）

        改进版：
        - 智能选择10种 layout 类型
        - 根据思维导图树形结构生成真实内容
        - 每页都有差异化的 visual_suggestion
        - 避免"核心内容N"式的占位符
        """
        slides = []
        page_num = 1
        topic = tree.get("name", "演示文稿")

        # ═══ 封面页 ═══
        slides.append({
            "page": page_num,
            "layout": "title",
            "title": topic,
            "subtitle": f"全面解析「{topic}」的核心知识体系与实践应用",
            "bullet_points": [],
            "speaker_notes":
                f"欢迎各位参与本次关于「{topic}」的分享。"
                f"今天我们将从基础概念出发，逐步深入到核心原理和实际应用，"
                f"帮助大家建立完整的知识框架。预计时长约{target_pages * 1.5}分钟。",
            "visual_suggestion": self._pick_visual_suggestion("title"),
        })
        page_num += 1

        # ═══ 遍历一级子节点 ═══
        children = tree.get("children", [])
        total_children = len(children)
        content_slides_created = 0

        for ci, child in enumerate(children):
            child_name = child.get("name", "")
            grandchildren = child.get("children", [])
            gc_count = len(grandchildren)

            if not child_name or page_num >= target_pages:
                continue

            # ── 判断是否需要章节页 ──
            needs_section = (
                gc_count >= 3 and target_pages >= 6 and
                ci < total_children - 1 and  # 最后一个一级节点不需要单独section
                content_slides_created >= 1  # 至少已有一些内容后再插section
            )

            if needs_section:
                slides.append({
                    "page": page_num,
                    "layout": "section",
                    "title": child_name,
                    "subtitle": "",
                    "bullet_points": [],
                    "speaker_notes":
                        f"接下来我们进入「{child_name}」部分，"
                        f"这是整个知识体系中的重要板块，将从多个维度进行深入讲解。",
                    "visual_suggestion": self._pick_visual_suggestion("section"),
                })
                page_num += 1

            # ── 为二级节点创建内容页 ──
            for gi, gc in enumerate(grandchildren):
                if page_num >= target_pages:
                    break

                gc_name = gc.get("name", "")
                if not gc_name:
                    continue

                # 智能选择 layout
                layout = self._smart_select_layout(
                    index=page_num, total=target_pages,
                    node=gc, sibling_count=gc_count
                )
                # 如果前面已经有太多同类型的，强制换一种
                recent_layouts = [s["layout"] for s in slides[-3:] if s.get("layout")]
                if recent_layouts.count(layout) >= 2:
                    fallback_layouts = ["content", "two_column", "cards_grid", "timeline", "chart"]
                    for fl in fallback_layouts:
                        if fl != layout:
                            layout = fl
                            break

                # 生成 bullet_points
                bullets = self._expand_node_to_bullets(gc, parent_name=child_name)

                # 根据不同 layout 适配 speaker_notes 和 visual_suggestion
                if layout == "comparison":
                    speaker_notes = (
                        f"本页对比分析「{gc_name}」的不同方面。"
                        f"建议采用逐项对比的方式讲解，突出各自优势和适用场景，"
                        f"最后给出总结性的选择建议。"
                    )
                elif layout == "timeline":
                    speaker_notes = (
                        f"本页以时间线/流程的形式介绍「{gc_name}」。"
                        f"建议按顺序逐步推进讲解，每个阶段说明其目标和关键产出，"
                        f"帮助听众建立清晰的过程认知。"
                    )
                elif layout == "chart":
                    speaker_notes = (
                        f"本页通过数据展示「{gc_name}」的关键指标。"
                        f"讲解时先说明数据来源和口径，再解读图表中的趋势和异常值，"
                        f"最后提炼出数据背后的洞察和建议。"
                    )
                elif layout == "quote":
                    speaker_notes = (
                        f"本页聚焦「{gc_name}」的核心观点或经典论述。"
                        f"建议停顿片刻让听众阅读引言，然后逐句解读其深层含义，"
                        f"联系实际案例说明这一观点的重要性。"
                    )
                elif layout == "cards_grid":
                    speaker_notes = (
                        f"本页用卡片网格呈现「{gc_name}」的多个并列要点。"
                        f"建议依次介绍每张卡片的核心内容，注意控制每张卡的讲解时长均匀，"
                        f"最后总结它们之间的共同点和联系。"
                    )
                elif layout == "two_column":
                    speaker_notes = (
                        f"本页采用双栏布局展示「{gc_name}」的两个侧面。"
                        f"建议先讲完一侧再切换到另一侧，或者左右对照着讲，"
                        f"最后强调两侧之间的关系和互补性。"
                    )
                else:
                    speaker_notes = (
                        f"本页重点讲解「{gc_name}」，建议先介绍基本概念建立认知，"
                        f"再深入技术细节，结合案例分析加深印象，最后强调注意事项。"
                        f"可在此处设置提问互动环节。"
                    )

                slides.append({
                    "page": page_num,
                    "layout": layout,
                    "title": gc_name,
                    "subtitle": "",
                    "bullet_points": bullets,
                    "speaker_notes": speaker_notes,
                    "visual_suggestion": self._pick_visual_suggestion(layout),
                })
                page_num += 1
                content_slides_created += 1

            # ── 如果没有二级节点，把一级节点直接做内容页 ──
            if not grandchildren and page_num < target_pages:
                layout = self._smart_select_layout(page_num, target_pages, child, 0)
                bullets = self._expand_node_to_bullets(child)
                slides.append({
                    "page": page_num,
                    "layout": layout,
                    "title": child_name,
                    "subtitle": "",
                    "bullet_points": bullets,
                    "speaker_notes":
                        f"本页围绕「{child_name}」展开，涵盖多个相关要点。"
                        f"讲解时注意各要点之间的逻辑关系，帮助听众建立系统性的认知。",
                    "visual_suggestion": self._pick_visual_suggestion(layout),
                })
                page_num += 1
                content_slides_created += 1

            if page_num >= target_pages:
                break

        # ═══ 结尾总结页 ═══
        slides.append({
            "page": page_num,
            "layout": "summary",
            "title": "总结与展望",
            "subtitle": "",
            "bullet_points": [
                f"【核心回顾】：今天我们围绕「{topic}」系统学习了理论基础、核心概念和关键技术，"
                f"建立了完整的知识框架体系。重点掌握了各模块之间的内在联系和相互作用机制。",

                f"【实践启示】：理论知识的学习最终要服务于实际应用。"
                f"建议大家在学习过程中多思考如何将所学内容运用到自己的工作和学习场景中，做到学以致用、知行合一。",

                f"【持续进阶】：学习是一个持续的过程，本次分享只是入门引导。"
                f"后续可以通过阅读扩展资料、参与项目实战、与同行交流等方式不断深化理解，实现能力的持续提升。",
            ],
            "speaker_notes":
                "总结时建议快速回顾每个章节的核心要点（每章一句话），"
                "然后强调实践的重要性，最后给出后续学习建议和资源推荐。预留时间答疑互动。",
            "visual_suggestion": self._pick_visual_suggestion("summary"),
        })

        return {
            "total_pages": len(slides),
            "topic": topic,
            "slides": slides
        }
    
    # ══════════════════════════════════
    #   标准化与Fallback
    # ══════════════════════════════════
    
    @staticmethod
    def _normalize_outline(outline: Dict, target_pages: int) -> Dict:
        """验证并标准化大纲结构"""
        if not isinstance(outline, dict):
            return MindmapExtractor._fallback_outline("", target_pages)
        
        slides = outline.get("slides", [])
        if not slides:
            return MindmapExtractor._fallback_outline("", target_pages)
        
        # 标准化每一页
        normalized_slides = []
        for i, slide in enumerate(slides):
            normalized_slide = {
                "page": i + 1,
                "layout": slide.get("layout", "content"),
                "title": slide.get("title", f"第{i + 1}页"),
                "subtitle": slide.get("subtitle", ""),
                "bullet_points": slide.get("bullet_points", []),
                "speaker_notes": slide.get("speaker_notes", ""),
                "visual_suggestion": slide.get("visual_suggestion", ""),
            }
            normalized_slides.append(normalized_slide)
        
        return {
            "total_pages": len(normalized_slides),
            "topic": outline.get("topic", "演示文稿"),
            "slides": normalized_slides
        }
    
    @staticmethod
    def _fallback_outline(content: str, target_pages: int) -> Dict:
        """
        增强版兜底大纲 — 当所有方法都失败时使用

        改进（不再输出"核心内容N"占位符）：
        1. 尝试从原始内容中提取结构信息
        2. 使用多样化的 layout 类型
        3. 每页都有丰富的 bullet_points
        4. 差异化的 visual_suggestion
        """
        import random

        topic = "演示文稿"
        extracted_topics = []

        # ── 尝试从内容中提取有用信息 ──
        if content and content.strip() and content != "学习内容":
            try:
                extractor = MindmapExtractor(llm_service=None)
                temp_tree = extractor._parse_markdown(content)
                topics = []
                MindmapExtractor._collect_node_names(temp_tree, topics, max_depth=2, max_count=12)
                if len(topics) >= 2:
                    extracted_topics = topics
                    topic = temp_tree.get("name", "") or topics[0] or (content[:50] + ("..." if len(content) > 50 else ""))
                elif topics:
                    topic = topics[0]
            except Exception:
                pass

            if len(extracted_topics) < 3:
                lines = content.replace("\r", "\n").split("\n")
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("```") or line.startswith("{"):
                        continue
                    if 4 <= len(line) <= 60 and line not in extracted_topics:
                        extracted_topics.append(line)

        if not topic or topic == "根节点":
            topic = (content or "演示文稿")[:40].strip() or "演示文稿"
        if len(topic) > 50:
            topic = topic[:47] + "..."

        if not extracted_topics:
            extracted_topics = [
                "背景与概述", "核心概念", "关键特性", "技术原理",
                "实践方法", "应用场景", "案例分析", "注意事项",
                "常见问题", "发展趋势", "总结与展望",
            ][:target_pages - 2]

        # ── Layout 轮换序列 ──
        layout_pool = ["content", "two_column", "cards_grid", "timeline", "chart", "comparison", "quote", "content"]

        # Visual 建议（多样化）
        visual_db = {
            "title": [
                "居中大标题+副标题，深蓝到紫色渐变底部光效，专业商务感",
                "全屏抽象几何背景图+半透明遮罩层+居中白色大标题",
                "左侧大号主题图形装饰+右侧标题副标题竖排，现代简约",
            ],
            "content": [
                "左侧大标题区(28%)+右侧要点列表区(72%)，每条配圆角图标和分隔线",
                "顶部醒目标题+下方三列等宽卡片式要点区域，每卡不同强调色",
                "左侧纵向图标导航栏+右侧主内容区，适合信息密度高的页面",
            ],
            "section": ["全屏深色渐变背景+超大白色章节标题(80pt)+左下角页码装饰线",
                        "左侧8px彩色竖条+右侧章节大标题(56pt)+一行英文副标题"],
            "summary": [
                "三列等宽总结卡片（回顾/启示/进阶），每列独立配色+底部感谢语横幅",
                "左侧核心要点时间轴回顾(50%)+右侧Q&A和联系方式(50%)",
            ],
            "chart": [
                "左侧标题和数据说明(35%)+右侧柱状图/饼图可视化区域(65%)，底部数据来源小字",
                "顶部标题+中间大型图表区+底部3个关键指标数据卡(KPI风格)",
            ],
            "comparison": [
                "左右双栏50:50对比布局，中间分隔线+差异高亮标注，优势绿/劣势红",
                "两张圆角卡片并排+底部对比总结文字块，卡片带阴影层次感",
            ],
            "timeline": [
                "垂直时间轴布局，左侧节点连线+右侧每阶段图标+2-3行描述文字",
                "水平步骤条导航(顶部)+下方每个步骤展开详情卡片",
            ],
            "quote": [
                "居中大号引用文字(48pt,深灰底色)+右下角来源署名+装饰引号元素",
                "全屏意境图背景+半透明遮罩上的白色引言，强视觉冲击力",
            ],
            "two_column": [
                "左图右文50:50分栏，图片圆角阴影效果，文字区含3个编号要点",
                "左理论解释(45%右浅蓝底)+右案例展示(55%右浅橙底)，中间细分割线",
            ],
            "cards_grid": [
                "2x2或3x2等大卡片网格，每卡含圆形图标+粗体标题+两行描述",
                "上方大标题+下方横向可滚动卡片组，每张卡独立主题色左边框",
            ],
        }

        slides = []
        page_num = 1

        # ═══ 第1页：封面 ═══
        slides.append({
            "page": page_num,
            "layout": "title",
            "title": topic,
            "subtitle": "系统化知识分享与深度解析",
            "bullet_points": [],
            "speaker_notes":
                f"欢迎各位参与本次关于「{topic}」的分享。"
                f"今天我们将围绕这一主题展开系统性讲解，帮助大家建立完整的认知框架。",
            "visual_suggestion": random.choice(visual_db["title"]),
        })
        page_num += 1

        # ═══ 中间内容页 ═══
        topic_idx = 0
        layout_idx = 0
        content_pages_needed = min(target_pages - 2, len(extracted_topics))

        for i in range(content_pages_needed):
            if page_num >= target_pages:
                break

            is_section = (i > 0 and i % 4 == 0 and target_pages >= 8)

            if is_section:
                section_title = extracted_topics[topic_idx] if topic_idx < len(extracted_topics) else f"部分 {(i // 4) + 1}"
                slides.append({
                    "page": page_num, "layout": "section", "title": section_title, "subtitle": "",
                    "bullet_points": [],
                    "speaker_notes": f"接下来进入「{section_title}」部分的学习。",
                    "visual_suggestion": random.choice(visual_db["section"]),
                })
                page_num += 1
                topic_idx += 1
                if page_num >= target_pages:
                    break

            current_title = extracted_topics[topic_idx] if topic_idx < len(extracted_topics) else f"核心内容 {i + 1}"
            topic_idx += 1

            layout = layout_pool[layout_idx % len(layout_pool)]
            layout_idx += 1
            title_lower = current_title.lower()
            if any(k in title_lower for k in ["对比", "比较", "vs"]):
                layout = "comparison"
            elif any(k in title_lower for k in ["流程", "步骤", "阶段"]):
                layout = "timeline"
            elif any(k in title_lower for k in ["数据", "统计", "分析", "趋势"]):
                layout = "chart"

            # 根据 layout 定制 bullet_points
            if layout == "comparison":
                bullets = [
                    f"【方案A视角】：从「{current_title}」的角度来看，第一种方式侧重于理论基础和系统性构建，其优势在于逻辑清晰、框架完整，适用于需要深入理解原理的场景。",
                    f"【方案B视角】：第二种方式则更注重实践效率和快速落地，通过迭代优化的方式逐步完善，优势是灵活性强、反馈周期短。",
                    f"【选择建议】：综合两者特点，推荐在初期学习时采用方案A建立框架，在实际项目中结合方案B的敏捷思路进行优化调整。",
                ]
            elif layout == "timeline":
                bullets = [
                    f"【阶段一：准备】— 「{current_title}」的起始阶段需要明确目标、梳理现状、准备资源，这一阶段的工作质量直接影响后续推进的顺利程度。",
                    f"【阶段二：执行】— 在准备工作就绪后进入核心执行环节，按照既定计划逐步推进各项目标，过程中需要持续监控进度和质量，及时纠偏。",
                    f"【阶段三：收尾】— 最后对成果进行验收评估，总结经验教训，形成可复用的方法论和最佳实践文档。",
                ]
            elif layout == "chart":
                bullets = [
                    f"【整体规模】：「{current_title}」的整体数据显示出稳定增长的趋势，核心指标较上一周期提升了约15%-25%，表明相关措施取得了显著成效。",
                    f"【细分维度】：从细分数据来看，各个维度的表现存在一定差异，其中表现突出的领域值得深入分析其成功要素并进行推广复制。",
                    f"【趋势预判】：基于现有数据和发展态势判断，未来该方向仍有较大的发展空间，建议持续关注关键指标的动态变化并及时调整策略。",
                ]
            elif layout == "quote":
                bullets = [
                    f"「{current_title}」的本质在于把握核心矛盾和关键路径。真正的精通不是知道所有答案，而是提出正确的问题。这一观点提醒我们在学习中要注重思维方式的培养。",
                    f"在实践中运用这一理念时，建议将复杂问题拆解为可管理的小模块，逐个击破后再进行整合，这种化繁为简的方法论已被大量成功案例验证。",
                ]
            elif layout == "cards_grid":
                bullets = [
                    f"【要点一】{current_title}的基础层面：涵盖定义、范围和基本假设，是理解整个知识体系的入口。",
                    f"【要点二】{current_title}的核心机制：描述内在运作原理和关键驱动因素，是深度理解的关键。",
                    f"【要点三】{current_title}的实践方法：提供具体可操作的步骤和工具，帮助将理论转化为行动。",
                    f"【要点四】{current_title}的常见陷阱：列出初学者容易踩的坑和错误认知，提前规避风险。",
                ]
            elif layout == "two_column":
                bullets = [
                    f"【理论层面】— 「{current_title}」的理论基础包括基本概念的准确定义、与其他相关概念的区别联系以及理论发展的历史脉络。",
                    f"【实践层面】— 将理论应用到实际场景时需要考虑具体的约束条件、可用资源和目标要求，通过案例分析来加深理解。",
                ]
            else:
                bullets = [
                    f"【概述】：了解「{current_title}」的基本定义和在整体知识架构中的定位，它是理解后续内容的重要基础。",
                    f"【核心要素】：包含基本原理、主要特征、适用条件等多个关键维度，每个维度都需要逐一理解清楚。",
                    f"【应用场景】：理论知识最终要服务于实际问题解决，这里列举典型的应用场景和案例来建立理论与实践的桥梁。",
                    f"【注意事项】：在使用过程中需要注意的关键点和常见误区，提前了解可以帮助少走弯路、提升效率。",
                ]

            notes_map = {
                "comparison": f"本页对比「{current_title}」的不同侧面，建议逐项讲解后给出总结性选择建议。",
                "timeline": f"本页以流程形式介绍「{current_title}」，按顺序推进，每阶段说明目标和产出。",
                "chart": f"本页展示「{current_title}」的相关数据，先说明口径再解读趋势，最后提炼洞察。",
                "quote": f"本页聚焦「{current_title}」的核心观点，停顿让听众阅读后逐句解读深层含义。",
                "cards_grid": f"本页用卡片网格呈现「{current_title}」的多个并列要点，均匀分配讲解时长。",
                "two_column": f"本页双栏展示「{current_title}」的两个侧面，先讲完一侧再切换或对照着讲。",
            }
            speaker_notes = notes_map.get(layout,
                f"本页讲解「{current_title}」，建议由浅入深：概念→细节→案例→注意事项，可设互动提问。")

            slides.append({
                "page": page_num, "layout": layout, "title": current_title, "subtitle": "",
                "bullet_points": bullets, "speaker_notes": speaker_notes,
                "visual_suggestion": random.choice(visual_db.get(layout, visual_db["content"])),
            })
            page_num += 1

        # ═══ 最后1页：总结 ═══
        if page_num <= target_pages:
            slides.append({
                "page": page_num, "layout": "summary", "title": "总结与展望", "subtitle": "",
                "bullet_points": [
                    f"【核心回顾】：本次分享围绕「{topic}」系统性地介绍了相关知识体系，涵盖了理论基础、核心概念、关键技术以及实践方法等多个维度。",
                    f"【学以致用】：建议大家将今天所学的内容与自身实际工作或学习场景相结合，通过动手实践来巩固理解，真正做到内化于心、外化于行。",
                    f"【持续成长】：本次分享只是一个起点，后续的成长还需要依靠持续的积累和实践。推荐通过扩展阅读、项目实战、社区交流等方式不断深化理解。",
                ],
                "speaker_notes": "总结时快速回顾各部分核心要点，强调知行合一的重要性，给出后续学习资源和建议，预留时间答疑互动。",
                "visual_suggestion": random.choice(visual_db["summary"]),
            })

        return {"total_pages": len(slides), "topic": topic, "slides": slides}

    @staticmethod
    def _collect_node_names(node: Dict, result: List[str], max_depth: int = 3, max_count: int = 15) -> None:
        """递归收集节点名称用于 fallback"""
        if len(result) >= max_count or max_depth <= 0:
            return
        name = node.get("name", "")
        if name and name != "根节点" and len(name) <= 60:
            result.append(name)
        for child in node.get("children", []):
            MindmapExtractor._collect_node_names(child, result, max_depth - 1, max_count)
            if len(result) >= max_count:
                break


# 全局单例
_extractor_instance = None


def get_mindmap_extractor(llm_service=None) -> MindmapExtractor:
    """获取导图提取器单例（每次调用时更新 llm_service，确保使用最新的 LLM 实例）"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = MindmapExtractor(llm_service)
    elif llm_service is not None:
        # 更新 llm_service（防止单例创建时 llm_service 为 None 的情况）
        _extractor_instance.llm_service = llm_service
    return _extractor_instance
