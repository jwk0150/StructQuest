"""
AI学习效果评估中心 API

提供六大模块数据接口：
① AI综合评估总评（大模型总结）
② 四个评分卡（知识掌握/练习效果/知识保持率/学习效率）
③ 学习行为分析（热力图/时段/资源占比）
④ AI智能诊断（发现/预测/风险/解释）
⑤ 资源优化记录（动态调整历史）
⑥ 学习计划优化（流程化路径）
"""
import json
import re
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func as sa_func, case, and_, desc
from app.db.session import get_db
from app.auth import get_current_user, get_required_user
from app.models.user import User
from app.models.study_session import StudySession
from app.models.learning_progress import LearningProgress
from app.models.knowledge_graph import KnowledgeNode
from app.models.exam_result import ExamResult
from app.models.learning_behavior import LearningBehavior
from app.models.student_profile import StudentProfile
from app.models.resource_adjustment import ResourceAdjustment
from app.models.learning_ecosystem import LearningPlan, LearningPlanStep
from app.utils.logger import get_logger

logger = get_logger("api.evaluation")

router = APIRouter(prefix="/api/evaluation", tags=["ai-evaluation"])

# ══════════════════════════════════════════════════
# Node ID → 中文名 映射缓存
# ══════════════════════════════════════════════════
_node_name_cache: dict = None


async def _get_node_name_map(db: AsyncSession) -> dict:
    """从 KnowledgeNode 表加载 id→title 映射"""
    global _node_name_cache
    if _node_name_cache is not None:
        return _node_name_cache
    try:
        result = await db.execute(select(KnowledgeNode.id, KnowledgeNode.title))
        rows = result.all()
        _node_name_cache = {row[0]: row[1] for row in rows}
    except Exception:
        _node_name_cache = {}
    return _node_name_cache


def _translate_nodes(ids: list) -> list:
    """将 node ID 列表翻译为中文名列表"""
    if _node_name_cache is None:
        return ids
    return [_node_name_cache.get(nid, nid) for nid in ids]

# ══════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════

def _tz8():
    return timezone(timedelta(hours=8))


def _now_local():
    return datetime.now(timezone.utc).astimezone(_tz8())


async def _get_profile(db: AsyncSession, user_id: int):
    """获取学生画像（StudentProfile > user.profile_data）"""
    sp_result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    sp = sp_result.scalar_one_or_none()
    if sp:
        return sp.to_dict()
    # 降级
    u_result = await db.execute(select(User).where(User.id == user_id))
    u = u_result.scalar_one_or_none()
    if u and u.profile_data and isinstance(u.profile_data, dict):
        return u.profile_data
    return {}


async def _call_llm(prompt: str, max_tokens: int = 1000) -> str:
    """调用 LLM 生成分析文本，失败返回空"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        import openai as openai_lib
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if not api_key:
            return ""
        client = openai_lib.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            messages=[
                {"role": "system", "content": "你是一位专业的学习效果分析师。只输出JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.debug(f"LLM调用失败: {e}")
        return ""


def _parse_llm_json(raw: str) -> dict:
    """从 LLM 回复中提取 JSON"""
    if not raw:
        return {}
    json_match = re.search(r'\{[\s\S]*\}', raw)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return {}


# ══════════════════════════════════════════════════
# 综合 Dashboard
# ══════════════════════════════════════════════════

@router.get("/dashboard")
async def get_evaluation_dashboard(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
    days: int = 7,
):
    """
    AI学习效果评估中心 — 一站式返回六大模块数据
    """
    user_id = user.id
    now = _now_local()
    range_start = now - timedelta(days=days)
    range_start_utc = range_start.astimezone(timezone.utc)

    profile = await _get_profile(db, user_id)

    # ── 公共数据：考试记录 ──
    exam_result = await db.execute(
        select(ExamResult).where(
            ExamResult.user_id == user_id,
            ExamResult.completed_at >= range_start_utc,
        ).order_by(ExamResult.completed_at.desc())
    )
    exams = exam_result.scalars().all()

    # ── 公共数据：学习时长 ──
    sess_result = await db.execute(
        select(StudySession).where(
            StudySession.user_id == user_id,
            StudySession.started_at >= range_start_utc,
        )
    )
    sessions = sess_result.scalars().all()
    total_seconds_range = sum(s.duration_seconds or 0 for s in sessions)

    # ── 公共数据：学习行为 ──
    beh_result = await db.execute(
        select(LearningBehavior).where(
            LearningBehavior.user_id == user_id,
            LearningBehavior.created_at >= range_start_utc,
        )
    )
    behaviors = beh_result.scalars().all()

    return {
        # ── ① AI综合评估 ──
        "ai_summary": await _build_ai_summary(db, user_id, profile, exams, sessions, total_seconds_range, days),

        # ── ② 四个评分卡 ──
        "score_cards": await _build_score_cards(db, user_id, profile, exams, sessions, total_seconds_range),

        # ── ③ 学习行为分析 ──
        "behavior_analysis": await _build_behavior_analysis(db, user_id, sessions, behaviors, range_start_utc, days),

        # ── ④ AI智能诊断 ──
        "ai_diagnosis": await _build_ai_diagnosis(db, user_id, profile, exams, behaviors, sessions),

        # ── ⑤ 资源优化记录 ──
        "resource_optimization": await _build_resource_optimization(db, user_id, limit=10),

        # ── ⑥ 学习计划优化 ──
        "plan_optimization": await _build_plan_optimization(db, user_id, profile),
    }


# ══════════════════════════════════════════════════
# ① AI综合评估总评
# ══════════════════════════════════════════════════

async def _build_ai_summary(
    db, user_id, profile, exams, sessions, total_seconds, days
) -> dict:
    # 计算基础指标
    mastery = profile.get("knowledge_mastery", {})
    avg_mastery = round(sum(float(v) for v in mastery.values()) / max(len(mastery), 1), 1) if mastery else 0

    # 练习正确率
    total_q = sum((e.details and len(json.loads(e.details) if isinstance(e.details, str) else e.details or []) or 0) for e in exams)
    correct_q = 0
    for e in exams:
        details = e.details
        if isinstance(details, str):
            try: details = json.loads(details)
            except: continue
        if isinstance(details, list):
            correct_q += sum(1 for d in details if d.get("correct", True))
    correct_rate = round(correct_q / max(total_q, 1) * 100, 1)

    # 学习效率 = 完成节点数 / 学习小时数
    completed_result = await db.execute(
        select(sa_func.count(LearningProgress.id)).where(
            LearningProgress.user_id == user_id,
            LearningProgress.status == "completed",
        )
    )
    completed_count = completed_result.scalar() or 0
    hours = max(total_seconds / 3600, 0.1)
    efficiency = round(completed_count / hours * 10, 1)  # 归一化

    # 综合评分
    activity_score = float(profile.get("activity_score", 0))
    focus_score = float(profile.get("focus_score", 75))
    activity = min(100, max(0, activity_score))
    
    # 加权总分
    composite = round(
        avg_mastery * 0.30 +
        correct_rate * 0.25 +
        min(100, efficiency) * 0.20 +
        activity * 0.15 +
        focus_score * 0.10
    , 1)

    # 星级
    if composite >= 90: stars = 5
    elif composite >= 75: stars = 4
    elif composite >= 60: stars = 3
    elif composite >= 40: stars = 2
    else: stars = 1

    # 状态标签
    if composite >= 85: status_label = "优秀"
    elif composite >= 70: status_label = "良好"
    elif composite >= 50: status_label = "一般"
    else: status_label = "需关注"

    # 趋势
    trend = profile.get("mastery_trend", "stable")
    trend_label = {"improving": "持续进步中", "stable": "状态稳定", "declining": "略有下滑"}.get(trend, "")

    # ★ LLM 生成评语
    risk_factors = profile.get("risk_factors", [])
    weaknesses = profile.get("weaknesses", [])
    strengths = profile.get("strengths", [])

    # ★ 加载节点名称映射，确保传给 LLM 的是中文名
    await _get_node_name_map(db)
    cn_weaknesses = _translate_nodes(weaknesses)
    cn_strengths = _translate_nodes(strengths)

    llm_prompt = f"""请根据以下学生学习数据生成一段80-120字的AI评估评语：

- 综合评分: {composite}/100
- 知识掌握均分: {avg_mastery}
- 练习正确率: {correct_rate}%
- 学习效率: {efficiency}
- 活跃度: {activity}%
- 趋势: {trend_label}
- 风险因素: {json.dumps(risk_factors[:2], ensure_ascii=False)}
- 薄弱点: {json.dumps(cn_weaknesses[:2], ensure_ascii=False)}
- 强项: {json.dumps(cn_strengths[:2], ensure_ascii=False)}

要求：用温暖、专业的语调，像学习教练一样给出评价和鼓励。指出1-2个具体问题和1个建议。
返回JSON: {{"summary_text": "...", "highlight": "今日最亮点的一句话", "concern": "需要关注的一句话"}}"""

    llm_raw = await _call_llm(llm_prompt, max_tokens=400)
    llm_data = _parse_llm_json(llm_raw)

    # 获取今日推荐（下一个学习步骤）
    today_recommendation = await _get_today_recommendation(db, user_id, profile)

    return {
        "composite_score": composite,
        "stars": stars,
        "status_label": status_label,
        "trend_label": trend_label,
        "summary_text": llm_data.get("summary_text", f"本周学习状态{status_label}。学习积极性较高（{activity}%），建议持续关注薄弱环节。"),
        "highlight": llm_data.get("highlight", ""),
        "concern": llm_data.get("concern", ""),
        "today_recommendation": today_recommendation,
        "avg_mastery": avg_mastery,
        "correct_rate": correct_rate,
        "efficiency": efficiency,
        "activity": activity,
    }


async def _get_today_recommendation(db, user_id, profile) -> dict:
    """获取今日推荐学习内容"""
    # 找下一个未完成的学习计划步骤
    plan_result = await db.execute(
        select(LearningPlan).where(
            LearningPlan.user_id == user_id,
            LearningPlan.status == "active",
        ).order_by(desc(LearningPlan.created_at)).limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if plan:
        step_result = await db.execute(
            select(LearningPlanStep).where(
                LearningPlanStep.plan_id == plan.id,
                LearningPlanStep.step_status == "pending",
            ).order_by(LearningPlanStep.step_no).limit(1)
        )
        step = step_result.scalar_one_or_none()
        if step:
            return {
                "topic": step.topic,
                "description": step.description or "",
                "difficulty": step.difficulty,
                "estimated_minutes": step.estimated_minutes,
                "bloom_level": step.bloom_level,
            }

    # 无计划时，推荐弱项中掌握度最低的
    mastery = profile.get("knowledge_mastery", {})
    if mastery:
        sorted_m = sorted(mastery.items(), key=lambda x: float(x[1]))[:1]
        if sorted_m:
            topic_name, score = sorted_m[0]
            # ★ 翻译为中文名
            await _get_node_name_map(db)
            cn_topic = _node_name_cache.get(topic_name, topic_name) if _node_name_cache else topic_name
            return {
                "topic": cn_topic,
                "description": f"当前掌握度 {float(score):.0f}%，建议优先学习",
                "difficulty": "medium",
                "estimated_minutes": 30,
                "bloom_level": "理解",
                "node_id": topic_name,  # 保留原始 ID 供前端跳转
            }

    return {"topic": "数据结构基本概念", "description": "建议从基础开始学习", "difficulty": "easy", "estimated_minutes": 20, "bloom_level": "记忆"}


# ══════════════════════════════════════════════════
# ② 四个评分卡
# ══════════════════════════════════════════════════

async def _build_score_cards(db, user_id, profile, exams, sessions, total_seconds) -> dict:
    """计算四个评分卡"""

    # 1. 知识掌握率
    mastery = profile.get("knowledge_mastery", {})
    knowledge_score = round(sum(float(v) for v in mastery.values()) / max(len(mastery), 1), 1) if mastery else 0

    # 2. 练习效果（正确率）
    total_q = 0; correct_q = 0
    for e in exams:
        details = e.details
        if isinstance(details, str):
            try: details = json.loads(details)
            except: continue
        if isinstance(details, list):
            total_q += len(details)
            correct_q += sum(1 for d in details if d.get("correct", True))
    practice_score = round(correct_q / max(total_q, 1) * 100, 1)

    # 3. 知识保持率（最近7天同知识点前后测试对比）
    retention_score = await _calc_retention(db, user_id)

    # 4. 学习效率
    completed_result = await db.execute(
        select(sa_func.count(LearningProgress.id)).where(
            LearningProgress.user_id == user_id,
            LearningProgress.status == "completed",
        )
    )
    count = completed_result.scalar() or 0
    hours = max(total_seconds / 3600, 0.1)
    efficiency_score = min(100, round(count / hours * 10, 1))

    # 变化量（较上周）
    last_week_start = (_now_local() - timedelta(days=14)).astimezone(timezone.utc)
    this_week_start = (_now_local() - timedelta(days=7)).astimezone(timezone.utc)

    # 上周正确率
    lw_result = await db.execute(
        select(ExamResult).where(
            ExamResult.user_id == user_id,
            ExamResult.completed_at >= last_week_start,
            ExamResult.completed_at < this_week_start,
        )
    )
    lw_exams = lw_result.scalars().all()
    lw_total = 0; lw_correct = 0
    for e in lw_exams:
        details = e.details
        if isinstance(details, str):
            try: details = json.loads(details)
            except: continue
        if isinstance(details, list):
            lw_total += len(details)
            lw_correct += sum(1 for d in details if d.get("correct", True))
    lw_rate = round(lw_correct / max(lw_total, 1) * 100, 1)
    practice_delta = round(practice_score - lw_rate, 1) if lw_total > 0 else 0

    return {
        "knowledge_mastery": {
            "label": "知识掌握",
            "score": knowledge_score,
            "max": 100,
            "bar_width": knowledge_score,
            "description": "基于所有已学知识点的掌握程度综合评估",
        },
        "practice_effect": {
            "label": "练习效果",
            "score": practice_score,
            "max": 100,
            "bar_width": practice_score,
            "description": f"最近练习正确率",
            "delta": practice_delta,
            "delta_label": f"{'+' if practice_delta >= 0 else ''}{practice_delta}%",
        },
        "knowledge_retention": {
            "label": "知识保持率",
            "score": retention_score,
            "max": 100,
            "bar_width": retention_score,
            "description": "同一知识点7天内重复测试的保持程度",
        },
        "learning_efficiency": {
            "label": "学习效率",
            "score": efficiency_score,
            "max": 100,
            "bar_width": efficiency_score,
            "description": f"近7天完成{count}个学习节点，共{round(hours,1)}小时",
        },
    }


async def _calc_retention(db, user_id) -> float:
    """计算知识保持率：对比同一知识点前后两次测试成绩"""
    tz = _tz8()
    now_utc = datetime.now(timezone.utc)
    week_ago = now_utc - timedelta(days=7)
    two_weeks_ago = now_utc - timedelta(days=14)

    # 获取两周内的考试记录，按 node_id 分组
    result = await db.execute(
        select(ExamResult).where(
            ExamResult.user_id == user_id,
            ExamResult.completed_at >= two_weeks_ago,
        ).order_by(ExamResult.node_id, ExamResult.completed_at)
    )
    all_exams = result.scalars().all()

    # 按知识点分组
    by_node = {}
    for e in all_exams:
        if e.node_id not in by_node:
            by_node[e.node_id] = []
        by_node[e.node_id].append(e)

    retention_rates = []
    for node_id, node_exams in by_node.items():
        if len(node_exams) < 2:
            continue
        # 取最早的1-2次和最近的1-2次
        first_avg = sum(e.score or 0 for e in node_exams[:2]) / min(2, len(node_exams))
        last_avg = sum(e.score or 0 for e in node_exams[-2:]) / min(2, len(node_exams))
        if first_avg > 0:
            retention_rates.append(min(100, (last_avg / first_avg) * 100))

    if retention_rates:
        return round(sum(retention_rates) / len(retention_rates), 1)
    return 70  # 默认值（无足够数据时）


# ══════════════════════════════════════════════════
# ③ 学习行为分析
# ══════════════════════════════════════════════════

async def _build_behavior_analysis(db, user_id, sessions, behaviors, range_start_utc, days) -> dict:
    """构建行为分析数据"""

    # 热力图数据
    heatmap_data = []
    for s in sessions:
        if s.started_at:
            date_str = s.started_at.astimezone(_tz8()).strftime("%Y-%m-%d")
            secs = s.duration_seconds or 0
            heatmap_data.append({"date": date_str, "minutes": round(secs / 60, 1)})

    # 聚合每日
    daily_agg = {}
    for h in heatmap_data:
        d = h["date"]
        if d not in daily_agg:
            daily_agg[d] = 0
        daily_agg[d] += h["minutes"]

    heatmap = [
        {"date": d, "activity_level": min(100, int(m / 3))}
        for d, m in daily_agg.items()
    ]

    # 学习时段分布
    time_slots = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}  # 上午/下午/晚上/深夜
    for s in sessions:
        if s.started_at:
            h = s.started_at.astimezone(_tz8()).hour
            secs = s.duration_seconds or 0
            if 6 <= h < 12: time_slots["morning"] += secs
            elif 12 <= h < 18: time_slots["afternoon"] += secs
            elif 18 <= h < 24: time_slots["evening"] += secs
            else: time_slots["night"] += secs

    total_slot_secs = sum(time_slots.values()) or 1
    time_distribution = [
        {"label": f"上午 6-12时", "hours": round(time_slots["morning"] / 3600, 1), "percent": round(time_slots["morning"] / total_slot_secs * 100, 1)},
        {"label": f"下午 12-18时", "hours": round(time_slots["afternoon"] / 3600, 1), "percent": round(time_slots["afternoon"] / total_slot_secs * 100, 1)},
        {"label": f"晚上 18-24时", "hours": round(time_slots["evening"] / 3600, 1), "percent": round(time_slots["evening"] / total_slot_secs * 100, 1)},
        {"label": f"深夜 0-6时", "hours": round(time_slots["night"] / 3600, 1), "percent": round(time_slots["night"] / total_slot_secs * 100, 1)},
    ]

    # 资源使用占比
    resource_count = {}
    for b in behaviors:
        rt = b.resource_type or "其他"
        resource_count[rt] = resource_count.get(rt, 0) + (b.duration_seconds or 0)

    total_resource = sum(resource_count.values()) or 1
    resource_usage = [
        {"type": "视频课" if k == "video" else "文档资料" if k in ("notes", "ppt") else "题目练习" if k in ("quiz", "exercise") else "动画演示" if k == "animation" else "代码案例" if k == "code_example" else k,
         "key": k,
         "minutes": round(v / 60, 1),
         "percent": round(v / total_resource * 100, 1)}
        for k, v in sorted(resource_count.items(), key=lambda x: -x[1])[:6]
    ]

    # 总学习时长
    total_hours = round(sum(s.duration_seconds or 0 for s in sessions) / 3600, 1)
    session_count = len(sessions)

    # 本周每天活跃情况
    today = _now_local().date()
    week_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.isoformat()
        mins = daily_agg.get(d_str, 0)
        week_days.append({
            "date": d_str,
            "day_name": ["周一","周二","周三","周四","周五","周六","周日"][d.weekday()],
            "minutes": round(mins, 1),
            "is_today": i == 0,
        })

    return {
        "total_hours": total_hours,
        "session_count": session_count,
        "heatmap": heatmap,
        "time_distribution": time_distribution,
        "resource_usage": resource_usage,
        "week_days": week_days,
        "peak_hour_slot": max(time_distribution, key=lambda x: x["hours"])["label"].split()[0] if time_distribution else "晚上",
    }


# ══════════════════════════════════════════════════
# ④ AI智能诊断
# ══════════════════════════════════════════════════

async def _build_ai_diagnosis(db, user_id, profile, exams, behaviors, sessions) -> dict:
    """AI智能诊断 — 4张诊断卡"""

    weaknesses = profile.get("weaknesses", [])
    risk_factors = profile.get("risk_factors", [])
    risk_level = profile.get("risk_level", "low")
    mastery = profile.get("knowledge_mastery", {})

    # ★ AI发现：从行为数据中总结
    behavior_types = {}
    for b in behaviors:
        bt = b.behavior_type
        behavior_types[bt] = behavior_types.get(bt, 0) + 1

    video_count = behavior_types.get("watch_video", 0) + behavior_types.get("view_resource", 0)
    practice_count = behavior_types.get("complete_exercise", 0) + behavior_types.get("submit_answer", 0)

    # 判断趋势
    discovery_text = ""
    if video_count > practice_count * 2 and practice_count > 0:
        discovery_text = f"最近7天观看视频类资源占比偏高（{video_count}次），但练习正确率未同步提高。AI认为存在被动学习倾向。"
    elif len(sessions) < 3:
        discovery_text = "最近学习频率偏低，建议至少每天安排30分钟学习时间。"
    else:
        discovery_text = "学习行为整体稳定，各项指标在正常范围内。继续保持当前节奏。"

    # ★ AI预测：基于 masterty trend 估算
    prediction_text = ""
    low_mastery = [(k, float(v)) for k, v in mastery.items() if float(v) < 60]
    if low_mastery:
        top_low = sorted(low_mastery, key=lambda x: x[1])[0]
        prediction_text = f"如果保持当前学习方式，预计「{top_low[0]}」仍需约3小时的学习才能达到掌握水平。"

    # ★ AI风险
    risk_text = ""
    high_risk = [r for r in risk_factors[:2]]

    # ★ AI解释（XAI）
    explanation_text = ""
    if weaknesses:
        # 找推荐路径的理由
        explanation_text = f"推荐优先学习薄弱环节，帮助构建完整知识体系。"

    # 诊断卡数据
    diagnosis_cards = [
        {
            "id": "discovery",
            "title": "AI发现",
            "icon": "🔍",
            "content": discovery_text or "正在分析你的学习行为模式...",
            "type": "info",
        },
        {
            "id": "prediction",
            "title": "AI预测",
            "icon": "🔮",
            "content": prediction_text or "尚未积累足够数据来进行预测分析。",
            "type": "prediction",
        },
        {
            "id": "risk",
            "title": "学习风险",
            "icon": "⚠️",
            "content": f"风险等级：{'高风险' if risk_level == 'high' else '中等风险' if risk_level == 'medium' else '低风险'}。\n{'；'.join(high_risk) if high_risk else '当前未检测到显著的学习风险。'}",
            "risk_level": risk_level,
            "risk_factors": high_risk,
            "type": "warning" if risk_level in ("medium", "high") else "success",
        },
        {
            "id": "explanation",
            "title": "AI解释",
            "icon": "💡",
            "content": explanation_text or "AI根据你的知识图谱依赖关系，为你推荐最优学习路径。",
            "type": "info",
        },
    ]

    return {"cards": diagnosis_cards}


# ══════════════════════════════════════════════════
# ⑤ 资源优化记录
# ══════════════════════════════════════════════════

async def _build_resource_optimization(db, user_id, limit=10) -> dict:
    """获取AI资源优化调整记录"""
    result = await db.execute(
        select(ResourceAdjustment).where(
            ResourceAdjustment.user_id == user_id,
        ).order_by(desc(ResourceAdjustment.created_at)).limit(limit)
    )
    records = result.scalars().all()

    items = []
    for r in records:
        # 生成友好描述
        type_labels = {
            "resource_type_change": "资源类型调整",
            "difficulty_adjust": "难度调整",
            "path_reroute": "学习路径重规划",
            "practice_volume_adjust": "练习数量调整",
            "plan_reorder": "学习顺序调整",
        }

        from_desc = ""
        to_desc = ""
        if r.from_value:
            from_desc = r.from_value.get("resource_type", "") or r.from_value.get("topic", "") or str(r.from_value)
        if r.to_value:
            to_desc = r.to_value.get("resource_type", "") or r.to_value.get("topic", "") or str(r.to_value)

        items.append({
            "id": r.id,
            "date": r.created_at.astimezone(_tz8()).strftime("%m月%d日") if r.created_at else "",
            "type": r.adjustment_type,
            "type_label": type_labels.get(r.adjustment_type, r.adjustment_type),
            "from_value": r.from_value,
            "to_value": r.to_value,
            "from_desc": from_desc,
            "to_desc": to_desc,
            "reason": r.reason or "",
            "improvement": r.improvement,
            "metric_before": r.metric_before,
            "metric_after": r.metric_after,
        })

    return {
        "total": len(items),
        "items": items,
        "has_more": len(items) >= limit,
    }


# ══════════════════════════════════════════════════
# ⑥ 学习计划优化
# ══════════════════════════════════════════════════

async def _build_plan_optimization(db, user_id, profile) -> dict:
    """获取学习计划优化（流程化展示）"""
    # 找最新的活跃计划
    plan_result = await db.execute(
        select(LearningPlan).where(
            LearningPlan.user_id == user_id,
            LearningPlan.status == "active",
        ).order_by(desc(LearningPlan.created_at)).limit(1)
    )
    plan = plan_result.scalar_one_or_none()

    if not plan:
        # 生成默认路径
        return {
            "steps": _default_plan_steps(profile),
            "total_minutes": 90,
            "difficulty_stars": 3,
            "rationale": "基于你的当前水平，AI 推荐从基础知识入手，逐步深入。",
            "mastery_improvement": 10,
        }

    step_result = await db.execute(
        select(LearningPlanStep).where(
            LearningPlanStep.plan_id == plan.id,
        ).order_by(LearningPlanStep.step_no)
    )
    steps = step_result.scalars().all()

    step_items = []
    for s in steps:
        step_items.append({
            "step_no": s.step_no,
            "topic": s.topic,
            "description": s.description or "",
            "difficulty": s.difficulty or "medium",
            "bloom_level": s.bloom_level or "理解",
            "estimated_minutes": s.estimated_minutes or 20,
            "status": s.step_status or "pending",
            "score": s.score,
        })

    total_minutes = sum(s["estimated_minutes"] for s in step_items)

    # 难度星
    diffs = {"easy": 1, "medium": 2, "hard": 3, "expert": 4}
    avg_diff = sum(diffs.get(s["difficulty"], 2) for s in step_items) / max(len(step_items), 1)
    difficulty_stars = round(avg_diff)

    # 估算掌握度提升
    pending_count = sum(1 for s in step_items if s["status"] == "pending")
    mastery_improvement = min(30, pending_count * 5)

    # 解释原因
    weaknesses = profile.get("weaknesses", [])
    rationale = f"基于AI分析，当前学习路径聚焦{'、'.join(weaknesses[:1]) if weaknesses else '核心知识点'}，按依赖关系排序，确保先掌握基础再挑战进阶内容。"

    return {
        "steps": step_items or _default_plan_steps(profile),
        "total_minutes": total_minutes or 90,
        "difficulty_stars": difficulty_stars or 3,
        "rationale": rationale,
        "mastery_improvement": mastery_improvement or 10,
        "plan_status": plan.status if plan else "active",
    }


def _default_plan_steps(profile) -> list:
    """无计划时的默认学习路径"""
    weaknesses = profile.get("weaknesses", [])
    return [
        {"step_no": 1, "topic": "链表复习" if "链表" in str(weaknesses) else "顺序表基础", "description": "巩固线性结构基础", "difficulty": "easy", "bloom_level": "记忆", "estimated_minutes": 20, "status": "pending", "score": None},
        {"step_no": 2, "topic": "二叉树遍历", "description": "掌握前中后层序遍历", "difficulty": "medium", "bloom_level": "理解", "estimated_minutes": 30, "status": "pending", "score": None},
        {"step_no": 3, "topic": "DFS算法动画", "description": "通过动画理解递归与回溯", "difficulty": "medium", "bloom_level": "应用", "estimated_minutes": 15, "status": "pending", "score": None},
        {"step_no": 4, "topic": "综合练习", "description": "完成10道配套练习题", "difficulty": "hard", "bloom_level": "应用", "estimated_minutes": 25, "status": "pending", "score": None},
        {"step_no": 5, "topic": "AI效果评估", "description": "检测学习效果并调整方案", "difficulty": "medium", "bloom_level": "评估", "estimated_minutes": 10, "status": "pending", "score": None},
    ]


# ══════════════════════════════════════════════════
# 单独接口：记录资源调整
# ══════════════════════════════════════════════════

class LogAdjustmentRequest(BaseModel):
    adjustment_type: str
    from_value: dict = {}
    to_value: dict = {}
    trigger_event: str = ""
    reason: str = ""
    metric_name: str = ""
    metric_before: float = None
    metric_after: float = None


@router.post("/log-adjustment")
async def log_adjustment(
    req: LogAdjustmentRequest,
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """记录一次资源/计划调整"""
    improvement = None
    if req.metric_before is not None and req.metric_after is not None and req.metric_before > 0:
        improvement = round((req.metric_after - req.metric_before) / req.metric_before * 100, 1)

    adj = ResourceAdjustment(
        user_id=user.id,
        adjustment_type=req.adjustment_type,
        from_value=req.from_value,
        to_value=req.to_value,
        trigger_event=req.trigger_event,
        reason=req.reason,
        metric_name=req.metric_name,
        metric_before=req.metric_before,
        metric_after=req.metric_after,
        improvement=improvement,
    )
    db.add(adj)
    await db.commit()
    await db.refresh(adj)

    logger.info(f"📝 [调整记录] user={user.id} type={req.adjustment_type}")
    return {"message": "调整已记录", "adjustment_id": adj.id}
