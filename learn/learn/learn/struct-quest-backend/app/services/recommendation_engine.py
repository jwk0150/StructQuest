"""
AI 推荐引擎
结合资源库 + 用户画像，使用 LLM 进行个性化推荐排序
"""

import json
import logging
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import ExternalResource, SOURCE_CHOICES, DIFFICULTY_BEGINNER, DIFFICULTY_INTERMEDIATE, DIFFICULTY_ADVANCED
from app.services.llm import llm_service
from app.services.user_profile import user_profile_service

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """AI 驱动的个性化推荐引擎"""

    # 推荐数量
    DEFAULT_LIMIT = 8
    MAX_CANDIDATES = 30

    async def get_recommendations(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = DEFAULT_LIMIT,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        获取个性化推荐资源列表
        
        参数:
            db: 数据库会话
            user_id: 用户ID
            limit: 返回数量
            force_refresh: 是否强制重新生成推荐理由
        """
        # 1. 获取用户画像
        try:
            profile = await user_profile_service.build_profile(db, user_id)
        except Exception as e:
            logger.warning(f"构建用户画像失败，使用默认画像: {e}")
            profile = self._default_profile()

        # 2. 获取候选资源集
        candidates = await self._get_candidates(db, profile, limit=self.MAX_CANDIDATES)
        
        if not candidates:
            return {
                "recommendations": [],
                "total": 0,
                "user_profile_summary": f"兴趣: {', '.join(profile.get('interests', ['算法', '数据结构'])[:3])}",
                "generated_at": datetime.now().isoformat(),
            }

        # 3. 使用 AI 对候选资源进行排序和生成推荐理由
        recommendations = await self._ai_rank_and_explain(candidates, profile, limit)

        # 4. 更新数据库中的推荐标记
        await self._mark_recommended(db, [r["id"] for r in recommendations])

        return {
            "recommendations": recommendations,
            "total": len(candidates),
            "user_profile_summary": (
                f"{profile.get('level', '').title()}水平 | "
                f"兴趣: {', '.join(profile.get('interests', ['算法'])[:3])}"
            ),
            "generated_at": datetime.now().isoformat(),
        }

    async def _get_candidates(
        self,
        db: AsyncSession,
        profile: Dict[str, Any],
        limit: int = 30,
    ) -> List[ExternalResource]:
        """获取候选资源集（基于画像初筛）"""
        query = (
            select(ExternalResource)
            .where(ExternalResource.summary.isnot(None))  # 有AI摘要的才考虑
            .order_by(
                ExternalResource.heat_score.desc(),
                ExternalResource.crawled_at.desc()
            )
            .limit(limit * 2)  # 多取一些用于筛选
        )

        result = await db.execute(query)
        resources = result.scalars().all()

        # 基于画像进行本地初筛
        interests = set(profile.get("interests", [])) | set(profile.get("recent_topics", []))
        weak_points = set(profile.get("weak_points", []))
        preferred_diff = profile.get("preferred_difficulty", ["medium"])
        
        diff_map = {"easy": DIFFICULTY_BEGINNER, "medium": DIFFICULTY_INTERMEDIATE, "hard": DIFFICULTY_ADVANCED}

        scored_resources = []
        for res in resources:
            score = res.heat_score or 50.0

            # 兴趣匹配加分
            res_tags = set(res.tags or [])
            if interests & res_tags:
                score += 20
            elif any(i.lower() in (res.title or "").lower() for i in list(interests)[:3]):
                score += 10

            # 薄弱点相关也加分（需要补强）
            if weak_points & res_tags:
                score += 15

            # 难度偏好匹配
            target_diff = diff_map.get(preferred_diff[0], DIFFICULTY_INTERMEDIATE)
            if res.difficulty == target_diff:
                score += 10
            elif res.difficulty in [diff_map.get(d) for d in preferred_diff]:
                score += 5

            # 来源多样性：最近爬取的新鲜内容加分
            if res.crawled_at and (datetime.now() - res.crawled_at.replace(tzinfo=None) < timedelta(days=3)):
                score += 8

            scored_resources.append((score, res))

        # 按综合得分排序，取 top N
        scored_resources.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored_resources[:limit]]

    async def _ai_rank_and_explain(
        self,
        candidates: List[ExternalResource],
        profile: Dict[str, Any],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        使用 LLM 对候选资源进行最终排序并生成推荐理由
        """
        # 准备发给 LLM 的候选信息（限制token）
        candidate_texts = []
        for i, c in enumerate(candidates[:16]):  # 最多16条给LLM排序
            src_info = SOURCE_CHOICES.get(c.source, {})
            candidate_texts.append(
                f"[{i+1}] 标题:{c.title}\n   来源:{src_info.get('label', c.source)}\n"
                f"   摘要:{c.summary or '暂无'}\n"
                f"   分类:{c.category or '通用'}\n   热度:{c.heat_score:.0f}"
            )

        prompt = f"""你是一个智能学习资源推荐助手。请根据用户画像，对以下外部学习资源进行评估排序。

## 用户画像
- 学习水平: {profile.get('level', 'intermediate')}
- 兴趣领域: {', '.join(profile.get('interests', ['算法', '数据结构'])[:5])}
- 薄弱环节: {', '.join(profile.get('weak_points', [])[:3]) or '无明显薄弱点'}
- 学习目标: {profile.get('goal', '提升编程能力')}
- 偏好难度: {', '.join(profile.get('preferred_difficulty', ['medium']))}

## 候选资源
{chr(10).join(candidate_texts)}

## 任务要求
1. 从以上资源中选出最符合该用户的 Top {min(limit, len(candidates))} 条
2. 返回 JSON 数组格式，每项包含：
   - id: 资源序号（对应上面的编号）
   - reason: 一句话中文推荐理由（不超过30字），说明为什么适合这个用户
3. 只返回JSON，不要其他文字

返回示例：
{{"rankings":[{{"id":3,"reason":"正好覆盖你的薄弱点-动态规划"}},{{"id":7,"reason":"B站高播放量教程，适合视觉学习者"}}]}}"""

        try:
            # 调用 LLM
            response_text = ""
            messages = [{"role": "user", "content": prompt}]
            
            provider = llm_service.get_provider("deepseek") or llm_service.get_provider(None)
            if provider:
                async for chunk in provider.generate_stream(messages):
                    response_text += chunk
                
                # 解析 LLM 返回的 JSON
                rankings = self._parse_ai_response(response_text)
                
                if rankings:
                    # 根据 AI 排序结果重组推荐列表
                    result = []
                    seen_ids = set()
                    
                    for ranking in rankings:
                        idx = ranking.get("id", 0) - 1  # 序号转索引
                        reason = ranking.get("reason", "")
                        
                        if 0 <= idx < len(candidates) and idx not in seen_ids:
                            res = candidates[idx]
                            seen_ids.add(idx)
                            d = res.to_dict()
                            d["ai_recommend_reason"] = reason
                            result.append(d)
                    
                    # 补充未进入AI排名但质量不错的资源
                    for i, c in enumerate(candidates):
                        if i not in seen_ids and len(result) < limit:
                            d = c.to_dict()
                            d["ai_recommend_reason"] = f"{SOURCE_CHOICES.get(c.source, {}).get('label', '')}热门资源"
                            result.append(d)
                    
                    return result[:limit]

        except Exception as e:
            logger.error(f"[RecommendationEngine] AI 排序失败: {e}")

        # AI 失败时降级为基于规则的排序
        fallback = []
        for c in candidates[:limit]:
            d = c.to_dict()
            d["ai_recommend_reason"] = f"热门{d.get('source_label','')}资源"
            fallback.append(d)
        return fallback

    def _parse_ai_response(self, text: str) -> List[Dict[str, str]]:
        """解析 LLM 返回的 JSON 排名结果"""
        text = text.strip()
        
        # 尝试提取 JSON
        json_match = None
        for pattern in [r'\{[\s\S]*\}', r'"rankings"\s*:\s*\[[\s\S]*\]']:
            import re
            m = re.search(pattern, text)
            if m:
                json_match = m.group()
                break
        
        if not json_match:
            # 尝试直接解析整个文本
            json_match = text
        
        try:
            data = json.loads(json_match)
            if isinstance(data, dict):
                return data.get("rankings", [])
            elif isinstance(data, list):
                return data
        except (json.JSONDecodeError, TypeError):
            pass

        return []

    async def _mark_recommended(self, db: AsyncSession, resource_ids: List[int]):
        """标记资源已被推荐"""
        if not resource_ids:
            return
        from sqlalchemy import update
        stmt = (
            update(ExternalResource)
            .where(ExternalResource.id.in_(resource_ids))
            .values(is_recommended=True)
        )
        await db.execute(stmt)
        await db.commit()

    def _default_profile(self) -> Dict[str, Any]:
        """默认用户画像（当无法获取真实画像时）"""
        return {
            "level": "intermediate",
            "interests": ["算法", "数据结构", "面试"],
            "weak_points": [],
            "goal": "exploration",
            "preferred_difficulty": ["medium"],
            "active_hours": "unknown",
            "recent_topics": ["算法", "数据结构"],
            "total_study_hours": 0,
        }


# 全局实例
recommendation_engine = RecommendationEngine()
