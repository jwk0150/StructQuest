"""
PPT 智能生成器 API 路由
========================

提供两个核心接口：

1. POST /api/ppt/parse-mindmap   — 第一阶段：解析思维导图 → 生成大纲JSON
2. POST /api/ppt/render          — 第三阶段：渲染最终PPT（HTML或PPTX）

额外接口：
3. GET  /api/ppt/templates       — 获取可用模板列表

三阶段流程：
  用户输入 → [parse-mindmap] → 大纲JSON → 用户编辑 → [render] → 文件输出
"""

import logging
import time
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("ppt_generator_api")

router = APIRouter(prefix="/api/ppt", tags=["PPT Generator"])


# ══════════════════════════════════
#   请求/响应模型
# ══════════════════════════════════

class MindmapParseRequest(BaseModel):
    """第一阶段请求：解析思维导图"""
    source: str = Field(
        ..., 
        description="输入源类型: mindmap | markmap | markdown | raw_text | existing",
        examples=["mindmap"]
    )
    content: str = Field(
        default="",
        description="原始内容（当source不为existing时必填）"
    )
    existing_mindmap: Optional[str] = Field(
        None,
        description="已有的思维导图JSON数据（source=existing时使用）"
    )
    target_pages: int = Field(
        default=10, ge=3, le=30,
        description="目标PPT页数（含封面和结尾，范围3-30）"
    )


class RenderRequest(BaseModel):
    """第三阶段请求：渲染最终PPT"""
    outline: Dict[str, Any] = Field(
        ...,
        description="用户修改后的最终大纲JSON"
    )
    format: str = Field(
        default="html",
        description="输出格式: html | pptx"
    )
    template: str = Field(
        default="academic",
        description="模板名称: academic | minimal | presentation"
    )


class TemplateResponse(BaseModel):
    """模板列表响应"""
    success: bool = True
    templates: List[Dict[str, Any]] = []


class OutlineResponse(BaseModel):
    """大纲生成响应"""
    success: bool
    outline: Optional[Dict[str, Any]] = None
    message: str = ""
    error: str = ""


class RenderResponse(BaseModel):
    """渲染结果响应"""
    success: bool
    file_url: Optional[str] = None
    file_path: Optional[str] = None
    download_name: Optional[str] = None
    render_time: float = 0.0
    format: str = ""
    error: str = ""


# ══════════════════════════════════
#   接口实现
# ══════════════════════════════════

@router.get("/templates", response_model=TemplateResponse)
async def get_templates():
    """
    获取所有可用的PPT模板
    
    返回模板列表，包含名称、描述、预览颜色等信息
    """
    from app.services.slide_templates import get_template_factory
    
    factory = get_template_factory()
    template_list = factory.get_template_list()
    
    return TemplateResponse(
        success=True,
        templates=template_list
    )


@router.post("/parse-mindmap", response_model=OutlineResponse)
async def parse_mindmap(req: MindmapParseRequest):
    """
    第一阶段：解析思维导图并生成PPT大纲
    
    流程：
      1. 根据source类型解析输入数据
      2. 将思维导图压缩为轻量文本（减少Token消耗）
      3. 调用AI（或规则引擎）生成结构化大纲JSON
    
    输入示例:
    - source="existing" + existing_mindmap="{...}" → 使用已有思维导图
    - source="markdown" + content="# 标题\\n## 子标题..." → 解析Markdown
    - source="mindmap" + content='{"name":"根","children":[...]}' → 解析JSON
    
    返回标准大纲JSON，供前端编辑器展示和修改
    """
    start_time = time.time()

    try:
        # 导入LLM服务（用于AI生成大纲）
        from app.services.llm import llm_service
        from app.services.mindmap_extractor import get_mindmap_extractor

        # 记录输入信息
        content_len = len(req.content) if req.content else 0
        mindmap_len = len(req.existing_mindmap) if req.existing_mindmap else 0
        logger.info(
            f"PPT大纲请求: source={req.source}, content_len={content_len}, "
            f"mindmap_len={mindmap_len}, target_pages={req.target_pages}"
        )

        # 创建提取器实例（注入LLM服务）
        extractor = get_mindmap_extractor(llm_service)

        # 执行提取
        outline = await extractor.extract(
            source_type=req.source,
            content=req.content,
            target_pages=req.target_pages,
            existing_mindmap=req.existing_mindmap,
        )

        elapsed = round(time.time() - start_time, 2)
        # 统计 layout 分布
        layouts = {}
        for s in outline.get("slides", []):
            l = s.get("layout", "unknown")
            layouts[l] = layouts.get(l, 0) + 1
        logger.info(
            f"PPT大纲完成 ({elapsed}s): {outline.get('total_pages')}页, "
            f"layout分布={layouts}"
        )

        return OutlineResponse(
            success=True,
            outline=outline,
            message=f"成功生成 {outline.get('total_pages', 0)} 页大纲（耗时 {elapsed}s）"
        )
        
    except ValueError as e:
        logger.warning(f"参数验证失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"思维导图解析异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")


@router.post("/render", response_model=RenderResponse)
async def render_ppt(req: RenderRequest):
    """
    第三阶段：渲染最终PPT文件
    
    接收用户修改后的最终大纲JSON，
    根据选择的格式（html/pptx）和模板进行渲染。
    
    格式说明：
    - html: 生成单文件静态HTML（浏览器直接打开可播放，支持键盘导航/打印PDF）
    - pptx: 生成PowerPoint文件（.pptx，可下载后用PowerPoint/WPS编辑）
    
    模板说明：
    - academic: 学术版（深蓝主色调，适合论文答辩）
    - minimal: 极简版（黑白灰，适合商务简报）
    - presentation: 演示版（渐变色+卡片，适合产品发布）
    """
    start_time = time.time()
    
    try:
        # 验证参数
        if req.format not in ("html", "pptx"):
            raise HTTPException(status_code=400, detail=f"不支持的格式: {req.format}")
        
        if req.template not in ("academic", "minimal", "presentation"):
            raise HTTPException(status_code=400, detail=f"不支持的模板: {req.template}")
        
        if not req.outline or "slides" not in req.outline:
            raise HTTPException(status_code=400, detail="大纲数据无效，缺少slides字段")
        
        topic = req.outline.get("topic", "演示文稿")
        
        if req.format == "html":
            # ── HTML 渲染路径 ──
            from app.services.html_renderer import get_html_renderer
            
            renderer = get_html_renderer()
            result = renderer.render(
                outline=req.outline,
                template_name=req.template,
            )
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result.get("error", "HTML渲染失败"))
            
            elapsed = round(time.time() - start_time, 2)
            
            return RenderResponse(
                success=True,
                file_url=result["file_url"],
                file_path=result["file_path"],
                download_name=f"{topic}.html",
                render_time=result["render_time"],
                format="html",
            )
        
        elif req.format == "pptx":
            # ── PPTX 渲染路径 ──
            from app.services.pptx_generator import get_pptx_generator
            
            generator = get_pptx_generator()
            
            # 将大纲转换为Markdown（复用现有逻辑）
            md_content = _outline_to_markdown(req.outline)
            
            result = generator.generate(
                outline_content=md_content,
                topic=topic,
            )
            
            if not result["success"]:
                error_msg = result.get("error", "PPTX生成失败")
                if "未安装" in error_msg or "python-pptx" in error_msg:
                    # 明确返回错误信息给前端，不再静默降级
                    logger.error(f"PPTX生成不可用: {error_msg}")
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            f"PPTX功能暂不可用（{error_msg}）。"
                            f"请安装依赖: pip install python-pptx，或选择HTML格式导出。"
                        ),
                    )

                raise HTTPException(status_code=500, detail=error_msg)
            
            elapsed = round(time.time() - start_time, 2)
            
            return RenderResponse(
                success=True,
                file_url=result["file_url"],
                file_path=result["file_path"],
                download_name=result.get("download_name", f"{topic}.pptx"),
                render_time=elapsed,
                format="pptx",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PPT渲染异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")


# ══════════════════════════════════
#   工具函数
# ══════════════════════════════════

def _outline_to_markdown(outline: Dict[str, Any]) -> str:
    """
    将标准大纲JSON转换为Markdown文本
    
    这是给现有的pptx_generator.py使用的中间格式。
    pptx_generator原本接受Markdown输入来构建幻灯片。
    """
    lines = []
    
    for slide in outline.get("slides", []):
        layout = slide.get("layout", "content")
        title = slide.get("title", "")
        bullets = slide.get("bullet_points", [])
        
        if layout == "title":
            lines.append(f"# {title}")
            subtitle = slide.get("subtitle", "")
            if subtitle:
                lines.append(f"*{subtitle}*")
            lines.append("")
        
        elif layout == "section":
            lines.append(f"\n# {title}\n")
        
        else:
            lines.append(f"## {title}")
            for bullet in bullets:
                lines.append(f"- {bullet}")
            lines.append("")
    
    return "\n".join(lines)
