"""
HTML 渲染引擎 (HTML Renderer)
=============================

功能：
1. 接收标准大纲JSON + 模板配置
2. 生成单文件静态HTML（浏览器直接打开可播放）
3. 支持响应式布局、动画过渡、代码高亮

特性：
- 单文件：所有CSS/JS内联，无需外部依赖（除了可选的CDN）
- 响应式：自适应不同屏幕尺寸
- 动画：页面切换平滑过渡
- 交互：键盘导航（方向键/空格）、点击切换页码
- 打印：支持直接打印/PDF导出
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("html_renderer")

# 输出目录
def _get_output_dir() -> Path:
    import os as _os3
    static_base = _os3.environ.get("STATIC_DIR", "/app/static")
    ppt_dir = _os3.environ.get("PPT_HTML_OUTPUT_DIR", _os3.path.join(static_base, "ppt"))
    dir_path = Path(ppt_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


class HTMLRenderer:
    """
    HTML渲染引擎 — 将PPT大纲渲染为可播放的单文件HTML
    
    使用方式:
        renderer = HTMLRenderer()
        result = renderer.render(outline, template_name="academic")
        # result.file_url → 前端访问路径
    """
    
    def render(
        self,
        outline: Dict[str, Any],
        template_name: str = "academic",
        template_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        渲染HTML
        
        Args:
            outline: 标准大纲JSON（来自MindmapExtractor输出）
            template_name: 模板名称 (academic/minimal/presentation)
            template_config: 可选的自定义模板配置覆盖
        
        Returns:
            {
                "success": bool,
                "file_url": str,
                "file_path": str,
                "render_time": float,
                "error": str | None
            }
        """
        import time
        start_time = time.time()
        
        result = {
            "success": False,
            "file_url": None,
            "file_path": None,
            "render_time": 0,
            "error": None,
        }
        
        try:
            # 获取模板配置
            from .slide_templates import get_template_factory
            factory = get_template_factory()
            
            if template_config:
                # 使用自定义配置
                tpl = template_config
            else:
                tpl_obj = factory.get_template(template_name)
                tpl = {
                    "css_variables": tpl_obj.css_variables,
                    "fonts": tpl_obj.fonts,
                    "layout": tpl_obj.layout,
                    "colors": tpl_obj.colors,
                }
            
            # 生成HTML内容
            html_content = self._generate_html(
                outline=outline,
                template=tpl,
                template_name=template_name
            )
            
            # 写入文件
            output_dir = _get_output_dir()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            safe_topic = re.sub(r'[^\w\-]', '_', outline.get("topic", "ppt"))[:30]
            filename = f"{safe_topic}_{timestamp}.html"
            filepath = output_dir / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            elapsed = time.time() - start_time
            
            result["success"] = True
            result["file_path"] = str(filepath)
            result["file_url"] = f"/static/ppt/{filename}"
            result["render_time"] = round(elapsed, 2)
            
            logger.info(f"HTML渲染成功: {filename} ({elapsed:.2f}s)")
            
        except Exception as e:
            result["error"] = f"HTML渲染异常: {str(e)}"
            logger.error(f"HTML渲染失败: {e}", exc_info=True)
        
        return result
    
    def _generate_html(
        self,
        outline: Dict[str, Any],
        template: Dict[str, Any],
        template_name: str,
    ) -> str:
        """生成完整HTML文档"""
        
        css_vars = template.get("css_variables", {})
        fonts = template.get("fonts", {})
        layout = template.get("layout", {})
        colors = template.get("colors", {})
        
        slides = outline.get("slides", [])
        topic = outline.get("topic", "演示文稿")
        
        # 构建幻灯片HTML
        slides_html = self._build_slides_html(slides, colors)
        
        # 构建导航点
        nav_dots = self._build_nav_dots(slides)
        
        # 完整HTML文档
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape_html(topic)} - StructQuest PPT</title>
{self._get_css_block(css_vars, fonts, layout, colors, template_name)}
</head>
<body>
<!-- 进度条 -->
<div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>

<!-- 幻灯片容器 -->
<div class="slide-container" id="slideContainer">
{slides_html}
</div>

<!-- 导航控制 -->
<button class="nav-btn nav-prev" id="prevBtn" title="上一页 (←)">‹</button>
<button class="nav-btn nav-next" id="nextBtn" title="下一页 (→/Space)">›</button>

<!-- 页码显示 -->
<div class="page-indicator">
    <span id="currentPage">1</span> / <span id="totalPages">{len(slides)}</span>
</div>

<!-- 导航点 -->
<div class="nav-dots">{nav_dots}</div>

<!-- 工具栏 -->
<div class="toolbar">
    <button onclick="toggleFullscreen()" title="全屏 (F)">⛶ 全屏</button>
    <button onclick="window.print()" title="打印/导出PDF">🖨️ 打印</button>
    <button onclick="toggleOverview()" title="概览 (O)">⊞ 概览</button>
</div>

<!-- 概览模式遮罩 -->
<div class="overview-overlay" id="overviewOverlay" onclick="toggleOverview()">
    <div class="overview-grid" onclick="event.stopPropagation()">
        {self._build_overview_thumbnails(slides, colors)}
    </div>
</div>

{self._get_js_block(len(slides))}
</body>
</html>"""
        
        return html
    
    def _build_slides_html(self, slides: List[Dict], colors: Dict) -> str:
        """构建所有幻灯片的HTML"""
        html_parts = []
        
        for idx, slide in enumerate(slides):
            page_num = slide.get("page", idx + 1)
            layout_type = slide.get("layout", "content")
            title = self._escape_html(slide.get("title", ""))
            subtitle = self._escape_html(slide.get("subtitle", ""))
            bullets = slide.get("bullet_points", [])
            
            # 根据布局类型选择不同模板
            if layout_type == "title":
                slide_html = self._render_title_slide(page_num, title, subtitle)
            elif layout_type == "section":
                slide_html = self._render_section_slide(page_num, title)
            elif layout_type == "summary":
                slide_html = self._render_summary_slide(page_num, title, bullets)
            else:
                slide_html = self._render_content_slide(page_num, title, bullets)
            
            active_class = "active" if idx == 0 else ""
            html_parts.append(f'<div class="slide {layout_type}-slide {active_class}" data-slide="{idx}">\n{slide_html}\n</div>')
        
        return "\n".join(html_parts)
    
    def _render_title_slide(self, page_num: int, title: str, subtitle: str) -> str:
        """渲染封面页"""
        subtitle_html = f'<h2 class="subtitle">{subtitle}</h2>' if subtitle else ''
        
        return f"""<div class="slide-inner title-layout">
    <div class="title-content">
        <h1 class="main-title">{title}</h1>
        {subtitle_html}
        <div class="title-decoration"></div>
        <p class="meta-info">StructQuest AI · 智能生成 · {self._get_current_date()}</p>
    </div>
</div>"""
    
    def _render_section_slide(self, page_num: int, title: str) -> str:
        """渲染章节分隔页"""
        return f"""<div class="slide-inner section-layout">
    <div class="section-content">
        <span class="section-label">CHAPTER</span>
        <h1 class="section-title">{title}</h1>
        <div class="section-line"></div>
    </div>
</div>"""
    
    def _render_content_slide(self, page_num: int, title: str, bullets: List[str]) -> str:
        """渲染内容页"""
        if not bullets:
            bullets_html = '<p class="empty-hint">（详细内容）</p>'
        else:
            items = []
            for i, bullet in enumerate(bullets):
                escaped = self._escape_html(bullet)
                items.append(f'<li class="bullet-item" style="--delay: {i * 0.08}s"><span class="bullet-marker"></span><span>{escaped}</span></li>')
            bullets_html = f'<ul class="bullet-list">\n' + "\n".join(items) + '\n</ul>'
        
        return f"""<div class="slide-inner content-layout">
    <header class="slide-header">
        <h2 class="slide-title">{title}</h2>
    </header>
    <div class="slide-body">
        {bullets_html}
    </div>
</div>"""
    
    def _render_summary_slide(self, page_num: int, title: str, bullets: List[str]) -> str:
        """渲染总结页"""
        cards = []
        for i, bullet in enumerate(bullets[:3]):
            escaped = self._escape_html(bullet)
            icon = ["✓", "★", "→"][i] if i < 3 else "•"
            cards.append(f'''<div class="summary-card" style="--card-index: {i}">
                <div class="summary-icon">{icon}</div>
                <p>{escaped}</p>
            </div>''')
        
        return f"""<div class="slide-inner summary-layout">
    <header class="slide-header">
        <h2 class="slide-title">{title}</h2>
    </header>
    <div class="slide-body">
        <div class="summary-grid">
            {chr(10).join(cards)}
        </div>
    </div>
</div>"""
    
    def _build_nav_dots(self, slides: List[Dict]) -> str:
        """构建导航点"""
        dots = []
        for i in range(len(slides)):
            active = 'class="active"' if i == 0 else ''
            dots.append(f'<span class="nav-dot" {active} data-goto="{i}" title="第{i+1}页"></span>')
        return "\n".join(dots)
    
    def _build_overview_thumbnails(self, slides: List[Dict], colors: Dict) -> str:
        """构建概览模式的缩略图"""
        thumbs = []
        for i, slide in enumerate(slides):
            title = self._escape_html(slide.get("title", f"第{i+1}页"))
            layout = slide.get("layout", "content")
            thumbs.append(f'''
            <div class="overview-thumb" data-goto="{i}" onclick="goToSlide({i})">
                <div class="thumb-preview thumb-{layout}">
                    <span>{title}</span>
                </div>
                <span class="thumb-label">{i+1}. {title[:15]}...</span>
            </div>''')
        return "\n".join(thumbs)
    
    # ══════════════════════════════════
    #   CSS 生成
    # ══════════════════════════════════
    
    def _get_css_block(self, css_vars, fonts, layout, colors, template_name) -> str:
        """生成完整的内联CSS"""
        root_vars = "\n".join([f"  {k}: {v};" for k, v in css_vars.items()])
        
        # 根据模板类型调整特殊样式
        extra_styles = ""
        if template_name == "presentation":
            extra_styles = """
.slide-header {
    background: linear-gradient(135deg, var(--title-bg-start), var(--title-bg-end)) !important;
}
.section-layout {
    background: linear-gradient(135deg, var(--primary), var(--primary-light)) !important;
}"""
        elif template_name == "minimal":
            extra_styles = """
.slide-header {
    border-bottom: 2px solid var(--text-primary) !important;
    background: transparent !important;
}
.slide-header .slide-title { color: var(--text-primary) !important; }"""
        
        return f"""<style>
/* ===== CSS变量（模板驱动）===== */
:root {{
{root_vars}
}}

/* ===== 重置与基础 ===== */
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ 
    width: 100%; height: 100%; overflow: hidden;
    font-family: var(--font-body);
    background: var(--bg); color: var(--text-primary);
}}

/* ===== 幻灯片容器 ===== */
.slide-container {{
    width: 100vw; height: 100vh; position: relative;
    overflow: hidden;
}}
.slide {{
    position: absolute; top: 0; left: 0;
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    opacity: 0; visibility: hidden;
    transform: translateX(60px);
    transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1),
                opacity 0.5s ease, visibility 0.5s;
    padding: {layout['padding']};
}}
.slide.active {{
    opacity: 1; visibility: visible;
    transform: translateX(0);
}}
.slide.prev {{
    transform: translateX(-60px);
}}

/* ===== 封面页 ===== */
.title-layout {{
    text-align: center;
    flex-direction: column;
}}
.main-title {{
    font-family: var(--font-title);
    font-size: {fonts['title_size']}; font-weight: 700;
    color: var(--primary-dark);
    line-height: 1.25;
    max-width: 900px;
    animation: fadeUp 0.8s ease both;
}}
.subtitle {{
    font-size: {fonts['subheading_size']};
    color: var(--text-secondary);
    margin-top: 20px;
    animation: fadeUp 0.8s 0.2s ease both;
}}
.title-decoration {{
    width: 80px; height: 4px;
    background: var(--accent);
    margin: 28px auto;
    border-radius: 2px;
    animation: expandWidth 0.6s 0.4s ease both;
}}
.meta-info {{
    font-size: {fonts['small_size']};
    color: var(--text-light);
    margin-top: 32px;
    letter-spacing: 2px;
}}

/* ===== 章节页 ===== */
.section-layout {{
    text-align: center;
    flex-direction: column;
}}
.section-content {{
    padding: 60px 40px;
}}
.section-label {{
    font-size: 14px; letter-spacing: 8px;
    color: var(--accent); font-weight: 600;
    text-transform: uppercase;
}}
.section-title {{
    font-size: {fonts['title_size']};
    color: white; font-weight: 700;
    margin-top: 16px;
}}
.section-line {{
    width: 60px; height: 3px;
    background: rgba(255,255,255,0.7);
    margin: 24px auto 0; border-radius: 2px;
}}
.section-layout {{
    background: var(--primary);
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    border-radius: var(--radius);
}}

/* ===== 内容页 ===== */
.content-layout {{
    width: 100%; height: 100%;
    display: flex; flex-direction: column;
}}
.slide-header {{
    padding: 24px 36px;
    background: var(--title-bg);
    border-radius: var(--radius) var(--radius) 0 0;
}}
.slide-title {{
    font-size: {fonts['heading_size']};
    font-weight: 700; color: white;
    font-family: var(--font-title);
}}
.slide-body {{
    flex: 1;
    padding: 36px 48px;
    overflow-y: auto;
    background: var(--bg);
    border-radius: 0 0 var(--radius) var(--radius);
    box-shadow: var(--shadow);
}}

/* ===== 要点列表 ===== */
.bullet-list {{
    list-style: none; padding: 0;
    max-width: 950px;
}}
.bullet-item {{
    display: flex; align-items: flex-start;
    gap: 16px; padding: 14px 0;
    opacity: 0; transform: translateY(20px);
    animation: fadeInUp 0.5s calc(var(--delay)) forwards;
}}
.bullet-marker {{
    flex-shrink: 0; width: 10px; height: 10px;
    border-radius: 50%;
    background: var(--primary);
    margin-top: 8px;
}}
.bullet-item span:last-child {{
    font-size: {fonts['body_size']};
    line-height: 1.65;
    color: var(--text-primary);
}}
.empty-hint {{
    color: var(--text-light); font-style: italic;
}}

/* ===== 总结页 ===== */
.summary-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 24px; margin-top: 12px;
}}
.summary-card {{
    padding: 28px 24px;
    background: var(--surface);
    border-radius: var(--radius);
    border-left: 4px solid var(--primary);
    animation: fadeInUp 0.5s calc(var(--card-index) * 0.15s) both;
}}
.summary-icon {{
    font-size: 28px; margin-bottom: 12px;
}}
.summary-card p {{
    font-size: {fonts['body_size']};
    color: var(--text-secondary);
    line-height: 1.6;
}}

/* ===== 导航控件 ===== */
.progress-bar {{
    position: fixed; top: 0; left: 0;
    width: 100%; height: 3px;
    background: var(--surface-dark);
    z-index: 200;
}}
.progress-fill {{
    height: 100%; width: 0%;
    background: var(--primary);
    transition: width 0.3s ease;
}}
.nav-btn {{
    position: fixed; top: 50%; transform: translateY(-50%);
    width: 48px; height: 48px;
    border: none; border-radius: 50%;
    background: rgba(0,0,0,0.06);
    color: var(--text-secondary);
    font-size: 26px; cursor: pointer;
    z-index: 150; transition: all 0.25s;
    display: flex; align-items: center; justify-content: center;
}}
.nav-btn:hover {{
    background: var(--primary); color: white;
}}
.nav-prev {{ left: 20px; }}
.nav-next {{ right: 20px; }}
.page-indicator {{
    position: fixed; bottom: 24px; right: 28px;
    font-size: 13px; color: var(--text-light);
    z-index: 150; font-variant-numeric: tabular-nums;
}}
/* 导航点 */
.nav-dots {{
    position: fixed; bottom: 24px; left: 50%;
    transform: translateX(-50%);
    display: flex; gap: 8px; z-index: 150;
}}
.nav-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--surface-dark);
    cursor: pointer; transition: all 0.25s;
}}
.nav-dot:hover {{ background: var(--primary-light); }}
.nav-dot.active {{
    background: var(--primary); width: 24px; border-radius: 4px;
}}
/* 工具栏 */
.toolbar {{
    position: fixed; top: 16px; right: 20px;
    display: flex; gap: 8px; z-index: 150;
}}
.toolbar button {{
    padding: 6px 14px; border: 1px solid var(--border);
    border-radius: var(--radius);
    background: rgba(255,255,255,0.92);
    font-size: 13px; cursor: pointer;
    transition: all 0.2s;
    backdrop-filter: blur(8px);
}}
.toolbar button:hover {{
    background: var(--primary); color: white;
    border-color: var(--primary);
}}

/* ===== 概览模式 ===== */
.overview-overlay {{
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.85);
    z-index: 300; display: none;
    padding: 40px; overflow-y: auto;
    backdrop-filter: blur(4px);
}}
.overview-overlay.show {{ display: block; }}
.overview-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 20px; max-width: 1200px; margin: 0 auto;
}}
.overview-thumb {{
    cursor: pointer; transition: transform 0.2s;
}}
.overview-thumb:hover {{ transform: scale(1.05); }}
.thumb-preview {{
    aspect-ratio: 16/9; border-radius: var(--radius);
    background: var(--surface);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; color: var(--text-secondary);
    padding: 16px; text-align: center;
    border: 2px solid transparent; transition: border-color 0.2s;
}}
.overview-thumb:hover .thumb-preview {{
    border-color: var(--primary);
}}
.thumb-title {{ background: var(--primary); color: white; }}
.thumb-section {{ background: var(--primary); color: white; }}
.thumb-summary {{ background: var(--surface-dark); }}
.thumb-label {{
    display: block; margin-top: 8px;
    font-size: 12px; color: #ccc; text-align: center;
}}

/* ===== 动画关键帧 ===== */
@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(24px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(18px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes expandWidth {{
    from {{ width: 0; }}
    to {{ width: 80px; }}
}}

/* ===== 响应式 ===== */
@media (max-width: 768px) {{
    .slide {{ padding: 30px 20px; }}
    .main-title {{ font-size: 32px; }}
    .slide-title {{ font-size: 22px; }}
    .slide-body {{ padding: 24px 20px; }}
    .bullet-item span:last-child {{ font-size: 16px; }}
    .summary-grid {{ grid-template-columns: 1fr; }}
    .nav-btn {{ width: 38px; height: 38px; font-size: 20px; }}
    .toolbar {{ top: 8px; right: 10px; }}
}}

/* ===== 打印样式 ===== */
@media print {{
    .nav-btn, .toolbar, .page-indicator, .nav-dots,
    .progress-bar, .overview-overlay {{ display: none !important; }}
    .slide {{ position: relative !important; opacity: 1 !important;
             visibility: visible !important; transform: none !important;
             page-break-after: always; height: auto; min-height: 100vh; }}
    .slide-container {{ overflow: visible; height: auto; }}
}}

/* 模板特有样式 */
{extra_styles}
</style>"""
    
    # ══════════════════════════════════
    #   JavaScript 生成
    # ══════════════════════════════════
    
    @staticmethod
    def _get_js_block(total_slides: int) -> str:
        """生成交互JavaScript"""
        return f"""<script>
(function() {{
var current = 0;
var total = {total_slides};
var slides = document.querySelectorAll('.slide');
var fill = document.getElementById('progressFill');
var currEl = document.getElementById('currentPage');

function showSlide(idx, direction) {{
    if (idx < 0 || idx >= total) return;
    var prevIdx = current;
    slides[prevIdx].classList.remove('active');
    slides[prevIdx].className += direction > 0 ? ' prev' : '';
    
    // Force reflow
    void slides[prevIdx].offsetHeight;
    
    current = idx;
    slides[current].className = slides[current].className.replace(/\\b(prev|active)\\b/g, '');
    slides[current].classList.add('active');
    
    // Update UI
    fill.style.width = ((current + 1) / total * 100) + '%';
    currEl.textContent = current + 1;
    
    // Update nav dots
    document.querySelectorAll('.nav-dot').forEach(function(d, i) {{
        d.classList.toggle('active', i === current);
    }});
}}

function nextSlide() {{ showSlide(current + 1, 1); }}
function prevSlide() {{ showSlide(current - 1, -1); }}
function goToSlide(i) {{ showSlide(i, i > current ? 1 : -1); }}

// Keyboard navigation
document.addEventListener('keydown', function(e) {{
    switch(e.key) {{
        case 'ArrowRight': case ' ': case 'PageDown': e.preventDefault(); nextSlide(); break;
        case 'ArrowLeft': case 'Backspace': case 'PageUp': e.preventDefault(); prevSlide(); break;
        case 'Home': goToSlide(0); break;
        case 'End': goToSlide(total - 1); break;
        case 'f': case 'F': toggleFullscreen(); break;
        case 'o': case 'O': toggleOverview(); break;
    }}
}});

// Button events
document.getElementById('prevBtn').addEventListener('click', prevSlide);
document.getElementById('nextBtn').addEventListener('click', nextSlide);

// Nav dot clicks
document.querySelectorAll('.nav-dot').forEach(function(dot) {{
    dot.addEventListener('click', function() {{
        goToSlide(parseInt(this.dataset.goto));
    }});
}});

// Touch swipe support
var touchStartX = 0;
document.addEventListener('touchstart', function(e) {{ touchStartX = e.touches[0].clientX; }});
document.addEventListener('touchend', function(e) {{
    var diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {{ diff > 0 ? nextSlide() : prevSlide(); }}
}});

// Fullscreen
function toggleFullscreen() {{
    if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen();
    }} else {{ document.exitFullscreen(); }}
}}

// Overview mode
function toggleOverview() {{
    var ov = document.getElementById('overviewOverlay');
    ov.classList.toggle('show');
}}

// Auto-hide nav on mobile
if ('ontouchstart' in window) {{
    var hideTimer;
    document.addEventListener('touchstart', function() {{
        clearTimeout(hideTimer);
        document.querySelector('.nav-btn.nav-prev').style.opacity = 1;
        document.querySelector('.nav-btn.nav-next').style.opacity = 1;
        hideTimer = setTimeout(function() {{
            document.querySelector('.nav-btn.nav-prev').style.opacity = 0.3;
            document.querySelector('.nav-btn.nav-next').style.opacity = 0.3;
        }}, 3000);
    }});
}}
}})();
</script>"""
    
    # ══════════════════════════════════
    #   工具方法
    # ══════════════════════════════════
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """HTML转义"""
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))
    
    @staticmethod
    def _get_current_date() -> str:
        """获取当前日期字符串"""
        return datetime.now().strftime("%Y年%m月%d日")


# 全局实例
_renderer_instance = None


def get_html_renderer() -> HTMLRenderer:
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = HTMLRenderer()
    return _renderer_instance
