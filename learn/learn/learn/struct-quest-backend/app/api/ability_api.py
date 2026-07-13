"""能力值 API——获取/重新计算用户六维学习能力"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth import get_required_user
from app.models.user import User
from app.services.ability_service import ability_service

router = APIRouter(prefix="/api/user", tags=["ability"])


@router.get("/ability")
async def get_user_ability(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户六维学习能力值。
    
    直接从 user_ability 表读取（自动触发衰减检查），
    如果用户还没有能力数据则初始化（全部为 0）。
    
    返回格式：
    {
        "visual": 65.0,
        "comprehensive": 58.0,
        "stability": 72.0,
        "exploration": 41.0,
        "theory": 60.0,
        "practice": 55.0
    }
    """
    ability_dict = await ability_service.get_ability(db, user.id)
    return ability_dict


@router.post("/ability/recalculate")
async def recalculate_user_ability(
    user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    """
    全量重新计算用户能力值（数据修复/校准用）。
    
    从数据库中的所有学习行为记录重新汇总计算，
    通常不需要调用，除非怀疑数据不一致。
    """
    ability_dict = await ability_service.full_recalculate(db, user.id)
    return {
        "message": "能力值已重新计算",
        "scores": ability_dict,
    }
