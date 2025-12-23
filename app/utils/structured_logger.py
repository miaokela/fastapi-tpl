"""
结构化日志组件 - 基于loguru
支持按日期自动拆分日志文件，自动清理过期日志

安装依赖：
    pip install loguru
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from loguru import logger as loguru_logger
from typing import Optional

from config.settings import settings


class JsonFileSink:
    """自定义JSON文件sink，支持日志轮转和保留"""
    
    def __init__(self, log_dir: Path, rotation: str = "00:00", retention: str = "7 days"):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.rotation = rotation
        self.retention = retention
        self.current_date = None
        self.current_file = None
        
    def _get_log_file(self):
        """获取当前日期的日志文件路径"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_date:
            self.current_date = today
            self.current_file = self.log_dir / f"{today}.log"
        return self.current_file
    
    def write(self, message):
        """写入日志（简洁JSON格式）"""
        record = message.record
        
        # 构建最小化日志：只有 created_at 和 message，其他都是用户传入的字段
        log_data = {
            "created_at": datetime.fromtimestamp(record["time"].timestamp()).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "message": record["message"],
        }
        
        # 添加用户传入的字段（直接作为顶级字段）
        if record["extra"]:
            log_data.update(record["extra"])
        
        # 写入文件
        log_file = self._get_log_file()
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        
        # 简单的日志轮转和保留（只做基本清理）
        self._cleanup_old_logs()
    
    def _cleanup_old_logs(self):
        """清理过期的日志文件"""
        # 简单实现：保留7天内的日志
        try:
            import os
            now = datetime.now()
            for file in self.log_dir.glob("*.log"):
                file_date = datetime.strptime(file.stem, "%Y-%m-%d")
                days_old = (now - file_date).days
                if days_old > 7:
                    os.remove(file)
        except Exception:
            pass  # 清理失败不影响日志记录


class StructuredLogger:
    """结构化日志记录器 - 基于loguru"""
    
    def __init__(
        self,
        name: str = "app",
        log_dir: str = "logs",
        rotation: str = "00:00",  # 每天午夜轮转
        retention: str = "7 days",  # 保留7天
        enable_file: bool = True,
        enable_console: bool = True,
    ):
        """
        初始化日志记录器
        
        Args:
            name: 日志记录器名称
            log_dir: 日志目录
            rotation: 轮转规则（00:00表示每天午夜）
                     也可以是 "100 MB" 或 "500 MB" 等大小规则
            retention: 保留规则（7 days, 14 days等）
                      也可以是 lambda函数或文件数量如 "10"
            enable_file: 是否启用文件输出
            enable_console: 是否启用控制台输出
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.logger = loguru_logger
        
        # 移除默认处理器
        self.logger.remove()
        
        # 添加控制台处理器
        if enable_console:
            self._add_console_handler()
        
        # 添加文件处理器
        if enable_file:
            self._add_file_handler()
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        if settings.DEBUG:
            # 开发模式：彩色输出
            self.logger.add(
                sys.stderr,
                level="DEBUG",
                format=(
                    "<level>{level: <8}</level> | "
                    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                    "<level>{message}</level>"
                ),
                colorize=True,
            )
    
    def _add_file_handler(self):
        """添加文件处理器"""
        sink = JsonFileSink(self.log_dir)
        
        self.logger.add(
            sink.write,
            level="DEBUG" if settings.DEBUG else "INFO",
            format="{message}",  # 格式化由sink处理
        )
    
    def bind(self, **context):
        """
        绑定上下文字段，这些字段会出现在所有后续日志中
        
        Example:
            >>> logger = StructuredLogger()
            >>> bound_logger = logger.bind(request_id="req_123", user_id=456)
            >>> bound_logger.info("处理请求")  # 自动包含request_id和user_id
        """
        return self.logger.bind(**context)
    
    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """
        记录INFO级别日志
        
        Example:
            >>> logger.info("用户创建成功", user_id=123, username="john")
        """
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """记录异常日志"""
        self.logger.exception(message, **kwargs)
    
    def trace_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """记录HTTP请求"""
        self.logger.info(
            f"{method} {path}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def trace_database(
        self,
        operation: str,
        table: str,
        duration_ms: float,
        **kwargs
    ):
        """记录数据库操作"""
        self.logger.info(
            f"DB {operation} {table}",
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def trace_cache(
        self,
        operation: str,
        key: str,
        hit: bool,
        duration_ms: float = 0,
        **kwargs
    ):
        """记录缓存操作"""
        self.logger.info(
            f"CACHE {operation} {key}",
            operation=operation,
            key=key,
            hit=hit,
            duration_ms=duration_ms,
            **kwargs
        )


# 全局日志记录器实例
_logger = StructuredLogger(
    name="app",
    log_dir="logs",
    rotation="00:00",  # 每天午夜轮转
    retention="7 days",  # 保留7天
    enable_file=True,
    enable_console=True,
)


# ============================================================================
# 便捷函数接口
# ============================================================================

def log_debug(message: str, **kwargs):
    """记录DEBUG日志"""
    _logger.debug(message, **kwargs)


def log_info(message: str, **kwargs):
    """
    记录INFO日志
    
    Example:
        >>> log_info("用户创建成功", user_id=1, username="john")
    """
    _logger.info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """记录WARNING日志"""
    _logger.warning(message, **kwargs)


def log_error(message: str, **kwargs):
    """记录ERROR日志"""
    _logger.error(message, **kwargs)


def log_critical(message: str, **kwargs):
    """记录CRITICAL日志"""
    _logger.critical(message, **kwargs)


def log_exception(message: str, **kwargs):
    """记录异常日志"""
    _logger.exception(message, **kwargs)


def trace_request(method: str, path: str, status_code: int, duration_ms: float, **kwargs):
    """记录HTTP请求"""
    _logger.trace_request(method, path, status_code, duration_ms, **kwargs)


def trace_database(operation: str, table: str, duration_ms: float, **kwargs):
    """记录数据库操作"""
    _logger.trace_database(operation, table, duration_ms, **kwargs)


def trace_cache(operation: str, key: str, hit: bool, duration_ms: float = 0, **kwargs):
    """记录缓存操作"""
    _logger.trace_cache(operation, key, hit, duration_ms, **kwargs)


def get_logger(name: str):
    """获取特定名称的logger实例"""
    return loguru_logger.bind(module=name)
