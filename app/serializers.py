"""
序列化器定义
使用 Tortoise ORM 的 pydantic_model_creator 自动生成 Pydantic 模型
"""
from tortoise.contrib.pydantic import pydantic_model_creator
from app.models.models import (
    User, UserProfile,
    IntervalSchedule, CrontabSchedule, PeriodicTask, TaskResult
)


# 用户相关序列化器
UserSerializer = pydantic_model_creator(User)
UserProfileSerializer = pydantic_model_creator(UserProfile)

# Celery 定时任务相关序列化器
IntervalScheduleSerializer = pydantic_model_creator(IntervalSchedule)
CrontabScheduleSerializer = pydantic_model_creator(CrontabSchedule)
PeriodicTaskSerializer = pydantic_model_creator(PeriodicTask)
TaskResultSerializer = pydantic_model_creator(TaskResult)
