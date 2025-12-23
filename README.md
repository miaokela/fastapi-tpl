# FastAPI TPL

一个功能完整的 FastAPI 基础项目模板，集成了用户认证、定时任务管理（类似 django-celery-beat）、Admin 管理后台等核心功能。

## ✨ 特性

- **FastAPI** - 现代高性能 Python Web 框架
- **Tortoise ORM** - 异步 ORM，支持 SQLite/PostgreSQL/MySQL
- **Celery + Redis** - 分布式任务队列
- **数据库定时任务调度** - 类似 django-celery-beat，支持动态管理定时任务
- **任务结果自动记录** - 自动记录任务执行结果，支持配置保留天数
- **JWT 认证** - 完整的用户注册、登录、权限控制
- **Admin 管理 API** - 用户管理、定时任务管理
- **Admin 管理后台** - 纯静态科技感 UI，无需额外前端框架
- **Docker 支持** - 容器化部署

## 📁 项目结构

```
fastapi-base/
├── app/
│   ├── admin/              # Admin 管理模块
│   │   ├── admin_views.py  # 管理接口
│   │   └── schemas.py      # 管理数据模式
│   ├── core/               # 核心功能
│   │   ├── deps.py         # 依赖注入
│   │   └── security.py     # 安全认证
│   ├── models/             # 数据模型
│   │   └── models.py       # Tortoise ORM 模型
│   ├── schemas/            # Pydantic 模式
│   │   ├── schemas.py      # 数据模式定义
│   │   └── validation_examples.py  # 验证示例
│   ├── services/           # 服务层
│   │   └── task_scheduler.py  # 定时任务服务
│   ├── utils/              # 工具模块
│   │   ├── helpers.py      # 辅助函数
│   │   ├── redis_client.py # Redis 客户端
│   │   ├── responses.py    # 响应格式
│   │   └── structured_logger.py  # 结构化日志
│   ├── views/              # 视图控制器
│   │   ├── user_views.py   # 用户视图
│   │   └── validation_routes.py  # 验证路由
│   └── serializers.py      # 序列化器
├── celery_app/             # Celery 应用
│   ├── celery.py           # Celery 配置 + 任务信号处理
│   ├── scheduler.py        # 数据库定时任务调度器
│   └── tasks/              # 任务模块
│       └── test_tasks.py   # 测试任务
├── config/                 # 配置文件
│   ├── database.py         # 数据库配置
│   ├── logging.py          # 日志配置
│   └── settings.py         # 应用设置
├── docs/                   # 项目文档
├── examples/               # 示例代码
├── static/                 # 静态文件
│   └── admin/              # Admin 管理后台前端
│       ├── index.html      # 主页面
│       ├── css/style.css   # 科技感样式
│       └── js/
│           ├── api.js      # API 接口封装
│           └── app.js      # 应用逻辑
├── http/                   # HTTP 测试文件
│   └── admin.http          # Admin API 测试
├── logs/                   # 日志目录
├── tests/                  # 测试用例
├── cli.py                  # 命令行工具
├── init_schema.sql         # 数据库初始化 SQL
├── main.py                 # 应用入口
├── requirements.txt        # Python 依赖
├── pyproject.toml          # 项目配置
├── docker-compose.yml      # Docker 配置
├── Dockerfile              # Docker 镜像构建
├── setup.sh                # 环境设置脚本
├── run_dev.sh              # 开发环境启动
└── run_celery.sh           # Celery 服务启动
```

## 🚀 快速开始

### 1. 环境设置

```bash
# 克隆项目
git clone <repository-url>
cd fastapi-base

# 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 或使用 setup.sh
chmod +x setup.sh
./setup.sh
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 配置 Redis、数据库等
```

### 3. 初始化数据库

```bash
sqlite3 default_db.sqlite3 < init_schema.sql
```

### 4. 启动服务

```bash
# 启动 FastAPI 应用
./run_dev.sh

# 启动 Celery Worker（新终端）
./run_celery.sh worker

# 启动 Celery Beat 定时任务调度（新终端）
./run_celery.sh beat
```

### 5. 访问应用

- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc
- **Admin 管理后台**: http://localhost:8000/admin
- **健康检查**: http://localhost:8000/health

## 🖥️ Admin 管理后台

本项目内置了一个纯静态的科技感管理后台，无需安装额外前端框架，开箱即用。

### 功能模块

| 模块 | 功能 |
|------|------|
| **仪表盘** | 用户统计、任务统计、系统概览 |
| **用户管理** | 用户列表、创建/编辑/删除用户、权限管理 |
| **定时任务** | 任务列表、创建/编辑/删除任务、启用/禁用、手动执行 |
| **执行结果** | 任务执行记录、状态查看、错误追踪 |

### 访问地址

启动服务后访问: http://localhost:8000/admin

### 登录方式

使用管理员账号登录（需要 `is_superuser=true` 或 `is_staff=true`）：
- 支持邮箱或用户名登录

### 界面特点

- **科技感深色主题**: 赛博朋克风格 UI，霓虹灯光效果
- **响应式设计**: 支持桌面和移动端
- **纯静态实现**: HTML + CSS + JavaScript，无需编译
- **实时反馈**: Toast 消息提示，操作状态即时反馈

### 配置选项

在 `config/settings.py` 中可配置：

```python
# 是否启用 Admin 系统（设为 False 可完全禁用管理后台）
ADMIN_ENABLED: bool = True
```

## 📡 API 接口

### 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |
| GET | `/auth/me` | 获取当前用户信息 |

### Admin 管理接口

> 需要管理员权限（is_superuser 或 is_staff）

#### 用户管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/admin/users` | 获取用户列表 |
| POST | `/api/v1/admin/users` | 创建用户 |
| GET | `/api/v1/admin/users/{id}` | 获取用户详情 |
| PUT | `/api/v1/admin/users/{id}` | 更新用户 |
| DELETE | `/api/v1/admin/users/{id}` | 删除用户 |

#### 定时任务管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/admin/tasks` | 获取定时任务列表 |
| POST | `/api/v1/admin/tasks` | 创建定时任务 |
| GET | `/api/v1/admin/tasks/{id}` | 获取任务详情 |
| PUT | `/api/v1/admin/tasks/{id}` | 更新任务 |
| DELETE | `/api/v1/admin/tasks/{id}` | 删除任务 |
| POST | `/api/v1/admin/tasks/{id}/enable` | 启用任务 |
| POST | `/api/v1/admin/tasks/{id}/disable` | 禁用任务 |
| POST | `/api/v1/admin/tasks/{id}/run` | 立即执行任务 |

#### 调度管理

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/admin/schedules/intervals` | 获取间隔调度列表 |
| POST | `/api/v1/admin/schedules/intervals` | 创建间隔调度 |
| GET | `/api/v1/admin/schedules/crontabs` | 获取 Crontab 调度列表 |
| POST | `/api/v1/admin/schedules/crontabs` | 创建 Crontab 调度 |

#### 其他

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/admin/results` | 获取任务执行结果 |
| GET | `/api/v1/admin/statistics` | 获取任务统计信息 |
| GET | `/api/v1/admin/available-tasks` | 获取可用 Celery 任务列表 |

## ⏰ 定时任务管理

本项目实现了类似 django-celery-beat 的数据库定时任务调度功能：

### 特性

- **动态管理**: 通过 API 或管理后台动态添加、修改、删除定时任务，无需重启服务
- **多种调度方式**: 支持间隔调度（Interval）和 Crontab 调度（二选一，互斥）
- **任务状态跟踪**: 记录任务执行次数、最后执行时间
- **任务结果自动存储**: 通过 Celery 信号自动记录任务执行结果和错误信息
- **自动清理过期记录**: 根据配置自动清理过期的任务结果

### 任务结果记录

系统通过 Celery 信号自动记录任务执行结果：

| 信号 | 触发时机 | 记录状态 |
|------|----------|----------|
| `task_prerun` | 任务开始执行 | STARTED |
| `task_success` | 任务成功完成 | SUCCESS |
| `task_failure` | 任务执行失败 | FAILURE |
| `task_revoked` | 任务被撤销 | REVOKED |

配置任务结果保留天数（`config/settings.py`）：

```python
# 任务结果保留天数，默认7天，超期自动清理
CELERY_TASK_RESULT_EXPIRES: int = 7
```

### 任务执行时间限制

```python
# 硬时间限制（秒），超时后任务会被强制终止（SIGKILL）
task_time_limit=300  # 5分钟

# 软时间限制（秒），超时后抛出 SoftTimeLimitExceeded 异常
# 任务可捕获该异常进行清理工作
task_soft_time_limit=240  # 4分钟
```

### 创建定时任务示例

```bash
# 创建间隔调度（每10秒）
curl -X POST "http://localhost:8000/api/v1/admin/schedules/intervals" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"every": 10, "period": "seconds"}'

# 创建定时任务
curl -X POST "http://localhost:8000/api/v1/admin/tasks" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-world-task",
    "task": "celery_app.tasks.test_tasks.hello_world",
    "interval_id": 1,
    "enabled": true,
    "description": "每10秒打印 Hello World"
  }'
```

## 🐳 Docker 部署

```bash
# 开发环境
docker-compose up -d

# 生产环境
./deploy.sh
```

## 📦 嵌入式单体部署（PyInstaller）

将整个应用打包成单个可执行文件，适用于嵌入式设备（如树莓派）或无 Python 环境的服务器部署。

### 打包流程

#### 1. 构建 ARM64 打包环境（macOS/x86 主机交叉编译）

```bash
# 构建 ARM64 Docker 镜像
docker buildx build --platform linux/arm64 -f Dockerfile.build -t fastapi-base-builder:arm64 .
```

#### 2. 执行打包

```bash
# 运行打包（输出到 dist/app）
docker run --platform linux/arm64 --rm -v "$(pwd)/dist:/output" fastapi-base-builder:arm64
```

#### 3. 部署到目标设备

```bash
# 复制可执行文件到目标设备
scp dist/app user@target-device:/opt/fastapi-app/

# 复制配置文件（可选）
scp .env user@target-device:/opt/fastapi-app/
```

### 运行命令

```bash
# 启动 FastAPI 服务（单 worker）
./app server

# 启动 FastAPI 服务（多 worker，生产模式）
./app server --host 0.0.0.0 --port 8000 --workers 4

# 启动 Celery Worker
./app worker

# 启动 Celery Beat 定时任务调度
./app beat

# 初始化数据库
./app init-db
```

### 配置说明

可执行文件运行时会自动读取同目录下的 `.env` 文件：

```bash
# .env 示例
DATABASE_URL=sqlite://./db.sqlite3
REDIS_URL=redis://:password@localhost:6379/0
CELERY_BROKER_URL=redis://:password@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:password@localhost:6379/2
SECRET_KEY=your-secret-key
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
```

### 一键打包脚本

```bash
chmod +x build_arm64.sh
./build_arm64.sh
```

### 打包原理

- 使用 PyInstaller 将 Python 应用打包成单个 ELF 可执行文件
- `app.spec` 配置文件会**自动扫描虚拟环境中所有已安装的包**，无需手动维护依赖列表
- 使用 `collect_all()` 收集每个包的模块、数据文件和二进制文件
- 最终生成约 40-50MB 的独立可执行文件

### 支持的平台

| 平台 | 架构 | 状态 |
|------|------|------|
| Linux | ARM64 (aarch64) | ✅ 已测试 |
| Linux | x86_64 | ⚠️ 需修改 Dockerfile.build |
| macOS | ARM64 (Apple Silicon) | ⚠️ 需本地打包 |

## 🧪 测试

```bash
# 运行所有测试
./run_tests.sh

# 运行单个测试
./run_single_test.sh tests/test_auth.py

# 使用 http 文件测试 API
# 在 VS Code 中安装 REST Client 扩展，打开 http/admin.http
```

## 📝 开发指南

### 添加新的 Celery 任务

1. 在 `celery_app/tasks/` 中创建任务文件
2. 定义任务函数：

```python
from celery_app.celery import celery_app

@celery_app.task(name="celery_app.tasks.my_tasks.my_task")
def my_task(arg1, arg2):
    # 任务逻辑
    return "result"
```

3. 在 `celery_app/celery.py` 中添加到 include 列表
4. 通过 Admin API 创建定时任务

### 添加新的数据模型

1. 在 `app/models/models.py` 中定义模型
2. 更新 `init_schema.sql` 添加建表语句
3. 重新初始化数据库

## ⚙️ 配置说明

主要配置在 `config/settings.py` 和 `.env` 文件中：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接 | sqlite://./default_db.sqlite3 |
| REDIS_URL | Redis 连接 | redis://localhost:6379/0 |
| CELERY_BROKER_URL | Celery Broker | redis://localhost:6379/1 |
| CELERY_RESULT_BACKEND | Celery 结果后端 | redis://localhost:6379/2 |
| CELERY_TASK_RESULT_EXPIRES | 任务结果保留天数 | 7 |
| SECRET_KEY | JWT 密钥 | 需修改 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token 过期时间 | 30 |
| ADMIN_ENABLED | 是否启用 Admin 系统 | True |

## 📄 许可证

MIT License


1. 周期任务、定时任务两个类型是否正常执行
2. 确认关闭任务后，任务不再执行，就是为了测试扫描能力
3. 和定时任务相关的字段是否有其真实意义，并且写入正常
