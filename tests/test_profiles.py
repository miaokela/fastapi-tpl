"""
测试用户资料 API
"""
import pytest
from httpx import AsyncClient

from app.models.models import UserProfile


class TestUserProfileAPI:
    """用户资料 API 测试"""
    
    @pytest.mark.asyncio
    async def test_get_profiles_list(self, client: AsyncClient, test_user, superuser_headers):
        """测试获取用户资料列表"""
        response = await client.get("/api/v1/profiles/", headers=superuser_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1000  # SUCCESS
        assert "items" in data["data"]
        assert isinstance(data["data"]["items"], list)
    
    @pytest.mark.asyncio
    async def test_get_profile_by_id(self, client: AsyncClient, test_user, superuser_headers):
        """测试获取指定用户资料"""
        profile = await UserProfile.get(user=test_user)
        response = await client.get(
            f"/api/v1/profiles/{profile.id}",
            headers=superuser_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1000  # SUCCESS
        assert data["data"]["first_name"] == "Test"
        assert data["data"]["last_name"] == "User"
    
    @pytest.mark.asyncio
    async def test_create_profile(self, client: AsyncClient, superuser_headers, db):
        """测试创建用户资料"""
        from app.core.security import get_password_hash
        from app.models.models import User
        
        # 先创建一个没有资料的用户
        user = await User.create(
            username="noprofile",
            email="noprofile@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=True
        )
        
        response = await client.post(
            "/api/v1/profiles/",
            headers=superuser_headers,
            json={
                "user_id": user.id,
                "first_name": "New",
                "last_name": "Profile",
                "phone": "1234567890"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1001  # CREATED
    
    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, test_user, superuser_headers):
        """测试更新用户资料"""
        profile = await UserProfile.get(user=test_user)
        response = await client.put(
            f"/api/v1/profiles/{profile.id}",
            headers=superuser_headers,
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "phone": "9876543210"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1000  # SUCCESS
        
        # 验证更新
        updated_profile = await UserProfile.get(id=profile.id)
        assert updated_profile.first_name == "Updated"
        assert updated_profile.last_name == "Name"
    
    @pytest.mark.asyncio
    async def test_partial_update_profile(self, client: AsyncClient, test_user, superuser_headers):
        """测试部分更新用户资料"""
        profile = await UserProfile.get(user=test_user)
        response = await client.patch(
            f"/api/v1/profiles/{profile.id}",
            headers=superuser_headers,
            json={
                "phone": "5555555555"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1000  # SUCCESS
        
        # 验证更新
        updated_profile = await UserProfile.get(id=profile.id)
        assert updated_profile.phone == "5555555555"
        assert updated_profile.first_name == "Test"  # 未修改字段保持不变
    
    @pytest.mark.asyncio
    async def test_delete_profile(self, client: AsyncClient, superuser_headers, db):
        """测试删除用户资料"""
        from app.core.security import get_password_hash
        from app.models.models import User
        
        # 创建用户和资料
        user = await User.create(
            username="profiletodelete",
            email="profiletodelete@example.com",
            hashed_password=get_password_hash("pass123"),
            is_active=True
        )
        profile = await UserProfile.create(
            user=user,
            first_name="To",
            last_name="Delete"
        )
        
        response = await client.delete(
            f"/api/v1/profiles/{profile.id}",
            headers=superuser_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1000  # SUCCESS
        
        # 验证已删除
        deleted_profile = await UserProfile.get_or_none(id=profile.id)
        assert deleted_profile is None
