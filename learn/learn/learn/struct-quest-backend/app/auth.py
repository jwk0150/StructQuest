"""JWT 认证工具（使用 Python 内置 hashlib，无需 passlib/bcrypt）"""
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.user import User

SECRET_KEY = "struct-quest-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码（PBKDF2-SHA256）"""
    try:
        salt, hash_value = hashed_password.split("$", 1)
        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        )
        return new_hash.hex() == hash_value
    except (ValueError, AttributeError):
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希（PBKDF2-SHA256 + 随机 salt）"""
    salt = os.urandom(16).hex()
    hash_value = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return f"{salt}${hash_value.hex()}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """从 JWT Token 获取当前用户（可选认证）

    认证策略：
    - 无 token → 返回 None（静默）
    - 有效 token → 返回 User
    - 无效/过期 token → 返回 None（静默，不报错）
      （前端可在 catch 中处理，避免强制跳转登录页）
    """
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            return None
        user_id = int(sub)  # python-jose 要求 sub 为字符串，转为 int 用于 DB 查询
    except (JWTError, Exception):
        # token 过期或无效 → 静默返回 None（不抛 401）
        return None

    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return user  # 用户不存在也返回 None，不抛错误
    except Exception as e:
        print(f"[Auth]  查询用户失败 user_id={user_id}: {e}")
        import traceback; traceback.print_exc()
        return None  # 降级为未登录，不阻塞请求


async def get_required_user(user: Optional[User] = Depends(get_current_user)) -> User:
    """必须认证的依赖"""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def get_admin_user(user: User = Depends(get_required_user)) -> User:
    """管理员认证依赖：必须登录且 is_admin=True"""
    if not getattr(user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
