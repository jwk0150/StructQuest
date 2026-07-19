"""
StructQuest 多智能体系统 — 全局共享状态定义（v3）
==================================================

Orchestrator 中心化架构：所有 Agent 不直接互相调用，
全部通过 Orchestrator 调度。每个 Agent 只读写自己负责的字段。

Agent 体系（7 个）:
  Orchestrator           — 流程大脑（不回答问题，只判断下一步谁工作）
  ProfileAgent           — 学生画像（只维护 student_profile 表）
  LearningAnalyticsAgent — 数据分析中心（活跃度/专注度/资源偏好/知识掌握/错误模式）
  PlannerAgent           — 学习规划师（基于画像+知识图谱规划路径）
  ResourceAgent          — 资源工厂（先检索后生成，保存到资源库）
  RecommendationAgent    — 首页推荐（排序+个性化）
  TutorAgent             — 学习老师（结合知识库+画像+错题回答问题）

数据驱动闭环:
  用户行为 → LearningAnalytics → Profile → Planner → Resource → Recommendation → Tutor
       ↑                                                                              │
       └──────────────────────────── 新的学习行为 ─────────────────────────────────────┘
"""

from typing import TypedDict, List, Dict, Any, Optional


# ══════════════════════════════════════════════════
#  认知画像
# ══════════════════════════════════════════════════

class CognitiveProfile(TypedDict, total=False):
    """认知画像 — 比 learning_style 更细粒度的认知特征"""
    mbti_style: str              # MBTI 简化风格
    feynman_adaptation: float    # 费曼法适配度 0~1
    abstract_reasoning: float    # 抽象推理能力 0~1
    concrete_example_need: float # 对具体例子的依赖度 0~1
    error_tolerance: float       # 对错误的容忍度
    preferred_depth: str         # 偏好深度: shallow/moderate/deep


# ══════════════════════════════════════════════════
#  学生画像（ProfileAgent 产出 — 唯一的画像表）
# ══════════════════════════════════════════════════

class StudentProfile(TypedDict, total=False):
    """学生画像 — ProfileAgent 的核心输出，持久化到 student_profile 表"""
    # 基础信息
    ability_level: str              # beginner / intermediate / advanced / expert
    learning_style: str             # visual / auditory / reading / hands_on
    pace: str                      # fast / moderate / slow
    interests: List[str]           # 兴趣方向

    # 知识维度（由 LearningAnalytics 更新，ProfileAgent 持有）
    knowledge_mastery: Dict[str, float]    # 知识点掌握度 {"DFS": 85, "Dijkstra": 35}
    strengths: List[str]            # 擅长领域
    weaknesses: List[str]           # 知识短板

    # 学习行为维度（由 LearningAnalytics 更新，ProfileAgent 持有）
    activity_score: float           # 学习活跃度 0~100
    focus_score: float             # 专注指数 0~100
    engagement_score: float        # 参与度 0~100
    resource_preferences: Dict[str, float]  # 资源偏好 {"视频": 85, "PPT": 60, "案例": 90}

    # 学习策略
    learning_rhythm: str           # 学习节奏: 持续型/突击型/碎片型
    daily_strategy: str            # 每日学习策略建议

    # 错误模式
    error_patterns: List[str]      # 已识别的错误模式
    primary_error_type: str        # 主要错误类型

    # 认知特征
    cognitive: CognitiveProfile

    # 元数据
    confidence_score: float        # 学习信心指数 0~100
    summary: str                   # 画像总结(200字以内)
    updated_at: str                # 最后更新时间


# ══════════════════════════════════════════════════
#  学习分析指标（LearningAnalyticsAgent 产出）
# ══════════════════════════════════════════════════

class LearningAnalytics(TypedDict, total=False):
    """数据分析中心 — LearningAnalyticsAgent 的统一输出"""
    # 活跃度
    activity_score: float           # 综合活跃度 0~100
    login_frequency: int            # 近期登录次数
    total_study_hours: float        # 总学习时长(小时)
    task_completion_rate: float     # 任务完成率 0~1

    # 专注度
    focus_score: float             # 专注指数 0~100
    pause_count: int               # 暂停次数
    page_switch_count: int         # 页面切换次数

    # 资源偏好
    resource_preferences: Dict[str, float]  # {"视频": 0.85, "PPT": 0.60, "案例": 0.90}
    preferred_resource_type: str   # 最偏好的资源类型

    # 知识掌握度追踪
    knowledge_mastery: Dict[str, float]   # {"DFS": 85, "BFS": 80, "Dijkstra": 35}
    mastery_trend: str             # 整体趋势: improving/stable/declining

    # 错误模式分析
    error_patterns: List[str]      # 错误模式列表
    primary_error_type: str        # 主要错误类型: 概念混淆/计算错误/逻辑漏洞/方法误用
    error_analysis_detail: str     # AI 分析的错误详细描述

    # 学习节奏
    learning_rhythm: str           # 持续型/突击型/碎片型
    peak_study_hours: str          # 高峰学习时段

    # ★ Growth（成长画像）— v3.1 新增
    growth_history: List[Dict[str, Any]]   # [{date, overall_score, mastered_topics}, ...]
    growth_trend: str              # 成长趋势: accelerating/steady/plateauing/declining

    # ★ Risk（学习风险画像）— v3.1 新增
    risk_level: str                # low/medium/high
    risk_factors: List[str]        # ["连续3天未完成任务", "图知识点长期未掌握"]
    consecutive_missed_tasks: int  # 连续未完成任务数
    consecutive_low_scores: int    # 连续低分次数
    stagnant_topics: List[str]     # 长期未掌握的知识点

    # 元数据
    analyzed_at: str               # 分析时间
    data_source_count: int         # 数据源数量


# ══════════════════════════════════════════════════
#  学习路径步骤（PlannerAgent 产出）
# ══════════════════════════════════════════════════

class PathStep(TypedDict):
    """学习路径中的一个可执行步骤"""
    step_id: int
    topic: str
    description: str
    difficulty: str                # easy / medium / hard
    bloom_level: str               # remember/understand/apply/analyze/evaluate/create
    estimated_minutes: int
    prerequisites: List[str]       # 前置知识点
    status: str                    # pending / in_progress / completed / skipped
    resources_generated: bool
    score: Optional[float]
    teaching_hint: str             # 针对该学生的教学建议


# ══════════════════════════════════════════════════
#  资源项（ResourceAgent 产出）
# ══════════════════════════════════════════════════

class ResourceItem(TypedDict, total=False):
    """生成的资源"""
    type: str                      # notes / mindmap / quiz / code_example / animation
    topic: str
    title: str
    content: str
    format: str                    # markdown / json / text / mermaid / python / video
    difficulty: str
    estimated_minutes: int
    source: str                    # cached(从资源库复用) / generated(AI新生成)
    rag_sources: List[str]
    tags: List[str]
    meta: Dict[str, Any]
    quiz_items: Optional[List[Dict]]  # quiz 结构化数据


class ResourceBundle(TypedDict, total=False):
    """资源包 — 5 种资源的统一输出"""
    notes: str
    mindmap: str
    quiz: List[Dict[str, Any]]
    code_example: str
    animation: Dict[str, Any]      # {video_url, source_code, ...}


# ══════════════════════════════════════════════════
#  知识追踪 & 测评结果（兼容旧版 AssessmentAgent）
# ══════════════════════════════════════════════════

class KnowledgeMastery(TypedDict, total=False):
    """单个知识点的掌握情况"""
    topic: str
    mastery_level: float
    last_assessed_at: str
    error_count: int
    success_count: int
    error_patterns: List[str]
    confidence_trend: str
    recommended_action: str


class AssessmentResult(TypedDict, total=False):
    """测评结果 — AssessmentAgent 核心输出"""
    overall_score: float
    step_scores: Dict[str, float]
    bloom_scores: Dict[str, float]
    strengths_identified: List[str]
    gaps_found: List[str]
    gap_details: List[Dict[str, Any]]
    recommendation: str
    should_adjust_path: bool
    adjustment_reason: str
    next_focus: str
    error_analysis: Dict[str, Any]
    knowledge_tracking: Dict[str, KnowledgeMastery]
    passed: bool


# ══════════════════════════════════════════════════
#  推荐结果（RecommendationAgent 产出）
# ══════════════════════════════════════════════════

class RecommendationItem(TypedDict, total=False):
    """单条推荐"""
    resource_id: int
    title: str
    type: str                      # 资源类型
    reason: str                    # 推荐理由（个性化）
    relevance_score: float         # 相关性评分
    source: str                    # 来源: cached/generated/external


class RecommendationResult(TypedDict, total=False):
    """推荐结果集"""
    items: List[RecommendationItem]
    total: int
    generated_at: str
    based_on: str                  # 推荐依据描述


# ══════════════════════════════════════════════════
#  辅导对话（TutorAgent 产出）— v4 多模态增强版
# ══════════════════════════════════════════════════

class TutorResourceAttachment(TypedDict, total=False):
    """Tutor 回复中附带的多模态资源"""
    type: str                      # mindmap / animation / ppt_outline / code_example / notes / exercise
    title: str                     # 资源标题
    content_text: str              # 文本内容（思维导图 Markdown、代码等）
    content_json: Optional[Dict]   # 结构化内容（练习题 JSON 等）
    format: str                    # markmap / video / pptx / python / markdown / json
    preview_url: Optional[str]     # 资源预览 URL
    file_url: Optional[str]        # 文件下载 URL
    thumbnail_url: Optional[str]   # 缩略图 URL
    generated_for: str             # 生成原因（e.g., "用户是视觉偏好者，用思维导图辅助理解"）
    quality_score: Optional[float] # 质量评分
    generation_time_seconds: Optional[float]  # 生成耗时
    metadata: Optional[Dict]       # 扩展元数据


class TutorResponse(TypedDict, total=False):
    """Tutor Agent 的回答（v4 多模态增强版）"""
    answer_text: str               # 回答文本
    referenced_knowledge: List[str]  # 引用的知识点
    used_context: str              # 使用的上下文来源: knowledge_base/student_profile/chat_history/error_book
    follow_up_suggestions: List[str]  # 建议的后续问题
    generated_visual: Optional[str]  # 可选：生成的图示/代码
    # ★ v4 新增：多模态资源
    resource_attachments: List[TutorResourceAttachment]  # 附带的多模态资源
    primary_format: str            # 主要回复格式: text_only / mindmap_enhanced / animation_enhanced / code_enhanced / ppt_enhanced / exercise_enhanced
    format_reason: str             # 为什么选择这个格式（可解释性）


# ══════════════════════════════════════════════════
#  全局共享状态（顶层）— v3 Orchestrator 架构
# ══════════════════════════════════════════════════

class LearningState(TypedDict, total=False):
    """
    Orchestrator 中心化架构的全局共享状态

    设计原则:
    - Orchestrator 是唯一的路由决策者
    - Agent 不直接互相调用，全部通过 Orchestrator 调度
    - 每个 Agent 只读写自己负责的字段
    - 所有 Agent 执行完后返回 Orchestrator 重新判断
    """

    # ====== 输入参数 ======
    user_id: str
    subject: str
    current_goal: str
    user_messages: List[str]
    user_answer: Optional[str]

    # ====== 事件驱动字段（v3 新增）======
    event_type: str                      # 事件类型（核心路由依据）
    event_payload: Dict[str, Any]       # 事件携带数据
    orchestrator_decision: Dict[str, Any]  # Orchestrator 决策记录
    pending_agents: List[str]           # 待执行的 Agent 队列
    session_phase: str                  # onboarding / learning_active / awaiting_user / completed

    # ====== 各 Agent 产出 ======
    # ProfileAgent → student_profile（唯一画像表）
    student_profile: StudentProfile

    # LearningAnalyticsAgent → analytics
    learning_analytics: LearningAnalytics

    # PlannerAgent → learning_path
    learning_path: List[PathStep]

    # ResourceAgent → resources + resource_bundle
    resources: List[ResourceItem]
    resource_bundle: ResourceBundle

    # RecommendationAgent → recommendation
    recommendation: RecommendationResult

    # TutorAgent → tutor_response + chat_response
    tutor_response: TutorResponse
    chat_response: Optional[str]        # 向前端直接返回的回答文本

    # ====== 控制字段 ======
    messages: List[Dict[str, Any]]     # Agent 决策日志（可观测性）
    current_step_index: int
    iteration_count: int
    max_iterations: int
    next_action: str                   # 下一步动作（路由控制）
    session_status: str                # running / completed / paused / error
    error: Optional[str]

    # ====== 扩展字段 ======
    rag_context: Optional[str]
    session_snapshot: Optional[Dict[str, Any]]


# ══════════════════════════════════════════════════
#  事件类型常量
# ══════════════════════════════════════════════════

class EventType:
    """用户事件类型 — Orchestrator 的路由依据"""
    USER_REGISTERED = "user_registered"            # 注册成功
    USER_LOGIN = "user_login"                      # 登录
    START_LEARNING = "start_learning"              # 开始学习
    COMPLETE_TEST = "complete_test"                # 完成测试
    SUBMIT_ANSWER = "submit_answer"                # 提交答案
    ASK_QUESTION = "ask_question"                  # 提出问题
    COMPLETE_LEARNING = "complete_learning"        # 完成学习
    CLICK_RECOMMENDATION = "click_recommendation"  # 点击推荐
    GENERATE_RESOURCE = "generate_resource"        # 生成资源
    REQUEST_MINDMAP = "request_mindmap"            # 生成思维导图
    REQUEST_CODE = "request_code_example"          # 生成代码案例
    REQUEST_ANIMATION = "request_animation"        # 生成动画
    REQUEST_EXERCISE = "request_exercise"          # 请求练习题
    DAILY_CHECKIN = "daily_checkin"               # 每日打卡
    CONTINUE_SESSION = "continue_session"          # 继续已有会话


# ══════════════════════════════════════════════════
#  工厂函数
# ══════════════════════════════════════════════════

def create_initial_state(
    user_id: str = "default",
    subject: str = "",
    goal: str = "",
    event_type: str = EventType.START_LEARNING,
    event_payload: Optional[Dict[str, Any]] = None,
) -> LearningState:
    """创建初始状态（v3 — Orchestrator 架构）"""
    return {
        "user_id": user_id,
        "subject": subject,
        "current_goal": goal,
        "user_messages": [],
        "user_answer": None,

        # 事件驱动
        "event_type": event_type,
        "event_payload": event_payload or {},
        "orchestrator_decision": {},
        "pending_agents": [],
        "session_phase": "onboarding",

        # Agent 产出（初始为空）
        "student_profile": {},
        "learning_analytics": {},
        "learning_path": [],
        "resources": [],
        "resource_bundle": {},
        "recommendation": {},
        "tutor_response": {},
        "chat_response": None,

        # 控制字段
        "messages": [],
        "current_step_index": 0,
        "iteration_count": 0,
        "max_iterations": 5,
        "next_action": "orchestrate",  # ★ 始终从 Orchestrator 开始
        "session_status": "running",
        "error": None,

        # 扩展
        "rag_context": None,
        "session_snapshot": None,
    }
