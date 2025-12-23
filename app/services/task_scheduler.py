"""
定时任务调度服务
提供类似 django-celery-beat 的功能
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from tortoise.exceptions import DoesNotExist

from app.models.models import (
    IntervalSchedule,
    CrontabSchedule,
    PeriodicTask,
    PeriodicTaskChanged,
    TaskResult,
)


class TaskSchedulerService:
    """定时任务调度服务"""
    
    # ==================== 间隔调度管理 ====================
    
    @staticmethod
    async def create_interval(every: int, period: str) -> IntervalSchedule:
        """创建间隔调度"""
        if period not in ["days", "hours", "minutes", "seconds", "microseconds"]:
            raise ValueError(f"无效的间隔类型: {period}")
        
        schedule, created = await IntervalSchedule.get_or_create(
            every=every,
            period=period
        )
        return schedule
    
    @staticmethod
    async def get_interval(interval_id: int) -> Optional[IntervalSchedule]:
        """获取间隔调度"""
        try:
            return await IntervalSchedule.get(id=interval_id)
        except DoesNotExist:
            return None
    
    @staticmethod
    async def list_intervals() -> List[IntervalSchedule]:
        """列出所有间隔调度"""
        return await IntervalSchedule.all()
    
    @staticmethod
    async def delete_interval(interval_id: int) -> bool:
        """删除间隔调度"""
        deleted_count = await IntervalSchedule.filter(id=interval_id).delete()
        if deleted_count > 0:
            await PeriodicTaskChanged.update_changed()
            return True
        return False
    
    # ==================== Crontab调度管理 ====================
    
    @staticmethod
    async def create_crontab(
        minute: str = "*",
        hour: str = "*",
        day_of_week: str = "*",
        day_of_month: str = "*",
        month_of_year: str = "*",
        timezone: str = "Asia/Shanghai"
    ) -> CrontabSchedule:
        """创建 Crontab 调度"""
        schedule = await CrontabSchedule.create(
            minute=minute,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            month_of_year=month_of_year,
            timezone=timezone
        )
        return schedule
    
    @staticmethod
    async def get_crontab(crontab_id: int) -> Optional[CrontabSchedule]:
        """获取 Crontab 调度"""
        try:
            return await CrontabSchedule.get(id=crontab_id)
        except DoesNotExist:
            return None
    
    @staticmethod
    async def list_crontabs() -> List[CrontabSchedule]:
        """列出所有 Crontab 调度"""
        return await CrontabSchedule.all()
    
    @staticmethod
    async def delete_crontab(crontab_id: int) -> bool:
        """删除 Crontab 调度"""
        deleted_count = await CrontabSchedule.filter(id=crontab_id).delete()
        if deleted_count > 0:
            await PeriodicTaskChanged.update_changed()
            return True
        return False
    
    # ==================== 定时任务管理 ====================
    
    @staticmethod
    async def create_periodic_task(
        name: str,
        task: str,
        interval_id: Optional[int] = None,
        crontab_id: Optional[int] = None,
        args: List = None,
        kwargs: Dict = None,
        queue: Optional[str] = None,
        priority: Optional[int] = None,
        expires: Optional[datetime] = None,
        one_off: bool = False,
        start_time: Optional[datetime] = None,
        enabled: bool = True,
        description: Optional[str] = None
    ) -> PeriodicTask:
        """创建定时任务"""
        if not interval_id and not crontab_id:
            raise ValueError("必须指定 interval_id 或 crontab_id")
        
        if interval_id and crontab_id:
            raise ValueError("只能指定 interval_id 或 crontab_id 其中之一")
        
        periodic_task = await PeriodicTask.create(
            name=name,
            task=task,
            interval_id=interval_id,
            crontab_id=crontab_id,
            args=json.dumps(args or []),
            kwargs=json.dumps(kwargs or {}),
            queue=queue,
            priority=priority,
            expires=expires,
            one_off=one_off,
            start_time=start_time,
            enabled=enabled,
            description=description
        )
        
        # 标记任务已变更
        await PeriodicTaskChanged.update_changed()
        
        return periodic_task
    
    @staticmethod
    async def get_periodic_task(task_id: int) -> Optional[PeriodicTask]:
        """获取定时任务"""
        try:
            return await PeriodicTask.get(id=task_id).prefetch_related("interval", "crontab")
        except DoesNotExist:
            return None
    
    @staticmethod
    async def get_periodic_task_by_name(name: str) -> Optional[PeriodicTask]:
        """根据名称获取定时任务"""
        try:
            return await PeriodicTask.get(name=name).prefetch_related("interval", "crontab")
        except DoesNotExist:
            return None
    
    @staticmethod
    async def list_periodic_tasks(
        enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PeriodicTask]:
        """列出定时任务"""
        query = PeriodicTask.all()
        
        if enabled is not None:
            query = query.filter(enabled=enabled)
        
        return await query.offset(offset).limit(limit).prefetch_related("interval", "crontab")
    
    @staticmethod
    async def update_periodic_task(
        task_id: int,
        **kwargs
    ) -> Optional[PeriodicTask]:
        """更新定时任务"""
        try:
            task = await PeriodicTask.get(id=task_id)
        except DoesNotExist:
            return None
        
        # 处理 args 和 kwargs 参数
        if "args" in kwargs and isinstance(kwargs["args"], list):
            kwargs["args"] = json.dumps(kwargs["args"])
        if "kwargs" in kwargs and isinstance(kwargs["kwargs"], dict):
            kwargs["kwargs"] = json.dumps(kwargs["kwargs"])
        
        # 检查调度配置是否改变（参考 django-celery-beat 逻辑）
        # 如果 interval 或 crontab 改变，需要重置 last_run_at
        schedule_changed = False
        if "interval_id" in kwargs and kwargs["interval_id"] != task.interval_id:
            schedule_changed = True
        if "crontab_id" in kwargs and kwargs["crontab_id"] != task.crontab_id:
            schedule_changed = True
        
        # 更新字段
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        # 如果调度配置改变，重置 last_run_at 让新调度立即生效
        if schedule_changed:
            task.last_run_at = None
        
        await task.save()
        
        # 标记任务已变更
        await PeriodicTaskChanged.update_changed()
        
        return task
    
    @staticmethod
    async def delete_periodic_task(task_id: int) -> bool:
        """删除定时任务"""
        deleted_count = await PeriodicTask.filter(id=task_id).delete()
        if deleted_count > 0:
            await PeriodicTaskChanged.update_changed()
            return True
        return False
    
    @staticmethod
    async def enable_task(task_id: int) -> bool:
        """启用任务"""
        task = await TaskSchedulerService.update_periodic_task(task_id, enabled=True)
        return task is not None
    
    @staticmethod
    async def disable_task(task_id: int) -> bool:
        """禁用任务"""
        task = await TaskSchedulerService.update_periodic_task(task_id, enabled=False)
        return task is not None
    
    @staticmethod
    async def run_task_now(task_id: int) -> Optional[str]:
        """立即执行任务"""
        from celery_app.celery import celery_app
        
        try:
            task = await PeriodicTask.get(id=task_id)
        except DoesNotExist:
            return None
        
        # 发送任务到 Celery
        result = celery_app.send_task(
            task.task,
            args=task.get_args(),
            kwargs=task.get_kwargs(),
            queue=task.queue
        )
        
        return result.id
    
    # ==================== 任务结果管理 ====================
    
    @staticmethod
    async def save_task_result(
        task_id: str,
        task_name: str,
        status: str,
        result: Any = None,
        traceback: str = None,
        args: str = None,
        kwargs: str = None,
        worker: str = None
    ) -> TaskResult:
        """保存任务执行结果"""
        task_result, created = await TaskResult.get_or_create(
            task_id=task_id,
            defaults={
                "task_name": task_name,
                "status": status,
                "result": json.dumps(result) if result else None,
                "traceback": traceback,
                "task_args": args,
                "task_kwargs": kwargs,
                "worker": worker,
            }
        )
        
        if not created:
            task_result.status = status
            task_result.result = json.dumps(result) if result else None
            task_result.traceback = traceback
            if status in [TaskResult.SUCCESS, TaskResult.FAILURE]:
                task_result.date_done = datetime.utcnow()
            await task_result.save()
        
        return task_result
    
    @staticmethod
    async def get_task_result(task_id: str) -> Optional[TaskResult]:
        """获取任务执行结果"""
        try:
            return await TaskResult.get(task_id=task_id)
        except DoesNotExist:
            return None
    
    @staticmethod
    async def list_task_results(
        task_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TaskResult]:
        """列出任务执行结果"""
        query = TaskResult.all()
        
        if task_name:
            query = query.filter(task_name=task_name)
        if status:
            query = query.filter(status=status)
        
        return await query.order_by("-date_created").offset(offset).limit(limit)
    
    @staticmethod
    async def cleanup_old_results(days: int = 30) -> int:
        """清理旧的任务结果"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = await TaskResult.filter(date_created__lt=cutoff_date).delete()
        return deleted_count
    
    # ==================== 调度信息获取 ====================
    
    @staticmethod
    async def get_all_schedules() -> Dict[str, Any]:
        """获取所有启用的调度配置（供 Celery Beat 使用）"""
        tasks = await PeriodicTask.filter(enabled=True).prefetch_related("interval", "crontab")
        
        schedules = {}
        for task in tasks:
            schedule_config = {
                "task": task.task,
                "args": task.get_args(),
                "kwargs": task.get_kwargs(),
            }
            
            if task.interval:
                schedule_config["schedule"] = task.interval.schedule
            elif task.crontab:
                schedule_config["schedule"] = task.crontab.schedule
            else:
                continue
            
            if task.queue:
                schedule_config["options"] = {"queue": task.queue}
            if task.priority is not None:
                schedule_config.setdefault("options", {})["priority"] = task.priority
            
            schedules[task.name] = schedule_config
        
        return schedules
    
    @staticmethod
    async def get_task_statistics() -> Dict[str, Any]:
        """获取任务统计信息"""
        total_tasks = await PeriodicTask.all().count()
        enabled_tasks = await PeriodicTask.filter(enabled=True).count()
        disabled_tasks = await PeriodicTask.filter(enabled=False).count()
        
        total_results = await TaskResult.all().count()
        success_results = await TaskResult.filter(status=TaskResult.SUCCESS).count()
        failure_results = await TaskResult.filter(status=TaskResult.FAILURE).count()
        pending_results = await TaskResult.filter(status=TaskResult.PENDING).count()
        
        return {
            "periodic_tasks": {
                "total": total_tasks,
                "enabled": enabled_tasks,
                "disabled": disabled_tasks
            },
            "task_results": {
                "total": total_results,
                "success": success_results,
                "failure": failure_results,
                "pending": pending_results
            }
        }
