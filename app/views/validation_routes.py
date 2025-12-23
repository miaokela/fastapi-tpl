"""
FastAPI 路由中的请求校验示例
展示如何在实际路由中使用Pydantic校验和自定义校验逻辑
"""

from fastapi import APIRouter, HTTPException, status, Body, Query, Path
from pydantic import ValidationError
import re

# 导入示例中的校验模型
from app.schemas.validation_examples import (
    ImprovedUserCreate,
    UserCheckAsync,
    ProductOrder,
)

# 假设有这样的模型（在实际项目中）
from app.models.models import User
from app.utils.responses import error, success, created, ResponseCode

router = APIRouter(prefix="/validation-examples", tags=["校验示例"])


# ============================================================================
# 1. 基础请求校验 - FastAPI自动处理
# ============================================================================

@router.post("/register", summary="用户注册（自动校验）")
async def register_user(user_data: ImprovedUserCreate):
    """
    FastAPI会自动执行ImprovedUserCreate中的所有校验：
    1. 字段类型检查
    2. 字段约束（长度、范围等）
    3. @field_validator 装饰器的自定义规则
    4. @model_validator 装饰器的模型级规则
    
    如果验证失败，FastAPI会自动返回422错误和详细的错误信息
    """
    # 如果代码执行到这里，说明user_data已经通过了所有校验
    
    # 检查用户名是否已存在（数据库级别的校验）
    existing_user = await User.get_or_none(username=user_data.username)
    if existing_user:
        return error(ResponseCode.USERNAME_EXISTS)
    
    # 检查邮箱是否已存在
    existing_email = await User.get_or_none(email=user_data.email)
    if existing_email:
        return error(ResponseCode.EMAIL_EXISTS)
    
    # 创建用户
    from app.core.security import get_password_hash
    user = await User.create(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=user_data.is_active,
    )
    
    return created({"user_id": user.id, "username": user.username})


# ============================================================================
# 2. 查询参数的校验
# ============================================================================

@router.get("/search")
async def search_users(
    # 字符串长度校验
    keyword: str = Query(..., min_length=1, max_length=50, description="搜索关键词"),
    
    # 整数范围校验
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    
    # 正则表达式校验
    sort_by: str = Query("created_at", regex="^(created_at|username|email)$", description="排序字段"),
):
    """
    查询参数也支持Field校验
    FastAPI会自动验证查询参数的类型、范围、格式等
    """
    return {
        "keyword": keyword,
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
    }


# ============================================================================
# 3. 路径参数的校验
# ============================================================================

@router.get("/users/{user_id}")
async def get_user(
    # 整数必须大于0
    user_id: int = Path(..., gt=0, description="用户ID"),
):
    """路径参数也可以进行约束验证"""
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    return success({"id": user.id, "username": user.username})


# ============================================================================
# 4. 复杂的自定义校验 - 数据库级别
# ============================================================================

@router.post("/order")
async def create_order(order: ProductOrder):
    """
    ProductOrder模型已经进行了基础校验和模型级别的折扣验证
    这里可以再进行数据库级别的校验（如库存检查）
    """
    # 检查产品是否存在
    # product = await Product.get_or_none(id=order.product_id)
    # if not product:
    #     return error(ResponseCode.NOT_FOUND, "产品不存在")
    
    # 检查库存
    # if product.stock < order.quantity:
    #     return error(ResponseCode.BAD_REQUEST, f"库存不足，仅剩{product.stock}个")
    
    return created({
        "order_id": 123,
        "total_price": order.original_price * order.quantity * (1 - order.discount_percent / 100)
    })


# ============================================================================
# 5. 手动验证（当需要自定义错误处理时）
# ============================================================================

@router.post("/manual-validation")
async def manual_validation(data: dict = Body(...)):
    """
    在某些特殊情况下，可能需要手动进行验证而不是依赖Pydantic自动验证
    """
    from app.schemas.validation_examples import ImprovedUserCreate
    
    try:
        # 手动创建Pydantic模型，触发验证
        user_data = ImprovedUserCreate(**data)
    except ValidationError as e:
        # 自定义错误处理
        errors = []
        for err in e.errors():
            field = err['loc'][0]
            message = err['msg']
            errors.append(f"{field}: {message}")
        
        return error(
            ResponseCode.VALIDATION_ERROR,
            "数据验证失败",
            data={"errors": errors}
        )
    
    # 验证通过后的处理
    return success({"message": "验证通过", "data": user_data.model_dump()})


# ============================================================================
# 6. 异步校验 - 检查用户名是否已存在
# ============================================================================

@router.post("/check-username")
async def check_username(username: str = Body(..., min_length=3, max_length=50)):
    """
    异步校验：检查用户名是否在数据库中已存在
    这种校验必须在路由处理器中进行，不能在Pydantic模型中进行
    """
    # 基础格式校验
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return error(ResponseCode.BAD_REQUEST, "用户名格式不正确")
    
    # 数据库级别的异步校验
    existing = await User.get_or_none(username=username)
    if existing:
        return error(ResponseCode.USERNAME_EXISTS, f"用户名 '{username}' 已存在")
    
    return success({"available": True, "message": "用户名可用"})


# ============================================================================
# 7. 条件校验的例子
# ============================================================================

class UpdateUserRequest:
    """更新用户信息时的条件校验"""
    pass


@router.put("/users/{user_id}")
async def update_user(
    user_id: int = Path(..., gt=0),
    username: str = Query(None, min_length=3, max_length=50),
    email: str = Query(None),
    new_password: str = Query(None, min_length=8),
    new_password_confirm: str = Query(None),
):
    """
    条件校验：
    - 如果提供了new_password，必须同时提供new_password_confirm且相等
    - email必须是有效的邮箱格式
    """
    from pydantic import EmailStr
    
    # 密码确认检查
    if new_password or new_password_confirm:
        if not new_password or not new_password_confirm:
            return error(ResponseCode.BAD_REQUEST, "修改密码时必须同时提供新密码和确认密码")
        
        if new_password != new_password_confirm:
            return error(ResponseCode.BAD_REQUEST, "新密码和确认密码不一致")
    
    # 邮箱格式检查
    if email:
        try:
            EmailStr.validate(email)
        except Exception:
            return error(ResponseCode.BAD_REQUEST, "邮箱格式不正确")
    
    return success({"message": "用户信息已更新"})


# ============================================================================
# 8. 错误处理 - 统一的验证错误响应
# ============================================================================

# 在main.py中可以添加全局异常处理器
"""
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI
from app.utils.responses import error, ResponseCode

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    # exc.errors() 返回所有验证错误的详细列表
    errors = []
    for error_item in exc.errors():
        field = '.'.join(str(loc) for loc in error_item['loc'][1:])
        message = error_item['msg']
        errors.append({"field": field, "message": message})
    
    return error(
        ResponseCode.VALIDATION_ERROR,
        "请求数据验证失败",
        data={"errors": errors}
    )
"""


# ============================================================================
# 9. 常用的Pydantic校验器参考
# ============================================================================

"""
常用Field约束：
- min_length / max_length：字符串长度
- ge / gt / le / lt：数值大小（greater/less than或equal）
- pattern / regex：正则表达式
- description：字段描述（用于文档）
- examples：示例值
- default / default_factory：默认值
- alias：字段别名（用于处理前端发送的不同字段名）

常用field_validator模式：
- mode='before'：在类型转换前验证（可以修改输入）
- mode='after'：在类型转换后验证（默认，验证最终值）
- mode='wrap'：包装型验证，可以自定义整个验证流程

常见的内置验证器：
- EmailStr：邮箱
- HttpUrl：URL
- UUID：UUID格式
- conint(ge=0, le=100)：条件整数
- constr(min_length=1, regex="...")：条件字符串
"""
