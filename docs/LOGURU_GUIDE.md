# 结构化日志组件使用指南（loguru版）

## 概述

结构化日志组件基于**loguru**库，提供了一个现代、灵活的日志记录系统。所有日志以JSON格式输出到文件，**自动按日期拆分**，**自动清理过期日志**。

## 核心特性

✨ **loguru库** - 现代化的日志库，API简洁  
✨ **JSON格式** - 所有日志都是JSON，便于自动化分析  
✨ **按日期拆分** - 每天自动生成一个日志文件（`YYYY-MM-DD.log`）  
✨ **自动清理** - 超过7天的日志自动删除（可配置）  
✨ **灵活字段** - 使用 `**kwargs` 接收任意数量的字段  
✨ **多级别支持** - DEBUG、INFO、WARNING、ERROR、CRITICAL  

## 快速开始

### 1. 安装

```bash
pip install loguru
# 或直接安装所有依赖
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

### 3. 日志输出位置和说明

```
logs/
├── 2025-12-23.log   ← 今天的日志
├── 2025-12-22.log   ← 昨天的日志
├── 2025-12-21.log   ← 更早的日志
└── ...
（7天后的日志自动删除）
```

**输出说明：**
- 📺 **控制台** - 实时显示（开发模式彩色，生产模式JSON）
- 📄 **文件** - 每天一个 `YYYY-MM-DD.log` 文件

## 配置说明

### 修改日志保留时间

编辑 `app/utils/structured_logger.py` 的全局实例配置：

```python
# 第285行左右
_logger = StructuredLogger(
    name="app",
    log_dir="logs",
    rotation="00:00",        # 每天午夜轮转
    retention="7 days",      # ← 改这里（默认7天）
    enable_file=True,
    enable_console=True,
)
```

**支持的保留规则：**

| 规则 | 说明 |
|------|------|
| `"7 days"` | 保留7天 |
| `"14 days"` | 保留14天 |
| `"30 days"` | 保留30天 |
| `"1 month"` | 保留1个月 |
| `"10"` | 保留最近10个文件 |

### 修改日志轮转时间

```python
# 默认：每天午夜00:00轮转
rotation="00:00"

# 其他选项：
rotation="10:00"      # 每天上午10:00轮转
rotation="500 MB"     # 文件大小达到500MB时轮转
rotation="1 GB"       # 文件大小达到1GB时轮转
rotation="midnight"   # 每天午夜轮转
```

### 创建自定义logger实例

```python
from app.utils.structured_logger import StructuredLogger

# 为特定模块创建日志记录器
user_logger = StructuredLogger(
    name="user_service",
    log_dir="logs/user",
    rotation="00:00",
    retention="14 days",  # 保留14天
    enable_file=True,
    enable_console=True,
)

user_logger.info("用户创建成功", user_id=123, username="john")
```

## 使用示例

### 1. 基础日志记录

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

### 2. 多字段日志

```python
log_info(
    "用户创建成功",
    user_id=123,
    username="john",
    email="john@example.com",
    registration_method="email",
    email_verified=True,
    source="mobile_app"
)
```

### 3. HTTP请求追踪

```python
from app.utils.structured_logger import trace_request

trace_request(
    method="POST",
    path="/api/v1/users",
    status_code=201,
    duration_ms=45.5,
    user_id=123,
    request_size=256,
    response_size=512
)
```

### 4. 数据库操作追踪

```python
from app.utils.structured_logger import trace_database

# 查询
trace_database(
    operation="SELECT",
    table="users",
    duration_ms=5.2,
    result_count=100
)

# 插入
trace_database(
    operation="INSERT",
    table="users",
    duration_ms=8.7,
    rows=1
)
```

### 5. 异常记录

```python
from app.utils.structured_logger import log_exception

try:
    raise ValueError("Invalid value")
except Exception as e:
    log_exception("用户注册失败", user_id=123, email="user@example.com")
```

## 与ELK Stack集成

### 使用Filebeat收集日志

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /path/to/fastapi-base/logs/*.log
    json.message_key: message
    json.keys_under_root: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "app-logs-%{+yyyy.MM.dd}"
```

## 日志查看命令

### 查看当天日志

```bash
cat logs/$(date +%Y-%m-%d).log
```

### 查看特定级别的日志

```bash
cat logs/2025-12-23.log | jq 'select(.level == "ERROR")'
cat logs/2025-12-23.log | jq 'select(.level == "WARNING")'
```

### 查看特定用户的日志

```bash
cat logs/2025-12-23.log | jq 'select(.user_id == 123)'
```

### 统计错误数量

```bash
cat logs/2025-12-23.log | jq 'select(.level == "ERROR")' | wc -l
```

### 查看最慢的请求

```bash
cat logs/2025-12-23.log | jq 'select(.duration_ms > 1000)' | sort -r | head -10
```

## FastAPI集成示例

### 在路由中使用

```python
from fastapi import APIRouter
from app.utils.structured_logger import log_info, trace_database, trace_request
import time

router = APIRouter()

@router.post("/api/v1/users")
async def create_user(user_data: UserCreate):
    start_time = time.time()
    
    # 记录请求开始
    log_info("开始创建用户", username=user_data.username, email=user_data.email)
    
    try:
        # 数据库操作
        db_start = time.time()
        user = await User.create(**user_data.model_dump())
        db_duration = (time.time() - db_start) * 1000
        
        # 记录数据库操作
        trace_database("INSERT", "users", db_duration, rows=1, user_id=user.id)
        
        # 记录成功
        log_info("用户创建成功", user_id=user.id, username=user.username)
        
        # 记录HTTP请求
        duration = (time.time() - start_time) * 1000
        trace_request("POST", "/api/v1/users", 201, duration, user_id=user.id)
        
        return {"user_id": user.id, "username": user.username}
    
    except Exception as e:
        from app.utils.structured_logger import log_exception
        log_exception("用户创建失败", username=user_data.username)
        raise
```

### 在中间件中使用

```python
from fastapi import FastAPI, Request
from app.utils.structured_logger import trace_request
import time

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    
    trace_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        client_host=request.client.host if request.client else "unknown"
    )
    
    return response
```

## 日志格式示例

### 控制台输出（开发模式）

```
DEBUG    | app:function:42 - 调试信息
INFO     | app:function:43 - 用户创建成功
WARNING  | app:function:44 - 登录失败，次数过多
ERROR    | app:function:45 - 数据库连接失败
```

### 文件输出（JSON格式）

```json
{"text": "{\"level\": \"INFO\", \"message\": \"用户登录成功\", \"user_id\": 123, \"username\": \"john\", \"ip\": \"192.168.1.1\"}", "record": {"elapsed": {"repr": "0:00:00.123456", "seconds": 0.123456}, "exception": null, "extra": {}, "file": {"name": "user_views.py", "path": "/path/to/user_views.py"}, "function": "login", "level": {"icon": "ℹ️", "name": "INFO", "no": 20}, "line": 42, "message": "用户登录成功", "module": "user_views", "name": "app", "process": {"id": 12345, "name": "MainProcess"}, "thread": {"id": 56789, "name": "MainThread"}, "time": {"repr": "2025-12-23T10:30:45.123456+00:00", "timestamp": 1703328645.123456}}}
```

## 最佳实践

### ✅ 应该做

1. **记录关键操作**
```python
log_info("重要操作完成", user_id=123, action="password_reset")
```

2. **包含请求ID追踪**
```python
log_info("处理请求", request_id="req_abc123", user_id=456)
```

3. **记录性能指标**
```python
trace_database("SELECT", "users", duration_ms=15.3)
```

4. **记录错误细节**
```python
log_error("操作失败", user_id=789, error=str(e), retry_count=3)
```

### ❌ 不应该做

1. **不要记录敏感信息**
```python
# ❌ 错误：不要记录密码
log_info("用户登录", password=user_password)

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

## 与loguru原生API兼容

如果需要使用loguru的原生API：

```python
from app.utils.structured_logger import logger

# 直接使用loguru的logger
logger.info("这是直接使用的日志")
logger.error("这是直接的错误日志")
logger.bind(user_id=123).info("绑定上下文的日志")
```

## 性能对比

| 库 | 优点 | 缺点 |
|---|------|------|
| 标准logging | 内置，无依赖 | 配置复杂，功能有限 |
| loguru | 现代、简洁、功能完整 | 额外依赖（值得） |
| structlog | 功能强大、企业级 | 配置复杂 |

## 常见问题

**Q: 如何改变日志保留天数？**  
A: 修改 `app/utils/structured_logger.py` 中的 `retention` 参数

**Q: 日志文件在哪里？**  
A: 所有日志在 `logs/` 目录，按日期拆分

**Q: 如何禁用控制台输出？**  
A: 将 `enable_console=False` 传给 `StructuredLogger()`

**Q: 可以自定义日志格式吗？**  
A: 可以，loguru支持自定义格式，参考官方文档

**Q: 性能如何？**  
A: loguru性能优异，JSON序列化开销<5%，值得使用
