# 简洁日志格式说明

## 格式设计理念

✅ **超级简洁** - 只有 `created_at` 和 `message`  
✅ **用户字段平铺** - 传入的参数直接作为顶级字段  
✅ **方便查询** - 用 `jq` 可以直接过滤任意字段  
✅ **按日期拆分** - 每天一个日志文件（YYYY-MM-DD.log）  
✅ **自动清理** - 默认保留7天，超期自动删除  

## 日志格式示例

### 基础日志
```json
{
  "created_at": "2025-12-23 10:30:45.123",
  "message": "用户登录成功",
  "user_id": 123,
  "username": "john",
  "ip": "192.168.1.1"
}
```

### 请求追踪
```json
{
  "created_at": "2025-12-23 10:30:45.867",
  "message": "POST /api/v1/users",
  "method": "POST",
  "path": "/api/v1/users",
  "status_code": 201,
  "duration_ms": 45.5,
  "user_id": 123
}
```

### 数据库操作
```json
{
  "created_at": "2025-12-23 10:30:45.867",
  "message": "DB INSERT users",
  "operation": "INSERT",
  "table": "users",
  "duration_ms": 8.7,
  "rows": 1,
  "user_id": 123
}
```

## 使用方式

### 记录信息
```python
from app.utils.structured_logger import log_info

log_info("用户创建成功", user_id=1, username="john", email="john@example.com")
```

### 记录错误
```python
from app.utils.structured_logger import log_error

log_error("数据库连接失败", host="localhost", port=5432, error="timeout")
```

### 追踪HTTP请求
```python
from app.utils.structured_logger import trace_request
import time

start = time.time()
# ... 处理请求 ...
duration = (time.time() - start) * 1000

trace_request("POST", "/api/v1/users", 201, duration, user_id=123)
```

### 追踪数据库操作
```python
from app.utils.structured_logger import trace_database
import time

start = time.time()
# ... 数据库操作 ...
duration = (time.time() - start) * 1000

trace_database("INSERT", "users", duration, rows=1, user_id=123)
```

## 查询日志

### 1. 查看所有日志
```bash
cat logs/2025-12-23.log | jq '.'
```

### 2. 查询特定用户
```bash
cat logs/2025-12-23.log | jq 'select(.user_id == 123)'
```

### 3. 查询特定消息
```bash
cat logs/2025-12-23.log | jq 'select(.message | contains("成功"))'
```

### 4. 查询所有数据库INSERT操作
```bash
cat logs/2025-12-23.log | jq 'select(.operation == "INSERT")'
```

### 5. 查询超过100ms的请求
```bash
cat logs/2025-12-23.log | jq 'select(.duration_ms > 100)'
```

### 6. 统计操作次数
```bash
cat logs/2025-12-23.log | jq -s 'group_by(.operation) | map({operation: .[0].operation, count: length})'
```

### 7. 查看最慢的5个请求
```bash
cat logs/2025-12-23.log | jq 'select(.duration_ms) | sort_by(.duration_ms) | reverse | .[0:5]'
```

## 日志文件位置

```
logs/
├── 2025-12-23.log    ← 今天的日志
├── 2025-12-22.log
├── 2025-12-21.log
├── ...
└── 2025-12-17.log    ← 7天前（自动删除更早的）
```

## 配置

### 修改保留天数

编辑 `app/utils/structured_logger.py` 第 222 行：

```python
_logger = StructuredLogger(
    name="app",
    log_dir="logs",
    rotation="00:00",
    retention="14 days",  # ← 改这里（7 days, 14 days, 30 days 等）
    enable_file=True,
    enable_console=True,
)
```

支持的保留规则：
- `"7 days"` - 7天
- `"14 days"` - 14天
- `"30 days"` - 30天
- `"1 month"` - 1个月
- `"10"` - 保留最近10个文件

### 修改轮转时间

```python
rotation="00:00"    # 每天午夜轮转（默认）
rotation="10:00"    # 每天上午10:00轮转
rotation="500 MB"   # 文件大小达到500MB时轮转
```

## 与以前的区别

| 功能 | 之前 | 现在 |
|------|------|------|
| 日志大小 | ~1KB/条（包含元数据） | ~200B/条（纯业务数据） |
| 查询复杂性 | 困难（需要jq提取record字段） | 简单（直接用jq查询） |
| 日志文件 | 嵌套JSON，难以阅读 | 扁平JSON，易读易查 |
| 元数据 | 包含线程/进程/文件/函数等 | 仅包含时间和消息 |
| 用户字段位置 | 嵌套在data字段中 | 作为顶级字段 |

## 最佳实践

✅ 传入有意义的业务字段
```python
log_info("订单创建成功", order_id=123, user_id=456, amount=99.9)
```

❌ 不要传入敏感信息
```python
# 不要这样做
log_info("登录成功", password="xxx")  # 危险！
```

✅ 用统一的字段名
```python
# 保持一致性
log_info("操作完成", user_id=123, duration_ms=45.5)  # 好
log_info("操作完成", uid=123, time_cost=45.5)  # 不一致
```

✅ message 保持简洁有意义
```python
log_info("用户注册成功", user_id=123, email="john@example.com")
log_error("发送邮件失败", user_id=123, error="SMTP timeout")
```

## FAQ

**Q: 为什么没有level字段？**  
A: level信息可以从message推断，而且我们按操作类型有专门的函数（log_info, log_error等），所以不需要在JSON中重复。

**Q: 怎样搜索所有日志文件？**  
A: 
```bash
# 查询最近7天的所有日志
cat logs/*.log | jq 'select(.user_id == 123)'

# 按创建时间排序
cat logs/*.log | jq -s 'sort_by(.created_at)'
```

**Q: 我需要知道日志来自哪个文件？**  
A: 日志文件名本身就包含日期，文件名格式是 YYYY-MM-DD.log。如果需要更细粒度，可以在message中包含模块名：
```python
log_info("用户管理: 创建成功", user_id=123)
```

**Q: 怎样集成到ELK或其他日志系统？**  
A: 由于是标准JSON格式，可以直接用 Filebeat/Fluentd 收集，完美兼容 Elasticsearch 等系统。
