"""
用户画像服务
从用户的学习记录、考试结果、学习会话中提取画像维度
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning_progress import LearningProgress
from app.models.study_session import StudySession
from app.models.exam_result import ExamResult
from app.models.user import User

logger = logging.getLogger(__name__)


class UserProfileService:
    """用户画像分析与生成器"""

    # 难度映射
    DIFFICULTY_MAP = {
        1: "beginner",
        2: "beginner", 
        3: "intermediate",
        4: "intermediate",
        5: "advanced",
        6: "advanced",
    }

    async def build_profile(self, db: AsyncSession, user_id: int) -> Dict[str, Any]:
        """
        构建完整用户画像
        
        返回:
        {
            "interests": ["二叉树", "动态规划"],      # 兴趣领域（最近学习的）
            "weak_points": ["红黑树", "KMP算法"],       # 薄弱点（错题/低分）
            "level": "intermediate",                    # 整体水平
            "goal": "exam",                             # 学习目标
            "preferred_difficulty": ["medium", "hard"],  # 偏好难度
            "active_hours": "evening",                  # 活跃时段
            "recent_topics": ["图论", "动态规划"],       # 最近关注话题
            "learning_streak": 7,                       # 连续学习天数
            "total_study_hours": 12.5                   # 总学习时长(h)
        }
        """
        # 并行获取各类数据
        progress_result = await db.execute(
            select(LearningProgress)
            .where(LearningProgress.user_id == user_id)
            .order_by(LearningProgress.updated_at.desc())
            .limit(50)
        )
        all_progress = progress_result.scalars().all()

        sessions_result = await db.execute(
            select(StudySession)
            .where(StudySession.user_id == user_id)
            .order_by(StudySession.started_at.desc())
            .limit(30)
        )
        sessions = sessions_result.scalars().all()

        exams_result = await db.execute(
            select(ExamResult)
            .where(ExamResult.user_id == user_id)
            .order_by(ExamResult.completed_at.desc())
            .limit(20)
        )
        exams = exams_result.scalars().all()

        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        # 构建各维度
        profile = {
            "user_id": user_id,
            **self._extract_interests(all_progress),
            **self._extract_weak_points(exams),
            **self._analyze_level(all_progress, exams),
            **self._detect_goal(user, sessions),
            **self._analyze_habits(sessions),
            **self._calc_stats(sessions),
        }

        logger.info(f"[UserProfile] 为用户 {user_id} 生成画像: level={profile.get('level')}, interests={len(profile.get('interests', []))}个")
        return profile

    def _extract_interests(self, progress_list: List[LearningProgress]) -> Dict[str, Any]:
        """从学习进度中提取兴趣领域"""
        topics = []
        for p in progress_list[:15]:
            if hasattr(p, 'node_id') and p.node_id:
                topics.append(str(p.node_id))
        
        # 最近学习的主题权重更高
        recent = topics[:8]
        older = topics[8:]
        
        interest_counter = Counter(recent + older)  # recent 权重更高（出现两次）
        
        return {
            "interests": [t for t, _ in interest_counter.most_common(10)],
            "recent_topics": recent[:6],
        }

    def _extract_weak_points(self, exams: List[ExamResult]) -> Dict[str, Any]:
        """从考试结果中提取薄弱点"""
        weak_topics = []
        
        for exam in exams:
            # 低分题目/章节作为薄弱点
            if exam.score is not None and exam.score < 70:  # 低于70分视为薄弱
                if hasattr(exam, 'chapter_id') and exam.chapter_id:
                    weak_topics.append(f"chapter_{exam.chapter_id}")
            
            # 从错误答案中推断
            if hasattr(exam, 'answers') and exam.answers:
                try:
                    answers = exam.answers if isinstance(exam.answers, dict) else {}
                    for qid, answer_data in answers.items():
                        if isinstance(answer_data, dict):
                            if not answer_data.get("is_correct", True):  # 答错的题
                                if answer_data.get("topic"):
                                    weak_topics.append(answer_data["topic"])
                except (TypeError, AttributeError):
                    pass

        weak_counter = Counter(weak_topics)
        return {
            "weak_points": [t for t, _ in weak_counter.most_common(8)] if weak_topics else [],
        }

    def _analyze_level(self, progress_list: List[LearningProgress], exams: List[ExamResult]) -> Dict[str, Any]:
        """分析用户整体水平"""
        # 基于已掌握的节点数和平均分数判断
        mastered_count = sum(1 for p in progress_list if getattr(p, 'status', '') == 'mastered')
        total_unique_nodes = len(set(getattr(p, 'node_id', None) for p in progress_list) - {None})
        
        avg_exam_score = 0
        if exams:
            scores = [e.score for e in exams if e.score is not None]
            avg_exam_score = sum(scores) / len(scores) if scores else 0

        # 综合判定
        if mastered_count >= 20 or avg_exam_score >= 85:
            level = "advanced"
            pref_diff = ["hard"]
        elif mastered_count >= 8 or avg_exam_score >= 65:
            level = "intermediate"
            pref_diff = ["medium", "hard"]
        else:
            level = "beginner"
            pref_diff = ["easy", "medium"]

        return {
            "level": level,
            "preferred_difficulty": pref_diff,
            "avg_exam_score": round(avg_exam_score, 1),
            "mastered_count": mastered_count,
        }

    def _detect_goal(self, user: Optional[User], sessions: List[StudySession]) -> Dict[str, Any]:
        """检测用户学习目标"""
        if user and user.learning_mode:
            from app.models.user import LEARNING_MODE_EXAM, LEARNING_MODE_BEGINNER, LEARNING_MODE_BASIC
            mode_map = {
                LEARNING_MODE_EXAM: "exam",
                LEARNING_MODE_BEGINNER: "interview",
                LEARNING_MODE_BASIC: "exploration",
            }
            goal = mode_map.get(user.learning_mode, "exploration")
        else:
            # 根据行为推测
            has_exams = any(True for _ in sessions[:5])
            goal = "exam" if has_exams else "exploration"

        return {"goal": goal}

    def _analyze_habits(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """分析学习习惯"""
        hour_counts = Counter()
        active_days = set()
        
        for s in sessions[:30]:
            started_at = s.started_at
            if not started_at:
                continue
            
            if hasattr(started_at, 'hour'):
                hour_counts[started_at.hour] += 1
            elif isinstance(started_at, str):
                try:
                    dt = datetime.fromisoformat(started_at)
                    hour_counts[dt.hour] += 1
                    active_days.add(dt.date())
                except (ValueError, TypeError):
                    pass

        # 判断活跃时段
        if hour_counts:
            morning = sum(hour_counts.get(h, 0) for h in range(6, 12))
            afternoon = sum(hour_counts.get(h, 0) for h in range(12, 18))
            evening = sum(hour_counts.get(h, 0) for h in range(18, 24))
            
            counts = {"morning": morning, "afternoon": afternoon, "evening": evening}
            active_hours = max(counts, key=counts.get)
        else:
            active_hours = "unknown"

        return {"active_hours": active_hours}

    def _calc_stats(self, sessions: List[StudySession]) -> Dict[str, Any]:
        """计算学习统计数据"""
        total_seconds = 0
        today_sessions = []
        week_ago = datetime.now() - timedelta(days=7)

        for s in sessions:
            duration = getattr(s, 'duration_seconds', None)
            if duration:
                total_seconds += duration

            started_at = s.started_at
            if started_at:
                try:
                    if isinstance(started_at, str):
                        st = datetime.fromisoformat(started_at)
                    elif hasattr(started_at, 'timestamp'):
                        st = started_at
                    else:
                        continue
                    
                    if st.date() == datetime.now().date():
                        today_sessions.append(st)
                except (ValueError, TypeError, AttributeError):
                    pass

        total_hours = round(total_seconds / 3600, 1)

        return {
            "total_study_hours": total_hours,
            "today_session_count": len(today_sessions),
        }


# 全局实例
user_profile_service = UserProfileService()
