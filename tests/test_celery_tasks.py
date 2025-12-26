#!/usr/bin/env python3
"""
Celery 任务单元测试
测试任务链式调用和 apply_async 方式调用
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

from celery_app.tasks.test_tasks import (
    hello_world,
    revoke_api_func_for_backend,
    handle_delete_standard_material,
    async_publish_uni_promotion_plan,
    chain_task_example,
    chain_task_with_prev_result,
)


class TestHelloWorld:
    """测试 hello_world 任务"""
    
    def test_hello_world_success(self):
        """测试 hello_world 任务执行成功"""
        result = hello_world()
        assert result == "Hello World!"


class TestRevokeApiFuncForBackend:
    """测试 revoke_api_func_for_backend 任务"""
    
    def test_revoke_api_func_for_backend_basic(self):
        """测试基本的 API 调用任务"""
        url = "https://example.com/api"
        data = {"key": "value"}
        headers = {"Content-Type": "application/json"}
        
        result = revoke_api_func_for_backend("post", url, json=data, headers=headers)
        
        assert result["method"] == "post"
        assert result["url"] == url
        assert result["status"] == "success"
    
    def test_revoke_api_func_for_backend_empty_data(self):
        """测试空数据的 API 调用任务"""
        url = "https://example.com/api"
        
        result = revoke_api_func_for_backend("get", url)
        
        assert result["method"] == "get"
        assert result["url"] == url
        assert result["status"] == "success"


class TestHandleDeleteStandardMaterial:
    """测试 handle_delete_standard_material 任务"""

    def test_handle_delete_standard_material_with_prev_result(self):
        """测试删除标准素材任务（带前一个任务的返回值）"""
        prev_result = {"method": "post", "url": "https://example.com/api", "status": "success"}
        adv_id = "adv_123"
        material_id = "mat_456"
        ad_id = "ad_789"

        result = handle_delete_standard_material(prev_result, adv_id, material_id, ad_id)

        assert result["prev_result"] == prev_result
        assert result["adv_id"] == adv_id
        assert result["material_id"] == material_id
        assert result["ad_id"] == ad_id
        assert result["status"] == "deleted"

    def test_handle_delete_standard_material_without_prev_result(self):
        """测试删除标准素材任务（不带前一个任务的返回值）"""
        adv_id = "adv_123"
        material_id = "mat_456"
        ad_id = "ad_789"

        result = handle_delete_standard_material(None, adv_id, material_id, ad_id)

        assert result["prev_result"] is None
        assert result["adv_id"] == adv_id
        assert result["material_id"] == material_id
        assert result["ad_id"] == ad_id
        assert result["status"] == "deleted"


class TestAsyncPublishUniPromotionPlan:
    """测试 async_publish_uni_promotion_plan 任务"""
    
    def test_async_publish_uni_promotion_plan_success(self):
        """测试发布推广计划任务（成功）"""
        result = async_publish_uni_promotion_plan(
            adv_id="adv_123",
            material_id="mat_456",
            retry_times=0
        )
        
        assert result["adv_id"] == "adv_123"
        assert result["material_id"] == "mat_456"
        assert result["status"] == "success"
    
    def test_async_publish_uni_promotion_plan_retry_within_limit(self):
        """测试发布推广计划任务（重试次数在限制内）"""
        result = async_publish_uni_promotion_plan(
            adv_id="adv_123",
            material_id="mat_456",
            retry_times=2
        )
        
        assert result["status"] == "success"
    
    def test_async_publish_uni_promotion_plan_retry_exceeded(self):
        """测试发布推广计划任务（重试次数超限）"""
        result = async_publish_uni_promotion_plan(
            adv_id="adv_123",
            material_id="mat_456",
            retry_times=5
        )
        
        assert result["status"] == "failed"
        assert result["retry_times"] == 5


class TestChainTaskExample:
    """测试链式任务示例"""

    @patch('celery_app.tasks.test_tasks.chain')
    def test_chain_task_example_success(self, mock_chain):
        """测试链式任务示例（成功启动）"""
        # 模拟 chain.apply_async 返回的 result
        mock_result = Mock()
        mock_result.status = "PENDING"
        mock_chain.return_value.apply_async.return_value = mock_result

        url = "https://example.com/api"
        data = {"key": "value"}
        headers = {"Content-Type": "application/json"}

        result = chain_task_example(url, data, headers)

        # 验证 chain 被调用
        mock_chain.assert_called_once()

        # 验证返回结果
        assert result["status"] == "chain_started"
        assert "next_run_time" in result

    @patch('celery_app.tasks.test_tasks.chain')
    def test_chain_task_example_default_params(self, mock_chain):
        """测试链式任务示例（使用默认参数）"""
        mock_chain.return_value.apply_async.return_value = Mock()

        result = chain_task_example()

        mock_chain.assert_called_once()
        assert result["status"] == "chain_started"


class TestChainTaskWithPrevResult:
    """测试使用前一个任务返回值的链式任务"""

    @patch('celery_app.tasks.test_tasks.chain')
    def test_chain_task_with_prev_result_success(self, mock_chain):
        """测试链式任务示例（使用返回值传递）"""
        mock_chain.return_value.apply_async.return_value = Mock()

        url = "https://example.com/api"
        data = {"key": "value"}
        headers = {"Content-Type": "application/json"}

        result = chain_task_with_prev_result(url, data, headers)

        # 验证 chain 被调用
        mock_chain.assert_called_once()

        # 验证返回结果
        assert result["status"] == "chain_started_with_prev_result"
        assert "next_run_time" in result

    @patch('celery_app.tasks.test_tasks.chain')
    def test_chain_result_passing_behavior(self, mock_chain):
        """
        测试 chain 中返回值传递的行为

        说明：
        - chain 默认会将前一个任务的返回值作为下一个任务的第一个参数
        - 使用 .s(args...) 会覆盖这个默认行为
        - 使用 .s(key=value) 则可以接收返回值作为第一个参数，同时指定其他参数
        """
        mock_chain.return_value.apply_async.return_value = Mock()

        url = "https://example.com/api"
        data = {"test": "data"}

        # 方式1: 使用位置参数（覆盖返回值传递）
        chain_task_example(url, data)

        # 方式2: 使用关键字参数（接收返回值）
        chain_task_with_prev_result(url, data)

        # 两种方式都调用了 chain
        assert mock_chain.call_count == 2


class TestApplyAsync:
    """测试 apply_async 调用方式"""
    
    @patch('celery_app.tasks.test_tasks.async_publish_uni_promotion_plan.apply_async')
    def test_apply_async_with_countdown(self, mock_apply_async):
        """测试使用 apply_async 并指定 countdown 延迟执行"""
        mock_result = Mock()
        mock_result.id = "task_id_123"
        mock_result.status = "PENDING"
        mock_apply_async.return_value = mock_result
        
        retry_args = ["adv_123", "mat_456"]
        retry_times = 1
        
        # 调用方式 1: 使用 args 和 kwargs
        async_publish_uni_promotion_plan.apply_async(
            args=retry_args,
            kwargs={"retry_times": retry_times},
            countdown=30,  # 30秒后重试
            queue="create_uni_plan",
        )
        
        # 验证 apply_async 被调用
        mock_apply_async.assert_called_once()
        call_kwargs = mock_apply_async.call_args[1]
        
        assert call_kwargs["args"] == retry_args
        assert call_kwargs["kwargs"] == {"retry_times": retry_times}
        assert call_kwargs["countdown"] == 30
        assert call_kwargs["queue"] == "create_uni_plan"
    
    @patch('celery_app.tasks.test_tasks.revoke_api_func_for_backend.apply_async')
    def test_apply_async_with_eta(self, mock_apply_async):
        """测试使用 apply_async 并指定 ETA（具体执行时间）"""
        mock_result = Mock()
        mock_result.id = "task_id_456"
        mock_result.status = "SCHEDULED"
        mock_apply_async.return_value = mock_result
        
        # 计算执行时间（当前时间 + 1小时）
        eta_time = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # 调用方式 2: 使用 args 和 eta
        revoke_api_func_for_backend.apply_async(
            args=["post", "https://example.com/api"],
            kwargs={"json": {"key": "value"}, "headers": {"Content-Type": "application/json"}},
            eta=eta_time,
        )
        
        # 验证 apply_async 被调用
        mock_apply_async.assert_called_once()
        call_kwargs = mock_apply_async.call_args[1]
        
        assert call_kwargs["eta"] == eta_time
    
    @patch('celery_app.tasks.test_tasks.hello_world.apply_async')
    def test_apply_async_simple(self, mock_apply_async):
        """测试简单的 apply_async 调用"""
        mock_result = Mock()
        mock_result.id = "task_id_789"
        mock_result.status = "PENDING"
        mock_apply_async.return_value = mock_result
        
        # 调用方式 3: 不带参数
        hello_world.apply_async()
        
        # 验证 apply_async 被调用
        mock_apply_async.assert_called_once()
    
    @patch('celery_app.tasks.test_tasks.handle_delete_standard_material.apply_async')
    def test_apply_async_with_ignore_result(self, mock_apply_async):
        """测试使用 ignore_result=True"""
        mock_result = Mock()
        mock_result.id = "task_id_999"
        mock_result.status = "PENDING"
        mock_apply_async.return_value = mock_result
        
        handle_delete_standard_material.apply_async(
            args=["adv_123", "mat_456", "ad_789"],
            ignore_result=True,
        )
        
        mock_apply_async.assert_called_once()
        call_kwargs = mock_apply_async.call_args[1]
        
        assert call_kwargs["ignore_result"] is True


class TestIntegrationChainAndApplyAsync:
    """集成测试：链式调用和 apply_async 的组合使用"""
    
    @patch('celery_app.tasks.test_tasks.chain')
    def test_integration_example(self, mock_chain):
        """
        集成测试示例：展示如何在实际场景中使用
        
        场景：
        1. 先启动一个链式任务（API调用 -> 删除素材）
        2. 同时使用 apply_async 启动一个带重试的推广任务
        """
        # 模拟 chain 返回
        mock_chain.return_value.apply_async.return_value = Mock()
        
        # 1. 启动链式任务 - 同步调用函数，函数内部使用 apply_async 提交子任务
        url = "https://example.com/api"
        data = {"action": "create"}
        headers = {"Authorization": "Bearer token123"}
        
        chain_result = chain_task_example(url, data, headers)
        assert chain_result["status"] == "chain_started"
        
        # 验证 chain 被调用
        mock_chain.assert_called_once()
        
        # 2. 模拟使用 apply_async 启动推广任务（重试场景）
        with patch('celery_app.tasks.test_tasks.async_publish_uni_promotion_plan.apply_async') as mock_apply:
            mock_apply.return_value = Mock(id="promote_task_id")
            
            retry_args = ["adv_123", "mat_456"]
            retry_times = 0
            
            async_publish_uni_promotion_plan.apply_async(
                args=retry_args,
                kwargs={"retry_times": retry_times},
                countdown=30,  # 30秒后重试
                queue="create_uni_plan",
            )
            
            # 验证 apply_async 被调用
            mock_apply.assert_called_once_with(
                args=retry_args,
                kwargs={"retry_times": retry_times},
                countdown=30,
                queue="create_uni_plan",
            )
    
    @patch('celery_app.tasks.test_tasks.chain')
    @patch('celery_app.tasks.test_tasks.chain_task_example.apply_async')
    def test_sync_vs_async_call_difference(self, mock_apply_async, mock_chain):
        """
        对比测试：同步调用 vs 异步调用任务函数
        
        说明：
        - 同步调用：chain_task_example(url, data, headers)
          立即执行函数，函数内部提交 chain 子任务到 worker
        - 异步调用：chain_task_example.apply_async(args=[url, data, headers])
          将任务本身提交到 worker，worker 执行时才会提交 chain 子任务
        """
        # 模拟 chain 返回
        mock_chain.return_value.apply_async.return_value = Mock()
        
        # 模拟 apply_async 返回
        mock_async_result = Mock()
        mock_async_result.id = "chain_task_id"
        mock_async_result.status = "PENDING"
        mock_apply_async.return_value = mock_async_result
        
        url = "https://example.com/api"
        data = {"test": "data"}
        headers = {"Authorization": "Bearer token"}
        
        # 1. 同步调用：立即执行函数
        sync_result = chain_task_example(url, data, headers)
        # 返回的是函数的返回值
        assert sync_result["status"] == "chain_started"
        assert "next_run_time" in sync_result
        # chain 被立即调用（在当前进程）
        assert mock_chain.called
        
        # 2. 异步调用：将任务提交到 worker
        async_result = chain_task_example.apply_async(args=[url, data, headers])
        # 返回的是 AsyncResult 对象
        assert async_result.id == "chain_task_id"
        assert async_result.status == "PENDING"
        # chain 不会被立即调用（等待 worker 执行）
        # mock_chain 的调用次数没有增加（因为这是新的调用）
        
        # 注意：在实际使用中：
        # - 如果需要立即触发 chain 子任务，使用同步调用
        # - 如果需要调度整个任务（支持重试、延迟执行等），使用异步调用


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
