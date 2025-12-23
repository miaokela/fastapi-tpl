"""
测试配置和 Fixtures
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

from main import app
from config.database import DATABASE_CONFIG
from app.models.models import User, UserProfile
from app.core.security import get_password_hash


# 配置测试数据库
TEST_DATABASE_CONFIG = {
    "connections": {
        "default": "sqlite://:memory:"
    },
    "apps": {
        "models": {
            "models": ["app.models"],
            "default_connection": "default",
        },
    },
}


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    """初始化测试数据库"""
    # 初始化数据库
    await Tortoise.init(config=TEST_DATABASE_CONFIG)
    await Tortoise.generate_schemas()
    
    yield
    
    # 清理数据库
    await Tortoise.close_connections()


@pytest_asyncio.fixture(scope="function")
async def client(db) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def test_user(db) -> User:
    """创建测试用户"""
    user = await User.create(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
        is_superuser=False
    )
    await UserProfile.create(
        user=user,
        first_name="Test",
        last_name="User"
    )
    return user


@pytest_asyncio.fixture(scope="function")
async def test_superuser(db) -> User:
    """创建测试超级管理员"""
    user = await User.create(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_superuser=True
    )
    await UserProfile.create(
        user=user,
        first_name="Admin",
        last_name="User"
    )
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_token(client: AsyncClient, test_user: User) -> str:
    """获取认证令牌"""
    response = await client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    return data["data"]["access_token"]


@pytest_asyncio.fixture(scope="function")
async def superuser_token(client: AsyncClient, test_superuser: User) -> str:
    """获取超级管理员令牌"""
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    return data["data"]["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token: str) -> dict:
    """创建认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def superuser_headers(superuser_token: str) -> dict:
    """创建超级管理员请求头"""
    return {"Authorization": f"Bearer {superuser_token}"}
