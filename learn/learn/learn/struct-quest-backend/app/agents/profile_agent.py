"""
Profile Agent（学生画像）— v3 精简版
==================================

定位：整个系统最重要的 Agent。维护 student_profile 这一张表。
不会生成资源、不会回答问题。

输入来源：
  - 注册信息（专业、课程、学习目标）
  - Learning Analytics（掌握度、专注度、偏好、风险）
  - Assessment 结果

工作流：
  首次注册 → 建立初始画像 → 保存数据库
  后续     → Learning Analytics 发现变化 → 更新画像 → 保存数据库

输出：student_profile（结构化的学生画像）
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.agents.base import BaseAgent
from app.agents.state import LearningState, StudentProfile
from app.utils.logger import get_logger

logger = get_logger("profile_agent")

# 延迟导入避免循环依赖
def _get_student_profile_model():
    from app.models.student_profile import StudentProfile as SPModel
    return SPModel


# ══════════════════════════════════════════════════
#  Prompt 模板
# ══════════════════════════════════════════════════

PROFILE_INIT_PROMPT = """你是一位专业的教育心理学家和学习分析专家。请根据以下新用户的完整冷启动数据生成初始学习画像。

## 基础信息（第一阶段：注册时采集）
- 专业: {major}
- 年级: {grade}
- 课程: {subject}
- 学习目标: {goal}
- 目标成绩: {target_score}
- 每天学习时间: {daily_study_time}
- 考试时间: {exam_date}

## 学习需求问卷（第二阶段）
- 学习目的: {learning_purpose}
- 偏好的学习方式: {preferred_styles}
- 每日学习时长: {daily_study_time}

## 诊断测试结果（第三阶段）
- 总体正确率: {diagnostic_accuracy}%
- 各模块掌握度: {diagnostic_mastery}
- 行为数据: {diagnostic_behavior}

## 知识库参考
{rag_context}

请综合以上所有数据，以 JSON 格式输出初始学习画像。注意：

1. **诊断测试是最重要的客观数据**：knowledge_mastery 字段必须直接使用诊断测试的各模块掌握度数据，不要编造。
2. **基础信息和问卷决定 resource_preferences**：
   - 偏好的学习方式直接映射为初始资源偏好权重（选中的给高分，未选的给低分）
   - 例如用户选了"视频讲解"+"图解" → resource_preferences: {{"视频": 90, "图解": 85, "讲义": 40, "代码": 30, "练习题": 35}}
3. **学习目的决定能力评估倾向**：
   - 考研/竞赛 → 预期基础较好，ability_level 可能偏高
   - 课程预习 → 可能是初学者，ability_level 可以偏保守
4. **每天学习时间决定 pace**：
   - 15分钟 → "碎片型"学习节奏
   - 2小时以上 → 可以安排深度学习

```json
{{
    "ability_level": "beginner|intermediate|advanced|expert",
    "learning_style": "visual|auditory|reading|hands_on",
    "pace": "fast|moderate|slow",
    "interests": ["从课程和诊断强项中推断的兴趣"],
    "strengths": ["诊断测试中正确率>70%的模块"],
    "weaknesses": ["诊断测试中正确率<50%的模块"],
    "knowledge_mastery": {{"数组": 85, "链表": 70, "栈": 60, ...}},
    "activity_score": 0,
    "focus_score": 75,
    "confidence_score": 60,
    "resource_preferences": {{"视频": 85, "图解": 75, "讲义": 40, "代码": 30, "练习题": 35}},
    "learning_rhythm": "持续型|碎片型|集中型",
    "daily_strategy": "根据学习目的和时间推荐的具体策略",
    "summary": "一段话总结学生的完整画像(150字以内)，必须提及：专业背景、学习目标、知识掌握概况、推荐学习方式",
    "weakness_summary": "用一句话概括最需要加强的1-2个模块",
    "cognitive": {{
        "mbti_style": "analyst|explorer|negotiator|sentinel",
        "feynman_adaptation": 0.5,
        "abstract_reasoning": 0.5,
        "concrete_example_need": 0.6,
        "error_tolerance": 0.6,
        "preferred_depth": "moderate"
    }}
}}
```
只输出 JSON，不要其他内容。"""


PROFILE_UPDATE_PROMPT = """你是一位学习分析师。请根据最新的分析数据更新学生画像。

## 当前画像
{current_profile}

## 最新分析数据
{analytics_data}

## 最新测评结果
{assessment_data}

## 学习路径进展
{path_progress}

请返回 JSON（只更新有变化的字段）：
```json
{{
    "ability_level": "...",
    "strengths": [...],
    "weaknesses": [...],
    "knowledge_mastery": {{"topic": score, ...}},
    "activity_score": 0-100,
    "focus_score": 0-100,
    "confidence_score": 0-100,
    "resource_preferences": {{"视频": 85, ...}},
    "learning_rhythm": "持续型|突击型|碎片型",
    "error_patterns": [...],
    "primary_error_type": "...",
    "daily_strategy": "学习策略建议",
    "summary": "更新的画像总结(200字以内)",
    "cognitive": {{...}}
}}
```
只返回 JSON，不要其他内容。"""


class ProfileAgent(BaseAgent):
    """
    学生画像 Agent v3 — 只维护 student_profile 表

    职责：
    1. 新用户注册 → 建立初始画像
    2. 接收 LearningAnalytics 数据 → 更新画像
    3. 不生成资源，不回答问题
    """

    @property
    def name(self) -> str:
        return "profile_agent"

    @property
    def description(self) -> str:
        return "维护学生画像 — 建立/更新/持久化 student_profile"

    # ═══════════════════════════════════════════
    #  核心 run 方法
    # ═══════════════════════════════════════════

    def run(self, state: LearningState) -> Dict[str, Any]:
        existing_profile = dict(state.get("student_profile", {}))
        analytics = state.get("learning_analytics", {})
        assessment = state.get("assessment", {})
        event_type = state.get("event_type", "")

        # 判断是首次建立还是更新
        is_first_time = not existing_profile or not existing_profile.get("ability_level")

        if is_first_time:
            logger.info("🆕 首次建立学习画像...")
            profile_data = self._build_initial_profile(state)
        else:
            logger.info("🔄 更新学习画像...")
            profile_data = self._update_profile(
                existing_profile, analytics, assessment, state
            )

        # 标记更新时间
        profile_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # ★ 持久化已移至 graph.run() 层统一处理，此处不再调用 _persist_to_db

        # 日志
        log = self._log(
            state,
            f"{'🆕 初始' if is_first_time else '🔄 更新'}画像完成 | "
            f"能力: {profile_data.get('ability_level', 'N/A')} | "
            f"掌握 {len(profile_data.get('knowledge_mastery', {}))} 个知识点 | "
            f"信心: {profile_data.get('confidence_score', 'N/A')}/100"
        )

        return {
            **log,
            "student_profile": profile_data,
            "next_action": "orchestrate",
        }

    # ═══════════════════════════════════════════
    #  首次建立画像
    # ═══════════════════════════════════════════

    def _build_initial_profile(self, state: LearningState) -> Dict[str, Any]:
        """新用户注册时建立初始画像（冷启动四阶段数据）"""
        subject = state.get("subject", "通用")
        goal = state.get("current_goal", "")
        event_payload = state.get("event_payload", {})
        rag_context = state.get("rag_context") or ""

        # 第一阶段：基础信息
        major = event_payload.get("major", "")
        grade = event_payload.get("grade", "")
        target_score = event_payload.get("target_score", "")
        daily_study_time = event_payload.get("daily_study_time", "")
        exam_date = event_payload.get("exam_date", "")

        # 第二阶段：学习需求问卷
        learning_purpose = event_payload.get("learning_purpose", "")
        preferred_styles = event_payload.get("preferred_styles", [])
        preferred_styles_str = "、".join(preferred_styles) if preferred_styles else "未填写"

        # 第三阶段：诊断测试结果
        diagnostic_accuracy = state.get("diagnostic_accuracy", 0)
        diagnostic_mastery = state.get("diagnostic_mastery", {})
        diagnostic_behavior = state.get("diagnostic_behavior", {})
        diagnostic_mastery_str = json.dumps(diagnostic_mastery, ensure_ascii=False) if diagnostic_mastery else "{}"
        diagnostic_behavior_str = json.dumps(diagnostic_behavior, ensure_ascii=False) if diagnostic_behavior else "{}"

        prompt = self._build_system_prompt(
            PROFILE_INIT_PROMPT,
            major=major or "未填写",
            grade=grade or "未填写",
            subject=subject,
            goal=goal or "未填写",
            target_score=target_score or "未设置",
            daily_study_time=daily_study_time or "未填写",
            exam_date=exam_date or "暂无",
            learning_purpose=learning_purpose or "未填写",
            preferred_styles=preferred_styles_str,
            diagnostic_accuracy=str(diagnostic_accuracy),
            diagnostic_mastery=diagnostic_mastery_str,
            diagnostic_behavior=diagnostic_behavior_str,
            rag_context=rag_context[:1000] if rag_context else "无",
        )

        try:
            response = self._call_llm(
                [{"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=2000,
            )
            profile = self._parse_json(response)
            profile = self._validate_profile(profile, subject, goal)

            # 注入诊断测试的客观数据（确保不会被 LLM 编造的数据覆盖）
            if diagnostic_mastery:
                profile["knowledge_mastery"] = diagnostic_mastery
            if diagnostic_behavior:
                profile["diagnostic_behavior"] = diagnostic_behavior

            # 注入用户填写的基础信息
            profile["major"] = major
            profile["grade"] = grade
            profile["learning_goal"] = goal
            profile["learning_purpose"] = learning_purpose
            profile["daily_study_time"] = daily_study_time

            return profile
        except Exception as e:
            logger.warning("LLM 初始画像失败: %s，使用默认画像", e)
            profile = self._default_profile(subject, goal)
            # 注入客观数据
            if diagnostic_mastery:
                profile["knowledge_mastery"] = diagnostic_mastery
            profile["major"] = major
            profile["grade"] = grade
            return profile

    # ═══════════════════════════════════════════
    #  更新画像
    # ═══════════════════════════════════════════

    def _update_profile(
        self,
        existing: Dict,
        analytics: Dict,
        assessment: Dict,
        state: LearningState,
    ) -> Dict[str, Any]:
        """基于最新分析数据更新画像"""
        profile = dict(existing)

        # ── 从 Analytics 直接合并数值字段 ──
        if analytics:
            # 知识掌握度
            analytics_mastery = analytics.get("knowledge_mastery", {})
            if analytics_mastery:
                existing_mastery = dict(profile.get("knowledge_mastery", {}))
                existing_mastery.update(analytics_mastery)
                profile["knowledge_mastery"] = existing_mastery

            # 活跃度 / 专注度
            if analytics.get("activity_score") is not None:
                profile["activity_score"] = analytics["activity_score"]
            if analytics.get("focus_score") is not None:
                profile["focus_score"] = analytics["focus_score"]

            # 资源偏好
            if analytics.get("resource_preferences"):
                profile["resource_preferences"] = analytics["resource_preferences"]

            # 错误模式
            if analytics.get("error_patterns"):
                existing_errors = set(profile.get("error_patterns", []))
                existing_errors.update(analytics["error_patterns"])
                profile["error_patterns"] = list(existing_errors)[:8]
            if analytics.get("primary_error_type"):
                profile["primary_error_type"] = analytics["primary_error_type"]

            # 学习节奏
            if analytics.get("learning_rhythm"):
                profile["learning_rhythm"] = analytics["learning_rhythm"]

        # ── 从 Assessment 更新掌握度和短板 ──
        if assessment:
            # 知识追踪
            knowledge_tracking = assessment.get("knowledge_tracking", {})
            if knowledge_tracking:
                mastery = dict(profile.get("knowledge_mastery", {}))
                for topic, data in knowledge_tracking.items():
                    if isinstance(data, dict):
                        mastery[topic] = float(data.get("mastery_level", 0))
                    else:
                        mastery[topic] = float(data) if data else 0
                profile["knowledge_mastery"] = mastery

            # 薄弱点
            gaps = assessment.get("gaps_found", [])
            if gaps:
                existing_weak = set(profile.get("weaknesses", []))
                existing_weak.update(gaps)
                profile["weaknesses"] = list(existing_weak)[:8]

            # 信心指数更新
            score = assessment.get("overall_score", 0)
            if isinstance(score, dict):
                score = score.get("overall_score", 0)
            score = float(score) if score else 0
            if score > 0:
                old_confidence = float(profile.get("confidence_score", 60))
                new_confidence = old_confidence * 0.7 + score * 0.3
                profile["confidence_score"] = round(new_confidence, 1)

        # ── 从学习路径更新进度感知 ──
        learning_path = state.get("learning_path", [])
        if learning_path:
            completed = sum(1 for s in learning_path if s.get("status") == "completed")
            total = len(learning_path)
            if total > 0:
                completion_ratio = completed / total
                # 根据完成率微调能力等级
                if completion_ratio > 0.8 and profile.get("ability_level") == "beginner":
                    profile["ability_level"] = "intermediate"

        # ── 每日策略更新 ──
        profile["daily_strategy"] = self._build_daily_strategy(profile)

        # ── 摘要更新 ──
        profile["summary"] = self._build_summary(profile)

        return profile

    # ═══════════════════════════════════════════
    #  每日策略生成
    # ═══════════════════════════════════════════

    def _build_daily_strategy(self, profile: Dict) -> str:
        """根据当前画像生成每日学习策略"""
        focus = float(profile.get("focus_score", 75))
        rhythm = profile.get("learning_rhythm", "持续型")
        pref_type = ""
        prefs = profile.get("resource_preferences", {})
        if prefs:
            pref_type = max(prefs, key=prefs.get)

        weak_count = len(profile.get("weaknesses", []))
        mastery = profile.get("knowledge_mastery", {})
        low_mastery = [t for t, s in mastery.items() if float(s) < 50]

        parts = []

        if rhythm == "突击型":
            parts.append("采用高强度集训节奏")
        elif rhythm == "碎片型":
            parts.append("采用15-20分钟碎片化学习")
        else:
            parts.append("保持每日稳定学习节奏")

        if focus < 60:
            parts.append("优先短任务维持专注度")
        elif focus >= 80:
            parts.append("可进入深度学习块")

        if pref_type:
            parts.append(f"以{pref_type}为主要学习材料")

        if low_mastery:
            parts.append(f"重点攻克: {'、'.join(low_mastery[:2])}")

        if weak_count > 3:
            parts.append("每日安排1个薄弱点专项练习")

        return "；".join(parts) if parts else "保持稳定的学习节奏，循序渐进"

    # ═══════════════════════════════════════════
    #  摘要生成
    # ═══════════════════════════════════════════

    def _build_summary(self, profile: Dict) -> str:
        """生成画像摘要"""
        level = profile.get("ability_level", "初学者")
        level_cn = {"beginner": "初学", "intermediate": "中等", "advanced": "进阶", "expert": "专家"}
        level_str = level_cn.get(level, level)

        mastery = profile.get("knowledge_mastery", {})
        avg_mastery = sum(float(v) for v in mastery.values()) / max(len(mastery), 1)

        rhythm = profile.get("learning_rhythm", "持续型")
        focus = profile.get("focus_score", 75)

        return (
            f"该学生处于{level_str}水平，{rhythm}学习，"
            f"平均掌握度 {avg_mastery:.0f}/100，专注度 {focus:.0f}/100。"
            f"建议策略: {profile.get('daily_strategy', '')}"
        )[:200]

    # ═══════════════════════════════════════════
    #  数据校验
    # ═══════════════════════════════════════════

    def _validate_profile(self, data: Dict, subject: str, goal: str) -> Dict:
        """确保画像数据完整"""
        defaults = {
            "ability_level": "beginner",
            "learning_style": "reading",
            "pace": "moderate",
            "interests": [subject],
            "strengths": [],
            "weaknesses": [f"{subject}基础概念"],
            "knowledge_mastery": {},
            "activity_score": 0.0,
            "focus_score": 75.0,
            "engagement_score": 70.0,
            "resource_preferences": {},
            "learning_rhythm": "持续型",
            "error_patterns": [],
            "primary_error_type": "",
            "daily_strategy": "保持稳定学习节奏，从基础开始循序渐进",
            "confidence_score": 60.0,
            "summary": f"该学生正在学习{subject}，目标为{goal}。建议从基础概念入手。",
            "cognitive": {
                "mbti_style": "sentinel",
                "feynman_adaptation": 0.5,
                "abstract_reasoning": 0.5,
                "concrete_example_need": 0.6,
                "error_tolerance": 0.6,
                "preferred_depth": "moderate",
            },
        }

        for key, default_val in defaults.items():
            data.setdefault(key, default_val)

        # 确保 cognitive 完整
        cog = data.setdefault("cognitive", {})
        for ck, cv in defaults["cognitive"].items():
            cog.setdefault(ck, cv)

        # 数值范围约束
        for field in ["activity_score", "focus_score", "confidence_score"]:
            data[field] = max(0, min(100, float(data.get(field, 50))))

        for field in ["feynman_adaptation", "abstract_reasoning", "concrete_example_need", "error_tolerance"]:
            val = data["cognitive"].get(field, 0.5)
            data["cognitive"][field] = max(0.0, min(1.0, float(val)))

        return data

    # ═══════════════════════════════════════════
    #  默认画像
    # ═══════════════════════════════════════════

    def _default_profile(self, subject: str, goal: str) -> Dict:
        """LLM 不可用时的默认画像"""
        return {
            "ability_level": "beginner",
            "learning_style": "reading",
            "pace": "moderate",
            "interests": [subject],
            "strengths": [f"{subject}基础知识学习意愿强"],
            "weaknesses": [f"{subject}进阶应用", "实践操作经验不足"],
            "knowledge_mastery": {},
            "activity_score": 0.0,
            "focus_score": 75.0,
            "resource_preferences": {"文档": 50.0, "案例": 30.0, "练习题": 20.0},
            "learning_rhythm": "持续型",
            "error_patterns": [],
            "primary_error_type": "",
            "daily_strategy": "保持稳定学习节奏，从基础开始循序渐进",
            "confidence_score": 60.0,
            "summary": f"该学生正在学习{subject}，目标是{goal}。当前处于初学者阶段，建议从基础概念入手。",
            "cognitive": {
                "mbti_style": "sentinel",
                "feynman_adaptation": 0.5,
                "abstract_reasoning": 0.4,
                "concrete_example_need": 0.7,
                "error_tolerance": 0.6,
                "preferred_depth": "moderate",
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ═══════════════════════════════════════════
    #  DB 持久化
    # ═══════════════════════════════════════════

    def _persist_to_db(
        self, user_id: str, profile_data: Dict, analytics: Dict, is_new: bool
    ):
        """将画像数据持久化到 student_profiles 表"""
        import asyncio
        from app.db.session import AsyncSessionLocal

        SPModel = _get_student_profile_model()

        async def _save():
            async with AsyncSessionLocal() as db:
                from sqlalchemy.future import select
                result = await db.execute(
                    select(SPModel).where(SPModel.user_id == int(user_id))
                )
                record = result.scalar_one_or_none()

                cognitive = profile_data.get("cognitive", {})

                if record:
                    # 更新已有记录
                    record.ability_level = profile_data.get("ability_level", record.ability_level)
                    record.learning_style = profile_data.get("learning_style", record.learning_style)
                    record.pace = profile_data.get("pace", record.pace)
                    record.learning_rhythm = profile_data.get("learning_rhythm",
                                            analytics.get("learning_rhythm", record.learning_rhythm))
                    record.knowledge_mastery = profile_data.get("knowledge_mastery", {})
                    record.activity_score = float(profile_data.get("activity_score",
                                                  analytics.get("activity_score", 0)))
                    record.focus_score = float(profile_data.get("focus_score",
                                               analytics.get("focus_score", 75)))
                    record.resource_preferences = profile_data.get("resource_preferences",
                                                analytics.get("resource_preferences", {}))
                    record.error_patterns = profile_data.get("error_patterns",
                                            analytics.get("error_patterns", []))
                    record.primary_error_type = profile_data.get("primary_error_type",
                                                analytics.get("primary_error_type", ""))
                    record.mastery_trend = analytics.get("mastery_trend",
                                           analytics.get("growth_trend", "stable"))
                    # Risk维度
                    record.risk_level = analytics.get("risk_level", "low")
                    record.risk_factors = analytics.get("risk_factors", [])
                    record.strengths = profile_data.get("strengths", [])
                    record.weaknesses = profile_data.get("weaknesses", [])
                    record.confidence_score = float(profile_data.get("confidence_score", 60))
                    record.cognitive_profile = cognitive
                    record.daily_strategy = profile_data.get("daily_strategy", "")
                    record.summary = profile_data.get("summary", "")
                    record.profile_version = (record.profile_version or 1) + 1
                    record.source = "agent"
                else:
                    # 新建记录
                    record = SPModel(
                        user_id=int(user_id),
                        ability_level=profile_data.get("ability_level", "beginner"),
                        learning_style=profile_data.get("learning_style", "reading"),
                        pace=profile_data.get("pace", "moderate"),
                        learning_rhythm=profile_data.get("learning_rhythm", "持续型"),
                        knowledge_mastery=profile_data.get("knowledge_mastery", {}),
                        activity_score=float(profile_data.get("activity_score",
                                               analytics.get("activity_score", 0))),
                        focus_score=float(profile_data.get("focus_score",
                                            analytics.get("focus_score", 75))),
                        resource_preferences=profile_data.get("resource_preferences",
                                             analytics.get("resource_preferences", {})),
                        error_patterns=profile_data.get("error_patterns", []),
                        primary_error_type=profile_data.get("primary_error_type", ""),
                        mastery_trend=analytics.get("mastery_trend", "stable"),
                        risk_level=analytics.get("risk_level", "low"),
                        risk_factors=analytics.get("risk_factors", []),
                        strengths=profile_data.get("strengths", []),
                        weaknesses=profile_data.get("weaknesses", []),
                        confidence_score=float(profile_data.get("confidence_score", 60)),
                        cognitive_profile=cognitive,
                        daily_strategy=profile_data.get("daily_strategy", ""),
                        summary=profile_data.get("summary", ""),
                        source="agent",
                    )
                    db.add(record)

                await db.commit()
                logger.info("💾 画像已持久化到DB: user=%s, level=%s, version=%d",
                           user_id, record.ability_level, record.profile_version)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                pool.submit(asyncio.run, _save()).result(timeout=10)
        else:
            asyncio.run(_save())

    # ═══════════════════════════════════════════
    #  降级策略
    # ═══════════════════════════════════════════

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        super().fallback(state, error)
        subject = state.get("subject", "通用")
        goal = state.get("current_goal", "")
        return {
            "next_action": "orchestrate",
            "student_profile": self._default_profile(subject, goal),
        }
