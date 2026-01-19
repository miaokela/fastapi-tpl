"""
自定义 Celery Beat 调度器
从数据库读取定时任务配置，类似 django-celery-beat

核心逻辑（参考 django-celery-beat）：
1. ModelEntry.__next__() 更新 last_run_at 和 total_run_count
2. reserve() 调用 next(entry) 并将任务名加入 _dirty 集合
3. sync() 将 _dirty 中的任务保存到数据库
4. schedule_changed() 检查 PeriodicTaskChanged 时间戳判断是否需要重载
5. schedule 属性在检测到变更时先 sync() 再重载
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from celery.beat import Scheduler, ScheduleEntry
from celery import schedules
from celery.utils.log import get_logger
from tortoise import Tortoise

from config.database import DATABASE_CONFIG

logger = get_logger(__name__)

# 默认最大检查间隔（秒）
DEFAULT_MAX_INTERVAL = 5


def now_utc():
    """返回带时区信息的UTC当前时间"""
    return datetime.now(timezone.utc)


class DatabaseScheduleEntry(ScheduleEntry):
    """
    数据库调度条目
    参考 django-celery-beat 的 ModelEntry
    """
    
    # 需要保存到数据库的字段
    save_fields = ['last_run_at', 'total_run_count']
    
    def __init__(self, task_model, app=None, **kwargs):
        self.task_model = task_model
        self.model_id = task_model.id
        self.app = app
        
        # 获取调度 schedule 对象
        if task_model.interval:
            schedule = task_model.interval.schedule
        elif task_model.crontab:
            schedule = task_model.crontab.schedule
        else:
            # 默认60秒
            schedule = schedules.schedule(timedelta(seconds=60))
        
        # 获取参数
        args = task_model.get_args()
        kwargs_dict = task_model.get_kwargs()
        
        # 构建 options
        options = {}
        if task_model.queue:
            options['queue'] = task_model.queue
        if task_model.priority is not None:
            options['priority'] = task_model.priority
        if task_model.expires:
            options['expires'] = task_model.expires
        
        # 处理 last_run_at
        # 当 last_run_at 为空时，设为昨天，让 celery crontab 的 is_due 返回 True
        # 但我们会在 is_due() 中额外判断是否真正到了触发时间（1秒阈值）
        if not task_model.last_run_at:
            task_model.last_run_at = now_utc() - timedelta(days=1)
        
        super().__init__(
            name=task_model.name,
            task=task_model.task,
            schedule=schedule,
            args=tuple(args),
            kwargs=kwargs_dict,
            options=options,
            last_run_at=task_model.last_run_at,
            total_run_count=task_model.total_run_count or 0,
            app=app
        )
    
    def __next__(self):
        """
        返回下一个实例，更新 last_run_at 和 total_run_count
        这是 django-celery-beat 的核心机制
        """
        # 更新 task_model 的运行信息
        self.task_model.last_run_at = now_utc()
        self.task_model.total_run_count = (self.task_model.total_run_count or 0) + 1
        
        # 返回新的 Entry 实例
        return self.__class__(self.task_model, app=self.app)
    
    def is_due(self):
        """
        检查任务是否应该执行
        完全参考 django-celery-beat 的 ModelEntry.is_due()
        """
        # 1. 任务被禁用 - 5秒后重新检查
        if not self.task_model.enabled:
            return schedules.schedstate(False, 5.0)
        
        # 2. START DATE: 只有在 start_time 之后才执行
        if self.task_model.start_time is not None:
            now = now_utc()
            if now < self.task_model.start_time:
                # 还没到开始时间，计算剩余等待时间
                time_remaining = (self.task_model.start_time - now).total_seconds()
                delay = max(1.0, time_remaining)
                # logger.debug(f"[IS_DUE] Task {self.name}: waiting for start_time, {delay:.0f}s remaining")
                return schedules.schedstate(False, delay)
        
        # 3. EXPIRED: 任务过期则禁用（如果有 expires 字段）
        if self.task_model.expires is not None:
            now = now_utc()
            if now >= self.task_model.expires:
                # logger.info(f"[IS_DUE] Task {self.name}: expired, disabling")
                # 注意：这里不直接修改数据库，只返回不执行
                return schedules.schedstate(False, 86400)  # 1天后重检查
        
        # 4. ONE OFF: 一次性任务执行后不再执行
        if self.task_model.one_off and self.task_model.total_run_count > 0:
            # logger.info(f"[IS_DUE] Task {self.name}: one_off task already executed")
            return schedules.schedstate(False, 86400)  # 1天后重检查
        
        # 5. 调用 Celery schedule 的 is_due 方法
        is_due, next_time_to_run = self.schedule.is_due(self.last_run_at)
        # logger.info(f"[IS_DUE] Task {self.name}: is_due={is_due}, next_time={next_time_to_run:.0f}s, last_run_at={self.last_run_at}")

        # 对于 crontab 调度，需要特殊处理
        # crontab 在 is_due=True 时会立即执行，不管 next_time
        # 所以如果 next_time > 1秒，说明还没到真正的触发时间
        if self.task_model.crontab and is_due and next_time_to_run > 1:
            # 还没到触发时间，返回 False，让 beat 继续等待
            # logger.info(f"[IS_DUE] Not yet due for {self.name}, waiting {next_time_to_run:.0f}s")
            return schedules.schedstate(False, min(next_time_to_run, 5))  # 最多等 5 秒后再检查

        return schedules.schedstate(is_due, next_time_to_run)
    
    def save(self):
        """保存任务运行信息到数据库（异步）"""
        # 这个方法会被 DatabaseScheduler.sync() 调用
        pass  # 实际保存由 DatabaseScheduler._save_entry() 处理
    
    def __repr__(self):
        return f"<DatabaseScheduleEntry: {self.name} ({self.task})>"


class DatabaseScheduler(Scheduler):
    """
    数据库调度器
    从 SQLite 数据库读取定时任务配置
    参考 django-celery-beat 的 DatabaseScheduler
    """
    
    Entry = DatabaseScheduleEntry
    
    # 同步间隔（秒）
    sync_every = 5
    
    # 数据库变更检查间隔
    UPDATE_INTERVAL = 5
    
    def __init__(self, *args, **kwargs):
        self._schedule: Dict[str, DatabaseScheduleEntry] = {}
        self._dirty: set = set()  # 需要保存的任务名集合
        self._last_timestamp: Optional[datetime] = None
        self._initial_read = True
        self._loop = None
        super().__init__(*args, **kwargs)
        self.max_interval = kwargs.get('max_interval') or DEFAULT_MAX_INTERVAL
    
    def _get_or_create_loop(self):
        """获取或创建事件循环"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    
    def _run_async(self, coro):
        """运行异步协程"""
        loop = self._get_or_create_loop()
        return loop.run_until_complete(coro)
    
    async def _init_db(self):
        """初始化数据库连接"""
        if not Tortoise._inited:
            await Tortoise.init(config=DATABASE_CONFIG)
            logger.info("Database connection initialized for scheduler")
    
    async def _close_db(self):
        """关闭数据库连接"""
        await Tortoise.close_connections()
    
    async def _get_changed_timestamp(self):
        """获取变更时间戳"""
        from app.models.models import PeriodicTaskChanged
        
        await self._init_db()
        
        try:
            marker = await PeriodicTaskChanged.get_or_none(id=1)
            return marker.last_update if marker else None
        except Exception as e:
            logger.error(f"Error getting change marker: {e}")
            return None
    
    async def _load_entries_from_db(self):
        """从数据库加载任务条目"""
        from app.models.models import PeriodicTask
        
        await self._init_db()
        
        try:
            tasks = await PeriodicTask.filter(enabled=True).prefetch_related("interval", "crontab")
            
            entries = {}
            for task in tasks:
                try:
                    entry = DatabaseScheduleEntry(task, app=self.app)
                    entries[task.name] = entry
                    logger.debug(f"Loaded task: {task.name}")
                except Exception as e:
                    logger.error(f"Error loading task {task.name}: {e}")
            
            return entries
        except Exception as e:
            logger.error(f"Error loading tasks from database: {e}")
            return {}
    
    async def _save_entry(self, entry: DatabaseScheduleEntry):
        """保存单个任务的运行信息到数据库"""
        from app.models.models import PeriodicTask
        
        await self._init_db()
        
        try:
            task = await PeriodicTask.get_or_none(name=entry.name)
            if task:
                task.last_run_at = entry.task_model.last_run_at
                task.total_run_count = entry.task_model.total_run_count
                await task.save(update_fields=['last_run_at', 'total_run_count', 'updated_at'])
                logger.debug(f"Saved task {entry.name}: last_run={task.last_run_at}, count={task.total_run_count}")
        except Exception as e:
            logger.error(f"Error saving task {entry.name}: {e}")
    
    def setup_schedule(self):
        """设置调度"""
        logger.info("Setting up database scheduler...")
        self._run_async(self._init_db())
        self._schedule = self._run_async(self._load_entries_from_db())
        logger.info(f"Loaded {len(self._schedule)} tasks from database")
    
    def schedule_changed(self):
        """
        检查配置是否已变更
        通过比较 PeriodicTaskChanged 时间戳判断
        """
        try:
            ts = self._run_async(self._get_changed_timestamp())
            
            if ts and ts > (self._last_timestamp if self._last_timestamp else ts):
                # 时间戳有变化，需要重载
                return True
            
            # 更新本地时间戳
            self._last_timestamp = ts
            return False
        except Exception as e:
            logger.error(f"Error checking schedule changes: {e}")
            return False
    
    @property
    def schedule(self):
        """
        获取调度表
        参考 django-celery-beat 的实现：
        1. 首次读取时加载
        2. 检测到变更时先 sync() 再重载
        """
        update = False
        
        if self._initial_read:
            logger.debug('DatabaseScheduler: initial read')
            update = True
            self._initial_read = False
        elif self.schedule_changed():
            logger.info('DatabaseScheduler: Schedule changed, reloading...')
            update = True
        
        if update:
            # 先同步脏数据到数据库
            self.sync()
            # 再从数据库重新加载
            self._schedule = self._run_async(self._load_entries_from_db())
            # 更新时间戳
            self._last_timestamp = self._run_async(self._get_changed_timestamp())
            logger.info(f"Reloaded {len(self._schedule)} tasks from database")
        
        return self._schedule
    
    def reserve(self, entry):
        """
        预留任务条目 - 在任务发送前调用
        参考 django-celery-beat：调用 next(entry) 并加入 _dirty 集合
        """
        # 调用 __next__ 更新 last_run_at 和 total_run_count
        new_entry = next(entry)
        
        # 将任务名加入脏数据集合，等待 sync() 保存
        self._dirty.add(new_entry.name)
        
        # 更新内存中的 schedule
        self._schedule[new_entry.name] = new_entry
        
        logger.debug(f"Reserved task {new_entry.name}: count={new_entry.total_run_count}, last_run={new_entry.last_run_at}")
        
        return new_entry
    
    def sync(self):
        """
        同步脏数据到数据库
        参考 django-celery-beat：只保存 _dirty 集合中的任务
        """
        if not self._dirty:
            return
        
        logger.debug(f"Syncing {len(self._dirty)} dirty tasks to database")
        
        while self._dirty:
            name = self._dirty.pop()
            try:
                entry = self._schedule.get(name)
                if entry:
                    self._run_async(self._save_entry(entry))
            except KeyError:
                pass
            except Exception as e:
                logger.error(f"Error syncing task {name}: {e}")
                # 失败的任务重新加入脏数据集合
                self._dirty.add(name)
                break
    
    def close(self):
        """关闭调度器"""
        self.sync()
        self._run_async(self._close_db())
        super().close()
    
    @property
    def info(self):
        """调度器信息"""
        return f"DatabaseScheduler: {len(self._schedule)} tasks"
