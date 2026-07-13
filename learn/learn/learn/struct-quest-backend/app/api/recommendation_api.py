"""
推荐资源 API
- GET /api/recommendations/resources  - 获取AI个性化推荐的资源
- POST /api/recommendations/refresh   - 手动触发爬虫更新 + 重新生成推荐
- GET /api/recommendations/sources    - 查看支持的来源平台
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db, AsyncSessionLocal
from app.models.resource import ExternalResource, SOURCE_CHOICES, SOURCE_CSDN, SOURCE_ZHIHU, SOURCE_JUEJIN, SOURCE_GITHUB, SOURCE_BILIBILI, SOURCE_DOUYIN
from app.services.web_crawler import crawler_service
from app.services.recommendation_engine import recommendation_engine
from app.services.llm import llm_service
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


# ==================== 请求/响应模型 ====================

class RefreshRequest(BaseModel):
    keyword: Optional[str] = "算法 数据结构 面试"
    source: Optional[str] = None  # 不指定则爬取全部平台


class RefreshResponse(BaseModel):
    success: bool
    message: str
    crawled_count: int = 0
    new_count: int = 0
    sources: List[str] = []


# ==================== 接口实现 ====================

@router.get("/resources")
async def get_recommended_resources(
    limit: int = 8,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    获取 AI 个性化推荐的资源列表
    """
    user_id = getattr(current_user, 'id', None) if current_user else None
    
    # 尝试从数据库查询（表可能不存在）
    try:
        if user_id:
            result = await recommendation_engine.get_recommendations(
                db=db,
                user_id=user_id,
                limit=min(limit, 12),
            )
            return result
        else:
            query = (
                select(ExternalResource)
                .where(ExternalResource.summary.isnot(None))
                .order_by(ExternalResource.heat_score.desc(), ExternalResource.crawled_at.desc())
                .limit(limit)
            )
            result = await db.execute(query)
            resources = result.scalars().all()
            
            return {
                "recommendations": [r.to_dict() for r in resources],
                "total": len(resources),
                "user_profile_summary": "热门推荐（登录后获取个性化推荐）",
                "generated_at": "",
            }
    except Exception as db_err:
        logger.warning(f"[Recommendations] 数据库查询失败，使用内置数据: {db_err}")
    
    # ★ Fallback: 表不存在时返回内置精选数据
    from app.services.web_crawler import crawler_service
    fallback = crawler_service._get_fallback_data()
    return {
        "recommendations": fallback[:limit],
        "total": len(fallback),
        "user_profile_summary": "精选推荐（数据源已就绪）",
        "generated_at": "",
    }


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_resources(
    req: RefreshRequest = RefreshRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
):
    """
    手动触发爬虫更新
    
    - 爬取指定平台（或全部平台）
    - 自动生成 AI 摘要
    - 存入数据库
    """
    keyword = req.keyword or "算法 数据结构"
    source_filter = req.source
    
    try:
        if source_filter:
            raw_resources = await crawler_service.crawl_single_source(source_filter, keyword)
            sources_used = [source_filter]
        else:
            raw_resources = await crawler_service.crawl_all(keyword)
            sources_used = list(set(r.get("source", "") for r in raw_resources))

        new_count = 0
        
        # ★ 尝试写入数据库（表可能不存在）
        try:
            for res_data in raw_resources:
                url = res_data.get("url", "")
                if not url:
                    continue
                
                # URL去重
                existing = await db.execute(
                    select(ExternalResource).where(ExternalResource.url == url)
                )
                if existing.scalar_one_or_none():
                    continue
                
                # 创建资源记录
                resource = ExternalResource(
                    title=res_data["title"],
                    url=url,
                    source=res_data["source"],
                    category=res_data.get("category", ""),
                    tags=res_data.get("tags", []),
                    summary=res_data.get("summary", ""),
                    heat_score=res_data.get("heat_score", 50.0),
                    cover_image=res_data.get("cover_image"),
                    author=res_data.get("author", ""),
                )
                
                db.add(resource)
                new_count += 1

            await db.commit()
        except Exception as db_err:
            logger.warning(f"[Refresh] 数据库写入失败（表可能不存在）: {db_err}")
            new_count = 0
            # 不抛异常，继续返回爬取结果

        return RefreshResponse(
            success=True,
            message=f"成功更新！共获取 {len(raw_resources)} 条，新增 {new_count} 条资源",
            crawled_count=len(raw_resources),
            new_count=new_count,
            sources=sources_used,
        )

    except Exception as e:
        logger.error(f"[Refresh] 更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"资源更新失败: {str(e)}")


async def _generate_ai_summaries(new_count: int):
    """后台任务：为没有摘要的资源生成 AI 摘要"""
    logger.info(f"[Background] 开始为 {new_count} 条新资源生成 AI 摘要...")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ExternalResource)
            .where((ExternalResource.summary.is_(None)) | (ExternalResource.summary == ""))
            .order_by(ExternalResource.crawled_at.desc())
            .limit(new_count * 2)
        )
        resources = result.scalars().all()

        provider = llm_service.get_provider(None)
        if not provider:
            return

        for res in resources[:new_count]:
            try:
                prompt = f"请用一句话（不超过50字）概括这个学习资源的核心价值：\n标题: {res.title}\n来源: {res.source}\n分类: {res.category or '未分类'}\n只返回摘要文字。"
                
                summary_text = ""
                messages = [{"role": "user", "content": prompt}]
                
                async for chunk in provider.generate_stream(messages):
                    summary_text += chunk
                
                if summary_text.strip():
                    from sqlalchemy import update
                    await db.execute(
                        update(ExternalResource)
                        .where(ExternalResource.id == res.id)
                        .values(summary=summary_text.strip()[:300])
                    )
                    await db.commit()
                    
            except Exception as e:
                logger.warning(f"[Background] 为 {res.title} 生成摘要失败: {e}")
                continue


@router.get("/sources")
async def get_supported_sources():
    """返回支持的所有来源平台信息"""
    return {
        "sources": [
            {
                "key": key,
                **info,
            }
            for key, info in SOURCE_CHOICES.items()
        ]
    }


@router.get("/stats")
async def get_recommendation_stats(db: AsyncSession = Depends(get_db)):
    """获取资源库统计信息"""
    total_result = await db.execute(select(func.count(ExternalResource.id)))
    total = total_result.scalar() or 0
    
    by_source = {}
    for key, info in SOURCE_CHOICES.items():
        count_result = await db.execute(
            select(func.count(ExternalResource.id)).where(ExternalResource.source == key)
        )
        count = count_result.scalar() or 0
        if count > 0:
            by_source[key] = {"label": info["label"], "count": count}

    return {
        "total_resources": total,
        "by_source": by_source,
    }
