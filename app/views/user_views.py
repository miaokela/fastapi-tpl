"""
用户相关视图
使用函数式编程实现
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Body, Path, Query
from fastapi.responses import JSONResponse
from datetime import datetime

from app.core.deps import get_current_active_user, get_current_superuser
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.models import User, UserProfile
from app.serializers import UserSerializer, UserProfileSerializer
from app.schemas.schemas import (
    UserCreate,
    Token,
)
from app.utils.responses import (
    ResponseCode, response, success, created, error
)


# 创建路由
auth_router = APIRouter()
user_management_router = APIRouter()


# ============================================================================
# 认证路由 (根路径)
# ============================================================================

@auth_router.post("/auth/register", summary="用户注册", tags=["认证"])
async def register(user_data: UserCreate = Body(...)):
    """用户注册 - POST /auth/register"""
    # 检查用户是否已存在
    existing_user = await User.get_or_none(username=user_data.username)
    if existing_user:
        return error(ResponseCode.USERNAME_EXISTS)
    
    existing_email = await User.get_or_none(email=user_data.email)
    if existing_email:
        return error(ResponseCode.EMAIL_EXISTS)
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    user = await User.create(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=getattr(user_data, 'is_active', True),
    )
    
    # 创建用户资料
    await UserProfile.create(user=user)
    
    return created({"user_id": user.id})


@auth_router.post("/auth/login", summary="用户登录", tags=["认证"])
async def login(username: str = Body(...), password: str = Body(...)):
    """用户登录（支持用户名或邮箱）"""
    # 支持用户名或邮箱登录
    user = await User.get_or_none(username=username)
    if not user:
        user = await User.get_or_none(email=username)
    
    if not user or not verify_password(password, user.hashed_password):
        return error(ResponseCode.UNAUTHORIZED, "用户名或密码不正确")
    
    if not user.is_active:
        return error(ResponseCode.BAD_REQUEST, "用户已被禁用")
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    await user.save()
    
    access_token = create_access_token(data={"sub": user.username})
    return success({"access_token": access_token, "token_type": "bearer"})


@auth_router.get("/auth/me", summary="获取当前用户信息", tags=["认证"])
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息 - GET /auth/me"""
    return await UserSerializer.from_tortoise_orm(current_user)


# ============================================================================
# 用户管理路由 (前缀 /api/v1)
# ============================================================================

@user_management_router.get("/users/", summary="获取用户列表", tags=["用户管理"])
async def list_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
):
    """获取用户列表"""
    queryset = User.all().offset(skip).limit(limit)
    total = await User.all().count()
    users = await queryset
    items = [await UserSerializer.from_tortoise_orm(u) for u in users]
    return success({"items": items, "total": total, "skip": skip, "limit": limit})


@user_management_router.post("/users/", summary="创建用户", tags=["用户管理"])
async def create_user(user_data: UserCreate):
    """创建用户"""
    # 检查用户是否已存在
    existing_user = await User.get_or_none(username=user_data.username)
    if existing_user:
        return error(ResponseCode.USERNAME_EXISTS)
    
    existing_email = await User.get_or_none(email=user_data.email)
    if existing_email:
        return error(ResponseCode.EMAIL_EXISTS)
    
    hashed_password = get_password_hash(user_data.password)
    user = await User.create(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=user_data.is_active,
    )
    
    # 创建用户资料
    await UserProfile.create(user=user)
    
    user_data = await UserSerializer.from_tortoise_orm(user)
    return created(user_data)


@user_management_router.get("/users/{user_id}", summary="获取用户详情", tags=["用户管理"])
async def get_user(user_id: int = Path(..., gt=0, description="用户ID")):
    """获取用户详情"""
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    user_data = await UserSerializer.from_tortoise_orm(user)
    return success(user_data)


@user_management_router.put("/users/{user_id}", summary="更新用户", tags=["用户管理"])
async def update_user(
    user_id: int = Path(..., gt=0, description="用户ID"),
    user_data: UserCreate = Body(...),
):
    """更新用户（全部字段）"""
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    # 检查用户名和邮箱是否与其他用户冲突
    if user_data.username != user.username:
        existing = await User.get_or_none(username=user_data.username)
        if existing:
            return error(ResponseCode.USERNAME_EXISTS)
    
    if user_data.email != user.email:
        existing = await User.get_or_none(email=user_data.email)
        if existing:
            return error(ResponseCode.EMAIL_EXISTS)
    
    # 更新字段
    user.username = user_data.username
    user.email = user_data.email
    user.is_active = user_data.is_active
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
    
    await user.save()
    user_resp = await UserSerializer.from_tortoise_orm(user)
    return success(user_resp)


@user_management_router.patch("/users/{user_id}", summary="部分更新用户", tags=["用户管理"])
async def partial_update_user(
    user_id: int = Path(..., gt=0, description="用户ID"),
    username: Optional[str] = Body(None),
    email: Optional[str] = Body(None),
    password: Optional[str] = Body(None),
    is_active: Optional[bool] = Body(None),
):
    """部分更新用户"""
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    if username is not None and username != user.username:
        existing = await User.get_or_none(username=username)
        if existing:
            return error(ResponseCode.USERNAME_EXISTS)
        user.username = username
    
    if email is not None and email != user.email:
        existing = await User.get_or_none(email=email)
        if existing:
            return error(ResponseCode.EMAIL_EXISTS)
        user.email = email
    
    if password is not None:
        user.hashed_password = get_password_hash(password)
    
    if is_active is not None:
        user.is_active = is_active
    
    await user.save()
    user_resp = await UserSerializer.from_tortoise_orm(user)
    return success(user_resp)


@user_management_router.delete("/users/{user_id}", summary="删除用户", tags=["用户管理"])
async def delete_user(
    user_id: int = Path(..., gt=0, description="用户ID"),
    current_user: User = Depends(get_current_superuser),
):
    """删除用户（需要超级用户权限）"""
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    # 不能删除自己（可选）
    if user.id == current_user.id:
        return error(ResponseCode.BAD_REQUEST, "Cannot delete yourself")
    
    await user.delete()
    return success(None, "用户删除成功")


# ============================================================================
# 用户资料管理路由 (前缀 /api/v1)
# ============================================================================

@user_management_router.get("/profiles/", summary="获取用户资料列表", tags=["用户资料管理"])
async def list_profiles(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
):
    """获取用户资料列表"""
    queryset = UserProfile.all().offset(skip).limit(limit)
    total = await UserProfile.all().count()
    profiles = await queryset
    items = [await UserProfileSerializer.from_tortoise_orm(p) for p in profiles]
    return success({"items": items, "total": total, "skip": skip, "limit": limit})


@user_management_router.post("/profiles/", summary="创建用户资料", tags=["用户资料管理"])
async def create_profile(
    user_id: int = Body(..., gt=0, description="用户ID"),
    first_name: Optional[str] = Body(None),
    last_name: Optional[str] = Body(None),
    phone: Optional[str] = Body(None),
):
    """创建用户资料"""
    # 检查用户是否存在
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    # 检查是否已有资料
    existing_profile = await UserProfile.get_or_none(user_id=user_id)
    if existing_profile:
        return error(ResponseCode.BAD_REQUEST, "Profile already exists for this user")
    
    profile = await UserProfile.create(
        user=user,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )
    profile_data = await UserProfileSerializer.from_tortoise_orm(profile)
    return created(profile_data)


@user_management_router.get("/profiles/{profile_id}", summary="获取用户资料详情", tags=["用户资料管理"])
async def get_profile(profile_id: int = Path(..., gt=0, description="资料ID")):
    """获取用户资料详情"""
    profile = await UserProfile.get_or_none(id=profile_id)
    if not profile:
        return error(ResponseCode.NOT_FOUND, "Profile not found")
    profile_data = await UserProfileSerializer.from_tortoise_orm(profile)
    return success(profile_data)


@user_management_router.put("/profiles/{profile_id}", summary="更新用户资料", tags=["用户资料管理"])
async def update_profile(
    profile_id: int = Path(..., gt=0, description="资料ID"),
    first_name: Optional[str] = Body(None),
    last_name: Optional[str] = Body(None),
    phone: Optional[str] = Body(None),
):
    """更新用户资料（全部字段）"""
    profile = await UserProfile.get_or_none(id=profile_id)
    if not profile:
        return error(ResponseCode.NOT_FOUND, "Profile not found")
    
    if first_name is not None:
        profile.first_name = first_name
    if last_name is not None:
        profile.last_name = last_name
    if phone is not None:
        profile.phone = phone
    
    await profile.save()
    profile_data = await UserProfileSerializer.from_tortoise_orm(profile)
    return success(profile_data)


@user_management_router.patch("/profiles/{profile_id}", summary="部分更新用户资料", tags=["用户资料管理"])
async def partial_update_profile(
    profile_id: int = Path(..., gt=0, description="资料ID"),
    first_name: Optional[str] = Body(None),
    last_name: Optional[str] = Body(None),
    phone: Optional[str] = Body(None),
):
    """部分更新用户资料"""
    profile = await UserProfile.get_or_none(id=profile_id)
    if not profile:
        return error(ResponseCode.NOT_FOUND, "Profile not found")
    
    if first_name is not None:
        profile.first_name = first_name
    if last_name is not None:
        profile.last_name = last_name
    if phone is not None:
        profile.phone = phone
    
    await profile.save()
    profile_data = await UserProfileSerializer.from_tortoise_orm(profile)
    return success(profile_data)


@user_management_router.delete("/profiles/{profile_id}", summary="删除用户资料", tags=["用户资料管理"])
async def delete_profile(
    profile_id: int = Path(..., gt=0, description="资料ID"),
    current_user: User = Depends(get_current_superuser),
):
    """删除用户资料（需要超级用户权限）"""
    profile = await UserProfile.get_or_none(id=profile_id)
    if not profile:
        return error(ResponseCode.NOT_FOUND, "Profile not found")
    
    await profile.delete()
    return success(None, "用户资料删除成功")


# 为了向后兼容，导出 auth_router 作为 router
router = auth_router
