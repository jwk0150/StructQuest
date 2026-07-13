import json
import logging
from typing import Optional, Any, List
from app.db.session import get_redis

logger = logging.getLogger(__name__)


class CacheService:
    """Redis 缓存服务"""

    # ===== 基础操作 =====

    @staticmethod
    async def get(key: str) -> Any:
        """获取缓存"""
        try:
            redis = await get_redis()
            if not redis:
                return None
            value = await redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"[Cache] GET {key} 失败: {e}")
            return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = 3600):
        """设置缓存（默认1小时过期）"""
        try:
            redis = await get_redis()
            if not redis:
                return
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            await redis.set(key, value, ex=ttl)
            logger.debug(f"[Cache] SET {key} TTL={ttl}s")
        except Exception as e:
            logger.error(f"[Cache] SET {key} 失败: {e}")

    @staticmethod
    async def delete(key: str):
        """删除缓存"""
        try:
            redis = await get_redis()
            if redis:
                await redis.delete(key)
        except Exception as e:
            logger.error(f"[Cache] DEL {key} 失败: {e}")

    @staticmethod
    async def exists(key: str) -> bool:
        """检查缓存是否存在"""
        try:
            redis = await get_redis()
            if redis:
                return await redis.exists(key) > 0
            return False
        except Exception:
            return False

    # ===== 用户相关缓存 =====
    USER_SESSION_PREFIX = "user:sessions:"      # 用户的所有聊天会话列表
    CHAT_MESSAGES_PREFIX = "chat:messages:"     # 某个聊天的消息列表
    USER_CONTENTS_PREFIX = "user:contents:"     # 用户生成的所有内容
    ONLINE_USERS_PREFIX = "online:user:"        # 在线用户状态

    @classmethod
    async def cache_chat_sessions(cls, user_id: int, sessions: list):
        """缓存用户的聊天会话列表（5分钟）"""
        key = f"{cls.USER_SESSION_PREFIX}{user_id}"
        await cls.set(key, sessions, ttl=300)

    @classmethod
    async def get_cached_sessions(cls, user_id: int) -> Optional[list]:
        """获取缓存的会话列表"""
        key = f"{cls.USER_SESSION_PREFIX}{user_id}"
        return await cls.get(key)

    @classmethod
    async def cache_chat_messages(cls, session_id: int, messages: list):
        """缓存某个聊天的消息（10分钟）"""
        key = f"{cls.CHAT_MESSAGES_PREFIX}{session_id}"
        await cls.set(key, messages, ttl=600)

    @classmethod
    async def get_cached_messages(cls, session_id: int) -> Optional[list]:
        """获取缓存的聊天消息"""
        key = f"{cls.CHAT_MESSAGES_PREFIX}{session_id}"
        return await cls.get(key)

    @classmethod
    async def invalidate_user_cache(cls, user_id: int):
        """清除用户相关的所有缓存（数据变更时调用）"""
        keys_to_delete = [
            f"{cls.USER_SESSION_PREFIX}{user_id}",
            f"{cls.USER_CONTENTS_PREFIX}{user_id}",
        ]
        
        for key in keys_to_delete:
            await cls.delete(key)
        
        logger.info(f"[Cache] 清除用户 {user_id} 的缓存")

    @classmethod
    async def set_online(cls, user_id: int, info: dict = None):
        """标记用户在线（30分钟自动过期）"""
        key = f"{cls.ONLINE_USERS_PREFIX}{user_id}"
        await cls.set(key, info or {"last_active": "now"}, ttl=1800)

    @classmethod
    async def is_online(cls, user_id: int) -> bool:
        """检查用户是否在线"""
        key = f"{cls.ONLINE_USERS_PREFIX}{user_id}"
        return await cls.exists(key)


# 全局实例
cache_service = CacheService()
