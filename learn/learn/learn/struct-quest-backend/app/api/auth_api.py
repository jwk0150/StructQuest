"""用户认证 API：注册 / 登录 / 游客 / 忘记密码 / 用户名查重"""
import uuid
import re
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.user import User
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_required_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ════════════════════════════════════════════════════════
#  工具函数
# ════════════════════════════════════════════════════════

def _check_password_strength(password: str) -> dict[str, str]:
    """评估密码强度，返回 {level, label, color, hint}"""
    if len(password) < 4:
        return {"level": "weak", "label": "弱", "color": "#ef4444", "hint": "至少 4 个字符"}
    
    score = 0
    checks = {
        "length": len(password) >= 8,
        "has_upper": bool(re.search(r'[A-Z]', password)),
        "lower": bool(re.search(r'[a-z]', password)),
        "number": bool(re.search(r'\d', password)),
        "special": bool(re.search(r'[^A-Za-z0-9]', password)),
    }
    
    score = sum(checks.values())
    
    if score <= 1:
        return {"level": "weak", "label": "弱", "color": "#ef4444", "hint": "建议混合使用大小写字母和数字"}
    elif score == 2:
        return {"level": "fair", "label": "一般", "color": "#f59e0b", "hint": "可以更复杂一些"}
    elif score == 3 or score == 4:
        return {"level": "good", "label": "较强", "color": "#22c55e", "hint": "强度不错"}
    else:
        return {"level": "strong", "label": "强", "color": "#10b981", "hint": "非常安全"}


# ════════════════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str | None = None
    email: str | None = None
    # ═══ 冷启动画像：第一阶段 — 基础信息 ═══
    major: str | None = None           # 专业
    grade: str | None = None           # 年级
    course: str | None = None          # 课程
    learning_goal: str | None = None   # 学习目标
    target_score: str | None = None    # 目标成绩（可选）
    daily_study_time: str | None = None  # 每天学习时间
    exam_date: str | None = None       # 考试时间（可选）

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2 or len(v) > 30:
            raise ValueError("用户名长度需在 2-30 个字符之间")
        # 禁止特殊字符（只允许字母数字下划线中文）
        if not re.match(r'^[\w\u4e00-\u9fff]+$', v):
            raise ValueError("用户名只能包含字母、数字、下划线和中文")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("密码长度至少需要 4 个字符")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str | None, values) -> str | None:
        if v is not None and v != values.data.get("password"):
            raise ValueError("两次输入的密码不一致")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str | None) -> str | None:
        if v is not None and "@" in v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v.strip()):
            raise ValueError("邮箱格式不正确")
        return v.strip() if v else None


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class CheckUsernameRequest(BaseModel):
    username: str


# ════════════════════════════════════════════════════════
# 响应辅助
# ════════════════════════════════════════════════════════

def _user_response(user: User, token: str | None = None) -> dict:
    """统一的用户响应格式"""
    resp = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "has_completed_onboarding": user.has_completed_onboarding,
        "profile_data": user.profile_data,
        "learning_mode": user.learning_mode or '',
        "is_admin": getattr(user, 'is_admin', False),
        # 冷启动画像字段
        "major": getattr(user, 'major', None),
        "grade": getattr(user, 'grade', None),
        "course": getattr(user, 'course', None),
        "learning_goal": getattr(user, 'learning_goal', None),
        "target_score": getattr(user, 'target_score', None),
        "daily_study_time": getattr(user, 'daily_study_time', None),
        "exam_date": getattr(user, 'exam_date', None),
        "learning_purpose": getattr(user, 'learning_purpose', None),
        "preferred_styles": getattr(user, 'preferred_styles', None),
        "diagnostic_results": getattr(user, 'diagnostic_results', None),
    }
    if token:
        resp["token"] = token
    return resp


# ════════════════════════════════════════════════════════
# API 端点
# ════════════════════════════════════════════════════════

@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新用户 → 返回 JWT Token + 密码强度提示"""
    # 检查用户名唯一性
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该用户名已被注册")

    # 检查邮箱唯一性
    if req.email:
        result = await db.execute(select(User).where(User.email == req.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="该邮箱已被注册")

    pwd_strength = _check_password_strength(req.password)

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=get_password_hash(req.password),
        has_completed_onboarding=False,
        learning_mode='',  # 新用户默认没有选择学习模式
        # 冷启动画像：第一阶段基础信息
        major=req.major,
        grade=req.grade,
        course=req.course,
        learning_goal=req.learning_goal,
        target_score=req.target_score,
        daily_study_time=req.daily_study_time,
        exam_date=req.exam_date,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "token": create_access_token({"sub": str(user.id)}),
        "user": _user_response(user),
        "password_strength": pwd_strength,
    }


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """登录 → 返回 JWT Token"""
    import traceback
    print('═══════════ [Auth] 收到登录请求 ═══════════')
    print(f"[Auth] 用户名: {req.username}")
    print(f"[Auth] 数据库URL: {os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./learn_ai.db')}")

    # 如果没有任何用户，自动创建默认管理员账号
    try:
        from sqlalchemy import func as sa_func
        print("[Auth] 开始查询用户表...")
        count_result = await db.execute(select(sa_func.count(User.id)))
        user_count = count_result.scalar() or 0
        print(f"[Auth] 当前用户数: {user_count}")
        if user_count == 0:
            print("[Auth] 数据库无用户，自动创建默认账号 admin/123456")
            default_user = User(
                username="admin",
                hashed_password=get_password_hash("123456"),
                has_completed_onboarding=True,
            )
            db.add(default_user)
            await db.commit()
            print("[Auth] ✅ 默认账号创建成功")
    except Exception as e:
        print(f"[Auth] ❌ 检查用户表失败: {e}")
        print(f"[Auth] 堆栈: {traceback.format_exc()}")

    try:
        print(f"[Auth] 开始查询 SQLite: SELECT * FROM users WHERE username='{req.username}'")
        result = await db.execute(select(User).where(User.username == req.username))
        user = result.scalar_one_or_none()
        print(f"[Auth] 查询完成: user={'✅ found' if user else '❌ not found'}")
    except Exception as e:
        print(f"[Auth] ❌ 数据库查询异常: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"数据库查询失败: {str(e)[:200]}")

    if not user:
        print(f"[Auth] ❌ 用户不存在: {req.username}")
        raise HTTPException(status_code=401, detail="用户名不存在")

    print(f"[Auth] 开始验证密码...")
    if not verify_password(req.password, user.hashed_password):
        print(f"[Auth] ❌ 密码错误: {req.username}")
        raise HTTPException(status_code=401, detail="密码错误")
    print(f"[Auth] ✅ 密码验证成功")

    print(f"[Auth] 开始生成 Token...")
    token = create_access_token({"sub": str(user.id)})
    print(f"[Auth] ✅ Token 生成成功")

    print(f"[Auth] ✅ 登录成功: {req.username}")
    print(f"[Auth] 返回数据: token长度={len(token)}, user={user.id}/{user.username}")
    print('═══════════ [Auth] 登录流程完成 ═══════════')

    return {
        "token": token,
        "user": _user_response(user),
    }


@router.get("/me")
async def get_me(user: User = Depends(get_required_user)):
    """获取当前用户信息"""
    return _user_response(user)


@router.post("/guest")
async def guest_login(db: AsyncSession = Depends(get_db)):
    """游客登录 → 自动创建临时账号"""
    guest_name = f"guest_{uuid.uuid4().hex[:8]}"
    user = User(
        username=guest_name,
        hashed_password=get_password_hash("guest"),
        has_completed_onboarding=False,
        learning_mode='',
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "token": create_access_token({"sub": str(user.id)}),
        "user": _user_response(user),
    }


@router.post("/forgot-password")
async def forgot_password(
    req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db),
):
    """
    忘记密码
    
    当前实现：查找用户并返回成功提示（模拟发送重置邮件）。
    生产环境应集成邮件服务发送含重置链接的邮件。
    """
    if not req.email:
        raise HTTPException(status_code=400, detail="请输入邮箱地址")

    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user:
        # 安全考虑：不透露邮箱是否已注册，统一返回成功
        # 防止枚举攻击
        return {
            "message": "如果该邮箱已注册，重置链接已发送",
            "detail": f"请检查您的邮箱 ({req.email})，点击邮件中的链接重置密码"
        }

    # TODO: 生产环境集成邮件服务 (如 Resend / SendGrid / SMTP)
    # 发送含重置 token 的邮件链接

    return {
        "message": "重置链接已发送到您的邮箱",
        "detail": f"请检查 {req.email} 中的邮件，点击链接完成密码重置",
        "username_hint": user.username,
    }


@router.get("/check-username")
async def check_username(username: str, db: AsyncSession = Depends(get_db)):
    """检查用户名是否可用（实时查重）"""
    if len(username) < 2:
        raise HTTPException(status_code=400, detail="用户名长度不足")

    username = username.strip()
    result = await db.execute(select(User).where(User.username == username))
    exists = result.scalar_one_or_none() is not None

    return {
        "available": not exists,
        "message": "该用户名可以使用" if not exists else "该用户名已被占用",
    }


@router.get("/password-strength")
async def password_strength(password: str):
    """评估密码强度（前端实时调用）"""
    if not password:
        return {"level": "", "label": "", "color": "", "hint": ""}
    return _check_password_strength(password)
