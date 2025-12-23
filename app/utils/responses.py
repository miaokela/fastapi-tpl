"""
API响应格式标准化模块
提供统一的响应格式封装，所有接口都返回 HTTP 200，通过 code 判断业务状态
"""

from enum import IntEnum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


# ============================================================================
# 响应码枚举
# ============================================================================

class ResponseCode(IntEnum):
    """响应状态码枚举"""
    # 成功状态码 (1xxx)
    SUCCESS = 1000                    # 操作成功
    CREATED = 1001                    # 创建成功
    UPDATED = 1002                    # 更新成功
    DELETED = 1003                    # 删除成功
    
    # 客户端错误 (4xxx)
    BAD_REQUEST = 4000                # 请求错误
    VALIDATION_ERROR = 4001           # 数据验证失败
    UNAUTHORIZED = 4010               # 未授权/未登录
    TOKEN_EXPIRED = 4011              # Token 已过期
    TOKEN_INVALID = 4012              # Token 无效
    FORBIDDEN = 4030                  # 权限不足
    NOT_FOUND = 4040                  # 资源不存在
    USER_NOT_FOUND = 4041             # 用户不存在
    TASK_NOT_FOUND = 4042             # 任务不存在
    CONFLICT = 4090                   # 资源冲突
    USERNAME_EXISTS = 4091            # 用户名已存在
    EMAIL_EXISTS = 4092               # 邮箱已存在
    TASK_NAME_EXISTS = 4093           # 任务名已存在
    
    # 服务端错误 (5xxx)
    SERVER_ERROR = 5000               # 服务器内部错误
    DATABASE_ERROR = 5001             # 数据库错误
    REDIS_ERROR = 5002                # Redis 错误
    CELERY_ERROR = 5003               # Celery 错误


# ============================================================================
# 响应消息映射
# ============================================================================

RESPONSE_MESSAGES: Dict[int, str] = {
    # 成功
    ResponseCode.SUCCESS: "操作成功",
    ResponseCode.CREATED: "创建成功",
    ResponseCode.UPDATED: "更新成功",
    ResponseCode.DELETED: "删除成功",
    
    # 客户端错误
    ResponseCode.BAD_REQUEST: "请求参数错误",
    ResponseCode.VALIDATION_ERROR: "数据验证失败",
    ResponseCode.UNAUTHORIZED: "请先登录",
    ResponseCode.TOKEN_EXPIRED: "登录已过期，请重新登录",
    ResponseCode.TOKEN_INVALID: "无效的认证信息",
    ResponseCode.FORBIDDEN: "权限不足",
    ResponseCode.NOT_FOUND: "资源不存在",
    ResponseCode.USER_NOT_FOUND: "用户不存在",
    ResponseCode.TASK_NOT_FOUND: "任务不存在",
    ResponseCode.CONFLICT: "资源冲突",
    ResponseCode.USERNAME_EXISTS: "用户名已存在",
    ResponseCode.EMAIL_EXISTS: "邮箱已存在",
    ResponseCode.TASK_NAME_EXISTS: "任务名已存在",
    
    # 服务端错误
    ResponseCode.SERVER_ERROR: "服务器内部错误",
    ResponseCode.DATABASE_ERROR: "数据库错误",
    ResponseCode.REDIS_ERROR: "Redis 连接错误",
    ResponseCode.CELERY_ERROR: "任务队列错误",
}


# ============================================================================
# 响应模型
# ============================================================================

class ApiResponse(BaseModel):
    """标准API响应格式"""
    code: int = ResponseCode.SUCCESS
    message: str = "操作成功"
    data: Optional[Any] = None


class PaginatedData(BaseModel):
    """分页数据结构"""
    items: List[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


class PaginatedResponse(BaseModel):
    """分页响应格式"""
    code: int = ResponseCode.SUCCESS
    message: str = "查询成功"
    data: PaginatedData


# ============================================================================
# 响应构建函数
# ============================================================================

def get_message(code: ResponseCode, custom_message: Optional[str] = None) -> str:
    """获取响应消息"""
    if custom_message:
        return custom_message
    return RESPONSE_MESSAGES.get(code, "未知状态")


def response(
    code: ResponseCode = ResponseCode.SUCCESS,
    message: Optional[str] = None,
    data: Any = None
) -> Dict[str, Any]:
    """
    统一响应构建函数
    
    Args:
        code: 响应码（ResponseCode 枚举）
        message: 自定义消息，为空则使用默认消息
        data: 响应数据
    
    Returns:
        标准响应字典
    """
    return {
        "code": int(code),
        "message": get_message(code, message),
        "data": data
    }


def success(data: Any = None, message: Optional[str] = None) -> Dict[str, Any]:
    """成功响应"""
    return response(ResponseCode.SUCCESS, message, data)


def created(data: Any = None, message: Optional[str] = None) -> Dict[str, Any]:
    """创建成功响应"""
    return response(ResponseCode.CREATED, message, data)


def updated(data: Any = None, message: Optional[str] = None) -> Dict[str, Any]:
    """更新成功响应"""
    return response(ResponseCode.UPDATED, message, data)


def deleted(data: Any = None, message: Optional[str] = None) -> Dict[str, Any]:
    """删除成功响应"""
    return response(ResponseCode.DELETED, message, data)


def error(
    code: ResponseCode = ResponseCode.BAD_REQUEST,
    message: Optional[str] = None,
    data: Any = None
) -> Dict[str, Any]:
    """错误响应"""
    return response(code, message, data)


def paginated(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    分页响应
    
    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码（从1开始）
        page_size: 每页数量
        message: 自定义消息
    
    Returns:
        分页响应字典
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return {
        "code": int(ResponseCode.SUCCESS),
        "message": get_message(ResponseCode.SUCCESS, message or "查询成功"),
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


# ============================================================================
# 兼容旧接口（保持向后兼容）
# ============================================================================

def success_response(
    data: Any = None,
    message: str = "操作成功",
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """成功响应（兼容旧接口）"""
    resp = success(data, message)
    if meta:
        resp["data"] = {"result": data, "meta": meta} if data else {"meta": meta}
    return resp


def error_response(
    message: str = "操作失败",
    errors: Optional[List[str]] = None,
    data: Any = None
) -> Dict[str, Any]:
    """错误响应（兼容旧接口）"""
    resp = error(ResponseCode.BAD_REQUEST, message, data)
    if errors:
        resp["data"] = {"errors": errors}
    return resp


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "查询成功"
) -> Dict[str, Any]:
    """分页响应（兼容旧接口）"""
    return paginated(items, total, page, page_size, message)


def validation_error_response(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """验证错误响应"""
    error_messages = []
    for err in errors:
        field = ".".join(str(loc) for loc in err["loc"])
        msg = err["msg"]
        error_messages.append(f"{field}: {msg}")
    
    return error(
        ResponseCode.VALIDATION_ERROR,
        "数据验证失败",
        {"errors": error_messages}
    )