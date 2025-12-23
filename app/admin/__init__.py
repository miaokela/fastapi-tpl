"""
Admin 管理模块
提供用户管理和定时任务管理的API
"""
from .admin_views import router as admin_router

__all__ = ["admin_router"]
