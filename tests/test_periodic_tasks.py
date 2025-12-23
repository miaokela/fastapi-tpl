#!/usr/bin/env python3
"""
定时任务测试脚本
测试周期任务和定时任务的执行情况
"""
import asyncio
import sys
from datetime import datetime, timedelta
from tortoise import Tortoise
from config.database import DATABASE_CONFIG
from app.models.models import (
    IntervalSchedule, CrontabSchedule, PeriodicTask, TaskResult
)


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(config=DATABASE_CONFIG)


async def close_db():
    """关闭数据库连接"""
    await Tortoise.close_connections()


async def list_tasks():
    """列出所有定时任务"""
    print("\n" + "="*80)
    print("当前所有定时任务:")
    print("="*80)
    
    tasks = await PeriodicTask.all().prefetch_related('interval', 'crontab')
    
    if not tasks:
        print("❌ 没有找到任何定时任务")
        return
    
    for task in tasks:
        print(f"\n📋 任务 ID: {task.id}")
        print(f"   名称: {task.name}")
        print(f"   任务路径: {task.task}")
        print(f"   是否启用: {'✅ 是' if task.enabled else '❌ 否'}")
        
        if task.interval:
            print(f"   调度类型: Interval (周期任务)")
            print(f"   调度: 每 {task.interval.every} {task.interval.period}")
        elif task.crontab:
            print(f"   调度类型: Crontab (定时任务)")
            print(f"   调度: {task.crontab}")
        
        print(f"   总运行次数: {task.total_run_count}")
        print(f"   最后运行时间: {task.last_run_at or '从未运行'}")
        print(f"   创建时间: {task.created_at}")
        print(f"   更新时间: {task.updated_at}")


async def check_task_results(task_name=None, limit=10):
    """检查任务执行结果"""
    print("\n" + "="*80)
    print(f"任务执行结果 (最近{limit}条):")
    print("="*80)
    
    query = TaskResult.all().order_by('-date_created').limit(limit)
    if task_name:
        query = query.filter(task_name__contains=task_name)
    
    results = await query
    
    if not results:
        print("❌ 没有找到任何执行结果")
        return
    
    for result in results:
        status_emoji = {
            "SUCCESS": "✅",
            "FAILURE": "❌",
            "STARTED": "🔄",
            "PENDING": "⏳",
            "REVOKED": "🚫"
        }.get(result.status, "❓")
        
        print(f"\n{status_emoji} {result.task_name}")
        print(f"   Task ID: {result.task_id}")
        print(f"   状态: {result.status}")
        print(f"   创建时间: {result.date_created}")
        print(f"   完成时间: {result.date_done or '未完成'}")
        if result.result:
            print(f"   结果: {result.result[:100]}")
        if result.traceback:
            print(f"   错误: {result.traceback[:200]}")


async def disable_task(task_name):
    """禁用指定任务"""
    task = await PeriodicTask.filter(name=task_name).first()
    if not task:
        print(f"❌ 未找到任务: {task_name}")
        return
    
    task.enabled = False
    await task.save()
    print(f"✅ 已禁用任务: {task_name}")


async def enable_task(task_name):
    """启用指定任务"""
    task = await PeriodicTask.filter(name=task_name).first()
    if not task:
        print(f"❌ 未找到任务: {task_name}")
        return
    
    task.enabled = True
    await task.save()
    print(f"✅ 已启用任务: {task_name}")


async def create_test_interval_task():
    """创建测试用的周期任务（每10秒执行一次）"""
    print("\n" + "="*80)
    print("创建测试周期任务 (Interval):")
    print("="*80)
    
    # 检查是否已存在
    existing = await PeriodicTask.filter(name="test-interval-10s").first()
    if existing:
        print(f"⚠️  任务已存在，将先删除旧任务...")
        await existing.delete()
    
    # 创建或获取间隔调度（每10秒）
    interval, created = await IntervalSchedule.get_or_create(
        every=10,
        period="seconds"
    )
    action = "创建" if created else "使用已存在"
    print(f"✅ {action}间隔调度: 每 {interval.every} {interval.period}")
    
    # 创建定时任务
    task = await PeriodicTask.create(
        name="test-interval-10s",
        task="celery_app.tasks.test_tasks.hello_world",
        interval=interval,
        enabled=True,
        description="测试任务 - 每10秒执行一次"
    )
    print(f"✅ 创建定时任务: {task.name}")
    print(f"   任务路径: {task.task}")
    print(f"   调度: 每 {interval.every} {interval.period}")
    print(f"   状态: {'已启用' if task.enabled else '已禁用'}")


async def create_test_crontab_task():
    """创建测试用的Crontab定时任务（每分钟执行一次）"""
    print("\n" + "="*80)
    print("创建测试定时任务 (Crontab):")
    print("="*80)
    
    # 检查是否已存在
    existing = await PeriodicTask.filter(name="test-crontab-every-minute").first()
    if existing:
        print(f"⚠️  任务已存在，将先删除旧任务...")
        await existing.delete()
    
    # 创建Crontab调度（每分钟的第0秒）
    crontab = await CrontabSchedule.create(
        minute="*",  # 每分钟
        hour="*",
        day_of_month="*",
        month_of_year="*",
        day_of_week="*",
        timezone="Asia/Shanghai"
    )
    print(f"✅ 创建Crontab调度: {crontab}")
    
    # 创建定时任务
    task = await PeriodicTask.create(
        name="test-crontab-every-minute",
        task="celery_app.tasks.test_tasks.hello_world",
        crontab=crontab,
        enabled=True,
        description="测试任务 - 每分钟执行一次"
    )
    print(f"✅ 创建定时任务: {task.name}")
    print(f"   任务路径: {task.task}")
    print(f"   调度: {crontab}")
    print(f"   状态: {'已启用' if task.enabled else '已禁用'}")


async def verify_task_fields():
    """验证定时任务相关字段是否有意义并写入正常"""
    print("\n" + "="*80)
    print("验证任务字段数据完整性:")
    print("="*80)
    
    tasks = await PeriodicTask.all().prefetch_related('interval', 'crontab')
    
    for task in tasks:
        print(f"\n📋 验证任务: {task.name}")
        
        # 检查基本字段
        checks = {
            "任务名称": task.name is not None and len(task.name) > 0,
            "任务路径": task.task is not None and len(task.task) > 0,
            "启用状态": isinstance(task.enabled, bool),
            "运行次数": isinstance(task.total_run_count, int) and task.total_run_count >= 0,
            "创建时间": task.created_at is not None,
            "更新时间": task.updated_at is not None,
        }
        
        # 检查调度配置
        has_interval = task.interval_id is not None
        has_crontab = task.crontab_id is not None
        checks["调度配置"] = (has_interval or has_crontab) and not (has_interval and has_crontab)
        
        # 检查最后运行时间的合理性
        if task.last_run_at:
            checks["最后运行时间"] = task.last_run_at <= datetime.utcnow()
        else:
            checks["最后运行时间"] = task.total_run_count == 0  # 如果从未运行，运行次数应为0
        
        # 输出检查结果
        all_passed = True
        for check_name, passed in checks.items():
            emoji = "✅" if passed else "❌"
            print(f"   {emoji} {check_name}: {passed}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"   ✅ 所有字段验证通过")
        else:
            print(f"   ❌ 存在字段验证失败")


async def delete_all_tasks():
    """删除所有测试任务（谨慎使用）"""
    print("\n" + "="*80)
    print("⚠️  删除所有定时任务:")
    print("="*80)
    
    # 删除所有任务
    deleted = await PeriodicTask.all().delete()
    print(f"✅ 已删除 {deleted} 个定时任务")
    
    # 删除所有调度
    interval_deleted = await IntervalSchedule.all().delete()
    crontab_deleted = await CrontabSchedule.all().delete()
    print(f"✅ 已删除 {interval_deleted} 个间隔调度")
    print(f"✅ 已删除 {crontab_deleted} 个Crontab调度")


async def main():
    """主函数"""
    await init_db()
    
    try:
        if len(sys.argv) < 2:
            print("使用方法:")
            print("  python test_periodic_tasks.py list                      # 列出所有任务")
            print("  python test_periodic_tasks.py results [task_name]       # 查看任务执行结果")
            print("  python test_periodic_tasks.py create-interval           # 创建测试周期任务")
            print("  python test_periodic_tasks.py create-crontab            # 创建测试Crontab任务")
            print("  python test_periodic_tasks.py disable <task_name>       # 禁用任务")
            print("  python test_periodic_tasks.py enable <task_name>        # 启用任务")
            print("  python test_periodic_tasks.py verify                    # 验证字段完整性")
            print("  python test_periodic_tasks.py cleanup                   # 删除所有任务")
            return
        
        command = sys.argv[1]
        
        if command == "list":
            await list_tasks()
        elif command == "results":
            task_name = sys.argv[2] if len(sys.argv) > 2 else None
            await check_task_results(task_name)
        elif command == "create-interval":
            await create_test_interval_task()
        elif command == "create-crontab":
            await create_test_crontab_task()
        elif command == "disable":
            if len(sys.argv) < 3:
                print("❌ 请指定任务名称")
            else:
                await disable_task(sys.argv[2])
        elif command == "enable":
            if len(sys.argv) < 3:
                print("❌ 请指定任务名称")
            else:
                await enable_task(sys.argv[2])
        elif command == "verify":
            await verify_task_fields()
        elif command == "cleanup":
            confirm = input("⚠️  确认删除所有任务? (yes/no): ")
            if confirm.lower() == "yes":
                await delete_all_tasks()
            else:
                print("已取消")
        else:
            print(f"❌ 未知命令: {command}")
    
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
