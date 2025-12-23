"""
Admin 管理视图
提供用户管理和定时任务管理的API接口
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from tortoise.expressions import Q

from app.core.deps import get_current_active_user, get_current_superuser
from app.core.security import get_password_hash
from app.models.models import (
    User, UserProfile,
    IntervalSchedule, CrontabSchedule, PeriodicTask, TaskResult
)
from app.services.task_scheduler import TaskSchedulerService
from app.utils.responses import (
    ResponseCode, response, success, created, updated, deleted, error, paginated
)
from .schemas import (
    # 用户管理
    UserAdminCreate, UserAdminUpdate, UserAdminResponse,
    # 间隔调度
    IntervalScheduleCreate, IntervalScheduleUpdate, IntervalScheduleResponse,
    # Crontab调度
    CrontabScheduleCreate, CrontabScheduleUpdate, CrontabScheduleResponse,
    # 定时任务
    PeriodicTaskCreate, PeriodicTaskUpdate, PeriodicTaskResponse,
    # 任务结果
    TaskResultResponse,
    # 统计
    TaskStatisticsResponse,
    # 可用任务
    AvailableTaskResponse,
)


router = APIRouter(prefix="/admin", tags=["Admin 管理"])


# ============================================================================
# 管理员权限检查
# ============================================================================

async def check_admin_permission(current_user: User = Depends(get_current_active_user)):
    """检查管理员权限（返回用户或None，不抛出异常）"""
    if not (current_user.is_superuser or current_user.is_staff):
        return None
    return current_user


async def require_admin(current_user: User = Depends(get_current_active_user)):
    """要求管理员权限的依赖"""
    if not (current_user.is_superuser or current_user.is_staff):
        return None
    return current_user


# ============================================================================
# 用户管理
# ============================================================================

@router.get("/users", summary="获取用户列表")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """获取用户列表（管理员）"""
    # 权限检查
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    query = User.all()
    
    if is_active is not None:
        query = query.filter(is_active=is_active)
    
    if search:
        query = query.filter(Q(username__icontains=search) | Q(email__icontains=search))
    
    total = await query.count()
    skip = (page - 1) * page_size
    users = await query.offset(skip).limit(page_size).order_by("-created_at")
    
    items = [UserAdminResponse.model_validate(u, from_attributes=True).model_dump() for u in users]
    
    return paginated(items, total, page, page_size)


@router.post("/users", summary="创建用户")
async def create_user(
    user_data: UserAdminCreate,
    current_user: User = Depends(get_current_superuser)
):
    """创建新用户（仅超级管理员）"""
    if current_user is None:
        return error(ResponseCode.FORBIDDEN)
    
    # 检查用户名是否存在
    if await User.filter(username=user_data.username).exists():
        return error(ResponseCode.USERNAME_EXISTS)
    
    # 检查邮箱是否存在
    if await User.filter(email=user_data.email).exists():
        return error(ResponseCode.EMAIL_EXISTS)
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    user = await User.create(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=user_data.is_active,
        is_superuser=user_data.is_superuser,
        is_staff=user_data.is_staff
    )
    
    # 创建用户资料
    await UserProfile.create(user=user)
    
    return created(UserAdminResponse.model_validate(user, from_attributes=True).model_dump())


@router.get("/users/{user_id}", summary="获取用户详情")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """获取用户详情"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    return success(UserAdminResponse.model_validate(user, from_attributes=True).model_dump())


@router.put("/users/{user_id}", summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    current_user: User = Depends(get_current_superuser)
):
    """更新用户信息（仅超级管理员）"""
    if current_user is None:
        return error(ResponseCode.FORBIDDEN)
    
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    update_data = user_data.model_dump(exclude_unset=True)
    
    # 检查用户名唯一性
    if "username" in update_data:
        if await User.filter(username=update_data["username"]).exclude(id=user_id).exists():
            return error(ResponseCode.USERNAME_EXISTS)
    
    # 检查邮箱唯一性
    if "email" in update_data:
        if await User.filter(email=update_data["email"]).exclude(id=user_id).exists():
            return error(ResponseCode.EMAIL_EXISTS)
    
    # 处理密码
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # 更新用户
    for key, value in update_data.items():
        setattr(user, key, value)
    await user.save()
    
    return updated(UserAdminResponse.model_validate(user, from_attributes=True).model_dump())


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser)
):
    """删除用户（仅超级管理员）"""
    if current_user is None:
        return error(ResponseCode.FORBIDDEN)
    
    if user_id == current_user.id:
        return error(ResponseCode.BAD_REQUEST, "不能删除自己")
    
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    await user.delete()
    return deleted()


# ============================================================================
# 间隔调度管理
# ============================================================================

@router.get("/schedules/intervals", summary="获取间隔调度列表")
async def list_intervals(
    current_user: User = Depends(get_current_active_user)
):
    """获取所有间隔调度"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    intervals = await TaskSchedulerService.list_intervals()
    result = []
    for interval in intervals:
        resp = IntervalScheduleResponse(
            id=interval.id,
            every=interval.every,
            period=interval.period,
            display=f"每 {interval.every} {interval.period}"
        )
        result.append(resp.model_dump())
    return success(result)


@router.post("/schedules/intervals", summary="创建间隔调度")
async def create_interval(
    data: IntervalScheduleCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建间隔调度"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    try:
        interval = await TaskSchedulerService.create_interval(
            every=data.every,
            period=data.period
        )
        return created(IntervalScheduleResponse(
            id=interval.id,
            every=interval.every,
            period=interval.period,
            display=f"每 {interval.every} {interval.period}"
        ).model_dump())
    except ValueError as e:
        return error(ResponseCode.BAD_REQUEST, str(e))


@router.put("/schedules/intervals/{interval_id}", summary="更新间隔调度")
async def update_interval(
    interval_id: int,
    data: IntervalScheduleUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新间隔调度"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    interval = await IntervalSchedule.get_or_none(id=interval_id)
    if not interval:
        return error(ResponseCode.NOT_FOUND, "间隔调度不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        await interval.update_from_dict(update_data).save()
        
        # 重置使用此 interval 的所有任务的 last_run_at
        # 参考 django-celery-beat：修改调度配置后，应让新配置立即生效
        from app.models.models import PeriodicTask, PeriodicTaskChanged
        await PeriodicTask.filter(interval_id=interval_id).update(last_run_at=None)
        
        # 触发调度器重载
        await PeriodicTaskChanged.update_changed()
    
    return updated(IntervalScheduleResponse(
        id=interval.id,
        every=interval.every,
        period=interval.period,
        display=f"每 {interval.every} {interval.period}"
    ).model_dump())


@router.delete("/schedules/intervals/{interval_id}", summary="删除间隔调度")
async def delete_interval(
    interval_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """删除间隔调度"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    if not await TaskSchedulerService.delete_interval(interval_id):
        return error(ResponseCode.NOT_FOUND, "间隔调度不存在")
    return deleted()


# ============================================================================
# Crontab 调度管理
# ============================================================================

@router.get("/schedules/crontabs", summary="获取Crontab调度列表")
async def list_crontabs(
    current_user: User = Depends(get_current_active_user)
):
    """获取所有 Crontab 调度"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    crontabs = await TaskSchedulerService.list_crontabs()
    result = []
    for crontab in crontabs:
        resp = CrontabScheduleResponse(
            id=crontab.id,
            minute=crontab.minute,
            hour=crontab.hour,
            day_of_week=crontab.day_of_week,
            day_of_month=crontab.day_of_month,
            month_of_year=crontab.month_of_year,
            timezone=crontab.timezone,
            display=str(crontab)
        )
        result.append(resp.model_dump())
    return success(result)


@router.post("/schedules/crontabs", summary="创建Crontab调度")
async def create_crontab(
    data: CrontabScheduleCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建 Crontab 调度"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    crontab = await TaskSchedulerService.create_crontab(
        minute=data.minute,
        hour=data.hour,
        day_of_week=data.day_of_week,
        day_of_month=data.day_of_month,
        month_of_year=data.month_of_year,
        timezone=data.timezone
    )
    return created(CrontabScheduleResponse(
        id=crontab.id,
        minute=crontab.minute,
        hour=crontab.hour,
        day_of_week=crontab.day_of_week,
        day_of_month=crontab.day_of_month,
        month_of_year=crontab.month_of_year,
        timezone=crontab.timezone,
        display=str(crontab)
    ).model_dump())


@router.put("/schedules/crontabs/{crontab_id}", summary="更新Crontab调度")
async def update_crontab(
    crontab_id: int,
    data: CrontabScheduleUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新 Crontab 调度"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    crontab = await CrontabSchedule.get_or_none(id=crontab_id)
    if not crontab:
        return error(ResponseCode.NOT_FOUND, "Crontab调度不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        await crontab.update_from_dict(update_data).save()
        
        # 重置使用此 crontab 的所有任务的 last_run_at
        # 参考 django-celery-beat：修改调度配置后，应让新配置立即生效
        from app.models.models import PeriodicTask, PeriodicTaskChanged
        await PeriodicTask.filter(crontab_id=crontab_id).update(last_run_at=None)
        
        # 触发调度器重载
        await PeriodicTaskChanged.update_changed()
    
    return updated(CrontabScheduleResponse(
        id=crontab.id,
        minute=crontab.minute,
        hour=crontab.hour,
        day_of_week=crontab.day_of_week,
        day_of_month=crontab.day_of_month,
        month_of_year=crontab.month_of_year,
        timezone=crontab.timezone,
        display=str(crontab)
    ).model_dump())


@router.delete("/schedules/crontabs/{crontab_id}", summary="删除Crontab调度")
async def delete_crontab(
    crontab_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """删除 Crontab 调度"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    if not await TaskSchedulerService.delete_crontab(crontab_id):
        return error(ResponseCode.NOT_FOUND, "Crontab调度不存在")
    return deleted()


# ============================================================================
# 定时任务管理
# ============================================================================

def _build_task_response(task) -> dict:
    """构建任务响应数据"""
    return PeriodicTaskResponse(
        id=task.id,
        name=task.name,
        task=task.task,
        interval_id=task.interval_id,
        interval_display=str(task.interval) if task.interval else None,
        crontab_id=task.crontab_id,
        crontab_display=str(task.crontab) if task.crontab else None,
        args=task.args,
        kwargs=task.kwargs,
        queue=task.queue,
        priority=task.priority,
        expires=task.expires,
        one_off=task.one_off,
        start_time=task.start_time,
        enabled=task.enabled,
        last_run_at=task.last_run_at,
        total_run_count=task.total_run_count,
        description=task.description,
        created_at=task.created_at,
        updated_at=task.updated_at
    ).model_dump()


@router.get("/tasks", summary="获取定时任务列表")
async def list_periodic_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    enabled: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
):
    """获取定时任务列表"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    skip = (page - 1) * page_size
    tasks = await TaskSchedulerService.list_periodic_tasks(
        enabled=enabled,
        limit=page_size,
        offset=skip
    )
    
    query = PeriodicTask.all()
    if enabled is not None:
        query = query.filter(enabled=enabled)
    total = await query.count()
    
    items = [_build_task_response(task) for task in tasks]
    
    return paginated(items, total, page, page_size)


@router.post("/tasks", summary="创建定时任务")
async def create_periodic_task(
    data: PeriodicTaskCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建定时任务"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    try:
        task = await TaskSchedulerService.create_periodic_task(
            name=data.name,
            task=data.task,
            interval_id=data.interval_id,
            crontab_id=data.crontab_id,
            args=data.args,
            kwargs=data.kwargs,
            queue=data.queue,
            priority=data.priority,
            expires=data.expires,
            one_off=data.one_off,
            start_time=data.start_time,
            enabled=data.enabled,
            description=data.description
        )
        
        # 重新获取以包含关联数据
        task = await TaskSchedulerService.get_periodic_task(task.id)
        
        return created(_build_task_response(task))
    except ValueError as e:
        return error(ResponseCode.BAD_REQUEST, str(e))


@router.get("/tasks/{task_id}", summary="获取定时任务详情")
async def get_periodic_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """获取定时任务详情"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    task = await TaskSchedulerService.get_periodic_task(task_id)
    if not task:
        return error(ResponseCode.TASK_NOT_FOUND)
    
    return success(_build_task_response(task))


@router.put("/tasks/{task_id}", summary="更新定时任务")
async def update_periodic_task(
    task_id: int,
    data: PeriodicTaskUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """更新定时任务"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    update_data = data.model_dump(exclude_unset=True)
    
    task = await TaskSchedulerService.update_periodic_task(task_id, **update_data)
    if not task:
        return error(ResponseCode.TASK_NOT_FOUND)
    
    # 重新获取以包含关联数据
    task = await TaskSchedulerService.get_periodic_task(task.id)
    
    return updated(_build_task_response(task))


@router.delete("/tasks/{task_id}", summary="删除定时任务")
async def delete_periodic_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """删除定时任务"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    if not await TaskSchedulerService.delete_periodic_task(task_id):
        return error(ResponseCode.TASK_NOT_FOUND)
    return deleted()


@router.post("/tasks/{task_id}/enable", summary="启用定时任务")
async def enable_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """启用定时任务"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    if not await TaskSchedulerService.enable_task(task_id):
        return error(ResponseCode.TASK_NOT_FOUND)
    return success(message="任务已启用")


@router.post("/tasks/{task_id}/disable", summary="禁用定时任务")
async def disable_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """禁用定时任务"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    if not await TaskSchedulerService.disable_task(task_id):
        return error(ResponseCode.TASK_NOT_FOUND)
    return success(message="任务已禁用")


@router.post("/tasks/{task_id}/run", summary="立即执行任务")
async def run_task_now(
    task_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """立即执行定时任务"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    task_result_id = await TaskSchedulerService.run_task_now(task_id)
    if not task_result_id:
        return error(ResponseCode.TASK_NOT_FOUND)
    return success({"task_id": task_result_id}, "任务已提交执行")


# ============================================================================
# 任务结果管理
# ============================================================================

@router.get("/results", summary="获取任务执行结果列表")
async def list_task_results(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_name: Optional[str] = None,
    task_status: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user)
):
    """获取任务执行结果列表"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    skip = (page - 1) * page_size
    results = await TaskSchedulerService.list_task_results(
        task_name=task_name,
        status=task_status,
        limit=page_size,
        offset=skip
    )
    
    query = TaskResult.all()
    if task_name:
        query = query.filter(task_name=task_name)
    if task_status:
        query = query.filter(status=task_status)
    total = await query.count()
    
    items = [TaskResultResponse.model_validate(r, from_attributes=True).model_dump() for r in results]
    
    return paginated(items, total, page, page_size)


@router.get("/results/{task_id}", summary="获取任务执行结果详情")
async def get_task_result(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """获取任务执行结果详情"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    result = await TaskSchedulerService.get_task_result(task_id)
    if not result:
        return error(ResponseCode.NOT_FOUND, "任务结果不存在")
    return success(TaskResultResponse.model_validate(result, from_attributes=True).model_dump())


@router.delete("/results/cleanup", summary="清理旧的任务结果")
async def cleanup_task_results(
    days: int = Query(30, ge=1, le=365, description="保留最近N天的结果"),
    current_user: User = Depends(get_current_superuser)
):
    """清理旧的任务结果（仅超级管理员）"""
    if current_user is None:
        return error(ResponseCode.FORBIDDEN)
    
    deleted_count = await TaskSchedulerService.cleanup_old_results(days=days)
    return success({"deleted_count": deleted_count}, f"已清理 {deleted_count} 条旧记录")


# ============================================================================
# 统计信息
# ============================================================================

@router.get("/statistics", summary="获取任务统计信息")
async def get_task_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """获取任务统计信息"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    stats = await TaskSchedulerService.get_task_statistics()
    return success(stats)


# ============================================================================
# 可用任务列表
# ============================================================================

@router.get("/available-tasks", summary="获取可用任务列表")
async def get_available_tasks(
    current_user: User = Depends(get_current_active_user)
):
    """获取系统中可用的 Celery 任务列表"""
    if not (current_user.is_superuser or current_user.is_staff):
        return error(ResponseCode.FORBIDDEN)
    
    from celery_app.celery import celery_app
    
    # 获取注册的任务
    registered_tasks = celery_app.tasks.keys()
    
    # 过滤掉内置任务
    available_tasks = []
    for task_name in registered_tasks:
        if not task_name.startswith("celery."):
            available_tasks.append(AvailableTaskResponse(
                name=task_name.split(".")[-1],
                path=task_name,
                description=None
            ).model_dump())
    
    return success(available_tasks)


# ============================================================================
# 日志查询
# ============================================================================

import json
import subprocess
from pathlib import Path


@router.get("/logs/files")
async def get_log_files(current_user: User = Depends(get_current_superuser)):
    """获取日志文件列表"""
    import re
    log_dir = Path("logs")
    if not log_dir.exists():
        return success([])
    
    # 只获取符合日期格式 YYYY-MM-DD.log 的文件，按日期倒序排列
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.log$')
    log_files = sorted(
        [f.name for f in log_dir.glob("*.log") if date_pattern.match(f.name)],
        reverse=True
    )
    
    return success(log_files)


@router.post("/logs/query")
async def query_logs(
    request_body: dict,
    current_user: User = Depends(get_current_superuser)
):
    """执行日志查询"""
    # 从请求体中获取参数
    filename = request_body.get("filename")
    jq_filter = request_body.get("jq_filter", ".")
    
    # 验证必需参数
    if not filename:
        return error(ResponseCode.INVALID_PARAMS, "文件名不能为空")
    
    log_dir = Path("logs")
    log_file = log_dir / filename
    
    # 安全检查：防止路径遍历
    if not log_file.resolve().is_relative_to(log_dir.resolve()):
        return error(ResponseCode.INVALID_PARAMS, "非法的文件名")
    
    if not log_file.exists():
        return error(ResponseCode.INVALID_PARAMS, "日志文件不存在")
    
    try:
        # 执行jq查询（使用 -c 输出紧凑格式，每个对象一行）
        with open(log_file, "r", encoding="utf-8") as f:
            result = subprocess.run(
                ["jq", "-c", jq_filter],
                stdin=f,
                capture_output=True,
                text=True,
                timeout=10
            )
        
        if result.returncode != 0:
            return error(ResponseCode.INTERNAL_ERROR, f"jq执行失败: {result.stderr}")
        
        # 解析结果
        results = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    # 如果不是JSON，作为字符串返回
                    results.append(line)
        
        return success({
            "filename": filename,
            "jq_filter": jq_filter,
            "count": len(results),
            "results": results
        })
    
    except subprocess.TimeoutExpired:
        return error(ResponseCode.INTERNAL_ERROR, "查询超时")
    except Exception as e:
        return error(ResponseCode.INTERNAL_ERROR, f"查询失败: {str(e)}")
