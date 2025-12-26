# Celery 集成测试指南

## 概述

本项目包含两种测试方式：
1. **单元测试** (`tests/test_celery_tasks.py`) - 使用 mock，不需要真实环境
2. **集成测试** (`tests/test_celery_integration.py`) - 需要真实的 Celery worker 和 Redis

## 快速开始

### 1. 启动 Redis

```bash
# 使用 Docker
docker run -d -p 6379:6379 redis

# 或使用本地安装的 Redis
redis-server
```

验证 Redis 是否运行：
```bash
redis-cli ping
# 应返回: PONG
```

### 2. 启动 Celery Worker

在终端中运行：
```bash
celery -A celery_app.celery worker --loglevel=info
```

### 3. 运行集成测试

使用脚本自动检查环境并运行测试：
```bash
./run_celery_integration_tests.sh
```

或手动运行：
```bash
# 只运行集成测试
pytest tests/test_celery_integration.py -v -m integration

# 运行所有 Celery 测试（包括单元测试和集成测试）
pytest tests/test_celery_*.py -v
```

## 测试类型对比

### 单元测试 (`tests/test_celery_tasks.py`)

**特点：**
- ✅ 快速执行（毫秒级）
- ✅ 不需要外部依赖
- ✅ 适合 CI/CD 流程
- ✅ 验证调用逻辑

**缺点：**
- ❌ 不测试真实执行环境
- ❌ 无法发现 worker 配置问题
- ❌ 不验证异步行为

**运行方式：**
```bash
# 默认运行（pytest.ini 配置为跳过集成测试）
pytest tests/test_celery_tasks.py -v

# 显式运行单元测试
pytest tests/test_celery_tasks.py -v -m "not integration"
```

### 集成测试 (`tests/test_celery_integration.py`)

**特点：**
- ✅ 测试真实执行环境
- ✅ 验证 worker 配置
- ✅ 测试异步行为
- ✅ 发现环境问题

**缺点：**
- ❌ 执行较慢（秒级到分钟级）
- ❌ 需要外部依赖（Redis、Worker）
- ❌ 不适合频繁执行

**运行方式：**
```bash
# 只运行集成测试
pytest tests/test_celery_integration.py -v -m integration

# 使用脚本自动检查环境
./run_celery_integration_tests.sh
```

## 测试示例

### 单元测试示例
```python
@patch('celery_app.tasks.test_tasks.chain')
def test_chain_task_example(self, mock_chain):
    """使用 mock 验证调用逻辑"""
    mock_chain.return_value.apply_async.return_value = Mock()
    
    result = chain_task_example(url, data, headers)
    
    assert result["status"] == "chain_started"
    mock_chain.assert_called_once()
```

### 集成测试示例
```python
@pytest.mark.integration
def test_hello_world_async(self):
    """使用真实 worker 测试任务执行"""
    task_result = hello_world.apply_async()
    
    # 等待真实 worker 执行完成
    result = task_result.get(timeout=5)
    
    assert result == "Hello World!"
```

## 常见问题

### 1. Redis 连接失败

**错误信息：**
```
Error: Redis 未运行
```

**解决方案：**
- 启动 Redis: `docker run -d -p 6379:6379 redis`
- 检查端口: `redis-cli ping`

### 2. Celery Worker 未运行

**错误信息：**
```
Error: Celery Worker 未运行
```

**解决方案：**
```bash
celery -A celery_app.celery worker --loglevel=info
```

### 3. 任务超时

**错误信息：**
```
TimeoutError: Operation timed out
```

**解决方案：**
- 增加 `get(timeout=...)` 的超时时间
- 检查 worker 是否正常运行
- 查看日志排查任务执行问题

### 4. Chain 任务未执行

**原因：** Chain 任务可能设置了 `eta`（延迟执行）

**解决方案：**
- 减少或移除 `eta` 延迟时间
- 等待足够时间让任务执行
- 使用 `task.forget()` 清除任务队列

## 测试最佳实践

### 1. 持续集成（CI/CD）

在 CI/CD 中使用单元测试：
```yaml
# .github/workflows/tests.yml
- name: Run unit tests
  run: pytest tests/test_celery_tasks.py -v
```

### 2. 本地开发

本地开发时同时运行两种测试：
```bash
# 终端 1: 启动 worker
celery -A celery_app.celery worker --loglevel=info

# 终端 2: 运行测试
pytest tests/ -v
```

### 3. 测试覆盖率

使用 pytest-cov 查看测试覆盖率：
```bash
# 单元测试覆盖率
pytest tests/test_celery_tasks.py --cov=celery_app.tasks --cov-report=html

# 集成测试覆盖率
pytest tests/test_celery_integration.py -m integration --cov=celery_app.tasks --cov-report=html
```

## 高级用法

### 1. 并发执行多个测试

```python
@pytest.mark.integration
def test_concurrent_tasks():
    """测试并发任务执行"""
    from celery import group

    # 创建任务组
    job = group(
        hello_world.s() for _ in range(10)
    )

    # 并发执行
    result = job.apply_async()

    # 等待所有任务完成
    results = result.get(timeout=30)

    assert len(results) == 10
    assert all(r == "Hello World!" for r in results)
```

### 2. 任务重试测试

```python
@pytest.mark.integration
def test_task_retry():
    """测试任务自动重试"""
    # 配置任务自动重试
    from celery import Task

    @celery_app.task(bind=True, max_retries=3)
    def flaky_task(self):
        import random
        if random.random() > 0.5:
            raise self.retry(countdown=1)
        return "success"

    # 执行任务
    result = flaky_task.apply_async()
    final_result = result.get(timeout=10)

    assert final_result == "success"
```

### 3. 任务链测试

```python
@pytest.mark.integration
def test_complex_chain():
    """测试复杂任务链"""
    from celery import chain, chord

    # 创建任务链
    workflow = chain(
        hello_world.s(),
        handle_delete_standard_material.s(
            adv_id="adv_123",
            material_id="mat_456",
            ad_id="ad_789"
        ),
        async_publish_uni_promotion_plan.s(
            adv_id="adv_123",
            material_id="mat_456"
        )
    )

    # 执行
    result = workflow.apply_async()
    final_result = result.get(timeout=15)

    assert final_result["status"] in ["success", "failed"]
```

## 参考资源

- [Celery 官方文档](https://docs.celeryproject.org/)
- [Pytest 文档](https://docs.pytest.org/)
- [Redis 文档](https://redis.io/docs/)
