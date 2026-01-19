"""
SQL 客户端测试
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sql_client_query_user(client: AsyncClient, test_user):
    """测试 SQL 客户端查询用户"""
    response = await client.get("/api/v1/debug/test/user")

    assert response.status_code == 200
    data = response.json()

    # 打印查询结果
    print(f"\n查询结果: {data}")

    # 验证响应格式
    assert "code" in data
    assert "message" in data
    assert "data" in data

    # 验证查询成功
    assert data["code"] == 1000
    assert data["message"] == "查询成功"
    assert data["data"] is not None
    assert data["data"]["id"] == test_user.id
    assert data["data"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_sql_list_all(client: AsyncClient):
    """测试获取所有 SQL ID 列表"""
    response = await client.get("/api/v1/debug/sql")

    assert response.status_code == 200
    data = response.json()

    # 验证返回了 SQL 列表
    assert "count" in data
    assert "sql_ids" in data
    assert isinstance(data["sql_ids"], list)
    # 应该至少有一个 SQL（user.index.fetch_by_id）
    assert data["count"] >= 1


@pytest.mark.asyncio
async def test_sql_get_detail(client: AsyncClient):
    """测试获取指定 SQL 的详细信息"""
    response = await client.get("/api/v1/debug/sql/user.index.fetch_by_id")

    assert response.status_code == 200
    data = response.json()

    # 验证返回了 SQL 详情
    assert "sql_id" in data
    assert "sql" in data
    assert data["sql_id"] == "user.index.fetch_by_id"
    assert "SELECT" in data["sql"]


@pytest.mark.asyncio
async def test_sql_get_detail_not_found(client: AsyncClient):
    """测试获取不存在的 SQL"""
    response = await client.get("/api/v1/debug/sql/non.existent.sql")

    # 全局异常处理器会把 404 转换为 200 响应
    assert response.status_code == 200
    data = response.json()
    # 验证返回了错误响应格式
    assert "code" in data
    assert "message" in data
    assert data["code"] == 4040  # NOT_FOUND
    assert "不存在" in data["message"] or "SQL" in data["message"]
