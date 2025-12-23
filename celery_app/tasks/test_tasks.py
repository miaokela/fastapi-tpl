"""
测试任务模块
"""
from celery_app.celery import celery_app


@celery_app.task(name="celery_app.tasks.test_tasks.hello_world")
def hello_world():
    """打印 Hello World 的测试任务"""
    print("Hello World!")
    return "Hello World!"
