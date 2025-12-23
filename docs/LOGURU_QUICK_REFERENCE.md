# 结构化日志快速参考

## 最常用的5行代码

```python
from app.utils.structured_logger import log_info, log_error, log_warning

# 记录信息
log_info("用户创建成功", user_id=123, username="john")

# 记录错误
log_error("数据库连接失败", error="timeout")

# 记录警告
log_warning("登录失败次数过多", user_id=456, attempt=5)
```

## 日志文件位置

```
logs/
├── 2025-12-23.log   ← 今天的日志（自动生成）
├── 2025-12-22.log
└── 2025-12-21.log
（自动删除7天前的文件）
```

## 查看日志命令

```bash
# 查看今天的日志
cat logs/$(date +%Y-%m-%d).log | jq

# 查看ERROR级别的日志
cat logs/$(date +%Y-%m-%d).log | jq 'select(.record.level.name == "ERROR")'

# 查看特定用户的日志
cat logs/$(date +%Y-%m-%d).log | jq 'select(.record.extra.user_id == 123)'

# 查看最慢的请求
cat logs/$(date +%Y-%m-%d).log | jq 'select(.record.extra.duration_ms > 1000)'
```

## 所有日志函数

### 基础日志

```python
from app.utils.structured_logger import (
    log_debug,      # 调试信息
    log_info,       # 普通信息
    log_warning,    # 警告信息
    log_error,      # 错误信息
    log_critical,   # 严重错误
    log_exception,  # 异常日志
)

log_info("消息", field1="value1", field2=123)
```

### 专用追踪函数

```python
from app.utils.structured_logger import (
    trace_request,   # HTTP请求
    trace_database,  # 数据库操作
    trace_cache,     # 缓存操作
)

trace_request("POST", "/api/users", 201, 45.5, user_id=123)
trace_database("INSERT", "users", 8.7, rows=1)
trace_cache("GET", "user:123", True, 0.5)
```

### 自定义logger实例

```python
from app.utils.structured_logger import get_logger

logger = get_logger("my_service")
logger.info("信息", field="value")
```

## 配置修改

### 保留天数

编辑 `app/utils/structured_logger.py` 第285行：

```python
_logger = StructuredLogger(
    retention="14 days",  # 改这里（默认7天）
)
```

### 轮转时间

```python
_logger = StructuredLogger(
    rotation="00:00",     # 每天午夜（默认）
    # rotation="10:00",   # 每天上午10:00
    # rotation="500 MB",  # 文件达到500MB时
)
```

## FastAPI集成示例

### 在路由中使用

```python
from fastapi import APIRouter
from app.utils.structured_logger import log_info, trace_database
import time

router = APIRouter()

@router.post("/api/v1/users")
async def create_user(user_data: UserCreate):
    start = time.time()
    
    log_info("创建用户", username=user_data.username)
    
    # 数据库操作
    db_start = time.time()
    user = await User.create(**user_data.model_dump())
    db_time = (time.time() - db_start) * 1000
    
    trace_database("INSERT", "users", db_time, rows=1, user_id=user.id)
    
    log_info("用户创建成功", user_id=user.id, username=user.username)
    
    return {"user_id": user.id}
```

### 在中间件中使用

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    from app.utils.structured_logger import trace_request
    import time
    
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    
    trace_request(
        request.method,
        request.url.path,
        response.status_code,
        duration
    )
    
    return response
```

## 常见场景

### 用户操作

```python
log_info("用户登录", user_id=123, ip="192.168.1.1")
log_warning("登录失败", user_id=456, attempt=3)
log_error("注册异常", username="john", error=str(e))
```

### 数据库操作

```python
trace_database("SELECT", "users", 5.2, result_count=100)
trace_database("INSERT", "orders", 12.3, rows=1, user_id=123)
trace_database("UPDATE", "users", 3.2, rows_affected=5)
```

### HTTP请求

```python
trace_request("GET", "/api/users", 200, 45.5)
trace_request("POST", "/api/users", 201, 78.2, user_id=123)
trace_request("DELETE", "/api/users/123", 204, 23.1)
```

### 异常处理

```python
try:
    result = do_something()
except Exception as e:
    log_exception("操作失败", user_id=123, action="delete")
```

## 日志消息示例

### ✅ 好的日志消息

```python
log_info("用户创建成功", user_id=123, username="john", email="john@example.com")
log_error("数据库连接失败", host="localhost", error="timeout", retry=3)
log_warning("缓存命中率低", cache_hit_rate=0.3, threshold=0.5)
```

### ❌ 不好的日志消息

```python
log_info("OK")                              # 太简单
log_error("错误")                           # 缺少详情
log_info("处理完成", full_response=response)  # 过多数据
```

## 日志级别使用指南

| 级别 | 何时使用 | 示例 |
|------|---------|------|
| DEBUG | 开发调试 | `log_debug("变量值", x=value)` |
| INFO | 重要操作 | `log_info("用户登录", user_id=123)` |
| WARNING | 潜在问题 | `log_warning("响应慢", duration_ms=5000)` |
| ERROR | 业务错误 | `log_error("操作失败", error=str(e))` |
| CRITICAL | 系统故障 | `log_critical("系统崩溃")` |

## 性能提示

1. **不要记录敏感信息**
   ```python
   log_info("用户登录", user_id=123)  # ✅
   log_info("用户登录", password="xxx")  # ❌
   ```

2. **适度logging**
   ```python
   # ❌ 过度
   log_info("进入函数")
   log_info("处理数据")
   log_info("返回结果")
   
   # ✅ 适度
   log_info("处理完成", count=100)
   ```

3. **避免大对象**
   ```python
   log_info("获取用户", user_id=user.id)  # ✅
   log_info("获取用户", user=user)        # ❌ 序列化成本高
   ```

## 生产环境检查清单

- [ ] 修改日志保留天数（根据磁盘空间）
- [ ] 检查轮转时间是否合理
- [ ] 验证日志目录权限正确
- [ ] 确认磁盘空间足够
- [ ] 设置日志监控告警
- [ ] 配置日志聚合工具（可选）

## 更多信息

- 📖 详细文档：[docs/LOGURU_GUIDE.md](./LOGURU_GUIDE.md)
- 📊 对比分析：[docs/LOGURU_vs_ALTERNATIVES.md](./LOGURU_vs_ALTERNATIVES.md)
- 🔧 源代码：[app/utils/structured_logger.py](../app/utils/structured_logger.py)
- 📝 loguru官方：https://github.com/Delgan/loguru
