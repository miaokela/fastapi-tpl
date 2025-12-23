"""
结构化日志使用示例
展示如何使用新的结构化日志组件
"""

from app.utils.structured_logger import (
    log_info,
    log_error,
    log_warning,
    trace_request,
    trace_database,
    trace_cache,
    trace_exception,
    get_logger,
)
import asyncio


def example_basic_logging():
    """基础日志记录示例"""
    print("\n=== 基础日志记录 ===")
    
    # 信息日志
    log_info("用户登录成功", user_id=123, username="john", ip="192.168.1.1")
    
    # 警告日志
    log_warning("登录失败，次数过多", user_id=456, attempt=5, ip="10.0.0.1")
    
    # 错误日志
    log_error("数据库连接失败", host="localhost", port=5432, error="timeout")


def example_http_logging():
    """HTTP请求日志示例"""
    print("\n=== HTTP请求日志 ===")
    
    # 记录成功的请求
    trace_request(
        method="POST",
        path="/api/v1/users",
        status_code=201,
        duration_ms=45.5,
        user_id=123,
        request_body_size=256,
        response_body_size=512
    )
    
    # 记录失败的请求
    trace_request(
        method="GET",
        path="/api/v1/users/999",
        status_code=404,
        duration_ms=12.3,
        user_id=123
    )


def example_database_logging():
    """数据库操作日志示例"""
    print("\n=== 数据库操作日志 ===")
    
    # 查询操作
    trace_database(
        operation="SELECT",
        table="users",
        duration_ms=5.2,
        query_count=1,
        result_count=100
    )
    
    # 插入操作
    trace_database(
        operation="INSERT",
        table="users",
        duration_ms=8.7,
        rows=1,
        user_id=123
    )
    
    # 更新操作
    trace_database(
        operation="UPDATE",
        table="users",
        duration_ms=3.2,
        rows_affected=5,
        condition="status='inactive'"
    )


def example_cache_logging():
    """缓存操作日志示例"""
    print("\n=== 缓存操作日志 ===")
    
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
        key="user:123:profile",
        hit=False,
        duration_ms=0.3
    )


def example_exception_logging():
    """异常日志示例"""
    print("\n=== 异常日志 ===")
    
    # 捕获并记录异常
    try:
        user_id = 123
        raise ValueError("Invalid user email format")
    except Exception as e:
        trace_exception(
            exception=e,
            message="用户创建失败",
            user_id=user_id,
            email="invalid@example"
        )
    
    # 捕获数据库异常
    try:
        raise ConnectionError("Database connection timeout")
    except Exception as e:
        trace_exception(
            exception=e,
            message="数据库连接异常",
            host="db.example.com",
            retry_count=3
        )


def example_custom_logger():
    """使用自定义日志记录器"""
    print("\n=== 自定义日志记录器 ===")
    
    # 为特定模块创建日志记录器
    user_logger = get_logger("user_service")
    auth_logger = get_logger("auth_service")
    
    # 使用模块日志记录器
    user_logger.info("用户信息已更新", user_id=123, fields=["email", "phone"])
    auth_logger.warning("认证失败", user_id=456, reason="expired_token")


def example_real_world_scenario():
    """真实场景示例：用户注册流程"""
    print("\n=== 真实场景：用户注册流程 ===")
    
    logger = get_logger("auth_service")
    
    # 1. 用户提交注册请求
    logger.info(
        "用户注册请求",
        username="newuser",
        email="newuser@example.com",
        ip="192.168.1.100"
    )
    
    # 2. 验证用户名是否存在（数据库查询）
    trace_database(
        operation="SELECT",
        table="users",
        duration_ms=2.3,
        query="SELECT id FROM users WHERE username=?",
        user_count=0
    )
    
    # 3. 验证邮箱是否存在（缓存查询）
    trace_cache(
        operation="GET",
        key="email:newuser@example.com",
        hit=False,
        duration_ms=0.5
    )
    
    # 4. 插入新用户（数据库写入）
    trace_database(
        operation="INSERT",
        table="users",
        duration_ms=5.1,
        rows=1
    )
    
    # 5. 设置缓存
    trace_cache(
        operation="SET",
        key="email:newuser@example.com",
        hit=False,
        duration_ms=1.2,
        ttl=86400
    )
    
    # 6. 发送欢迎邮件任务
    logger.info(
        "欢迎邮件任务已提交",
        user_id=1,
        email="newuser@example.com",
        task_id="task_123"
    )
    
    # 7. 响应HTTP请求
    trace_request(
        method="POST",
        path="/api/v1/auth/register",
        status_code=201,
        duration_ms=38.4,
        user_id=1
    )
    
    logger.info(
        "用户注册成功",
        user_id=1,
        username="newuser",
        email="newuser@example.com"
    )


def example_logging_with_context():
    """带上下文信息的日志记录"""
    print("\n=== 带上下文的日志记录 ===")
    
    logger = get_logger("api_service")
    
    # 请求上下文
    request_id = "req_123abc"
    user_id = 456
    
    # 所有日志都包含请求ID和用户ID
    logger.info(
        "处理用户请求",
        request_id=request_id,
        user_id=user_id,
        action="update_profile"
    )
    
    trace_database(
        operation="UPDATE",
        table="users",
        duration_ms=4.2,
        request_id=request_id,
        user_id=user_id,
        fields=["name", "avatar"]
    )
    
    trace_request(
        method="PUT",
        path="/api/v1/users/456",
        status_code=200,
        duration_ms=25.3,
        request_id=request_id,
        user_id=user_id
    )


# ============================================================================
# 日志输出示例
# ============================================================================

"""
运行此脚本后，你会看到以下格式的日志输出：

控制台输出（JSON格式）：
{"level": "INFO", "message": "用户登录成功", "created_at": "2025-12-23T10:30:45.123456", "logger": "app", "user_id": 123, "username": "john", "ip": "192.168.1.1"}

文件输出（logs/app.json.log）：
{"level": "INFO", "message": "用户登录成功", "created_at": "2025-12-23T10:30:45.123456", "logger": "app", "user_id": 123, "username": "john", "ip": "192.168.1.1"}
{"level": "WARNING", "message": "登录失败，次数过多", "created_at": "2025-12-23T10:30:46.234567", "logger": "app", "user_id": 456, "attempt": 5, "ip": "10.0.0.1"}
...

日志文件可以直接用ELK Stack或其他日志分析工具解析。

优势：
1. 结构化：每条日志都是有效的JSON
2. 可扩展：可以添加任意的自定义字段
3. 易分析：可以通过jq或编程语言直接解析
4. 性能：JSON格式在日志聚合系统中性能更好
5. 可读性：所有信息都在一条日志中，无需关联多条日志
"""


if __name__ == "__main__":
    print("结构化日志使用示例\n")
    
    example_basic_logging()
    example_http_logging()
    example_database_logging()
    example_cache_logging()
    example_exception_logging()
    example_custom_logger()
    example_real_world_scenario()
    example_logging_with_context()
    
    print("\n✅ 所有日志已输出到控制台和 logs/app.json.log 文件")
    print("检查 logs/app.json.log 查看完整的日志内容")
