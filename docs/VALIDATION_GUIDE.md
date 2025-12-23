"""
FastAPI 请求校验完整指南
包含常见场景和最佳实践
"""

# ============================================================================
# 快速参考表
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────┐
│                    FastAPI 校验方式速查表                                │
├─────────────────────────────────────────────────────────────────────────┤
│ 校验类型          │ 实现方式        │ 何时使用         │ 优先级          │
├─────────────────────────────────────────────────────────────────────────┤
│ 基础类型          │ Python 类型提示 │ 总是             │ 最高            │
│ 字段约束          │ Field(...)      │ 总是             │ 最高            │
│ 单字段自定义      │ @field_validator│ 复杂字段规则     │ 高              │
│ 多字段关联        │ @model_validator│ 字段间有依赖     │ 高              │
│ 异步校验(如DB检查)│ 在路由处理器中  │ 需要I/O操作      │ 中              │
│ 全局异常处理      │ @app.exception  │ 统一错误格式     │ 中              │
└─────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# 场景 1: 用户注册 - 完整的校验流程
# ============================================================================

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
import re
from typing import Optional


class UserRegistrationRequest(BaseModel):
    """用户注册请求"""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名: 3-50字符"
    )
    
    email: EmailStr = Field(..., description="邮箱: 必须是有效邮箱")
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="密码: 8-100字符，需要大小写、数字、特殊字符"
    )
    
    password_confirm: str = Field(..., description="确认密码")
    
    agree_terms: bool = Field(..., description="是否同意服务条款")
    
    # ===== 单字段校验 =====
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        # 检查格式：必须以字母开头，只能包含字母、数字、下划线
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('用户名必须以字母开头，只能包含字母、数字、下划线')
        
        # 检查黑名单
        blacklist = ['admin', 'root', 'system', 'test']
        if v.lower() in blacklist:
            raise ValueError(f'用户名 "{v}" 已被保留')
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        errors = []
        
        # 检查强度
        if len(v) < 8:
            errors.append('至少8个字符')
        if not any(c.isupper() for c in v):
            errors.append('需要至少一个大写字母')
        if not any(c.islower() for c in v):
            errors.append('需要至少一个小写字母')
        if not any(c.isdigit() for c in v):
            errors.append('需要至少一个数字')
        if not any(c in '!@#$%^&*_-' for c in v):
            errors.append('需要至少一个特殊字符(!@#$%^&*_-)')
        
        if errors:
            raise ValueError(f'密码强度不足: {", ".join(errors)}')
        
        return v
    
    # ===== 模型级校验 =====
    @model_validator(mode='after')
    def validate_registration(self):
        # 检查两次密码是否一致
        if self.password != self.password_confirm:
            raise ValueError('两次输入的密码不一致')
        
        # 检查是否同意服务条款
        if not self.agree_terms:
            raise ValueError('必须同意服务条款才能注册')
        
        return self


# 使用示例：
"""
POST /register
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "agree_terms": true
}

失败示例 (自动返回422):
{
    "username": "123abc",  # ❌ 必须以字母开头
    "email": "invalid",     # ❌ 邮箱格式不正确
    "password": "weak",     # ❌ 密码强度不足
    "password_confirm": "weak",
    "agree_terms": false    # ❌ 必须同意服务条款
}
"""


# ============================================================================
# 场景 2: 订单创建 - 条件校验
# ============================================================================

class OrderItem(BaseModel):
    """订单项"""
    product_id: int = Field(..., gt=0, description="产品ID")
    quantity: int = Field(..., ge=1, le=1000, description="数量(1-1000)")
    price: float = Field(..., gt=0, description="单价")


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    
    items: list[OrderItem] = Field(..., min_items=1, max_items=100, description="订单项")
    
    discount_percent: float = Field(0, ge=0, le=100, description="折扣百分比(0-100)")
    
    # 优惠券代码（可选）
    coupon_code: Optional[str] = Field(None, min_length=1, max_length=50)
    
    # 备注（可选）
    remarks: Optional[str] = Field(None, max_length=500)
    
    @model_validator(mode='after')
    def validate_order(self):
        # 计算总金额
        total_amount = sum(item.quantity * item.price for item in self.items)
        
        # 检查折扣逻辑
        if self.discount_percent > 0 and total_amount < 100:
            raise ValueError('订单金额不足100元不能享受折扣')
        
        # 如果有优惠券，检查格式
        if self.coupon_code:
            if not re.match(r'^[A-Z0-9]{6,}$', self.coupon_code):
                raise ValueError('优惠券代码格式不正确')
        
        return self


# ============================================================================
# 场景 3: 搜索过滤 - 查询参数校验
# ============================================================================

from enum import Enum
from datetime import date


class SortOrder(str, Enum):
    """排序顺序"""
    ASC = "asc"
    DESC = "desc"


class SearchFilter(BaseModel):
    """搜索过滤条件"""
    
    # 关键词搜索
    keyword: Optional[str] = Field(None, min_length=1, max_length=100)
    
    # 分页
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页大小(1-100)")
    
    # 排序
    sort_by: str = Field("created_at", regex="^(created_at|name|price|rating)$")
    sort_order: SortOrder = Field(SortOrder.DESC)
    
    # 日期范围
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # 价格范围
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    
    @field_validator('keyword')
    @classmethod
    def validate_keyword(cls, v):
        if v and len(v.strip()) == 0:
            raise ValueError('关键词不能为空')
        return v.strip() if v else None
    
    @model_validator(mode='after')
    def validate_search_filter(self):
        # 检查日期顺序
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError('开始日期不能晚于结束日期')
        
        # 检查价格范围
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError('最低价格不能高于最高价格')
        
        return self


# ============================================================================
# 场景 4: 批量操作 - 列表校验
# ============================================================================

class BulkDeleteRequest(BaseModel):
    """批量删除请求"""
    
    ids: list[int] = Field(
        ...,
        min_items=1,
        max_items=1000,
        description="要删除的ID列表(1-1000项)"
    )
    
    confirm: bool = Field(
        ...,
        description="二次确认"
    )
    
    @field_validator('ids')
    @classmethod
    def validate_ids(cls, v):
        # 检查是否有重复
        if len(v) != len(set(v)):
            raise ValueError('ID列表中有重复项')
        
        # 检查所有ID都大于0
        if any(id <= 0 for id in v):
            raise ValueError('ID必须大于0')
        
        return v
    
    @model_validator(mode='after')
    def check_confirmation(self):
        if not self.confirm:
            raise ValueError('必须确认才能执行批量删除')
        return self


# ============================================================================
# 场景 5: 复杂业务逻辑 - 自定义异步验证
# ============================================================================

"""
在FastAPI路由中的异步校验示例：

from fastapi import APIRouter
from app.models.models import User

router = APIRouter()

@router.post("/register")
async def register(data: UserRegistrationRequest):
    # 到这里，Pydantic的所有校验都已通过
    
    # 进行异步数据库校验
    existing_user = await User.get_or_none(username=data.username)
    if existing_user:
        return error(ResponseCode.USERNAME_EXISTS, "用户名已存在")
    
    existing_email = await User.get_or_none(email=data.email)
    if existing_email:
        return error(ResponseCode.EMAIL_EXISTS, "邮箱已被注册")
    
    # 创建用户
    user = await User.create(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    
    return created({"user_id": user.id})
"""


# ============================================================================
# 最佳实践总结
# ============================================================================

"""
✅ 应该做:
1. 使用Pydantic BaseModel定义所有请求体
2. 使用Field指定约束条件（min_length, max_length, ge, le等）
3. 使用@field_validator进行单字段的复杂校验
4. 使用@model_validator进行多字段的关联校验
5. 在路由处理器中进行异步校验（数据库查询等）
6. 统一处理验证错误，返回友好的错误信息
7. 在文档中清楚地说明每个字段的要求

❌ 不应该做:
1. 不要在路由处理器中重复进行Pydantic已经做过的校验
2. 不要忽视自定义校验消息，保持用户友好
3. 不要让异步操作出现在@field_validator中（违反性能）
4. 不要忘记处理RequestValidationError异常
5. 不要在密码等敏感字段中使用过于详细的错误信息


📊 性能考虑:
- Pydantic校验很快，在请求处理之前就拦截了错误请求
- 异步校验（如数据库查询）应该在通过基础校验后再执行
- 使用缓存来避免重复的异步校验

🔒 安全考虑:
- 永远不要相信前端发送的数据
- 对敏感操作进行额外的权限检查
- 不要在错误信息中暴露系统内部信息
- 对输入进行长度限制，防止DoS攻击
"""


# ============================================================================
# 常用的Pydantic验证器参考
# ============================================================================

"""
字段约束 (Field 参数):
├── 字符串
│   ├── min_length / max_length
│   ├── pattern / regex
│   └── Example: Field(..., min_length=3, max_length=50)
│
├── 数值
│   ├── ge (>=) / gt (>)
│   ├── le (<=) / lt (<)
│   └── Example: Field(..., ge=0, le=100)
│
├── 列表
│   ├── min_items / max_items
│   └── Example: Field(..., min_items=1, max_items=10)
│
└── 所有字段
    ├── default / default_factory
    ├── alias (别名)
    ├── title / description
    ├── examples
    └── Example: Field(default=0, description="描述")

验证器装饰器:
├── @field_validator('field_name')
│   ├── mode='before' (类型转换前)
│   ├── mode='after' (类型转换后，默认)
│   └── mode='wrap' (包装模式)
│
└── @model_validator(mode='after')
    └── 用于多字段验证

内置验证类型:
├── EmailStr (邮箱)
├── HttpUrl (URL)
├── UUID (UUID)
├── conint(ge=0, le=100) (条件整数)
├── constr(min_length=1) (条件字符串)
└── Field(discriminator='type') (协别字段)
"""
