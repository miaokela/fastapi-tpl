"""
Admin 管理模块的 Schema 定义
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 用户管理 Schema ====================

class UserAdminCreate(BaseModel):
    """管理员创建用户"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")
    is_active: bool = Field(default=True, description="是否激活")
    is_superuser: bool = Field(default=False, description="是否为超级管理员")
    is_staff: bool = Field(default=False, description="是否为管理员")


class UserAdminUpdate(BaseModel):
    """管理员更新用户"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_staff: Optional[bool] = None


class UserAdminResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    is_staff: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    items: List[UserAdminResponse]


# ==================== 间隔调度 Schema ====================

class IntervalScheduleCreate(BaseModel):
    """创建间隔调度"""
    every: int = Field(..., gt=0, description="间隔数量")
    period: str = Field(..., description="间隔类型: days/hours/minutes/seconds")


class IntervalScheduleUpdate(BaseModel):
    """更新间隔调度"""
    every: Optional[int] = Field(None, gt=0, description="间隔数量")
    period: Optional[str] = Field(None, description="间隔类型: days/hours/minutes/seconds")


class IntervalScheduleResponse(BaseModel):
    """间隔调度响应"""
    id: int
    every: int
    period: str
    display: str = ""

    class Config:
        from_attributes = True


# ==================== Crontab调度 Schema ====================

class CrontabScheduleCreate(BaseModel):
    """创建 Crontab 调度"""
    minute: str = Field(default="*", description="分钟 (0-59)")
    hour: str = Field(default="*", description="小时 (0-23)")
    day_of_week: str = Field(default="*", description="星期几 (0-6)")
    day_of_month: str = Field(default="*", description="日期 (1-31)")
    month_of_year: str = Field(default="*", description="月份 (1-12)")
    timezone: str = Field(default="Asia/Shanghai", description="时区")


class CrontabScheduleUpdate(BaseModel):
    """更新 Crontab 调度"""
    minute: Optional[str] = Field(None, description="分钟 (0-59)")
    hour: Optional[str] = Field(None, description="小时 (0-23)")
    day_of_week: Optional[str] = Field(None, description="星期几 (0-6)")
    day_of_month: Optional[str] = Field(None, description="日期 (1-31)")
    month_of_year: Optional[str] = Field(None, description="月份 (1-12)")
    timezone: Optional[str] = Field(None, description="时区")


class CrontabScheduleResponse(BaseModel):
    """Crontab 调度响应"""
    id: int
    minute: str
    hour: str
    day_of_week: str
    day_of_month: str
    month_of_year: str
    timezone: str
    display: str = ""

    class Config:
        from_attributes = True


# ==================== 定时任务 Schema ====================

class PeriodicTaskCreate(BaseModel):
    """创建定时任务"""
    name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    task: str = Field(..., description="任务路径")
    interval_id: Optional[int] = Field(None, description="间隔调度ID")
    crontab_id: Optional[int] = Field(None, description="Crontab调度ID")
    args: List = Field(default=[], description="位置参数")
    kwargs: Dict[str, Any] = Field(default={}, description="关键字参数")
    queue: Optional[str] = Field(None, description="队列名称")
    priority: Optional[int] = Field(None, ge=0, le=9, description="优先级")
    expires: Optional[datetime] = Field(None, description="过期时间")
    one_off: bool = Field(default=False, description="是否只执行一次")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    enabled: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(None, description="任务描述")


class PeriodicTaskUpdate(BaseModel):
    """更新定时任务"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    task: Optional[str] = None
    interval_id: Optional[int] = None
    crontab_id: Optional[int] = None
    args: Optional[List] = None
    kwargs: Optional[Dict[str, Any]] = None
    queue: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=9)
    expires: Optional[datetime] = None
    one_off: Optional[bool] = None
    start_time: Optional[datetime] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class PeriodicTaskResponse(BaseModel):
    """定时任务响应"""
    id: int
    name: str
    task: str
    interval_id: Optional[int] = None
    interval_display: Optional[str] = None
    crontab_id: Optional[int] = None
    crontab_display: Optional[str] = None
    args: str
    kwargs: str
    queue: Optional[str] = None
    priority: Optional[int] = None
    expires: Optional[datetime] = None
    one_off: bool
    start_time: Optional[datetime] = None
    enabled: bool
    last_run_at: Optional[datetime] = None
    total_run_count: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PeriodicTaskListResponse(BaseModel):
    """定时任务列表响应"""
    total: int
    items: List[PeriodicTaskResponse]


# ==================== 任务结果 Schema ====================

class TaskResultResponse(BaseModel):
    """任务结果响应"""
    id: int
    task_id: str
    task_name: Optional[str] = None
    task_args: Optional[str] = None
    task_kwargs: Optional[str] = None
    status: str
    result: Optional[str] = None
    traceback: Optional[str] = None
    date_created: datetime
    date_done: Optional[datetime] = None
    worker: Optional[str] = None

    class Config:
        from_attributes = True


class TaskResultListResponse(BaseModel):
    """任务结果列表响应"""
    total: int
    items: List[TaskResultResponse]


# ==================== 统计信息 Schema ====================

class TaskStatisticsResponse(BaseModel):
    """任务统计响应"""
    periodic_tasks: Dict[str, int]
    task_results: Dict[str, int]


# ==================== 可用任务列表 ====================

class AvailableTaskResponse(BaseModel):
    """可用任务响应"""
    name: str
    path: str
    description: Optional[str] = None
