"""
日志配置模块
- 按天轮转日志文件
- 保留最近7天的日志
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from config.settings import settings


def setup_logging():
    """配置日志系统"""
    
    # 确保日志目录存在
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "app.log")
    
    # 日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 清除已有的处理器
    root_logger.handlers.clear()
    
    # 文件处理器 - 按天轮转，保留7天
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",      # 每天午夜轮转
        interval=1,           # 间隔1天
        backupCount=7,        # 保留7个备份
        encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"  # 备份文件后缀格式：app.log.2025-11-28
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别（减少噪音）
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("tortoise").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str = None) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)
