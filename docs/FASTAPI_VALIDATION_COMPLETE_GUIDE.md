# FastAPI 请求校验完全指南

## 核心概念

在FastAPI中，请求校验主要通过**Pydantic**库实现。当客户端发送请求时，FastAPI会自动：

1. **类型转换和验证** - 确保数据类型正确
2. **字段约束检查** - 检查长度、范围、格式等
3. **自定义校验规则** - 执行自定义验证逻辑
4. **生成API文档** - 自动生成OpenAPI文档

## 校验的四个层次

### 1️⃣ 基础类型验证（自动）
```python
from pydantic import BaseModel

class User(BaseModel):
    username: str        # 必须是字符串
    age: int            # 必须是整数
    is_active: bool     # 必须是布尔值
```

**FastAPI自动处理的事项：**
- 类型转换（"123" → 123）
- 类型检查（拒绝非法类型）
- 错误时返回422状态码

### 2️⃣ 字段约束（Field）
```python
from pydantic import Field

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    age: int = Field(..., ge=0, le=150)  # greater/less than
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
```

**常用约束：**
- `min_length` / `max_length` - 字符串长度
- `ge` (>=) / `gt` (>) / `le` (<=) / `lt` (<) - 数值范围
- `pattern` / `regex` - 正则表达式
- `min_items` / `max_items` - 列表大小

### 3️⃣ 单字段自定义验证（@field_validator）
```python
from pydantic import field_validator

class User(BaseModel):
    username: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v
```

**何时使用：**
- 字段值的复杂逻辑检查
- 依赖外部规则或数据的验证
- 需要修改或转换输入值

### 4️⃣ 模型级验证（@model_validator）
```python
from pydantic import model_validator

class UserRegistration(BaseModel):
    password: str
    password_confirm: str
    
    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError('两次密码不一致')
        return self
```

**何时使用：**
- 多字段之间有依赖关系
- 需要根据多个字段的组合进行验证
- 字段间的逻辑约束

## 异步验证（数据库检查）

对于需要I/O操作的验证（如检查用户名是否已存在），**不能**在Pydantic模型中进行：

```python
# ❌ 错误的方式 - 在@field_validator中做异步操作
@field_validator('username')
@classmethod
async def check_username_exists(cls, v):  # 这不会工作！
    user = await User.get_or_none(username=v)
    if user:
        raise ValueError('用户名已存在')
    return v
```

**✅ 正确的方式 - 在路由处理器中进行**

```python
from fastapi import APIRouter

@router.post("/register")
async def register(user_data: UserRegistration):
    # 到这里，Pydantic的所有校验都已通过
    
    # 进行异步数据库验证
    existing = await User.get_or_none(username=user_data.username)
    if existing:
        return error(ResponseCode.USERNAME_EXISTS)
    
    # 创建用户...
```

## 常见的校验场景

### 场景 1: 用户注册
```python
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # 内置邮箱验证
    password: str = Field(..., min_length=8)
    password_confirm: str
    
    @field_validator('username')
    @classmethod
    def valid_username(cls, v):
        if not v.isalnum():
            raise ValueError('只能包含字母和数字')
        return v
    
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError('密码不一致')
        return self
```

### 场景 2: 查询过滤
```python
class SearchFilter(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field('created_at', regex='^(created_at|name|price)$')
    
    @model_validator(mode='after')
    def validate_filter(self):
        if self.page_size > 100 and self.keyword:
            # 搜索时限制最大页数
            self.page_size = 100
        return self
```

### 场景 3: 范围验证
```python
class DateRangeFilter(BaseModel):
    start_date: date
    end_date: date
    
    @model_validator(mode='after')
    def valid_date_range(self):
        if self.start_date > self.end_date:
            raise ValueError('开始日期不能晚于结束日期')
        return self
```

## 内置验证类型

```python
from pydantic import EmailStr, HttpUrl, UUID, conint, constr
from typing import Annotated

# 邮箱
email: EmailStr

# URL
url: HttpUrl

# UUID
id: UUID

# 条件整数（0-100）
score: Annotated[int, conint(ge=0, le=100)]

# 条件字符串
code: Annotated[str, constr(min_length=6, pattern=r'^[A-Z0-9]+$')]
```

## 错误处理

### 默认错误响应（422 Unprocessable Entity）
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "username"],
      "msg": "String should have at least 3 characters",
      "input": "ab",
      "ctx": {"min_length": 3}
    }
  ]
}
```

### 自定义错误处理
```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.utils.responses import error, ResponseCode

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = []
    for err in exc.errors():
        field = '.'.join(str(x) for x in err['loc'][1:])
        message = err['msg']
        errors.append({"field": field, "message": message})
    
    return error(
        ResponseCode.VALIDATION_ERROR,
        "请求数据验证失败",
        data={"errors": errors}
    )
```

## 最佳实践

### ✅ 应该做

1. **定义清晰的Pydantic模型**
```python
class CreateUserRequest(BaseModel):
    """清晰的文档字符串"""
    username: str = Field(..., description="用户名，3-50字符")
```

2. **使用Field指定约束**
```python
username: str = Field(..., min_length=3, max_length=50)
```

3. **单独处理异步验证**
```python
# 在路由处理器中进行数据库检查
existing = await User.get_or_none(username=username)
```

4. **提供清晰的错误消息**
```python
raise ValueError('用户名必须以字母开头')
```

5. **在文档中说明验证规则**
```python
username: str = Field(..., description="用户名: 3-50字符，必须以字母开头")
```

### ❌ 不应该做

1. **不要在@field_validator中进行异步操作**
```python
# ❌ 错误
@field_validator('username')
async def check(cls, v):  # 这是错的
    ...
```

2. **不要重复验证**
```python
# ❌ 坏的做法
class User(BaseModel):
    age: int = Field(..., ge=0, le=150)

# 在路由中再次检查
if age < 0 or age > 150:  # 这是多余的
    ...
```

3. **不要在error信息中暴露敏感信息**
```python
# ❌ 不安全
raise ValueError(f"Database error: {db_error}")

# ✅ 安全
raise ValueError("操作失败，请稍后重试")
```

4. **不要忽视性能**
```python
# ❌ 低效：对每个字符进行数据库查询
@field_validator('items')
def check_items(cls, v):
    for item in v:
        db.query(item)  # 多次数据库查询！
```

## 调试技巧

### 查看Pydantic模型的JSON Schema
```python
from pydantic import BaseModel

class User(BaseModel):
    username: str

# 查看JSON Schema
print(User.model_json_schema())
```

### 测试验证规则
```python
from pydantic import ValidationError

try:
    user = User(username="ab")  # 太短
except ValidationError as e:
    print(e.errors())  # 打印所有错误
    print(e.json())    # JSON格式
```

### 在FastAPI文档中查看
- 访问 `http://localhost:8000/docs`
- 点击"Try it out"测试验证
- 查看"Schema"了解验证规则

## 参考：验证装饰器速查

| 装饰器 | 用途 | 何时执行 | 说明 |
|-------|------|--------|------|
| `@field_validator('field')` | 单字段验证 | 字段解析后 | mode='after'（默认） |
| `@field_validator('field', mode='before')` | 单字段验证 | 类型转换前 | 可以修改输入值 |
| `@field_validator(multiple=True)` | 多字段 | 各自解析后 | 对多个字段应用同一规则 |
| `@model_validator()` | 模型级验证 | 所有字段解析后 | 用于多字段关联验证 |

## 完整示例：订单系统

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date
from typing import Optional

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=1000)
    price: float = Field(..., gt=0)

class CreateOrderRequest(BaseModel):
    items: list[OrderItem] = Field(..., min_items=1, max_items=100)
    coupon_code: Optional[str] = Field(None, min_length=6)
    discount_percent: float = Field(0, ge=0, le=100)
    
    @field_validator('coupon_code')
    @classmethod
    def validate_coupon(cls, v):
        if v and not v.isupper():
            raise ValueError('优惠券代码必须大写')
        return v
    
    @model_validator(mode='after')
    def validate_order(self):
        total = sum(item.quantity * item.price for item in self.items)
        
        # 折扣逻辑：只能折扣超过100元的订单
        if self.discount_percent > 0 and total < 100:
            raise ValueError('订单金额不足100元，不能使用折扣')
        
        return self

# 在路由中
@router.post("/orders")
async def create_order(order: CreateOrderRequest):
    # 到这里，order已经通过了所有验证
    
    # 检查库存（异步验证）
    for item in order.items:
        product = await Product.get_or_none(id=item.product_id)
        if not product or product.stock < item.quantity:
            return error(ResponseCode.BAD_REQUEST, "库存不足")
    
    # 创建订单...
```

## 更多资源

- [Pydantic官方文档](https://docs.pydantic.dev/)
- [FastAPI验证文档](https://fastapi.tiangolo.com/tutorial/body/)
- [JSON Schema规范](https://json-schema.org/)
