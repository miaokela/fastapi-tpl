#!/usr/bin/env python3
"""
Celery 任务集成测试
需要启动真实的 Celery worker 和消息代理（Redis/RabbitMQ）

使用方法：
1. 启动 Redis: docker run -d -p 6379:6379 redis
2. 启动 Celery worker: celery -A celery_app.celery worker --loglevel=info
3. 运行测试: pytest tests/test_celery_integration.py -v

注意：集成测试需要真实的 Redis/Celery worker 环境
"""
import pytest
import time
from datetime import datetime, timedelta, timezone
from celery.result import AsyncResult

from celery_app.tasks.test_tasks import (
    hello_world,
    revoke_api_func_for_backend,
    handle_delete_standard_material,
    async_publish_uni_promotion_plan,
    chain_task_example,
    chain_task_with_prev_result,
)
from celery_app.celery import celery_app


class TestCeleryIntegration:
    """Celery 任务集成测试 - 需要真实的 worker 环境"""

    @pytest.mark.integration
    def test_hello_world_sync(self):
        """测试 hello_world 任务（同步执行）"""
        result = hello_world()
        assert result == "Hello World!"

    @pytest.mark.integration
    def test_hello_world_async(self):
        """测试 hello_world 任务（异步执行，需要 worker）"""
        # 提交任务
        task_result = hello_world.apply_async()

        # 等待任务完成（最多 5 秒）
        task_result.get(timeout=5)

        # 验证结果
        assert task_result.status == "SUCCESS"
        assert task_result.result == "Hello World!"

    @pytest.mark.integration
    def test_revoke_api_func_for_backend_async(self):
        """测试 API 调用任务（异步执行）"""
        url = "https://example.com/api"
        data = {"key": "value"}
        headers = {"Content-Type": "application/json"}

        # 异步提交任务
        task_result = revoke_api_func_for_backend.apply_async(
            args=["post", url],
            kwargs={"json": data, "headers": headers}
        )

        # 等待任务完成
        result = task_result.get(timeout=5)

        # 验证结果
        assert result["method"] == "post"
        assert result["url"] == url
        assert result["status"] == "success"

    @pytest.mark.integration
    def test_handle_delete_standard_material_with_prev_result(self):
        """测试删除素材任务（带前一个任务结果）"""
        # 模拟前一个任务的结果
        prev_result = {"method": "post", "url": "https://example.com/api", "status": "success"}
        adv_id = "adv_123"
        material_id = "mat_456"
        ad_id = "ad_789"

        # 异步提交任务
        task_result = handle_delete_standard_material.apply_async(
            args=[prev_result, adv_id, material_id, ad_id]
        )

        # 等待任务完成
        result = task_result.get(timeout=5)

        # 验证结果
        assert result["prev_result"] == prev_result
        assert result["adv_id"] == adv_id
        assert result["material_id"] == material_id
        assert result["ad_id"] == ad_id
        assert result["status"] == "deleted"

    @pytest.mark.integration
    def test_async_publish_uni_promotion_plan_success(self):
        """测试推广计划任务（成功场景）"""
        retry_args = ["adv_123", "mat_456"]
        retry_times = 0

        # 异步提交任务
        task_result = async_publish_uni_promotion_plan.apply_async(
            args=retry_args,
            kwargs={"retry_times": retry_times},
            countdown=30,  # 30秒后重试
            queue="create_uni_plan",
        )

        # 注意：由于使用了 countdown=30，任务会在 30 秒后才执行
        # 这里我们验证任务已提交
        assert task_result.id is not None
        assert task_result.status in ["PENDING", "STARTED", "SUCCESS"]

        # 如果不想等待 30 秒，可以使用 celery.control.revoke() 撤销任务
        # 但为了完整测试，这里不撤销

    @pytest.mark.integration
    def test_async_publish_uni_promotion_plan_retry_exceeded(self):
        """测试推广计划任务（重试超限场景）"""
        retry_args = ["adv_123", "mat_456"]
        retry_times = 5  # 超过限制

        # 异步提交任务（不使用 countdown，立即执行）
        task_result = async_publish_uni_promotion_plan.apply_async(
            args=retry_args,
            kwargs={"retry_times": retry_times},
        )

        # 等待任务完成
        result = task_result.get(timeout=5)

        # 验证结果
        assert result["status"] == "failed"
        assert result["retry_times"] == 5

    @pytest.mark.integration
    def test_chain_task_example(self):
        """测试链式任务示例 1（覆盖返回值）"""
        # 同步调用，函数内部使用 chain.apply_async 提交子任务
        url = "https://example.com/api"
        data = {"test": "data"}
        headers = {"Authorization": "Bearer token"}

        result = chain_task_example(url, data, headers)

        # 验证返回值
        assert result["status"] == "chain_started"
        assert "next_run_time" in result

        # 注意：由于子任务设置了 eta（延迟执行），需要等待 5 分钟
        # 这里我们只验证 chain 已启动
        # 实际的子任务执行需要更长时间

    @pytest.mark.integration
    def test_chain_task_with_prev_result(self):
        """测试链式任务示例 2（使用返回值传递）"""
        url = "https://example.com/api"
        data = {"test": "data"}
        headers = {"Authorization": "Bearer token"}

        result = chain_task_with_prev_result(url, data, headers)

        # 验证返回值
        assert result["status"] == "chain_started_with_prev_result"
        assert "next_run_time" in result

    @pytest.mark.integration
    def test_task_result_retrieval(self):
        """测试任务结果检索"""
        # 提交任务
        task_result = hello_world.apply_async()
        task_id = task_result.id

        # 等待任务完成
        task_result.get(timeout=5)

        # 通过 task_id 重新获取结果
        async_result = AsyncResult(task_id, app=celery_app)

        # 验证可以检索到结果
        assert async_result.status == "SUCCESS"
        assert async_result.result == "Hello World!"

    @pytest.mark.integration
    def test_task_with_eta(self):
        """测试带 ETA（指定执行时间）的任务"""
        # 计算执行时间（当前时间 + 2 秒）
        eta_time = datetime.now(timezone.utc) + timedelta(seconds=2)

        # 提交任务，指定执行时间
        task_result = hello_world.apply_async(eta=eta_time)

        # 验证任务状态
        assert task_result.status in ["PENDING", "STARTED"]

        # 等待任务完成
        result = task_result.get(timeout=10)

        # 验证结果
        assert result == "Hello World!"

    @pytest.mark.integration
    def test_chain_with_tasks(self):
        """测试使用 chain() 创建任务链"""
        # 创建任务链
        from celery import chain

        # 定义任务链
        task_chain = chain(
            hello_world.s(),
            handle_delete_standard_material.s(
                adv_id="adv_123",
                material_id="mat_456",
                ad_id="ad_789"
            )
        )

        # 异步执行任务链
        result = task_chain.apply_async()

        # 等待任务链完成
        final_result = result.get(timeout=10)

        # 验证最终结果
        assert final_result["status"] == "deleted"
        assert final_result["adv_id"] == "adv_123"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
