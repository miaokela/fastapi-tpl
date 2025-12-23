import os
from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序配置"""
    
    # 应用基本信息
    APP_NAME: str = "FastAPI Base"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite://./default_db.sqlite3"
    
    # Redis配置
    REDIS_URL: str = "redis://:123456@localhost:6379/0"
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://:123456@localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://:123456@localhost:6379/2"
    CELERY_TASK_RESULT_EXPIRES: int = 7  # 数据库中任务结果保留天数（仅用于celery_task_result表清理）
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-please-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 管理员配置
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_ENABLED: bool = True  # 是否启用后台管理系统
    
    # CORS配置
    ALLOWED_HOSTS: list = ["*"]
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
    ]
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "uploads"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()