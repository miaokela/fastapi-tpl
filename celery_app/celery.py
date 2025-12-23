from celery import Celery
from celery.signals import setup_logging as celery_setup_logging, task_prerun, task_success, task_failure, task_revoked
from config.settings import settings
import asyncio
from datetime import datetime, timedelta
import json
import traceback as tb

# 创建Celery应用
celery_app = Celery(
    "fastapi-base",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["celery_app.tasks.test_tasks"]
)


@celery_setup_logging.connect
def config_loggers(*args, **kwargs):
    """配置 Celery 使用统一的日志系统"""
    from config.logging import setup_logging
    setup_logging()

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务路由（使用默认 celery 队列）
    task_routes={
        "celery_app.tasks.test_tasks.*": {"queue": "celery"},
    },
    
    # 任务执行时间限制
    # task_time_limit: 硬时间限制（秒），超时后任务会被强制终止（SIGKILL）
    # task_soft_time_limit: 软时间限制（秒），超时后抛出 SoftTimeLimitExceeded 异常，任务可捕获该异常进行清理
    task_time_limit=300,  # 5分钟，超时强制终止
    task_soft_time_limit=240,  # 4分钟，超时抛出异常
    
    # 任务结果配置
    # result_expires: Redis中任务结果的过期时间（秒），0表示永不过期，1表示1秒后移除
    result_expires=1,  # 1秒后从Redis移除任务结果
    
    # 使用数据库调度器（类似 django-celery-beat）
    # 启动 beat 时使用: celery -A celery_app.celery beat -S celery_app.scheduler:DatabaseScheduler
    beat_scheduler="celery_app.scheduler:DatabaseScheduler",
    
    # 默认定时任务配置（仅在不使用数据库调度器时生效）
    # 使用数据库调度器后，这些配置将被忽略，所有定时任务通过 Admin 管理
    beat_schedule={},
)

# 自动发现任务
celery_app.autodiscover_tasks(["celery_app.tasks"])


# ============================================
# 任务结果记录信号处理
# ============================================

def run_async(coro):
    """在同步环境中运行异步代码"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


async def _save_task_result(
    task_id: str,
    task_name: str,
    status: str,
    result=None,
    traceback_str: str = None,
    args: str = None,
    kwargs: str = None,
    worker: str = None
):
    """保存任务结果到数据库"""
    from tortoise import Tortoise
    from app.models.models import TaskResult
    from config.database import DATABASE_CONFIG
    
    # 初始化数据库连接（如果还未连接）
    if not Tortoise._inited:
        await Tortoise.init(config=DATABASE_CONFIG)
    
    try:
        task_result, created = await TaskResult.get_or_create(
            task_id=task_id,
            defaults={
                "task_name": task_name,
                "status": status,
                "result": json.dumps(result) if result is not None else None,
                "traceback": traceback_str,
                "task_args": args,
                "task_kwargs": kwargs,
                "worker": worker,
            }
        )
        
        if not created:
            task_result.status = status
            task_result.result = json.dumps(result) if result is not None else None
            task_result.traceback = traceback_str
            task_result.worker = worker
            if status in [TaskResult.SUCCESS, TaskResult.FAILURE, TaskResult.REVOKED]:
                task_result.date_done = datetime.utcnow()
            await task_result.save()
        
        return task_result
    except Exception as e:
        print(f"保存任务结果失败: {e}")
        return None


async def _cleanup_old_results():
    """清理过期的任务结果"""
    from tortoise import Tortoise
    from app.models.models import TaskResult
    from config.database import DATABASE_CONFIG
    
    if not Tortoise._inited:
        await Tortoise.init(config=DATABASE_CONFIG)
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=settings.CELERY_TASK_RESULT_EXPIRES)
        deleted_count = await TaskResult.filter(date_created__lt=cutoff_date).delete()
        if deleted_count > 0:
            print(f"已清理 {deleted_count} 条过期任务结果记录")
    except Exception as e:
        print(f"清理任务结果失败: {e}")


@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **kw):
    """任务开始前记录"""
    try:
        run_async(_save_task_result(
            task_id=task_id,
            task_name=task.name,
            status="STARTED",
            args=json.dumps(args) if args else "[]",
            kwargs=json.dumps(kwargs) if kwargs else "{}",
            worker=task.request.hostname if hasattr(task.request, 'hostname') else None
        ))
    except Exception as e:
        print(f"记录任务开始失败: {e}")


@task_success.connect
def task_success_handler(sender, result, **kwargs):
    """任务成功时记录结果"""
    try:
        run_async(_save_task_result(
            task_id=sender.request.id,
            task_name=sender.name,
            status="SUCCESS",
            result=result,
            worker=sender.request.hostname if hasattr(sender.request, 'hostname') else None
        ))
        # 每次任务成功后，尝试清理过期记录（概率性清理，避免每次都清理）
        import random
        if random.random() < 0.01:  # 1%的概率触发清理
            run_async(_cleanup_old_results())
    except Exception as e:
        print(f"记录任务成功失败: {e}")


@task_failure.connect
def task_failure_handler(sender, task_id, exception, traceback, einfo, **kwargs):
    """任务失败时记录结果"""
    try:
        traceback_str = ''.join(tb.format_exception(type(exception), exception, traceback)) if traceback else str(exception)
        run_async(_save_task_result(
            task_id=task_id,
            task_name=sender.name,
            status="FAILURE",
            result=str(exception),
            traceback_str=traceback_str,
            worker=sender.request.hostname if hasattr(sender.request, 'hostname') else None
        ))
    except Exception as e:
        print(f"记录任务失败失败: {e}")


@task_revoked.connect
def task_revoked_handler(sender, request, terminated, signum, expired, **kwargs):
    """任务被撤销时记录"""
    try:
        run_async(_save_task_result(
            task_id=request.id,
            task_name=sender.name if sender else request.task,
            status="REVOKED",
            result=f"terminated={terminated}, signum={signum}, expired={expired}"
        ))
    except Exception as e:
        print(f"记录任务撤销失败: {e}")