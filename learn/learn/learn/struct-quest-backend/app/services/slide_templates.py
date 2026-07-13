"""
PPT 模板工厂 (Template Factory)
==============================

存储三套预设模板的配置：
- 学术版 (academic): 深蓝/白/灰配色，适合论文答辩、课程汇报
- 极简版 (minimal): 黑/白/细线框，适合商务简报、快速演示  
- 演示版 (presentation): 渐变蓝紫/卡片式，适合产品发布、创意展示

每套模板包含：
  colors: 完整配色方案
  fonts: 字体配置
  layout: 布局参数
  css_template: HTML渲染用的CSS变量
  pptx_theme: PPTX渲染用的主题配置
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TemplateConfig:
    """单个模板配置"""
    name: str                           # 模板名称（英文ID）
    display_name: str                   # 显示名称（中文）
    description: str                    # 描述文字
    colors: Dict[str, str]              # 颜色映射
    fonts: Dict[str, Any]               # 字体配置
    layout: Dict[str, Any]              # 布局参数
    css_variables: Dict[str, str]       # CSS变量（用于HTML渲染）
    pptx_theme: Dict[str, Any]          # PPTX主题配置


# ══════════════════════════════════════
#   模板定义
# ══════════════════════════════════════

# ── 学术版 (Academic) ──
ACADEMIC_TEMPLATE = TemplateConfig(
    name="academic",
    display_name="学术版",
    description="简约专业风格，深蓝主色调\n适合：论文答辩、课程汇报、学术交流",
    colors={
        "primary": "#1a237e",           # 深靛蓝（主色）
        "primary_light": "#3949ab",     # 浅靛蓝
        "primary_dark": "#0d1642",      # 深靛蓝
        "secondary": "#0d47a1",         # 蓝色辅助
        "accent": "#00897b",            # 青绿强调色
        "background": "#ffffff",        # 白色背景
        "surface": "#f5f5f5",           # 浅灰表面
        "surface_dark": "#e0e0e0",      # 深灰表面
        "text_primary": "#212121",      # 主文本
        "text_secondary": "#616161",    # 次要文本
        "text_light": "#9e9e9e",        # 浅色文本
        "border": "#bdbdbd",            # 边框色
        "success": "#2e7d32",           # 成功绿
        "warning": "#f57c00",           # 警告橙
        "error": "#c62828",             # 错误红
        "title_bg": "#1a237e",          # 标题栏背景
        "footer_bg": "#eceff1",         # 页脚背景
        "card_bg": "#ffffff",           # 卡片背景
        "code_bg": "#263238",           # 代码块背景
        "highlight": "#e8eaf6",         # 高亮背景
    },
    fonts={
        "title": "'Noto Serif SC', 'SimSun', 'Microsoft YaHei', serif",
        "heading": "'Noto Sans SC', 'Microsoft YaHei', sans-serif",
        "body": "'Noto Sans SC', 'Microsoft YaHei', sans-serif",
        "code": "'Fira Code', 'Consolas', 'Courier New', monospace",
        "title_size": "42px",
        "heading_size": "28px",
        "subheading_size": "22px",
        "body_size": "18px",
        "small_size": "14px",
        "code_size": "14px",
    },
    layout={
        "max_width": "1200px",
        "padding": "60px",
        "border_radius": "4px",
        "shadow": "0 4px 20px rgba(0,0,0,0.08)",
        "transition": "all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    },
    css_variables={
        "--primary": "#1a237e",
        "--primary-light": "#3949ab",
        "--primary-dark": "#0d1642",
        "--secondary": "#0d47a1",
        "--accent": "#00897b",
        "--bg": "#ffffff",
        "--surface": "#f5f5f5",
        "--surface-dark": "#e0e0e0",
        "--text-primary": "#212121",
        "--text-secondary": "#616161",
        "--text-light": "#9e9e9e",
        "--border": "#bdbdbd",
        "--title-bg": "#1a237e",
        "--footer-bg": "#eceff1",
        "--card-bg": "#ffffff",
        "--code-bg": "#263238",
        "--code-text": "#aed581",
        "--highlight": "#e8eaf6",
        "--shadow": "0 4px 20px rgba(0,0,0,0.08)",
        "--radius": "4px",
        "--font-title": "'Noto Serif SC', 'SimSun', serif",
        "--font-body": "'Noto Sans SC', 'Microsoft YaHei', sans-serif",
        "--font-code": "'Fira Code', 'Consolas', monospace",
    },
    pptx_theme={
        "title_font": "SimSun",
        "body_font": "Microsoft YaHei",
        "code_font": "Consolas",
        "title_size": 44,
        "heading1_size": 32,
        "heading2_size": 24,
        "body_size": 18,
        "small_size": 14,
        "brand_color": "1a237e",
        "accent_color": "0d47a1",
        "text_color": "212121",
        "text_secondary": "616161",
        "bg_color": "FFFFFF",
        "surface_color": "F5F5F5",
        "circle_colors": [
            ("3949ab", "283593"),
            ("0d47a1", "1565c0"),
            ("00897b", "00695c"),
            ("f57c00", "e65100"),
            ("c62828", "b71c1c"),
            ("6a1b9a", "4a148c"),
        ],
        "header_style": "solid_bar",
        "card_style": "minimal_shadow",
        "bullet_style": "numbered_circle",
    }
)

# ── 极简版 (Minimal) ──
MINIMAL_TEMPLATE = TemplateConfig(
    name="minimal",
    display_name="极简版",
    description="黑白灰极简风格，线条清晰\n适合：商务简报、快速演示、内部会议",
    colors={
        "primary": "#212121",           # 黑色（主色）
        "primary_light": "#424242",     # 深灰
        "primary_dark": "#000000",      # 纯黑
        "secondary": "#616161",         # 灰色辅助
        "accent": "#757575",            # 中灰强调色
        "background": "#ffffff",        # 白色背景
        "surface": "#fafafa",           # 极浅灰表面
        "surface_dark": "#e0e0e0",      # 浅灰表面
        "text_primary": "#212121",      # 黑色主文本
        "text_secondary": "#616161",    # 灰色次要文本
        "text_light": "#9e9e9e",        # 浅灰色文本
        "border": "#e0e0e0",            # 细线边框
        "success": "#2e7d32",           # 成功绿
        "warning": "#e65100",           # 警告橙
        "error": "#c62828",             # 错误红
        "title_bg": "#212121",          # 黑色标题栏
        "footer_bg": "#fafafa",         # 极浅灰页脚
        "card_bg": "#ffffff",           # 白色卡片
        "code_bg": "#212121",           # 深黑代码块
        "highlight": "#f5f5f5",         # 极浅高亮
    },
    fonts={
        "title": "'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        "heading": "'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        "body": "'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif",
        "code": "'SF Mono', 'Consolas', 'Monaco', monospace",
        "title_size": "48px",
        "heading_size": "30px",
        "subheading_size": "24px",
        "body_size": "18px",
        "small_size": "14px",
        "code_size": "13px",
    },
    layout={
        "max_width": "1000px",
        "padding": "80px",
        "border_radius": "0px",
        "shadow": "none",
        "transition": "all 0.3s ease",
    },
    css_variables={
        "--primary": "#212121",
        "--primary-light": "#424242",
        "--primary-dark": "#000000",
        "--secondary": "#616161",
        "--accent": "#757575",
        "--bg": "#ffffff",
        "--surface": "#fafafa",
        "--surface-dark": "#e0e0e0",
        "--text-primary": "#212121",
        "--text-secondary": "#616161",
        "--text-light": "#9e9e9e",
        "--border": "#e0e0e0",
        "--title-bg": "#212121",
        "--footer-bg": "#fafafa",
        "--card-bg": "#ffffff",
        "--code-bg": "#212121",
        "--code-text": "#a5d6a7",
        "--highlight": "#f5f5f5",
        "--shadow": "none",
        "--radius": "0px",
        "--font-title": "'Helvetica Neue', 'PingFang SC', sans-serif",
        "--font-body": "'Helvetica Neue', 'PingFang SC', sans-serif",
        "--font-code": "'SF Mono', 'Consolas', monospace",
    },
    pptx_theme={
        "title_font": "Microsoft YaHei",
        "body_font": "Microsoft YaHei",
        "code_font": "Consolas",
        "title_size": 48,
        "heading1_size": 30,
        "heading2_size": 24,
        "body_size": 17,
        "small_size": 13,
        "brand_color": "212121",
        "accent_color": "616161",
        "text_color": "212121",
        "text_secondary": "616161",
        "bg_color": "FFFFFF",
        "surface_color": "FAFAFA",
        "circle_colors": [
            ("424242", "212121"),
            ("616161", "424242"),
            ("757575", "616161"),
            ("9e9e9e", "757575"),
            ("bdbdbd", "9e9e9e"),
            ("e0e0e0", "bdbdbd"),
        ],
        "header_style": "thin_line",
        "card_style": "line_border",
        "bullet_style": "dash_line",
    }
)

# ── 演示版 (Presentation) ──
PRESENTATION_TEMPLATE = TemplateConfig(
    name="presentation",
    display_name="演示版",
    description="渐变色彩+现代卡片风格\n适合：产品发布、创意展示、公开演讲",
    colors={
        "primary": "#667eea",           # 渐变起点（蓝紫）
        "primary_light": "#764ba2",     # 渐变终点（紫）
        "primary_dark": "#4c51bf",      # 深蓝紫
        "secondary": "#f093fb",         # 粉紫辅助
        "accent": "#f5576c",            # 珊瑚强调色
        "background": "#fafbff",        # 极淡蓝白背景
        "surface": "#ffffff",           # 白色表面
        "surface_dark": "#f0ebf8",      # 淡紫表面
        "text_primary": "#2d3748",      # 深灰主文本
        "text_secondary": "#718096",    # 灰色次要文本
        "text_light": "#a0aec0",        # 浅色文本
        "border": "#e2e8f0",            # 边框色
        "success": "#38a169",           # 成功绿
        "warning": "#dd6b20",           # 警告橙
        "error": "#e53e3e",             # 错误红
        "title_bg_start": "#667eea",    # 标题栏渐变起
        "title_bg_end": "#764ba2",      # 标题栏渐变终
        "footer_bg": "#f7fafc",         # 页脚背景
        "card_bg": "#ffffff",           # 卡片背景
        "code_bg": "#1a202c",           # 暗色代码块
        "highlight": "#ebf4ff",         # 蓝色高亮
    },
    fonts={
        "title": "'Poppins', 'Noto Sans SC', 'Microsoft YaHei', sans-serif",
        "heading": "'Poppins', 'Noto Sans SC', 'Microsoft YaHei', sans-serif",
        "body": "'Inter', 'Noto Sans SC', 'Microsoft YaHei', sans-serif",
        "code": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
        "title_size": "52px",
        "heading_size": "32px",
        "subheading_size": "24px",
        "body_size": "19px",
        "small_size": "15px",
        "code_size": "14px",
    },
    layout={
        "max_width": "1100px",
        "padding": "50px",
        "border_radius": "12px",
        "shadow": "0 10px 40px rgba(102,126,234,0.15)",
        "transition": "all 0.5s cubic-bezier(0.4, 0, 0.2, 1)",
    },
    css_variables={
        "--primary": "#667eea",
        "--primary-light": "#764ba2",
        "--primary-dark": "#4c51bf",
        "--secondary": "#f093fb",
        "--accent": "#f5576c",
        "--bg": "#fafbff",
        "--surface": "#ffffff",
        "--surface-dark": "#f0ebf8",
        "--text-primary": "#2d3748",
        "--text-secondary": "#718096",
        "--text-light": "#a0aec0",
        "--border": "#e2e8f0",
        "--title-bg-start": "#667eea",
        "--title-bg-end": "#764ba2",
        "--footer-bg": "#f7fafc",
        "--card-bg": "#ffffff",
        "--code-bg": "#1a202c",
        "--code-text": "#68d391",
        "--highlight": "#ebf4ff",
        "--shadow": "0 10px 40px rgba(102,126,234,0.15)",
        "--radius": "12px",
        "--font-title": "'Poppins', 'Noto Sans SC', sans-serif",
        "--font-body": "'Inter', 'Noto Sans SC', sans-serif",
        "--font-code": "'JetBrains Mono', 'Fira Code', monospace",
    },
    pptx_theme={
        "title_font": "Microsoft YaHei",
        "body_font": "Microsoft YaHei",
        "code_font": "Consolas",
        "title_size": 50,
        "heading1_size": 34,
        "heading2_size": 26,
        "body_size": 19,
        "small_size": 15,
        "brand_color": "667eea",
        "accent_color": "764ba2",
        "text_color": "2d3748",
        "text_secondary": "718096",
        "bg_color": "FFFFFF",
        "surface_color": "FAFBFF",
        "circle_colors": [
            ("667eea", "5a67d8"),
            ("764ba2", "805ad5"),
            ("f093fb", "#d53f8c"),
            ("f5576c", "#ed8936"),
            ("38a169", "#3182ce"),
            ("ecc94b", "#d69e2e"),
        ],
        "header_style": "gradient_bar",
        "card_style": "rounded_shadow",
        "bullet_style": "icon_dot",
    }
)


# ══════════════════════════════════════
#   模板注册表
# ══════════════════════════════════════

TEMPLATE_REGISTRY: Dict[str, TemplateConfig] = {
    "academic": ACADEMIC_TEMPLATE,
    "minimal": MINIMAL_TEMPLATE,
    "presentation": PRESENTATION_TEMPLATE,
}


# ══════════════════════════════════════
#   工厂方法
# ══════════════════════════════════════

class TemplateFactory:
    """
    模板工厂 — 提供统一的模板访问接口
    
    使用方式:
        factory = TemplateFactory()
        template = factory.get_template("academic")
        css_vars = template.css_variables
    """
    
    def __init__(self):
        self._registry = TEMPLATE_REGISTRY
    
    def get_template(self, template_name: str) -> TemplateConfig:
        """获取指定模板"""
        if template_name not in self._registry:
            available = list(self._registry.keys())
            raise ValueError(
                f"未知模板 '{template_name}'，可用模板: {available}"
            )
        return self._registry[template_name]
    
    def get_all_templates(self) -> Dict[str, TemplateConfig]:
        """获取所有模板"""
        return dict(self._registry)
    
    def get_template_list(self) -> list:
        """获取模板列表（用于前端选择器）"""
        return [
            {
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "preview_colors": {
                    "primary": t.colors.get("primary", ""),
                    "accent": t.colors.get("accent", ""),
                    "background": t.colors.get("background", ""),
                    "surface": t.colors.get("surface", ""),
                }
            }
            for t in self._registry.values()
        ]
    
    def get_css_root_variables(self, template_name: str) -> str:
        """生成 CSS :root 变量声明"""
        tpl = self.get_template(template_name)
        lines = [":root {"]
        for var_name, value in tpl.css_variables.items():
            lines.append(f"  {var_name}: {value};")
        lines.append("}")
        return "\n".join(lines)
    
    def get_pptx_theme(self, template_name: str) -> Dict[str, Any]:
        """获取PPTX主题配置"""
        tpl = self.get_template(template_name)
        return dict(tpl.pptx_theme)


# 全局工厂实例
_factory_instance = None


def get_template_factory() -> TemplateFactory:
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = TemplateFactory()
    return _factory_instance
