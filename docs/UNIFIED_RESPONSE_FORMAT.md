# API 响应格式统一规范

## 核心原则

**所有API响应（成功、失败、异常）都采用统一的JSON格式**，前端只需处理一种格式：

```json
{
  "code": 1000,
  "message": "操作成功",
  "data": null
}
```

## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | `int` | 业务状态码（不是HTTP状态码） |
| `message` | `str` | 描述信息 |
| `data` | `any` | 响应数据（可选，错误时通常为null或错误详情） |

## HTTP 状态码策略

⚠️ **重要**：**所有响应都返回 HTTP 200**

- ✅ 成功请求 → HTTP 200
- ✅ 验证错误 → HTTP 200（原来422）
- ✅ 服务器错误 → HTTP 200（原来500）
- ✅ 授权错误 → HTTP 200（原来401/403）

**业务状态通过 `code` 字段判断，不通过HTTP状态码**

### 为什么这样做？

1. **统一处理** - 前端不需要处理多种HTTP状态码
2. **更清晰的业务状态** - `code` 字段明确表示业务状态
3. **更好的跨域支持** - 避免OPTIONS预检请求的复杂性
4. **移动端友好** - 某些移动框架对HTTP状态码的处理有限制
5. **前端统一** - 所有异常都走同一个catch块处理

## 响应码分类

### ✅ 成功响应 (1xxx)

```python
ResponseCode.SUCCESS = 1000        # 通用成功
ResponseCode.CREATED = 1001        # 创建成功（POST）
ResponseCode.UPDATED = 1002        # 更新成功（PUT/PATCH）
ResponseCode.DELETED = 1003        # 删除成功（DELETE）
```

**示例：**
```json
{
  "code": 1000,
  "message": "操作成功",
  "data": {
    "user_id": 123,
    "username": "john"
  }
}
```

### ❌ 客户端错误 (4xxx)

```python
ResponseCode.BAD_REQUEST = 4000           # 请求参数错误
ResponseCode.VALIDATION_ERROR = 4001      # 数据验证失败
ResponseCode.UNAUTHORIZED = 4010          # 未授权/未登录
ResponseCode.TOKEN_EXPIRED = 4011         # Token已过期
ResponseCode.TOKEN_INVALID = 4012         # Token无效
ResponseCode.FORBIDDEN = 4030             # 权限不足
ResponseCode.NOT_FOUND = 4040             # 资源不存在
ResponseCode.USER_NOT_FOUND = 4041        # 用户不存在
ResponseCode.USERNAME_EXISTS = 4091       # 用户名已存在
ResponseCode.EMAIL_EXISTS = 4092          # 邮箱已存在
```

**验证错误示例：**
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

**其他客户端错误示例：**
```json
{
  "code": 4091,
  "message": "用户名已存在",
  "data": null
}
```

### 🔴 服务器错误 (5xxx)

```python
ResponseCode.SERVER_ERROR = 5000      # 服务器内部错误
ResponseCode.DATABASE_ERROR = 5001    # 数据库错误
ResponseCode.REDIS_ERROR = 5002       # Redis错误
ResponseCode.CELERY_ERROR = 5003      # Celery错误
```

**调试模式下：**
```json
{
  "code": 5000,
  "message": "服务器内部错误",
  "data": {
    "detail": "division by zero"
  }
}
```

**生产模式下：**
```json
{
  "code": 5000,
  "message": "服务器内部错误",
  "data": null
}
```

## 三层响应处理

### 1️⃣ 业务逻辑中（应用层）

使用 `success()` / `error()` 函数：

```python
from app.utils.responses import success, error, created, ResponseCode

# 成功响应
@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await User.get_or_none(id=user_id)
    if not user:
        return error(ResponseCode.USER_NOT_FOUND)  # {code: 4041, message: "...", data: null}
    return success({"id": user.id, "name": user.name})  # {code: 1000, message: "...", data: {...}}

# 创建响应
@router.post("/users")
async def create_user(user_data: UserCreate):
    user = await User.create(**user_data.model_dump())
    return created({"user_id": user.id})  # {code: 1001, message: "...", data: {...}}
```

### 2️⃣ 验证错误（Pydantic）

FastAPI自动触发，异常处理器统一转换：

```python
# 前端发送：
{
  "email": "invalid",
  "password": "123"
}

# FastAPI自动返回：
{
  "code": 4001,
  "message": "请求数据验证失败",
  "data": {
    "errors": [
      {"field": "email", "message": "invalid email format", "type": "value_error"},
      {"field": "password", "message": "ensure this value has at least 8 characters", "type": "value_error"}
    ]
  }
}
```

### 3️⃣ 未捕获异常（全局处理器）

自动捕获并转换为统一格式：

```python
# 代码中发生异常：
raise ValueError("Something went wrong")

# 自动返回（调试模式）：
{
  "code": 5000,
  "message": "服务器内部错误",
  "data": {
    "detail": "Something went wrong"
  }
}

# 生产模式：
{
  "code": 5000,
  "message": "服务器内部错误",
  "data": null
}
```

## 前端处理示例

### JavaScript (Fetch API)

```javascript
async function fetchAPI(url, options) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();  // 所有响应都是JSON
    
    // 统一处理所有响应（HTTP 200）
    if (data.code >= 1000 && data.code < 4000) {
      // 成功
      console.log(data.message);
      return data.data;
    } else {
      // 错误
      console.error(`[${data.code}] ${data.message}`);
      if (data.code === 4001) {
        // 处理验证错误
        showValidationErrors(data.data.errors);
      } else if (data.code === 4010) {
        // 处理未授权
        redirectToLogin();
      }
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
}

// 使用
const userData = await fetchAPI('/api/v1/users/123', {method: 'GET'});
```

### Python (requests)

```python
import requests

def api_request(method, url, **kwargs):
    response = requests.request(method, url, **kwargs)
    data = response.json()
    
    if 1000 <= data['code'] < 4000:
        # 成功
        return data.get('data')
    else:
        # 错误
        print(f"[{data['code']}] {data['message']}")
        if data['code'] == 4001:
            # 处理验证错误
            for error in data['data']['errors']:
                print(f"  - {error['field']}: {error['message']}")
        raise Exception(data['message'])

# 使用
user = api_request('GET', 'http://localhost:8000/api/v1/users/123')
```

### Vue 3 + Axios

```typescript
const api = axios.create({
  baseURL: 'http://localhost:8000'
});

api.interceptors.response.use(
  response => {
    const data = response.data;
    
    if (data.code >= 1000 && data.code < 4000) {
      // 成功
      return data.data;
    } else {
      // 错误
      const error = new Error(data.message);
      error.code = data.code;
      error.details = data.data;
      return Promise.reject(error);
    }
  },
  error => {
    // 网络错误
    console.error('Network error:', error);
    return Promise.reject(error);
  }
);

// 使用
try {
  const user = await api.get('/api/v1/users/123');
  console.log(user);  // 这里是data字段的内容
} catch (error) {
  if (error.code === 4001) {
    // 处理验证错误
  } else if (error.code === 4010) {
    // 处理未授权
  }
}
```

## 最佳实践

### ✅ 应该做

1. **总是使用响应函数**
```python
from app.utils.responses import success, error, created, ResponseCode

# 好的
return success({"id": 1})
return error(ResponseCode.USER_NOT_FOUND)
return created({"user_id": 1})
```

2. **为验证错误提供字段级别信息**
```python
# 在自定义验证器中
@field_validator('email')
@classmethod
def validate_email(cls, v):
    if not is_valid_email(v):
        raise ValueError('邮箱格式不正确')  # 会被异常处理器自动提取
    return v
```

3. **在错误响应中包含必要的信息**
```python
# 好的
return error(
    ResponseCode.BAD_REQUEST,
    "库存不足",
    data={"required": 10, "available": 5}
)
```

### ❌ 不应该做

1. **不要返回不同的HTTP状态码**
```python
# ❌ 错误
raise HTTPException(status_code=401, detail="Unauthorized")

# ✅ 正确
return error(ResponseCode.UNAUTHORIZED, "未授权")
```

2. **不要自己创建响应对象**
```python
# ❌ 错误
return {
    "success": False,
    "message": "Error",
    "status_code": 400
}

# ✅ 正确
return error(ResponseCode.BAD_REQUEST)
```

3. **不要在生产环境暴露详细错误**
```python
# ❌ 错误（生产环境）
data={"detail": str(exception)}

# ✅ 正确
# 由settings.DEBUG控制是否返回详情
```

## 迁移指南

如果你有现有的API使用不同的响应格式：

### 旧格式 → 新格式

**旧：**
```json
{
  "success": true,
  "data": {...},
  "status_code": 200
}
```

**新：**
```json
{
  "code": 1000,
  "message": "操作成功",
  "data": {...}
}
```

**旧：**
```json
{
  "error": true,
  "message": "User not found",
  "status_code": 404
}
```

**新：**
```json
{
  "code": 4041,
  "message": "用户不存在",
  "data": null
}
```

## 参考：响应码速查表

| 场景 | 响应码 | 消息 |
|------|--------|------|
| 用户成功创建 | 1001 | 创建成功 |
| 用户成功更新 | 1002 | 更新成功 |
| 用户成功删除 | 1003 | 删除成功 |
| 参数验证失败 | 4001 | 请求数据验证失败 |
| 用户未登录 | 4010 | 请先登录 |
| Token已过期 | 4011 | 登录已过期，请重新登录 |
| Token无效 | 4012 | 无效的认证信息 |
| 权限不足 | 4030 | 权限不足 |
| 用户不存在 | 4041 | 用户不存在 |
| 用户名已存在 | 4091 | 用户名已存在 |
| 邮箱已存在 | 4092 | 邮箱已存在 |
| 服务器内部错误 | 5000 | 服务器内部错误 |
| 数据库错误 | 5001 | 数据库错误 |

