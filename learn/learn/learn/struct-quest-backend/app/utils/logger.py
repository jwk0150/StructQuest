"""
统一日志系统
============

所有 Agent 和 API 使用统一 logger，输出到：
  1. 控制台（彩色，方便开发调试）
  2. logs/struct_quest.log 文件（持久化，方便排查线上问题）

使用方式：
  from app.utils.logger import get_logger
  logger = get_logger("resource_agent")

  logger.info("🚀 开始生成学习资源")
  logger.warning("⚠️ LLM 调用失败，使用降级策略")
  logger.error("❌ 生成失败: %s", error)
  logger.debug("调试信息")  # 仅在 LOG_LEVEL=DEBUG 时输出

日志格式：
  2026-05-21 14:07:33 | INFO  | resource_agent | 🚀 开始生成学习资源

配置环境变量：
  LOG_LEVEL       — 日志级别，默认 INFO（开发时设 DEBUG）
  LOG_DIR         — 日志目录，默认 logs/
  LOG_FILE        — 日志文件名，默认 struct_quest.log
  LOG_MAX_BYTES   — 单文件最大字节数，默认 10MB
  LOG_BACKUP_COUNT— 保留的历史文件数，默认 5
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


# ── 默认配置 ──

DEFAULT_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DEFAULT_LOG_DIR = os.getenv("LOG_DIR", "logs")
DEFAULT_LOG_FILE = os.getenv("LOG_FILE", "learn.log")
DEFAULT_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10 * 1024 * 1024))  # 10MB
DEFAULT_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# 已创建的 logger 缓存（避免重复添加 handler）
_loggers: dict = {}

# 全局 handler 是否已初始化（确保根 logger 只配一次）
_handlers_initialized = False


# ── 日志格式 ──

FILE_FORMAT = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

CONSOLE_FORMAT = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)


def _init_root_handlers():
    """初始化根 logger 的 handler（只执行一次）"""
    global _handlers_initialized
    if _handlers_initialized:
        return
    _handlers_initialized = True

    root = logging.getLogger("app")

    # 控制台 handler（Windows 兼容 UTF-8）
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, TypeError):
        pass
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CONSOLE_FORMAT)
    console_handler.setLevel(logging.DEBUG)
    root.addHandler(console_handler)

    # 文件 handler
    try:
        log_dir = Path(DEFAULT_LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / DEFAULT_LOG_FILE

        file_handler = RotatingFileHandler(
            str(log_path),
            maxBytes=DEFAULT_MAX_BYTES,
            backupCount=DEFAULT_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(FILE_FORMAT)
        file_handler.setLevel(logging.DEBUG)
        root.addHandler(file_handler)
    except Exception as e:
        # 文件 handler 创建失败不影响控制台输出
        root.warning("日志文件创建失败(%s)，仅使用控制台输出", e)

    # 设置根 logger 级别
    level = getattr(logging, DEFAULT_LEVEL, logging.INFO)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """
    获取命名 logger

    Args:
        name: 模块/Agent 名称，如 "resource_agent"、"api.learning"

    Returns:
        配置好的 Logger 实例

    用法：
        logger = get_logger("resource_agent")
        logger.info("开始生成")
    """
    # 确保根 handler 已初始化
    _init_root_handlers()

    # 使用 "app.xxx" 命名空间，确保继承根 logger 的 handler
    full_name = f"app.{name}" if not name.startswith("app.") else name

    if full_name in _loggers:
        return _loggers[full_name]

    logger = logging.getLogger(full_name)
    logger.propagate = True  # 传播到根 logger，由根的 handler 统一输出

    _loggers[full_name] = logger
    return logger
