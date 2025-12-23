from datetime import datetime
from tortoise.models import Model
from tortoise import fields
import json


class TimestampMixin:
    """时间戳混入类"""
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")


class User(Model, TimestampMixin):
    """用户模型"""
    
    id = fields.IntField(pk=True, description="用户ID")
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    email = fields.CharField(max_length=100, unique=True, description="邮箱")
    hashed_password = fields.CharField(max_length=255, description="密码哈希")
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_superuser = fields.BooleanField(default=False, description="是否为超级管理员")
    is_staff = fields.BooleanField(default=False, description="是否为管理员")
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    
    class Meta:
        table = "users"
        table_description = "用户表"
    
    def __str__(self):
        return self.username


class UserProfile(Model, TimestampMixin):
    """用户资料模型"""
    
    id = fields.IntField(pk=True, description="资料ID")
    user = fields.OneToOneField("models.User", related_name="profile", description="用户")
    first_name = fields.CharField(max_length=50, null=True, description="名")
    last_name = fields.CharField(max_length=50, null=True, description="姓")
    phone = fields.CharField(max_length=20, null=True, description="电话")
    avatar = fields.CharField(max_length=255, null=True, description="头像URL")
    bio = fields.TextField(null=True, description="个人简介")
    
    class Meta:
        table = "user_profiles"
        table_description = "用户资料表"


# ============================================================================
# Celery Beat 定时任务模型 (类似 django-celery-beat)
# ============================================================================

class IntervalSchedule(Model):
    """
    间隔调度模型
    类似 django-celery-beat 的 IntervalSchedule
    """
    PERIOD_CHOICES = [
        ("days", "天"),
        ("hours", "小时"),
        ("minutes", "分钟"),
        ("seconds", "秒"),
        ("microseconds", "微秒"),
    ]
    
    id = fields.IntField(pk=True)
    every = fields.IntField(description="间隔数量")
    period = fields.CharField(max_length=24, description="间隔类型(days/hours/minutes/seconds)")
    
    class Meta:
        table = "celery_interval_schedule"
        table_description = "间隔调度表"
        unique_together = (("every", "period"),)
    
    def __str__(self):
        return f"每 {self.every} {self.period}"
    
    @property
    def schedule(self):
        """返回 celery schedule 对象"""
        from celery.schedules import schedule
        from datetime import timedelta
        return schedule(timedelta(**{self.period: self.every}))


class CrontabSchedule(Model):
    """
    Crontab 调度模型
    类似 django-celery-beat 的 CrontabSchedule
    """
    id = fields.IntField(pk=True)
    minute = fields.CharField(max_length=240, default="*", description="分钟 (0-59)")
    hour = fields.CharField(max_length=96, default="*", description="小时 (0-23)")
    day_of_week = fields.CharField(max_length=64, default="*", description="星期几 (0-6, 0是周日)")
    day_of_month = fields.CharField(max_length=124, default="*", description="日期 (1-31)")
    month_of_year = fields.CharField(max_length=64, default="*", description="月份 (1-12)")
    timezone = fields.CharField(max_length=64, default="Asia/Shanghai", description="时区")
    
    class Meta:
        table = "celery_crontab_schedule"
        table_description = "Crontab调度表"
    
    def __str__(self):
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month_of_year} {self.day_of_week}"
    
    @property
    def schedule(self):
        """返回 celery crontab 对象，使用配置的时区"""
        from celery.schedules import crontab
        from datetime import datetime
        import pytz
        
        # 获取时区对象
        tz = pytz.timezone(self.timezone) if self.timezone else pytz.timezone('Asia/Shanghai')
        
        # 使用 nowfun 让 crontab 使用本地时区判断
        return crontab(
            minute=self.minute,
            hour=self.hour,
            day_of_week=self.day_of_week,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year,
            nowfun=lambda: datetime.now(tz),
        )


class PeriodicTask(Model, TimestampMixin):
    """
    定时任务模型
    类似 django-celery-beat 的 PeriodicTask
    """
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=200, unique=True, description="任务名称")
    task = fields.CharField(max_length=200, description="任务路径 (如: celery_app.tasks.general_tasks.test_periodic_task)")
    
    # 调度方式 (二选一)
    interval = fields.ForeignKeyField(
        "models.IntervalSchedule", 
        related_name="periodic_tasks", 
        null=True,
        on_delete=fields.SET_NULL,
        description="间隔调度"
    )
    crontab = fields.ForeignKeyField(
        "models.CrontabSchedule", 
        related_name="periodic_tasks", 
        null=True,
        on_delete=fields.SET_NULL,
        description="Crontab调度"
    )
    
    # 任务参数
    args = fields.TextField(default="[]", description="位置参数 (JSON格式)")
    kwargs = fields.TextField(default="{}", description="关键字参数 (JSON格式)")
    
    # 任务配置
    queue = fields.CharField(max_length=200, null=True, description="队列名称")
    exchange = fields.CharField(max_length=200, null=True, description="交换机")
    routing_key = fields.CharField(max_length=200, null=True, description="路由键")
    priority = fields.IntField(null=True, description="优先级 (0-9)")
    
    # 过期设置
    expires = fields.DatetimeField(null=True, description="过期时间")
    expire_seconds = fields.IntField(null=True, description="过期秒数")
    
    # 执行控制
    one_off = fields.BooleanField(default=False, description="是否只执行一次")
    start_time = fields.DatetimeField(null=True, description="开始时间")
    enabled = fields.BooleanField(default=True, description="是否启用")
    
    # 执行统计
    last_run_at = fields.DatetimeField(null=True, description="上次运行时间")
    total_run_count = fields.IntField(default=0, description="总运行次数")
    date_changed = fields.DatetimeField(auto_now=True, description="修改时间")
    
    # 描述
    description = fields.TextField(null=True, description="任务描述")
    
    class Meta:
        table = "celery_periodic_task"
        table_description = "定时任务表"
    
    def __str__(self):
        return self.name
    
    @property
    def schedule_display(self):
        """显示调度信息"""
        if self.interval_id:
            return f"间隔: 每 {self.interval}"
        elif self.crontab_id:
            return f"Crontab: {self.crontab}"
        return "未设置调度"
    
    def get_args(self):
        """获取位置参数"""
        try:
            return json.loads(self.args) if self.args else []
        except json.JSONDecodeError:
            return []
    
    def get_kwargs(self):
        """获取关键字参数"""
        try:
            return json.loads(self.kwargs) if self.kwargs else {}
        except json.JSONDecodeError:
            return {}


class PeriodicTaskChanged(Model):
    """
    定时任务变更标记
    用于通知 Celery Beat 重新加载配置
    """
    id = fields.IntField(pk=True)
    last_update = fields.DatetimeField(auto_now=True, description="最后更新时间")
    
    class Meta:
        table = "celery_periodic_task_changed"
        table_description = "定时任务变更标记表"
    
    @classmethod
    async def update_changed(cls):
        """更新变更标记"""
        obj, _ = await cls.get_or_create(id=1)
        obj.last_update = datetime.utcnow()
        await obj.save()
        return obj


class TaskResult(Model):
    """
    任务执行结果模型
    记录任务执行历史
    """
    id = fields.IntField(pk=True)
    task_id = fields.CharField(max_length=255, unique=True, description="任务ID")
    task_name = fields.CharField(max_length=255, null=True, index=True, description="任务名称")
    task_args = fields.TextField(null=True, description="任务参数")
    task_kwargs = fields.TextField(null=True, description="任务关键字参数")
    status = fields.CharField(max_length=50, default="PENDING", index=True, description="状态")
    result = fields.TextField(null=True, description="执行结果")
    traceback = fields.TextField(null=True, description="错误堆栈")
    date_created = fields.DatetimeField(auto_now_add=True, description="创建时间")
    date_done = fields.DatetimeField(null=True, description="完成时间")
    worker = fields.CharField(max_length=100, null=True, description="执行的Worker")
    
    # 任务状态常量
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"
    
    class Meta:
        table = "celery_task_result"
        table_description = "任务执行结果表"
    
    def __str__(self):
        return f"{self.task_name}[{self.task_id}] - {self.status}"


# ============================================================================
# 注意：不使用自动信号处理
# 原因：任务正常执行时更新 last_run_at/total_run_count 不应触发配置重载
# 只有通过 Admin API 修改任务配置时，才需要手动调用 PeriodicTaskChanged.update_changed()
# ============================================================================