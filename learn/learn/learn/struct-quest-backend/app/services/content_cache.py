"""
内容缓存服务 — 三层缓存架构（SQLite 精确匹配 + ChromaDB 语义匹配 + Redis 可选）

核心理念：
- AI 生成的所有资源都被缓存下来，下次请求直接从缓存返回
- 精确匹配：SHA256(topic + resource_type + subject) 哈希键查 SQLite
- 语义匹配：向量化查询 → ChromaDB 相似度匹配 → 阈值 > 0.92 复用
- 自动入库：LLM 生成完成后，后台异步写入 SQLite + ChromaDB + Redis

使用方式：
    from app.services.content_cache import ContentCacheService
    cache = ContentCacheService()

    # 查询缓存
    cached = await cache.get_cache("notes", "链表", "数据结构")
    if cached:
        return cached  # 命中，直接返回

    # 生成后写入缓存
    content = await llm_generate(...)
    await cache.save_cache("notes", "链表", "数据结构", content)
"""
import hashlib
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger("content_cache")

# 语义匹配阈值（余弦距离，越小越相似）
SEMANTIC_SIMILARITY_THRESHOLD = 0.92  # ChromaDB 使用 cosine 距离，需要转换为相似度


class ContentCacheService:
    """
    三层缓存架构

    L1: Redis (可选，<1ms)
    L2: SQLite 精确哈希匹配 (<5ms)
    L3: ChromaDB 语义相似匹配 (<100ms)
    L4: 兜底 → LLM 生成后自动写入 L1+L2+L3
    """

    def __init__(self):
        self._rag_service = None
        self._redis = None
        self._redis_available = False

    # ═══════════════════════════════════════════
    #  缓存键生成
    # ═══════════════════════════════════════════

    @staticmethod
    def _cache_key(resource_type: str, topic: str, subject: str) -> str:
        """生成精确匹配缓存键"""
        raw = f"{subject}::{topic}::{resource_type}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _semantic_query(resource_type: str, topic: str, subject: str) -> str:
        """生成语义检索查询"""
        return f"{subject} {topic} {resource_type} 学习资源"

    # ═══════════════════════════════════════════
    #  查询缓存（三层逐步查询）
    # ═══════════════════════════════════════════

    async def get_cache(
        self, resource_type: str, topic: str, subject: str = "数据结构"
    ) -> Optional[str]:
        """
        三层缓存查询：精确 → 语义 → None

        返回命中的内容文本，未命中返回 None。
        完全兼容 SQLite 异步环境（FastAPI + aiosqlite 无事件循环冲突）。
        """
        cache_key = self._cache_key(resource_type, topic, subject)

        # ── L1: Redis ──
        redis_result = await self._get_from_redis(cache_key)
        if redis_result:
            logger.info("⚡ L1 命中(Redis): %s/%s/%s", resource_type, topic, subject)
            return redis_result

        # ── L2: SQLite 精确哈希匹配 ──
        sqlite_result = await self._get_from_sqlite(resource_type, topic, subject, cache_key)
        if sqlite_result:
            logger.info("💾 L2 命中(SQLite精确): %s/%s/%s", resource_type, topic, subject)
            # 回写 Redis
            asyncio.ensure_future(self._set_to_redis(cache_key, sqlite_result))
            return sqlite_result

        # ── L3: ChromaDB 语义相似匹配 ──
        semantic_result = await self._get_from_chromadb(resource_type, topic, subject)
        if semantic_result:
            logger.info("🧠 L3 命中(ChromaDB语义): %s/%s/%s", resource_type, topic, subject)
            # 回写 SQLite + Redis
            asyncio.ensure_future(self._save_to_sqlite(resource_type, topic, subject, cache_key, semantic_result))
            asyncio.ensure_future(self._set_to_redis(cache_key, semantic_result))
            return semantic_result

        logger.info("❌ 缓存未命中: %s/%s/%s", resource_type, topic, subject)
        return None

    # ═══════════════════════════════════════════
    #  写入缓存（三层全部写入）
    # ═══════════════════════════════════════════

    async def save_cache(
        self, resource_type: str, topic: str, subject: str, content: str
    ) -> None:
        """
        生成完成后，将内容写入所有缓存层。
        使用 asyncio.create_task 后台异步写入，不阻塞主流程。
        """
        cache_key = self._cache_key(resource_type, topic, subject)

        logger.info("📝 写入缓存: %s/%s/%s (%d 字符)", resource_type, topic, subject, len(content))

        # 并行写入三层
        tasks = [
            self._save_to_sqlite(resource_type, topic, subject, cache_key, content),
            self._save_to_chromadb(resource_type, topic, subject, content),
            self._set_to_redis(cache_key, content),
        ]
        # 不使用 await gather，允许部分失败不影响整体
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning("缓存写入层%d失败: %s", i + 1, r)

    # ═══════════════════════════════════════════
    #  L1: Redis 实现
    # ═══════════════════════════════════════════

    async def _ensure_redis(self):
        """懒初始化 Redis 连接"""
        if self._redis is not None:
            return
        try:
            from app.db.session import get_redis
            self._redis = await get_redis()
            if self._redis:
                self._redis_available = True
                logger.info("✅ Redis 缓存层可用")
            else:
                logger.info("ℹ️ Redis 不可用，跳过 L1 缓存")
        except Exception as e:
            logger.info("ℹ️ Redis 连接失败: %s", e)

    async def _get_from_redis(self, cache_key: str) -> Optional[str]:
        """从 Redis 读取缓存（24h TTL）"""
        if not self._redis_available:
            await self._ensure_redis()
        if not self._redis_available or not self._redis:
            return None
        try:
            val = await self._redis.get(f"cache:{cache_key}")
            return val if val else None
        except Exception:
            return None

    async def _set_to_redis(self, cache_key: str, content: str) -> None:
        """写入 Redis（24h TTL）"""
        if not self._redis_available:
            await self._ensure_redis()
        if not self._redis_available or not self._redis:
            return
        try:
            await self._redis.setex(f"cache:{cache_key}", 86400, content)
        except Exception as e:
            logger.debug("Redis 写入失败: %s", e)

    # ═══════════════════════════════════════════
    #  L2: SQLite 实现（使用现有 ResourceAsset 表）
    # ═══════════════════════════════════════════

    async def _get_from_sqlite(
        self, resource_type: str, topic: str, subject: str, cache_key: str
    ) -> Optional[str]:
        """从 SQLite 精确匹配查询"""
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import select, func
            from app.models.learning_ecosystem import ResourceAsset

            async with AsyncSessionLocal() as db:
                # 尝试用缓存键查
                result = await db.execute(
                    select(ResourceAsset).where(
                        ResourceAsset.asset_type == resource_type,
                        ResourceAsset.topic == topic,
                        ResourceAsset.subject == subject,
                        ResourceAsset.review_status.in_(["approved", "pending"]),
                    )
                    .order_by(ResourceAsset.quality_score.desc().nullslast())
                    .limit(1)
                )
                asset = result.scalar_one_or_none()

                if asset and asset.content_text:
                    # 更新使用计数
                    try:
                        meta = dict(asset.metadata_json or {})
                        meta["cache_hits"] = meta.get("cache_hits", 0) + 1
                        meta["last_used_at"] = datetime.now().isoformat()
                        asset.metadata_json = meta
                        await db.commit()
                    except Exception:
                        pass
                    return asset.content_text

                return None
        except Exception as e:
            logger.debug("SQLite 缓存查询失败: %s", e)
            return None

    async def _save_to_sqlite(
        self, resource_type: str, topic: str, subject: str, cache_key: str, content: str
    ) -> None:
        """写入 SQLite（使用 ResourceAsset 表）"""
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import select
            from app.models.learning_ecosystem import ResourceAsset

            async with AsyncSessionLocal() as db:
                # 检查是否已存在
                result = await db.execute(
                    select(ResourceAsset).where(
                        ResourceAsset.asset_type == resource_type,
                        ResourceAsset.topic == topic,
                        ResourceAsset.subject == subject,
                    )
                )
                existing = result.scalar_one_or_none()

                if existing:
                    # 更新已有记录
                    existing.content_text = content
                    existing.review_status = "pending"
                    existing.metadata_json = {
                        **(existing.metadata_json or {}),
                        "cache_key": cache_key,
                        "updated_at": datetime.now().isoformat(),
                        "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                    }
                else:
                    # 新建记录
                    asset = ResourceAsset(
                        asset_type=resource_type,
                        topic=topic,
                        subject=subject,
                        content_text=content,
                        source_type="system",
                        title=f"{resource_type}: {topic}",
                        review_status="pending",
                        quality_score=80,  # 默认质量分
                        metadata_json={
                            "cache_key": cache_key,
                            "created_at": datetime.now().isoformat(),
                            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                        },
                    )
                    db.add(asset)

                await db.commit()
                logger.debug("SQLite 缓存写入成功: %s", cache_key[:16])
        except Exception as e:
            logger.warning("SQLite 缓存写入失败: %s", e)

    # ═══════════════════════════════════════════
    #  L3: ChromaDB 语义缓存实现
    # ═══════════════════════════════════════════

    def _get_rag_service(self):
        """获取 RAG 服务实例"""
        if self._rag_service is None:
            from app.services.rag import rag_service
            self._rag_service = rag_service
        return self._rag_service

    async def _get_from_chromadb(
        self, resource_type: str, topic: str, subject: str
    ) -> Optional[str]:
        """从 ChromaDB 做语义相似匹配"""
        try:
            rag = self._get_rag_service()
            query = self._semantic_query(resource_type, topic, subject)

            # 使用带分数的检索
            results = rag.retrieve_with_scores(query, k=3)
            if not results:
                return None

            # 余弦距离 → 相似度 = 1 - distance
            # 检查是否有高相似度结果
            for r in results:
                score = r.get("score", 999)
                similarity = 1.0 - score  # 转换为相似度
                if similarity >= SEMANTIC_SIMILARITY_THRESHOLD:
                    logger.debug("ChromaDB 语义匹配: 相似度=%.4f", similarity)
                    return r["content"]

            return None
        except Exception as e:
            logger.debug("ChromaDB 语义查询失败: %s", e)
            return None

    async def _save_to_chromadb(
        self, resource_type: str, topic: str, subject: str, content: str
    ) -> None:
        """将 AI 生成的内容写入 ChromaDB 向量库"""
        try:
            rag = self._get_rag_service()
            collection = rag._get_collection()
            if not collection:
                logger.warning("ChromaDB 集合未初始化，跳过向量缓存")
                return

            from app.services.rag import EmbeddingClient

            # 先删除旧的同类内容（可选：避免重复）
            existing = collection.get(
                where={"$and": [
                    {"cache_type": resource_type},
                    {"cache_topic": topic},
                ]},
                include=[]
            )
            existing_ids = existing.get("ids", []) if existing else []
            if existing_ids:
                collection.delete(ids=existing_ids)
                logger.debug("清理旧向量缓存: %d 条", len(existing_ids))

            # 切分内容
            text_splitter = rag.text_splitter
            from langchain_core.documents import Document as LCDocument
            docs = text_splitter.split_documents([
                LCDocument(page_content=content, metadata={
                    "cache_type": resource_type,
                    "cache_topic": topic,
                    "cache_subject": subject,
                    "source": "ai_generated",
                })
            ])

            if not docs:
                return

            # 向量化
            texts = [d.page_content for d in docs]
            emb_client = EmbeddingClient()
            embeddings = emb_client.embed_documents(texts)

            # 入库
            import uuid
            ids = [f"ai_{resource_type}_{topic}_{uuid.uuid4().hex[:8]}_{i}" for i in range(len(docs))]
            metadatas = [{
                "cache_type": resource_type,
                "cache_topic": topic,
                "cache_subject": subject,
                "source": "ai_generated",
                "chunk_index": str(i),
            } for i in range(len(docs))]

            # 分批写入
            batch_size = 50
            for i in range(0, len(texts), batch_size):
                end = min(i + batch_size, len(texts))
                collection.add(
                    ids=ids[i:end],
                    documents=texts[i:end],
                    embeddings=embeddings[i:end],
                    metadatas=metadatas[i:end],
                )

            logger.info("✅ ChromaDB 向量缓存写入: %d chunks (type=%s, topic=%s)",
                        len(docs), resource_type, topic)
        except Exception as e:
            logger.warning("ChromaDB 向量缓存写入失败: %s", e)

    # ═══════════════════════════════════════════
    #  管理 API：缓存统计与清理
    # ═══════════════════════════════════════════

    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        stats = {"sqlite": {"count": 0}, "chromadb": {"count": 0}, "redis": {"available": False}}
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import select, func
            from app.models.learning_ecosystem import ResourceAsset

            async with AsyncSessionLocal() as db:
                total = await db.execute(select(func.count(ResourceAsset.id)))
                stats["sqlite"]["count"] = total.scalar() or 0

                # 统计各类型
                type_result = await db.execute(
                    select(ResourceAsset.asset_type, func.count(ResourceAsset.id))
                    .group_by(ResourceAsset.asset_type)
                )
                stats["sqlite"]["by_type"] = {
                    row[0]: row[1] for row in type_result.all()
                }

            # ChromaDB 统计
            try:
                rag = self._get_rag_service()
                collection = rag._get_collection()
                if collection:
                    count = collection.count()
                    stats["chromadb"]["count"] = count
                    all_meta = collection.get(include=["metadatas"])
                    metadatas = all_meta.get("metadatas") or []
                    ai_count = sum(1 for m in metadatas if m and m.get("source") == "ai_generated")
                    stats["chromadb"]["ai_generated_chunks"] = ai_count
                    stats["chromadb"]["uploaded_chunks"] = count - ai_count
            except Exception:
                pass

            # Redis 状态
            await self._ensure_redis()
            stats["redis"]["available"] = self._redis_available
        except Exception as e:
            stats["error"] = str(e)

        return stats

    async def invalidate_cache(
        self, resource_type: str = None, topic: str = None, subject: str = None
    ) -> Dict[str, Any]:
        """清除缓存（支持按类型/主题/学科过滤）"""
        deleted = {"sqlite": 0, "chromadb": 0, "redis": 0}
        try:
            from app.db.session import AsyncSessionLocal
            from sqlalchemy import delete
            from app.models.learning_ecosystem import ResourceAsset

            async with AsyncSessionLocal() as db:
                stmt = delete(ResourceAsset)
                if resource_type:
                    stmt = stmt.where(ResourceAsset.asset_type == resource_type)
                if topic:
                    stmt = stmt.where(ResourceAsset.topic == topic)
                if subject:
                    stmt = stmt.where(ResourceAsset.subject == subject)
                result = await db.execute(stmt)
                deleted["sqlite"] = result.rowcount
                await db.commit()

            # ChromaDB 清理
            if resource_type and topic:
                try:
                    rag = self._get_rag_service()
                    collection = rag._get_collection()
                    if collection:
                        existing = collection.get(
                            where={"$and": [
                                {"cache_type": resource_type},
                                {"cache_topic": topic},
                            ]},
                            include=[]
                        )
                        existing_ids = existing.get("ids", []) if existing else []
                        if existing_ids:
                            collection.delete(ids=existing_ids)
                            deleted["chromadb"] = len(existing_ids)
                except Exception:
                    pass
        except Exception as e:
            logger.error("缓存清除失败: %s", e)
            deleted["error"] = str(e)

        return {"message": "缓存已清除", "deleted": deleted}


# 全局单例
cache_service = ContentCacheService()
