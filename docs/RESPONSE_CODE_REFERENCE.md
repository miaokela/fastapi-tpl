# API响应格式速查表

## 核心规则

| 类型 | HTTP状态码 | 响应结构 |
|------|-----------|--------|
| 所有响应 | **200** | `{code, message, data}` |

## 响应码速查

### ✅ 成功 (1xxx)

| code | 适用场景 |
|------|--------|
| 1000 | 通用成功 / GET / 查询 |
| 1001 | 创建成功 / POST |
| 1002 | 更新成功 / PUT/PATCH |
| 1003 | 删除成功 / DELETE |

**示例：**
```python
# GET /users/123
return success({"id": 123, "name": "John"})

# POST /users
return created({"user_id": 123})

# PUT /users/123
return updated({"id": 123, "name": "John Updated"})

# DELETE /users/123
return deleted({"id": 123})
```

### ❌ 客户端错误 (4xxx)

| code | 含义 | 何时返回 |
|------|------|--------|
| 4000 | 请求参数错误 | 参数验证失败（非Pydantic） |
| 4001 | 数据验证失败 | Pydantic验证失败 |
| 4010 | 未授权 | 未登录或Token验证失败 |
| 4011 | Token已过期 | Token的exp字段过期 |
| 4012 | Token无效 | Token签名错误 |
| 4030 | 权限不足 | 有身份但权限不够 |
| 4040 | 资源不存在 | 通用资源不存在 |
| 4041 | 用户不存在 | 特定：用户不存在 |
| 4042 | 任务不存在 | 特定：任务不存在 |
| 4091 | 用户名已存在 | 注册时重复 |
| 4092 | 邮箱已存在 | 注册时重复 |

**示例：**
```python
# 参数错误
return error(ResponseCode.BAD_REQUEST, "参数错误")

# Pydantic验证失败（自动处理）
# POST /users {"email": "invalid"}
# → 自动返回 code: 4001

# 用户不存在
user = await User.get_or_none(id=user_id)
if not user:
    return error(ResponseCode.USER_NOT_FOUND)

# 用户名已存在
if existing_user:
    return error(ResponseCode.USERNAME_EXISTS)
```

### 🔴 服务器错误 (5xxx)

| code | 含义 |
|------|------|
| 5000 | 服务器内部错误（未知异常） |
| 5001 | 数据库错误 |
| 5002 | Redis错误 |
| 5003 | Celery错误 |

**示例：**
```python
# 自动捕获的未处理异常
# → 自动返回 code: 5000

# 手动处理数据库错误
try:
    await User.create(...)
except DatabaseError as e:
    return error(ResponseCode.DATABASE_ERROR, "数据库操作失败")
```

## 三种常见场景的完整例子

### 场景1：用户注册（包含验证）

```python
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field
from app.utils.responses import error, created, ResponseCode

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

@router.post("/register")
async def register(req: RegisterRequest):
    """
    响应场景：
    1. 验证失败 → HTTP 200, code: 4001 ✅ (自动处理)
    2. 用户名重复 → HTTP 200, code: 4091 ✅ (手动检查)
    3. 邮箱重复 → HTTP 200, code: 4092 ✅ (手动检查)
    4. 创建成功 → HTTP 200, code: 1001 ✅
    """
    
    # Pydantic已经验证了：username长度、email格式、password长度
    # 如果验证失败，这里代码不会执行，异常处理器返回 {code: 4001, ...}
    
    # 业务级验证（数据库检查）
    if await User.get_or_none(username=req.username):
        return error(ResponseCode.USERNAME_EXISTS)
    
    if await User.get_or_none(email=req.email):
        return error(ResponseCode.EMAIL_EXISTS)
    
    # 创建用户
    user = await User.create(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password)
    )
    
    return created({"user_id": user.id, "username": user.username})
```

**前端处理：**
```javascript
async function register(username, email, password) {
  const response = await fetch('/register', {
    method: 'POST',
    body: JSON.stringify({username, email, password})
  });
  
  const data = await response.json();  // 总是200，所以总是JSON
  
  if (data.code === 1001) {
    // 创建成功
    console.log('注册成功，用户ID:', data.data.user_id);
  } else if (data.code === 4001) {
    // 验证错误
    data.data.errors.forEach(err => {
      showError(`${err.field}: ${err.message}`);
    });
  } else if (data.code === 4091) {
    // 用户名重复
    showError('用户名已存在');
  } else if (data.code === 4092) {
    // 邮箱重复
    showError('邮箱已存在');
  }
}
```

### 场景2：获取用户信息（包含认证）

```python
from fastapi import Depends
from app.core.deps import get_current_active_user

@router.get("/users/{user_id}")
async def get_user(user_id: int, current_user: User = Depends(get_current_active_user)):
    """
    响应场景：
    1. 未登录 → HTTP 200, code: 4010 ✅ (Depends失败)
    2. Token过期 → HTTP 200, code: 4010 ✅ (Token验证失败)
    3. 用户不存在 → HTTP 200, code: 4041 ✅
    4. 成功返回 → HTTP 200, code: 1000 ✅
    """
    
    # 如果没登录或Token无效，这里代码不会执行
    # 异常处理器返回 {code: 4010, message: "未授权", data: null}
    
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    return success({
        "id": user.id,
        "username": user.username,
        "email": user.email
    })
```

**前端处理：**
```javascript
async function getUser(userId, token) {
  const response = await fetch(`/users/${userId}`, {
    headers: {'Authorization': `Bearer ${token}`}
  });
  
  const data = await response.json();
  
  if (data.code === 1000) {
    // 成功
    showUser(data.data);
  } else if (data.code === 4010) {
    // 未授权
    redirectToLogin();
  } else if (data.code === 4041) {
    // 用户不存在
    showError('用户不存在');
  }
}
```

### 场景3：更新用户信息（完整示例）

```python
class UpdateUserRequest(BaseModel):
    username: str = Field(None, min_length=3, max_length=50)
    email: EmailStr = None
    password: str = Field(None, min_length=8)

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    req: UpdateUserRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    响应场景：
    1. 验证失败 → HTTP 200, code: 4001 ✅ (自动)
    2. 未登录 → HTTP 200, code: 4010 ✅ (自动)
    3. 权限不足 → HTTP 200, code: 4030 ✅ (手动)
    4. 用户不存在 → HTTP 200, code: 4041 ✅ (手动)
    5. 用户名重复 → HTTP 200, code: 4091 ✅ (手动)
    6. 更新成功 → HTTP 200, code: 1002 ✅
    """
    
    # 检查权限
    if current_user.id != user_id:
        return error(ResponseCode.FORBIDDEN, "只能修改自己的信息")
    
    # 获取目标用户
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)
    
    # 检查用户名重复
    if req.username and req.username != user.username:
        if await User.get_or_none(username=req.username):
            return error(ResponseCode.USERNAME_EXISTS)
    
    # 更新字段
    if req.username:
        user.username = req.username
    if req.email:
        user.email = req.email
    if req.password:
        user.hashed_password = hash_password(req.password)
    
    await user.save()
    
    return updated({
        "id": user.id,
        "username": user.username,
        "email": user.email
    })
```

## 快速排查指南

### 为什么返回了HTTP 200却显示错误？

✅ **这是正常的！** 新的设计中所有响应都是HTTP 200，业务状态通过`code`字段判断。

```python
# 之前（错误的做法）
if response.status_code != 200:
    # 处理错误
    
# 现在（正确的做法）
if response['code'] >= 4000:
    # 处理错误
```

### 验证错误的格式是什么？

```json
{
  "code": 4001,
  "message": "请求数据验证失败",
  "data": {
    "errors": [
      {
        "field": "email",
        "message": "invalid email format",
        "type": "value_error"
      },
      {
        "field": "password",
        "message": "ensure this value has at least 8 characters",
        "type": "value_error"
      }
    ]
  }
}
```

### 服务器错误会显示堆栈跟踪吗？

**生产环境（DEBUG=False）：**
```json
{
  "code": 5000,
  "message": "服务器内部错误",
  "data": null
}
```

**开发环境（DEBUG=True）：**
```json
{
  "code": 5000,
  "message": "服务器内部错误",
  "data": {
    "detail": "division by zero"
  }
}
```

## 常见错误

### ❌ 错误：还在使用HTTP状态码判断

```javascript
// 错误
if (response.status === 200) {
  // 处理成功
} else if (response.status === 422) {
  // 处理验证错误
}
```

### ✅ 正确：使用code字段判断

```javascript
const data = await response.json();
if (data.code >= 1000 && data.code < 4000) {
  // 处理成功
} else if (data.code === 4001) {
  // 处理验证错误
}
```

### ❌ 错误：在异常处理器中仍然返回不同的HTTP状态码

```python
# 错误
return JSONResponse(status_code=401, content=error_data)
```

### ✅ 正确：总是返回HTTP 200

```python
# 正确
return JSONResponse(status_code=200, content=error_data)
```

## Python使用示例

### 使用响应函数

```python
from app.utils.responses import success, error, created, updated, deleted, ResponseCode

# 成功响应
return success({"id": 1, "name": "John"})  # code: 1000

# 创建响应
return created({"id": 1})  # code: 1001

# 更新响应
return updated({"id": 1})  # code: 1002

# 删除响应
return deleted({"id": 1})  # code: 1003

# 错误响应
return error(ResponseCode.BAD_REQUEST)  # code: 4000
return error(ResponseCode.USER_NOT_FOUND)  # code: 4041
return error(ResponseCode.VALIDATION_ERROR, "自定义消息")  # code: 4001

# 带data的错误响应
return error(
    ResponseCode.VALIDATION_ERROR,
    "验证失败",
    data={"errors": [...]}
)
```

## 关键代码位置

- [app/utils/responses.py](../app/utils/responses.py) - 响应函数定义
- [main.py](../main.py) - 全局异常处理器（第100-170行）
- [docs/UNIFIED_RESPONSE_FORMAT.md](./UNIFIED_RESPONSE_FORMAT.md) - 详细规范

