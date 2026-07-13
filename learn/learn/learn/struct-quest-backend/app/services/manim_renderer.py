"""
Manim 视频渲染服务
==================

工作流程：
1. LLM 生成 Manim Python 代码
2. 沙箱环境执行代码，渲染 MP4 视频
3. 返回视频路径和源码（支持前端修改后重新渲染）

安全措施：
- 进程超时控制 (默认 120s)
- 输出目录隔离
- 禁止危险操作（文件系统、网络等）
"""

import os
import re
import json
import tempfile
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger("manim_renderer")

# 输出目录（延迟初始化，避免模块加载时在 Windows 上失败）
def _get_output_dir() -> Path:
    """获取输出目录，确保存在"""
    static_base = os.environ.get("STATIC_DIR", "/app/static")
    video_dir = os.environ.get("MANIM_OUTPUT_DIR", os.path.join(static_base, "videos"))
    dir_path = Path(video_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

# Manim 代码安全检查：禁止的危险模式
DANGEROUS_PATTERNS = [
    r"\bimport\s+os\b",
    r"os\.(system|remove|rmdir|rename|exec|popen|spawn)",
    r"\bsubprocess\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bcompile\s*\(",
    r"\b__import__\s*\(",
    r'\bopen\s*\([\'"].*[\'"]\s*.*\bw\b',   # open("...", "w") 写入模式
    r"\bshutil\b",
    r"\bsignal\b",
    r"\bsocket\b",
    r"\brequests?\b",
    r"\burllib",
]

# Manim 代码模板前缀（强制使用安全配置）
MANIM_HEADER = '''from manim import *
import numpy as np

# 安全配置：限制渲染参数
config.media_width = "1920"
config.media_height = "1080"
config.frame_rate = 30
config.background_color = "#1a1a2e"

'''


class ManimRenderer:
    """Manim 视频渲染器"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or _get_output_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 检查 manim 是否可用
        self._manim_available = self._check_manim()

    def _check_manim(self) -> bool:
        """检查 manim 命令是否可用"""
        try:
            result = subprocess.run(
                ["manim", "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info("✅ Manim 可用: %s", result.stdout.strip().split("\n")[0])
                return True
            else:
                logger.warning("⚠️ Manim 命令返回非零: %s", result.stderr[:200])
                return False
        except FileNotFoundError:
            logger.warning("⚠️ Manim 未安装或不在 PATH 中")
            return False
        except Exception as e:
            logger.warning("⚠️ Manim 检查异常: %s", e)
            return False

    @property
    def available(self) -> bool:
        """是否可用"""
        return self._manim_available

    def validate_code(self, code: str) -> Tuple[bool, str]:
        """
        验证 Manim 代码安全性

        Returns:
            (is_valid, error_message)
        """
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"代码包含不安全的操作: {pattern}"

        # 必须包含 Scene 类
        if "class" not in code or "Scene" not in code:
            return False, "代码必须定义一个继承自 Scene 的类"

        # 必须有 construct 方法
        if "def construct" not in code:
            return False, "代码必须实现 construct 方法"

        return True, ""

    def render(
        self,
        code: str,
        scene_name: str = "AlgorithmScene",
        timeout: int = 120,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        渲染 Manim 代码为 MP4 视频

        Args:
            code: Manim Python 代码
            scene_name: Scene 类名
            timeout: 渲染超时(秒)
            task_id: 任务ID（用于文件命名）

        Returns:
            {
                "success": bool,
                "video_url": str or None,      # 视频访问URL
                "video_path": str or None,     # 视频文件本地路径
                "source_code": str,            # 完整源码
                "scene_name": str,
                "render_time": float,          # 渲染耗时(秒)
                "error": str or None,
                "logs": str,                   # 渲染日志
                "thumbnail_url": str or None,   # 缩略图
            }
        """
        task_id = task_id or datetime.now().strftime("%Y%m%d%H%M%S%f")
        result = {
            "success": False,
            "video_url": None,
            "video_path": None,
            "source_code": code,
            "scene_name": scene_name,
            "render_time": 0,
            "error": None,
            "logs": "",
            "thumbnail_url": None,
        }

        # 验证代码安全性
        is_valid, error_msg = self.validate_code(code)
        if not is_valid:
            result["error"] = error_msg
            logger.error("❌ Manim 代码验证失败: %s", error_msg)
            return result

        # 创建临时工作目录
        work_dir = tempfile.mkdtemp(prefix=f"manim_{task_id}_")
        script_path = os.path.join(work_dir, "animation.py")

        try:
            # 写入完整脚本（智能拼接）
            code_stripped = code.strip()

            # 始终在 import 之后注入安全配置（Manim 0.20+ 要求字符串类型）
            config_patch = '''
# === 安全配置注入 ===
config.media_width = "1920"
config.media_height = "1080"
config.frame_rate = 30
config.background_color = "#1a1a2e"
'''

            if "from manim import" in code_stripped or "import manim" in code_stripped:
                # 代码已有 import，在第一个 import manim 行后注入配置
                lines = code_stripped.split('\n')
                out_lines = []
                injected = False
                for line in lines:
                    out_lines.append(line)
                    if not injected and ('import manim' in line or 'from manim import' in line):
                        out_lines.append(config_patch)
                        injected = True
                full_code = '\n'.join(out_lines)
                logger.info("🎬 用户代码包含 manim import，在导入后注入安全配置")
            else:
                # 补充完整 header
                full_code = MANIM_HEADER + "\n" + code_stripped
                logger.info("🎬 补充完整 MANIM_HEADER")

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(full_code)

            logger.info("🎬 最终脚本前200字符: %s", full_code[:200])

            logger.info("🎬 开始渲染 Manim 动画 [task=%s, scene=%s]", task_id, scene_name)
            start_time = datetime.now()

            # 执行 manim 渲染
            cmd = [
                "manim",
                "-ql",           # 低质量预览（更快）
                "--media_dir", str(self.output_dir / task_id),
                "--disable_caching",
                script_path,
                scene_name,
            ]

            logger.info("🎬 执行渲染命令: %s", " ".join(cmd))

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir,
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            result["render_time"] = round(elapsed, 2)

            # 完整记录日志（不再截断，方便排查问题）
            result["logs"] = proc.stdout[-5000:] if proc.stdout else ""
            if proc.stderr:
                result["logs"] += "\n--- STDERR (full) ---\n" + proc.stderr[-5000:]

            logger.info("🎬 Manim 进程退出码: %d, stdout长度: %d, stderr长度: %d",
                       proc.returncode, len(proc.stdout or ""), len(proc.stderr or ""))

            if proc.returncode == 0:
                # 查找生成的 MP4 文件（多位置搜索，兼容不同 Manim 版本）
                search_dirs = []

                # 位置1: --media_dir 指定的路径（标准位置）
                media_dir = self.output_dir / task_id / "videos"
                if media_dir.exists():
                    search_dirs.append(media_dir)

                # 位置2: --media_dir 根目录（某些版本直接放这里）
                flat_dir = self.output_dir / task_id
                if flat_dir.exists():
                    search_dirs.append(flat_dir)

                # 位置3: 脚本工作目录（manim 可能忽略 --media_dir）
                if os.path.isdir(work_dir):
                    search_dirs.append(Path(work_dir))

                # 位置4: 默认 manim 输出目录 (C:\Users\xxx\media)
                default_media = Path.home() / "media"
                if default_media.exists():
                    search_dirs.append(default_media)

                # 位置5: 项目 static 根目录的 videos 子目录
                static_videos = self.output_dir
                if static_videos.exists():
                    # 也直接搜 output_dir 本身（manim 有时直接放这里）
                    search_dirs.append(static_videos)

                # 去重
                seen = set()
                unique_dirs = []
                for sd in search_dirs:
                    resolved = str(sd.resolve())
                    if resolved not in seen:
                        seen.add(resolved)
                        unique_dirs.append(sd)

                logger.info("🎬 开始搜索 MP4，共 %d 个搜索目录", len(unique_dirs))

                # 在所有位置递归搜索
                video_files = []
                for sd in unique_dirs:
                    if sd.exists():
                        found = list(sd.rglob("*.mp4"))
                        video_files.extend(found)
                        if found:
                            logger.info("🎬 在 %s 找到 %d 个 MP4: %s",
                                       sd, len(found), [f.name for f in found[:5]])
                        else:
                            logger.info("🎬 在 %s 未找到 MP4（目录存在: %s）", sd, sd.exists())
                    else:
                        logger.info("🎬 搜索目录不存在: %s", sd)

                if video_files:
                    # 优先选择非 partial 的完整视频文件
                    full_videos = [f for f in video_files if "partial_movie_files" not in str(f)]
                    if full_videos:
                        # 取最新的完整视频
                        full_videos.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                        video_path = full_videos[0]
                    else:
                        # 只有 partial 文件，取最大的（最可能是完整的）
                        video_files.sort(key=lambda p: p.stat().st_size, reverse=True)
                        video_path = video_files[0]
                        logger.warning("⚠️ 仅找到 partial 文件，使用最大的: %s (%.2fMB)",
                                     video_path.name, video_path.stat().st_size / (1024*1024))

                    # 复制到统一的输出位置
                    final_name = f"{task_id}_{scene_name}.mp4"
                    final_path = self.output_dir / final_name
                    shutil.copy2(video_path, final_path)

                    # 尝试生成缩略图
                    thumb_path = self._generate_thumbnail(final_path, task_id)

                    result["success"] = True
                    result["video_url"] = f"/static/videos/{final_name}"
                    result["video_path"] = str(final_path)
                    result["thumbnail_url"] = f"/static/videos/thumb_{task_id}.png" if thumb_path else None

                    file_size_mb = os.path.getsize(final_path) / (1024 * 1024)
                    logger.info(
                        "✅ Manim 渲染成功! [%.1fs, %.2fMB] %s (源: %s)",
                        elapsed, file_size_mb, final_name, video_path
                    )
                else:
                    # 详细诊断信息
                    searched = [str(s.resolve()) for s in unique_dirs]
                    # 检查 Manim 是否实际渲染了场景（可能在 stderr/stdout 中有线索）
                    stderr_tail = (proc.stderr or "")[-500:]
                    stdout_tail = (proc.stdout or "")[-500:]
                    result["error"] = (
                        f"渲染完成但未找到输出视频。"
                        f"搜索路径({len(searched)}个): {searched}; "
                        f"stdout尾部: {stdout_tail[-200:]}; "
                        f"stderr尾部: {stderr_tail[-200:]}"
                    )
                    logger.warning("⚠️ 未找到MP4文件。搜索路径: %s", searched)
                    logger.warning("⚠️ stdout[-1000:]: %s", stdout_tail)
                    logger.warning("⚠️ stderr[-1000:]: %s", stderr_tail)
            else:
                # 提取关键错误信息
                stderr_text = proc.stderr or ""
                stdout_text = proc.stdout or ""
                combined = stderr_text + "\n" + stdout_text

                # ── 策略：从 Rich/普通 traceback 中提取真正的异常 ──
                detail_msg = self._extract_manim_error(combined, proc.returncode)

                result["error"] = detail_msg
                logger.error("❌ Manim 渲染失败 [code=%d]: %s\n--- STDERR ---\n%s\n--- STDOUT ---\n%s",
                           proc.returncode, detail_msg, stderr_text[-3000:], stdout_text[-1000:])

        except subprocess.TimeoutExpired:
            result["error"] = f"渲染超时 ({timeout}s)"
            result["render_time"] = timeout
            logger.error("❌ Manim 渲染超时: %ds", timeout)

        except Exception as e:
            result["error"] = f"渲染异常: {str(e)}"
            logger.error("❌ Manim 渲染异常: %s", e, exc_info=True)

        finally:
            # 清理临时目录
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

        return result

    @staticmethod
    def _extract_manim_error(combined_output: str, exit_code: int) -> str:
        """
        从 Manim 的 Rich-formatted 输出中提取真正的 Python 异常信息。

        Manim 使用 Rich 库格式化 traceback，输出类似：
        ┌─────────────────────── Traceback (most recent call last) ───────────────────────┐
        │ File ".../animation.py", line 42, in construct                                 │
        │     obj = SomeClass()                                                          │
        │ NameError: name 'SomeClass' is not defined                                     │
        └─────────────────────────────────────────────────────────────────────────────────┘

        此方法剥离 Rich 边框字符，优先返回用户代码中的实际异常。
        """
        # ── 1. 清理 Rich 边框字符 ──
        rich_chars = set("┌┐└┘│─├┤┬┴┼╭╮╰╯═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬")
        cleaned_lines = []
        for line in combined_output.split("\n"):
            stripped = line.strip()
            # 移除纯边框行（只含 Rich 字符和空格）
            if stripped and not all(c in rich_chars or c.isspace() for c in stripped):
                # 移除行内的 Rich 边框字符
                clean = "".join(c for c in stripped if c not in rich_chars)
                if clean.strip():
                    cleaned_lines.append(clean.strip())

        if not cleaned_lines:
            return f"渲染失败 (exit code {exit_code}): 无输出"

        # ── 2. 按优先级查找异常信息 ──
        # 优先级 1: 找 "XxxError: message" 格式的最终异常
        exception_pattern = re.compile(
            r"^(\w+(?:Error|Exception|Warning|Interrupt))(?:\s*:\s*(.*))?$",
            re.IGNORECASE,
        )
        # 优先级 2: 找用户代码中的 File "..." 行（带行号和函数名）
        file_pattern = re.compile(
            r'File\s+"([^"]+)"(?:,\s*line\s+(\d+))?.*(?:in\s+(\w+))?'
        )

        exception_line = None
        exception_message = ""
        user_files = []  # 用户代码中的文件引用
        manim_files = []  # Manim 内部文件引用
        last_significant = []

        for i, line in enumerate(cleaned_lines):
            m = exception_pattern.search(line)
            if m:
                exception_line = line
                exception_message = m.group(2) or ""

            fm = file_pattern.search(line)
            if fm:
                fpath = fm.group(1)
                if ("manim" in fpath.replace("\\", "/").lower()
                        or "site-packages" in fpath
                        or "lib" in fpath.split("/")[-2:]) :
                    manim_files.append(line)
                else:
                    user_files.append(line)

            # 收集有意义的行（非 Manim 内部框架行）
            lower = line.lower()
            if not any(skip in lower for skip in [
                "error_console", "print_exception", "endsceneearlyexception",
                "rerunsceneexception", "traceback (most recent call last)",
            ]):
                last_significant.append(line)

        # ── 3. 组装最终错误信息 ──
        parts = []

        if exception_line:
            parts.append(exception_line)
        elif last_significant:
            # 取最后 3 个有意义的行
            parts.append(last_significant[-1])

        if user_files:
            # 显示用户代码中出错的位置
            parts.append(f"位置: {user_files[-1]}")
        elif manim_files:
            parts.append(f"位置: {manim_files[-1]}")

        if exception_message and not parts[0].endswith(exception_message):
            if parts and exception_message not in parts[0]:
                pass  # 异常行已包含 message

        if not parts:
            # 完全无法解析，取最后 3 个非空行
            fallback = [l for l in cleaned_lines[-5:] if l]
            if fallback:
                parts.append("; ".join(fallback))

        detail = f"渲染失败: {' | '.join(parts)}" if parts else f"渲染失败 (exit code {exit_code})"
        return detail

    def _generate_thumbnail(self, video_path: Path, task_id: str) -> Optional[str]:
        """从视频中提取第一帧作为缩略图"""
        try:
            thumb_path = self.output_dir / f"thumb_{task_id}.png"
            # 使用 ffmpeg 提取第一帧
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_path),
                "-vframes", "1", "-q:v", "2",
                str(thumb_path),
            ], capture_output=True, timeout=10)
            return str(thumb_path) if thumb_path.exists() else None
        except Exception as e:
            logger.debug("缩略图生成失败: %s", e)
            return None


# ── 全局单例 ──

_instance: Optional[ManimRenderer] = None


def get_renderer() -> ManimRenderer:
    """获取 Manim 渲染器单例"""
    global _instance
    if _instance is None:
        _instance = ManimRenderer()
    return _instance


# ── LLM 代码生成 Prompt ──

ANIMATION_PROMPT_TEMPLATE = """你是一位算法可视化专家和 Manim 动画大师。

## 任务
为以下算法/数据结构概念编写一段 Manim (Community Edition) Python 代码，生成教学动画。

## 主题
{topic}

## 步骤描述
{description}

## 难度等级
{difficulty}
## 目标布鲁姆层级
{bloom_level}

## 学生画像
- 能力水平: {ability_level}
- 学习偏好: {learning_style}
- 认知特征: {feynman_score} 费曼适配度

## 要求

### 代码结构要求：
```python
class {scene_name}(Scene):
    def construct(self):
        # 你的动画代码
        pass
```

### 动画设计原则：
1. **渐进式展示**：不要一次性显示所有内容，逐步呈现每个步骤
2. **颜色编码**：用不同颜色区分不同元素（比较元素、已排序、当前焦点等）
3. **文字说明**：关键步骤添加 Text 或 Tex 标注
4. **时间节奏**：适当使用 wait() 让观众消化信息
5. **视觉清晰**：字号够大，对比度足够

### 具体场景要求（根据 topic 类型选择）：

**如果是搜索/查找算法**（如二分查找、线性搜索）：
- 展示数组元素和左右指针
- 高亮比较过程
- 标注 mid 计算
- 用 FadeOut 表示排除区域

**如果是排序算法**（如快速排序、归并排序）：
- 展示数组初始状态
- 动态高亮 pivot/基准值
- 分区过程的可视化
- 递归调用的层次感

**如果是树/图算法**（如 DFS、BFS、遍历）：
- 绘制树形/图形结构
- 用移动的点表示遍历路径
- 已访问节点变色
- 层序标注

**如果是链表操作**（如反转、合并）：
- 绘制链表节点和指针
- 动画展示指针重定向
- 节点数值更新动画

**如果是数学概念**（如递归、动态规划）：
- 用图形辅助理解
- 递归调用栈可视化
- 状态转移表格填充

### 技术约束：
- 使用 manim Community Edition 语法（兼容 v0.18+）
- ⚠️ 不要设置 config.media_width / config.media_height（系统会自动注入字符串值）
- 场景类名必须是 `{scene_name}`
- 只使用 manim 库 + numpy，不依赖其他第三方包
- 控制总帧数在 300~800 帧（10~26秒视频）
- 使用 `-ql` 质量（低质量预览模式）

### 禁止事项：
- 不要使用 ShowPassingFlash 等可能引起闪烁的效果
- 不要使用太多同时发生的动画
- 不要在 construct 中使用无限循环

请直接输出完整的 Python 代码（不需要 markdown 包裹）："""


def build_animation_prompt(
    topic: str,
    description: str = "",
    difficulty: str = "medium",
    bloom_level: str = "understand",
    ability_level: str = "intermediate",
    learning_style: str = "visual",
    feynman_score: float = 0.7,
    scene_name: str = "AlgorithmScene",
) -> str:
    """构建动画代码生成的 prompt"""
    return ANIMATION_PROMPT_TEMPLATE.format(
        topic=topic,
        description=description or f"可视化演示「{topic}」的完整执行过程",
        difficulty=difficulty,
        bloom_level=bloom_level,
        ability_level=ability_level,
        learning_style=learning_style,
        feynman_score=feynman_score,
        scene_name=scene_name,
    )
