# 结构化日志组件使用指南（loguru版）

## 概述

结构化日志组件基于**loguru**库，提供了一个现代、灵活的日志记录系统。所有日志以JSON格式输出到文件，自动按日期拆分，自动清理过期日志。

## 核心特性

✨ **loguru库** - 现代化的日志库，API简洁  
✨ **JSON格式** - 所有日志都是JSON，便于自动化分析  
✨ **按日期拆分** - 每天自动生成一个日志文件（YYYY-MM-DD.log）  
✨ **自动清理** - 超过7天的日志自动删除（可配置）  
✨ **灵活字段** - 使用 `**kwargs` 接收任意数量的字段  
✨ **多级别支持** - DEBUG、INFO、WARNING、ERROR、CRITICAL  
✨ **特殊追踪方法** - HTTP、数据库、缓存的专用方法  

## 快速开始

### 1. 安装

```bash
pip install loguru
# 或者，包已包含在requirements.txt中
pip install -r requirements.txt
```

### 2. 基本用法

```python
from app.utils.structured_logger import log_info, log_error, log_warning

# 记录信息
log_info("用户登录成功", user_id=123, username="john", ip="192.168.1.1")

# 记录警告
log_warning("登录失败，次数过多", user_id=456, attempt=5)

# 记录错误
log_error("数据库连接失败", host="localhost", port=5432, error="timeout")
```

### 3. 日志输出位置

所有日志自动输出到：
- 📁 **控制台** - 实时查看（开发模式彩色，生产模式JSON）
- 📄 **文件** - `logs/YYYY-MM-DD.log` （按日期拆分）

**日志保留策略：** 自动删除7天前的日志文件

## 详细配置

### 1. 简单日志记录

```python
from app.utils.structured_logger import log_info, log_error, log_warning

# 记录信息日志
log_info("用户登录成功", user_id=123, username="john")

# 输出：
# {"level": "INFO", "message": "用户登录成功", "created_at": "2025-12-23T10:30:45.123456", "logger": "app", "user_id": 123, "username": "john"}

# 记录警告日志
log_warning("登录失败，次数过多", user_id=456, attempt=5, ip="10.0.0.1")

# 记录错误日志
log_error("数据库连接失败", host="localhost", port=5432, error="timeout")
```

### 2. 日志级别

```python
from app.utils.structured_logger import (
    log_debug,      # 调试信息
    log_info,       # 一般信息
    log_warning,    # 警告信息
    log_error,      # 错误信息
    log_critical,   # 严重错误
)

log_debug("调试信息", debug_field="value")
log_info("普通信息", info_field="value")
log_warning("警告信息", warning_field="value")
log_error("错误信息", error_field="value")
log_critical("严重错误", critical_field="value")
```

### 3. 字段灵活性

日志函数接受任意数量的关键字参数，这些参数会自动添加到日志中：

```python
# 支持多个字段
log_info(
    "用户创建成功",
    user_id=123,
    username="john",
    email="john@example.com",
    registration_method="email",
    email_verified=True,
    source="mobile_app",
    custom_field_1="value1",
    custom_field_2="value2"
)

# 支持不同的数据类型
log_info(
    "订单创建",
    order_id=1001,
    amount=99.99,
    items=3,
    paid=False,
    tags=["vip", "first-order"],
    metadata={"source": "api", "version": "v2"}
)
```

## 高级用法

### 1. HTTP请求追踪

```python
from app.utils.structured_logger import trace_request

# 记录HTTP请求
trace_request(
    method="POST",
    path="/api/v1/users",
    status_code=201,
    duration_ms=45.5,
    user_id=123,
    request_size=256,
    response_size=512
)

# 输出：
# {"level": "INFO", "message": "POST /api/v1/users", "created_at": "...", "method": "POST", "path": "/api/v1/users", "status_code": 201, "duration_ms": 45.5, "user_id": 123, ...}
```

### 2. 数据库操作追踪

```python
from app.utils.structured_logger import trace_database

# 查询
trace_database(
    operation="SELECT",
    table="users",
    duration_ms=5.2,
    result_count=100,
    query="SELECT * FROM users WHERE active=1"
)

# 插入
trace_database(
    operation="INSERT",
    table="users",
    duration_ms=8.7,
    rows=1,
    user_id=123
)

# 更新
trace_database(
    operation="UPDATE",
    table="users",
    duration_ms=3.2,
    rows_affected=5
)

# 删除
trace_database(
    operation="DELETE",
    table="logs",
    duration_ms=12.4,
    rows_affected=1000
)
```

### 3. 缓存操作追踪

```python
from app.utils.structured_logger import trace_cache

# 缓存命中
trace_cache(
    operation="GET",
    key="user:123:profile",
    hit=True,
    duration_ms=0.8
)

# 缓存未命中
trace_cache(
    operation="GET",
    key="user:456:profile",
    hit=False,
    duration_ms=0.5
)

# 设置缓存
trace_cache(
    operation="SET",
    key="user:789:profile",
    hit=False,
    duration_ms=2.1,
    ttl=3600
)

# 删除缓存
trace_cache(
    operation="DELETE",
    key="session:abc123",
    hit=False,
    duration_ms=0.3
)
```

### 4. 异常追踪

```python
from app.utils.structured_logger import trace_exception

try:
    user_id = 123
    raise ValueError("Invalid email format")
except Exception as e:
    # 自动捕获异常类型和消息
    trace_exception(
        exception=e,
        message="用户创建失败",
        user_id=user_id,
        email="invalid@example"
    )

# 输出：
# {"level": "ERROR", "message": "用户创建失败", "exception_type": "ValueError", "exception_message": "Invalid email format", "user_id": 123, ...}
```

### 5. 自定义日志记录器

```python
from app.utils.structured_logger import get_logger

# 为特定模块创建日志记录器
user_logger = get_logger("user_service")
auth_logger = get_logger("auth_service")
payment_logger = get_logger("payment_service")

# 使用模块日志记录器
user_logger.info("用户信息已更新", user_id=123, fields=["email", "phone"])
auth_logger.warning("认证失败", user_id=456, reason="expired_token")
payment_logger.error("支付失败", order_id=789, error="card_declined")
```

## 在FastAPI中集成

### 1. 在路由处理器中使用

```python
from fastapi import APIRouter, Depends
from app.utils.structured_logger import log_info, trace_request, trace_database
from app.core.deps import get_current_user
import time

router = APIRouter()

@router.post("/api/v1/users")
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_user)):
    start_time = time.time()
    
    # 记录请求信息
    log_info(
        "开始创建用户",
        username=user_data.username,
        email=user_data.email,
        created_by=current_user.id
    )
    
    try:
        # 数据库操作
        db_start = time.time()
        user = await User.create(
            username=user_data.username,
            email=user_data.email
        )
        db_duration = (time.time() - db_start) * 1000
        
        # 记录数据库操作
        trace_database(
            operation="INSERT",
            table="users",
            duration_ms=db_duration,
            rows=1,
            user_id=user.id
        )
        
        # 记录成功
        log_info(
            "用户创建成功",
            user_id=user.id,
            username=user.username,
            created_by=current_user.id
        )
        
        # 记录HTTP请求
        duration = (time.time() - start_time) * 1000
        trace_request(
            method="POST",
            path="/api/v1/users",
            status_code=201,
            duration_ms=duration,
            user_id=user.id
        )
        
        return {"user_id": user.id, "username": user.username}
    
    except Exception as e:
        from app.utils.structured_logger import trace_exception
        
        trace_exception(
            exception=e,
            message="用户创建失败",
            username=user_data.username,
            email=user_data.email
        )
        raise
```

### 2. 中间件中使用

```python
from fastapi import FastAPI, Request
from app.utils.structured_logger import trace_request
import time

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 计算耗时
    duration_ms = (time.time() - start_time) * 1000
    
    # 记录请求
    trace_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        client_host=request.client.host if request.client else "unknown"
    )
    
    return response
```

### 3. 异常处理器中使用

```python
from fastapi.exceptions import RequestValidationError
from app.utils.structured_logger import trace_exception

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_exception(
        exception=exc,
        message="请求验证失败",
        method=request.method,
        path=request.url.path
    )
    
    # 返回错误响应...
```

## 日志文件位置

所有日志都输出到：`logs/app.json.log`

每条日志是一个完整的JSON对象，占用一行。这样可以直接使用 `jq` 等工具解析：

```bash
# 查看所有日志
cat logs/app.json.log

# 查看特定级别的日志
cat logs/app.json.log | jq 'select(.level == "ERROR")'

# 查看特定用户的日志
cat logs/app.json.log | jq 'select(.user_id == 123)'

# 统计日志数量
cat logs/app.json.log | wc -l

# 查看最慢的请求
cat logs/app.json.log | jq 'select(.duration_ms > 1000)' | head -10

# 统计错误日志
cat logs/app.json.log | jq 'select(.level == "ERROR")' | wc -l
```

## 日志格式

每条日志都包含以下基础字段：

```json
{
  "level": "INFO",
  "message": "用户登录成功",
  "created_at": "2025-12-23T10:30:45.123456",
  "logger": "app",
  // ... 自定义字段
  "user_id": 123,
  "username": "john",
  "ip": "192.168.1.1"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| level | string | 日志级别：DEBUG/INFO/WARNING/ERROR/CRITICAL |
| message | string | 日志消息 |
| created_at | string | ISO格式时间戳，自动生成 |
| logger | string | 日志记录器名称 |
| ... | any | 通过 `**kwargs` 传入的自定义字段 |

## 与ELK Stack集成

### 使用Filebeat收集日志

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /path/to/fastapi-base/logs/app.json.log
    json.message_key: message
    json.keys_under_root: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "app-logs-%{+yyyy.MM.dd}"
```

### 使用Logstash解析日志

```ruby
input {
  file {
    path => "/path/to/logs/app.json.log"
    codec => json
  }
}

filter {
  # 可以添加更多的过滤规则
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "app-logs-%{+yyyy.MM.dd}"
  }
}
```

## 性能考虑

1. **JSON序列化** - 每条日志都需要JSON序列化，占用一定的CPU
2. **文件I/O** - 同时写入控制台和文件，有一定的I/O开销
3. **建议** - 在生产环境中，将INFO级别日志重定向到异步处理或日志聚合服务

## 与Python logging对比

| 特性 | 传统logging | 结构化日志 |
|------|-----------|----------|
| 输出格式 | 文本（难以解析） | JSON（易于解析） |
| 灵活性 | 有限 | 极高（任意字段） |
| 时间戳 | 手动添加 | 自动生成 |
| 日志聚合 | 困难 | 容易 |
| 可视化 | 困难 | 容易（Kibana等） |
| 搜索过滤 | 正则表达式 | 结构化查询 |

## 最佳实践

### ✅ 应该做

1. **为重要操作添加日志**
```python
log_info("关键操作", operation="user_create", user_id=123)
```

2. **包含请求ID用于追踪**
```python
log_info("处理请求", request_id="req_abc123", user_id=456)
```

3. **记录性能指标**
```python
trace_database("SELECT", "users", duration_ms=15.3)
```

4. **记录异常细节**
```python
trace_exception(e, "操作失败", user_id=789)
```

5. **使用有意义的消息**
```python
log_info("用户创建成功", ...)  # ✅ 清晰
log_info("OK", ...)             # ❌ 不清晰
```

### ❌ 不应该做

1. **不要记录敏感信息**
```python
# ❌ 错误
log_info("用户登录", password=user.password)

# ✅ 正确
log_info("用户登录", user_id=user.id)
```

2. **不要过度logging**
```python
# ❌ 过度
log_info("进入函数")
log_info("处理数据")
log_info("返回结果")

# ✅ 适度
log_info("处理完成", result_count=100)
```

3. **不要忘记关键信息**
```python
# ❌ 缺少上下文
log_error("操作失败")

# ✅ 包含上下文
log_error("用户创建失败", username=username, error=str(e))
```

## 示例输出

运行 `python examples/structured_logger_examples.py`：

```
=== 基础日志记录 ===
{"level": "INFO", "message": "用户登录成功", "created_at": "2025-12-23T10:35:12.123456", "logger": "app", "user_id": 123, "username": "john", "ip": "192.168.1.1"}
{"level": "WARNING", "message": "登录失败，次数过多", "created_at": "2025-12-23T10:35:13.234567", "logger": "app", "user_id": 456, "attempt": 5, "ip": "10.0.0.1"}
{"level": "ERROR", "message": "数据库连接失败", "created_at": "2025-12-23T10:35:14.345678", "logger": "app", "host": "localhost", "port": 5432, "error": "timeout"}

=== HTTP请求日志 ===
{"level": "INFO", "message": "POST /api/v1/users", "created_at": "2025-12-23T10:35:15.456789", "logger": "app", "method": "POST", "path": "/api/v1/users", "status_code": 201, "duration_ms": 45.5, "user_id": 123, "request_body_size": 256, "response_body_size": 512}
...
```

## 常见问题

**Q: 如何改变日志级别？**  
A: 修改 `config/settings.py` 中的 `DEBUG` 设置

**Q: 如何禁用文件日志？**  
A: 修改 `app/utils/structured_logger.py` 中的 `_setup_logger()` 方法

**Q: 如何添加全局上下文字段（如request_id）？**  
A: 使用线程本地存储或fastapi.context

**Q: 性能如何？**  
A: 与传统logging相比，JSON序列化增加约10-20%的开销，但便于分析，值得权衡

