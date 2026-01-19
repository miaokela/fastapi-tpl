from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from app.core.security import verify_token
from app.models.models import User
from app.utils.sql_client import sql_client


async def get_current_user(request: Request) -> User:
    """获取当前用户 - 从 Authorization header 中提取 Bearer token"""
    # 获取 Authorization header
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权：缺少认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 解析 Bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未授权：无效的认证格式",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未授权：无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = verify_token(token)
    if username is None:
        raise credentials_exception
    
    user = await User.get_or_none(username=username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_sql_client():
    """获取 SQL 客户端依赖"""
    return sql_client