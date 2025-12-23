from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from tortoise.contrib.fastapi import register_tortoise
from contextlib import asynccontextmanager
import os

from config.settings import settings
from config.database import DATABASE_CONFIG
from config.logging import setup_logging, get_logger
from app.utils.redis_client import redis_client
from app.utils.responses import error, ResponseCode
from app.views.user_views import router as user_router, user_management_router
from app.admin import admin_router


# 配置日志（按天轮转，保留7天）
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("FastAPI应用启动中...")
    
    # 初始化 Tortoise ORM
    from tortoise import Tortoise
    await Tortoise.init(config=DATABASE_CONFIG)
    await Tortoise.generate_schemas()
    logger.info("数据库连接成功")
    
    # 连接Redis
    try:
        await redis_client.connect()
        logger.info("Redis连接成功")
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
    
    # 创建超级管理员账户
    try:
        await create_superuser()
    except Exception as e:
        logger.error(f"创建超级管理员失败: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("FastAPI应用关闭中...")
    
    # 断开Redis连接
    try:
        await redis_client.disconnect()
        logger.info("Redis连接已断开")
    except Exception as e:
        logger.error(f"Redis断开连接失败: {e}")
    
    # 关闭数据库连接
    await Tortoise.close_connections()
    logger.info("数据库连接已断开")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    description="FastAPI基础项目，集成Celery、Redis、Tortoise ORM、JWT认证",
    lifespan=lifespan
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


# 全局异常处理 - 统一响应格式 {code, message, data}
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    HTTP异常处理
    将Starlette的HTTPException转换为统一的API响应格式
    """
    # 根据HTTP状态码映射到相应的ResponseCode
    code_mapping = {
        400: ResponseCode.BAD_REQUEST,
        401: ResponseCode.UNAUTHORIZED,
        403: ResponseCode.FORBIDDEN,
        404: ResponseCode.NOT_FOUND,
        409: ResponseCode.CONFLICT,
        422: ResponseCode.VALIDATION_ERROR,
        500: ResponseCode.SERVER_ERROR,
    }
    
    response_code = code_mapping.get(exc.status_code, ResponseCode.SERVER_ERROR)
    
    # 处理认证错误信息
    message = exc.detail
    if exc.status_code == 401:
        message = "未授权：请先登录或提供有效的认证信息"
    elif exc.status_code == 403:
        message = "权限不足：您没有足够的权限访问此资源"
    
    return JSONResponse(
        status_code=200,  # 始终返回200，通过code字段判断业务状态
        content=error(response_code, message)
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    请求验证异常处理（Pydantic验证失败）
    统一的响应格式包含所有验证错误详情
    """
    # 提取验证错误信息
    errors = []
    for error_item in exc.errors():
        field = '.'.join(str(loc) for loc in error_item['loc'][1:])
        message = error_item['msg']
        error_type = error_item['type']
        errors.append({
            "field": field,
            "message": message,
            "type": error_type
        })
    
    return JSONResponse(
        status_code=200,  # 始终返回200，通过code字段判断业务状态
        content=error(
            ResponseCode.VALIDATION_ERROR,
            "请求数据验证失败",
            data={"errors": errors}
        )
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    通用异常处理
    捕获所有未处理的异常，统一转换为标准响应格式
    """
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    # 只在调试模式下返回详细错误信息
    error_detail = str(exc) if settings.DEBUG else None
    
    return JSONResponse(
        status_code=200,  # 始终返回200，通过code字段判断业务状态
        content=error(
            ResponseCode.SERVER_ERROR,
            "服务器内部错误",
            data={"detail": error_detail} if settings.DEBUG else None
        )
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


# 注册路由
def register_routes():
    """注册所有路由"""
    
    # 包含认证路由（已在 user_views.py 中通过 add_api_route 注册）
    app.include_router(user_router)
    
    # 包含 Admin 管理路由（根据配置决定是否启用）
    if settings.ADMIN_ENABLED:
        app.include_router(admin_router, prefix="/api/v1")
    
    # 包含用户管理路由（函数式编程实现）
    app.include_router(user_management_router, prefix="/api/v1")


# Celery任务路由
@app.post("/api/v1/tasks/send-email")
async def trigger_send_email(email: str, username: str):
    """触发发送邮件任务"""
    from celery_app.tasks.email_tasks import send_welcome_email
    
    task = send_welcome_email.delay(email, username)
    return {
        "message": "邮件发送任务已提交",
        "task_id": task.id,
        "status": "pending"
    }


@app.post("/api/v1/tasks/generate-report")
async def trigger_generate_report(report_type: str, filters: dict = None):
    """触发生成报告任务"""
    from celery_app.tasks.general_tasks import generate_report
    
    task = generate_report.delay(report_type, filters)
    return {
        "message": "报告生成任务已提交",
        "task_id": task.id,
        "status": "pending"
    }


@app.get("/api/v1/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务状态"""
    from celery_app.celery import celery_app
    
    task_result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }


# Redis缓存示例路由
@app.get("/api/v1/cache/test")
async def test_cache():
    """测试Redis缓存"""
    key = "test_key"
    value = {"message": "Hello Redis!", "timestamp": "2024-01-01 12:00:00"}
    
    # 设置缓存
    await redis_client.set_value(key, value, expire=60)
    
    # 获取缓存
    cached_value = await redis_client.get_value(key)
    
    return {
        "cached_value": cached_value,
        "cache_exists": await redis_client.exists(key),
        "cache_ttl": await redis_client.get_ttl(key)
    }


# 复杂查询示例路由
@app.get("/api/v1/reports/user-stats")
async def get_user_stats():
    """获取用户统计报告"""
    try:
        # 这里可以添加实际的统计查询逻辑
        # 例如使用 Tortoise ORM
        stats = {
            "total_users": 0,
            "active_users": 0,
            "recent_registrations": 0,
            "message": "统计功能可用，需要实现具体的查询逻辑"
        }
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def create_superuser():
    """创建超级管理员账户"""
    from app.models.models import User, UserProfile
    from app.core.security import get_password_hash
    
    # 检查是否已存在超级管理员
    existing_admin = await User.get_or_none(email=settings.ADMIN_EMAIL)
    if existing_admin:
        logger.info("超级管理员账户已存在")
        return
    
    # 创建超级管理员
    hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
    admin_user = await User.create(
        username="admin",
        email=settings.ADMIN_EMAIL,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=True
    )
    
    # 创建管理员资料
    await UserProfile.create(
        user=admin_user,
        first_name="系统",
        last_name="管理员"
    )
    
    logger.info(f"超级管理员账户创建成功: {settings.ADMIN_EMAIL}")


# 注册路由（不再使用 register_tortoise）
register_routes()


# 挂载静态文件目录 - Admin管理后台
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if settings.ADMIN_ENABLED and os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Admin管理后台入口
if settings.ADMIN_ENABLED:
    @app.get("/admin")
    @app.get("/admin/")
    async def admin_page():
        """Admin管理后台页面"""
        admin_index = os.path.join(STATIC_DIR, "admin", "index.html")
        if os.path.exists(admin_index):
            return FileResponse(admin_index)
        return JSONResponse(
            status_code=404,
            content={"message": "Admin页面未找到"}
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )