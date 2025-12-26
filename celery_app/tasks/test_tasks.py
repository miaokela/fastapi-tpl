"""
测试任务模块
"""
from celery import chain
from datetime import datetime, timedelta, timezone
from celery_app.celery import celery_app


@celery_app.task(name="celery_app.tasks.test_tasks.hello_world")
def hello_world():
    """打印 Hello World 的测试任务"""
    print("Hello World!")
    return "Hello World!"


@celery_app.task(name="celery_app.tasks.test_tasks.revoke_api_func_for_backend")
def revoke_api_func_for_backend(method: str, url: str, json: dict = None, headers: dict = None):
    """
    调用后端 API 的任务
    Args:
        method: HTTP 方法 (post, get, etc.)
        url: 请求 URL
        json: 请求体数据
        headers: 请求头
    """
    print(f"调用后端 API: {method} {url}")
    print(f"请求头: {headers}")
    print(f"请求数据: {json}")
    return {"method": method, "url": url, "status": "success"}


@celery_app.task(name="celery_app.tasks.test_tasks.handle_delete_standard_material")
def handle_delete_standard_material(prev_result: dict = None, adv_id: str = None, material_id: str = None, ad_id: str = None):
    """
    处理删除标准素材的任务
    
    注意：在 chain 中，前一个任务的返回值会自动作为第一个参数传递
    Args:
        prev_result: 前一个任务的返回值（chain 自动传递）
        adv_id: 广告 ID
        material_id: 素材 ID
        ad_id: 广告 ID
    """
    print(f"前一个任务的结果: {prev_result}")
    print(f"删除标准素材: adv_id={adv_id}, material_id={material_id}, ad_id={ad_id}")
    return {
        "prev_result": prev_result,
        "adv_id": adv_id,
        "material_id": material_id,
        "ad_id": ad_id,
        "status": "deleted"
    }


@celery_app.task(name="celery_app.tasks.test_tasks.async_publish_uni_promotion_plan")
def async_publish_uni_promotion_plan(adv_id: str = None, material_id: str = None, retry_times: int = 0):
    """
    异步发布通用推广计划的任务（支持重试）
    Args:
        adv_id: 广告 ID
        material_id: 素材 ID
        retry_times: 重试次数
    """
    print(f"发布通用推广计划: adv_id={adv_id}, material_id={material_id}, retry_times={retry_times}")
    if retry_times < 3:
        print("任务执行成功")
        return {"adv_id": adv_id, "material_id": material_id, "status": "success"}
    else:
        print(f"重试次数过多: {retry_times}")
        return {"adv_id": adv_id, "material_id": material_id, "status": "failed", "retry_times": retry_times}


@celery_app.task(name="celery_app.tasks.test_tasks.chain_task_example")
def chain_task_example(url: str = "https://example.com/api", data: dict = None, headers: dict = None):
    """
    链式任务示例 1 - 展示如何使用 chain 进行任务链式调用
    注意：这种方式会覆盖 chain 默认传递返回值的行为
    
    Args:
        url: API URL
        data: 请求数据
        headers: 请求头
    """
    if data is None:
        data = {"key": "value"}
    if headers is None:
            headers = {"Content-Type": "application/json"}

    # 计算下次运行时间（当前时间 + 5分钟）
    next_run_time = datetime.now(timezone.utc) + timedelta(minutes=5)

    # 示例参数
    adv_id = "adv_123"
    material_id = "mat_456"
    ad_id = "ad_789"

    # 使用 chain 进行链式调用
    # 方式1: 明确指定所有参数（会覆盖默认的返回值传递）
    chain(
        revoke_api_func_for_backend.s("post", url, json=data, headers=headers).set(
            eta=next_run_time
        ),
        handle_delete_standard_material.s(adv_id, material_id, ad_id),
    ).apply_async(ignore_result=True)

    print(f"已启动链式任务，将在 {next_run_time} 执行")
    return {"status": "chain_started", "next_run_time": next_run_time.isoformat()}


@celery_app.task(name="celery_app.tasks.test_tasks.chain_task_with_prev_result")
def chain_task_with_prev_result(url: str = "https://example.com/api", data: dict = None, headers: dict = None):
    """
    链式任务示例 2 - 展示 chain 中使用前一个任务返回值的方式

    Args:
        url: API URL
        data: 请求数据
        headers: 请求头
    """
    if data is None:
        data = {"key": "value"}
    if headers is None:
        headers = {"Content-Type": "application/json"}

    # 计算下次运行时间（当前时间 + 5分钟）
    next_run_time = datetime.now(timezone.utc) + timedelta(minutes=5)

    # 示例参数
    adv_id = "adv_123"
    material_id = "mat_456"
    ad_id = "ad_789"

    # 使用 chain 进行链式调用
    # 方式2: 使用默认的返回值传递（前一个任务的返回值会自动作为第一个参数）
    # 这里使用 .s() 或不指定参数，让 chain 自动传递返回值
    # 然后使用部分参数或通过关键字参数指定后续参数
    chain(
        revoke_api_func_for_backend.s("post", url, json=data, headers=headers).set(
            eta=next_run_time
        ),
        handle_delete_standard_material.s(adv_id=adv_id, material_id=material_id, ad_id=ad_id),
    ).apply_async(ignore_result=True)

    print(f"已启动链式任务（使用返回值传递），将在 {next_run_time} 执行")
    return {"status": "chain_started_with_prev_result", "next_run_time": next_run_time.isoformat()}
