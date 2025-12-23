"""
测试通用端点
"""
import pytest
from httpx import AsyncClient


class TestGeneralEndpoints:
    """通用端点测试"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """测试健康检查端点"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app_name" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """测试根路径"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
    
    @pytest.mark.asyncio
    async def test_docs_endpoint(self, client: AsyncClient):
        """测试 API 文档端点"""
        response = await client.get("/docs")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_openapi_json(self, client: AsyncClient):
        """测试 OpenAPI JSON"""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
