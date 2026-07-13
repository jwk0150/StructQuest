"""
学习模式配置服务
=================

根据学习模式（基础 / 入门 / 考试）提供差异化配置：
- 每日任务数量
- 学习时长建议
- 内容推荐策略
- 难度系数
"""

from app.models.user import (
    LEARNING_MODE_BASIC,
    LEARNING_MODE_BEGINNER,
    LEARNING_MODE_EXAM,
)

# ════════════════════════════════════════════════════════
# 模式完整配置
# ════════════════════════════════════════════════════════

MODE_CONFIG = {
    LEARNING_MODE_BASIC: {
        "label": "基础模式",
        "icon": "🌱",
        "color": "#22c55e",
        "suitable_for": ["零基础用户", "初次接触该领域用户", "学习兴趣培养阶段"],
        "features": ["内容简单易懂", "学习压力低", "注重兴趣激发", "每日任务量较少"],
        # 今日任务
        "daily_task": {
            "count_range": [1, 3],
            "types": ["阅读文章", "学习1个概念", "完成1次签到"],
            "difficulty": "easy",
        },
        # 今日学习
        "study": {
            "duration_range": [10, 20],   # 分钟
            "content_style": ["碎片化", "图文优先", "视频辅助"],
            "priority": ["趣味内容", "通俗解读", "入门知识"],
        },
        # 热点推荐
        "recommendation": {
            "topics": ["通俗解读", "入门知识", "热门案例", "趣味内容"],
            "example": "3分钟看懂什么是AI",
            "max_difficulty": "easy",
        },
        # 智能升级阈值
        "upgrade_threshold": {
            "min_days": 7,
            "min_study_minutes": 120,
            "min_tasks_completed": 10,
            "min_accuracy": 0.6,
        },
    },
    LEARNING_MODE_BEGINNER: {
        "label": "入门模式",
        "icon": "📚",
        "color": "#3b82f6",
        "suitable_for": ["已具备基础认知", "希望系统学习用户"],
        "features": ["内容具有一定深度", "开始建立知识体系", "任务难度中等", "增加实践训练"],
        # 今日任务
        "daily_task": {
            "count_range": [3, 5],
            "types": ["阅读文章", "完成练习", "输出学习笔记"],
            "difficulty": "medium",
        },
        # 今日学习
        "study": {
            "duration_range": [20, 40],
            "content_style": ["系统课程", "知识体系构建", "适量练习"],
            "priority": ["行业热点", "技术解析", "应用案例"],
        },
        # 热点推荐
        "recommendation": {
            "topics": ["行业热点", "技术解析", "应用案例"],
            "example": "DeepSeek如何实现推理能力",
            "max_difficulty": "medium",
        },
        # 智能升级阈值
        "upgrade_threshold": {
            "min_days": 14,
            "min_study_minutes": 300,
            "min_tasks_completed": 30,
            "min_accuracy": 0.7,
        },
    },
    LEARNING_MODE_EXAM: {
        "label": "考试模式",
        "icon": "🎯",
        "color": "#f97316",
        "suitable_for": ["备考用户", "需要快速提升成绩用户"],
        "features": ["高强度学习", "重点考点覆盖", "高频真题训练", "强化知识点记忆"],
        # 今日任务
        "daily_task": {
            "count_range": [5, 8],
            "types": ["刷题训练", "模拟考试", "错题复盘", "考点背诵"],
            "difficulty": "hard",
        },
        # 今日学习
        "study": {
            "duration_range": [40, 90],
            "content_style": ["专项训练", "高频考点", "真题模拟", "阶段测试"],
            "priority": ["高频考点", "政策变化", "重点知识总结", "真题关联内容"],
        },
        # 热点推荐
        "recommendation": {
            "topics": ["高频考点", "政策变化", "重点知识总结", "真题关联内容"],
            "example": "近三年考试中出现频率最高的知识点",
            "max_difficulty": "hard",
        },
        # 智能降级阈值（学习表现下降时提示切回入门模式）
        "downgrade_threshold": {
            "max_consecutive_low_scores": 3,
            "min_accuracy": 0.4,
        },
    },
}


def get_mode_config(mode: str) -> dict:
    """获取指定模式的完整配置"""
    return MODE_CONFIG.get(mode, MODE_CONFIG[LEARNING_MODE_BASIC])


def get_daily_task_count(mode: str) -> int:
    """根据模式返回今日建议任务数（取范围中值）"""
    config = get_mode_config(mode)
    lo, hi = config["daily_task"]["count_range"]
    return (lo + hi) // 2


def get_study_duration_range(mode: str) -> list:
    """根据模式返回建议学习时长范围（分钟）"""
    config = get_mode_config(mode)
    return config["study"]["duration_range"]


def get_recommendation_topics(mode: str) -> list:
    """根据模式返回推荐主题列表"""
    config = get_mode_config(mode)
    return config["recommendation"]["topics"]


def adapt_content_by_mode(content_list: list, mode: str) -> list:
    """
    根据模式过滤/排序内容列表
    - basic:     保留趣味、入门内容，过滤高难度
    - beginner:  保留中等难度，过滤过于学术的内容
    - exam:       优先高频考点、真题类内容
    """
    config = get_mode_config(mode)
    max_difficulty = config["recommendation"].get("max_difficulty", "medium")

    difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
    max_level = difficulty_order.get(max_difficulty, 1)

    def content_difficulty(item) -> int:
        d = (item.get("difficulty") or "medium").lower()
        return difficulty_order.get(d, 1)

    filtered = [c for c in content_list if content_difficulty(c) <= max_level]

    # exam 模式：按考点频率排序（假设内容有 frequency 字段）
    if mode == LEARNING_MODE_EXAM:
        filtered.sort(key=lambda c: c.get("frequency", 0), reverse=True)

    return filtered if filtered else content_list


def check_upgrade(user_stats: dict, current_mode: str) -> dict | None:
    """
    智能成长检测：根据用户学习数据判断是否建议升级

    user_stats 格式：
    {
        "days_active": 12,          # 活跃天数
        "total_study_minutes": 240, # 总学习分钟数
        "tasks_completed": 15,       # 完成任务数
        "avg_accuracy": 0.75,        # 平均正确率
    }

    返回：
        None  → 不建议升级
        dict   → {"suggested_mode": "...", "reason": "..."}
    """
    if current_mode == LEARNING_MODE_EXAM:
        return None  # 已是最高级

    thresholds = MODE_CONFIG.get(current_mode, {}).get("upgrade_threshold", {})
    if not thresholds:
        return None

    checks = [
        user_stats.get("days_active", 0) >= thresholds.get("min_days", 999),
        user_stats.get("total_study_minutes", 0) >= thresholds.get("min_study_minutes", 999),
        user_stats.get("tasks_completed", 0) >= thresholds.get("min_tasks_completed", 999),
        user_stats.get("avg_accuracy", 0) >= thresholds.get("min_accuracy", 1.0),
    ]

    # 满足至少 3/4 条件时建议升级
    if sum(checks) >= 3:
        if current_mode == LEARNING_MODE_BASIC:
            return {
                "suggested_mode": LEARNING_MODE_BEGINNER,
                "suggested_label": MODE_CONFIG[LEARNING_MODE_BEGINNER]["label"],
                "reason": "你的学习表现优秀，建议开启【入门模式】获得更系统的学习体验。",
            }
        elif current_mode == LEARNING_MODE_BEGINNER:
            return {
                "suggested_mode": LEARNING_MODE_EXAM,
                "suggested_label": MODE_CONFIG[LEARNING_MODE_EXAM]["label"],
                "reason": "恭喜你已达到更高学习水平，建议开启【考试模式】进行高效提升。",
            }

    return None


def check_downgrade(user_stats: dict, current_mode: str) -> dict | None:
    """
    智能降级检测：考试模式用户表现持续低迷时建议降级
    """
    if current_mode != LEARNING_MODE_EXAM:
        return None

    threshold = MODE_CONFIG[LEARNING_MODE_EXAM].get("downgrade_threshold", {})
    consecutive_low = user_stats.get("consecutive_low_scores", 0)
    avg_acc = user_stats.get("avg_accuracy", 1.0)

    if (consecutive_low >= threshold.get("max_consecutive_low_scores", 3) or
            avg_acc < threshold.get("min_accuracy", 0.4)):
        return {
            "suggested_mode": LEARNING_MODE_BEGINNER,
            "suggested_label": MODE_CONFIG[LEARNING_MODE_BEGINNER]["label"],
            "reason": "检测到你近期学习压力较大，建议切换至【入门模式】巩固基础后再挑战考试模式。",
        }

    return None
