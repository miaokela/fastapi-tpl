"""
FastAPI请求校验示例
展示Pydantic v2中的各种校验方式
"""

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional
import re


# ============================================================================
# 1. 基础类型约束（最简单）
# ============================================================================

class BasicValidation(BaseModel):
    """基础字段约束示例"""
    # 字符串长度
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    
    # 邮箱（内置验证）
    email: EmailStr
    
    # 密码
    password: str = Field(..., min_length=6, max_length=100)
    
    # 整数范围
    age: int = Field(..., ge=0, le=150, description="年龄(0-150)")
    
    # 浮点数
    score: float = Field(..., ge=0.0, le=100.0, description="评分(0-100)")
    
    # 正则表达式
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号")
    
    # 枚举
    gender: str = Field(default="unknown", description="性别: male/female/unknown")


# ============================================================================
# 2. 单字段校验（@field_validator）
# ============================================================================

class UserWithFieldValidation(BaseModel):
    """单字段级校验示例"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    
    # 校验用户名：只允许字母、数字、下划线
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名只能包含字母、数字和下划线')
        if v[0].isdigit():
            raise ValueError('用户名不能以数字开头')
        return v
    
    # 校验密码强度
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        errors = []
        if len(v) < 8:
            errors.append('密码至少8个字符')
        if not any(c.isupper() for c in v):
            errors.append('密码必须包含至少一个大写字母')
        if not any(c.isdigit() for c in v):
            errors.append('密码必须包含至少一个数字')
        if not any(c in '!@#$%^&*' for c in v):
            errors.append('密码必须包含至少一个特殊字符(!@#$%^&*)')
        
        if errors:
            raise ValueError(' ; '.join(errors))
        return v
    
    # 校验邮箱：某些域名不允许
    @field_validator('email', mode='after')
    @classmethod
    def validate_email_domain(cls, v):
        blacklist_domains = ['qq.com', 'temp-mail.com']
        domain = v.split('@')[1].lower()
        if domain in blacklist_domains:
            raise ValueError(f'不允许使用 {domain} 邮箱')
        return v


# ============================================================================
# 3. 模型级校验（@model_validator） - 多字段关联验证
# ============================================================================

class UserRegistration(BaseModel):
    """注册时需要密码确认"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    password_confirm: str
    
    # 多字段校验：确认密码
    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError('密码和确认密码不一致')
        return self


class ProductOrder(BaseModel):
    """订单：价格和折扣的关联验证"""
    product_id: int
    quantity: int = Field(..., ge=1, description="数量至少为1")
    original_price: float = Field(..., gt=0, description="原价")
    discount_percent: float = Field(default=0, ge=0, le=100, description="折扣百分比")
    
    @model_validator(mode='after')
    def validate_discount(self):
        # 折扣金额不能超过原价
        max_discount = self.original_price * self.quantity
        actual_discount = max_discount * (self.discount_percent / 100)
        
        if self.discount_percent > 50 and self.quantity > 100:
            raise ValueError('批量购买（>100）折扣不能超过50%')
        
        return self


# ============================================================================
# 4. 高级用法：自定义异步校验
# ============================================================================

class UserCheckAsync(BaseModel):
    """异步校验示例（检查用户名是否已存在）"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    
    @field_validator('username')
    @classmethod
    def validate_username_format(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('用户名格式不正确')
        return v
    
    # 注意：异步验证需要在路由中使用async def和await
    # 不能直接在Pydantic模型中进行，需要在路由处理器中实现


# ============================================================================
# 5. 条件校验
# ============================================================================

class UserProfile(BaseModel):
    """用户资料：某些字段是条件的"""
    name: str = Field(..., min_length=1, max_length=100)
    is_student: bool = False
    school_name: Optional[str] = None
    graduation_year: Optional[int] = None
    
    @model_validator(mode='after')
    def check_student_info(self):
        # 如果是学生，学校名和毕业年份是必需的
        if self.is_student:
            if not self.school_name:
                raise ValueError('学生必须提供学校名称')
            if not self.graduation_year:
                raise ValueError('学生必须提供毕业年份')
            if self.graduation_year < 2000 or self.graduation_year > 2100:
                raise ValueError('毕业年份必须在2000-2100之间')
        return self


# ============================================================================
# 6. 自定义类型（Annotated）
# ============================================================================

from typing import Annotated
from pydantic import constr, conint

# 定义可重用的验证类型
UsernameType = Annotated[str, Field(min_length=3, max_length=50)]
PasswordType = Annotated[str, Field(min_length=8)]
PortType = Annotated[int, Field(ge=1, le=65535)]

class ServerConfig(BaseModel):
    """使用自定义类型"""
    host_username: UsernameType
    host_password: PasswordType
    port: PortType
    debug_mode: bool = False


# ============================================================================
# 7. 实际项目改进：改进的UserCreate
# ============================================================================

class ImprovedUserCreate(BaseModel):
    """改进后的用户创建模型，包含多种校验"""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="用户名: 3-50字符，只能包含字母、数字、下划线"
    )
    
    email: EmailStr = Field(..., description="邮箱地址")
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="密码: 至少8个字符，必须包含大小写字母、数字、特殊字符"
    )
    
    password_confirm: str = Field(..., description="确认密码")
    
    is_active: bool = Field(default=True, description="是否激活")
    
    # 单字段校验
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError('用户名必须以字母开头，只能包含字母、数字和下划线')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        checks = {
            '至少8个字符': len(v) >= 8,
            '包含大写字母': any(c.isupper() for c in v),
            '包含小写字母': any(c.islower() for c in v),
            '包含数字': any(c.isdigit() for c in v),
            '包含特殊字符': any(c in '!@#$%^&*_-' for c in v),
        }
        
        failed = [k for k, v in checks.items() if not v]
        if failed:
            raise ValueError(f'密码必须满足以下条件: {", ".join(failed)}')
        return v
    
    # 模型级校验
    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError('密码和确认密码必须一致')
        return self


# ============================================================================
# 配置模型：忽略额外字段或禁止额外字段
# ============================================================================

class StrictUserCreate(BaseModel):
    """严格模式：不允许额外字段"""
    username: str
    email: EmailStr
    
    model_config = {
        'extra': 'forbid',  # 禁止额外字段，会抛出ValidationError
        # 'extra': 'ignore',  # 忽略额外字段
    }
