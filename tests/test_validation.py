"""
FastAPI 校验规则测试示例
展示如何测试Pydantic的验证规则
"""

import pytest
from pydantic import ValidationError
from app.schemas.validation_examples import (
    ImprovedUserCreate,
    ProductOrder,
    UserProfile,
)


class TestUserValidation:
    """用户数据验证测试"""
    
    def test_valid_user_creation(self):
        """测试有效的用户创建"""
        user = ImprovedUserCreate(
            username="john_doe",
            email="john@example.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!",
            is_active=True
        )
        assert user.username == "john_doe"
        assert user.email == "john@example.com"
    
    def test_username_format_validation(self):
        """测试用户名格式校验"""
        # ❌ 用户名不能以数字开头
        with pytest.raises(ValidationError) as exc_info:
            ImprovedUserCreate(
                username="123john",
                email="john@example.com",
                password="SecurePass123!",
                password_confirm="SecurePass123!",
            )
        assert "用户名必须以字母开头" in str(exc_info.value)
        
        # ❌ 用户名只能包含字母、数字、下划线
        with pytest.raises(ValidationError) as exc_info:
            ImprovedUserCreate(
                username="john-doe",
                email="john@example.com",
                password="SecurePass123!",
                password_confirm="SecurePass123!",
            )
        assert "用户名必须以字母开头" in str(exc_info.value)
    
    def test_username_length_validation(self):
        """测试用户名长度校验"""
        # ❌ 用户名太短
        with pytest.raises(ValidationError):
            ImprovedUserCreate(
                username="ab",
                email="test@example.com",
                password="SecurePass123!",
                password_confirm="SecurePass123!",
            )
        
        # ✅ 用户名长度符合要求
        user = ImprovedUserCreate(
            username="validusername",
            email="test@example.com",
            password="SecurePass123!",
            password_confirm="SecurePass123!",
        )
        assert len(user.username) > 3
    
    def test_password_strength_validation(self):
        """测试密码强度校验"""
        # ❌ 密码过于简单（没有大写字母）
        with pytest.raises(ValidationError) as exc_info:
            ImprovedUserCreate(
                username="john_doe",
                email="john@example.com",
                password="simplepass123",  # 没有大写字母
                password_confirm="simplepass123",
            )
        assert "包含大写字母" in str(exc_info.value)
        
        # ❌ 密码过于简单（没有数字）
        with pytest.raises(ValidationError) as exc_info:
            ImprovedUserCreate(
                username="john_doe",
                email="john@example.com",
                password="SimplePassword!",  # 没有数字
                password_confirm="SimplePassword!",
            )
        assert "包含数字" in str(exc_info.value)
        
        # ❌ 密码过于简单（没有特殊字符）
        with pytest.raises(ValidationError) as exc_info:
            ImprovedUserCreate(
                username="john_doe",
                email="john@example.com",
                password="SimplePass123",  # 没有特殊字符
                password_confirm="SimplePass123",
            )
        assert "包含特殊字符" in str(exc_info.value)
    
    def test_password_confirmation_validation(self):
        """测试密码确认校验"""
        # ❌ 两次密码不一致
        with pytest.raises(ValidationError) as exc_info:
            ImprovedUserCreate(
                username="john_doe",
                email="john@example.com",
                password="SecurePass123!",
                password_confirm="DifferentPass123!",
            )
        assert "密码和确认密码必须一致" in str(exc_info.value)
    
    def test_email_validation(self):
        """测试邮箱格式校验"""
        # ❌ 无效的邮箱格式
        with pytest.raises(ValidationError):
            ImprovedUserCreate(
                username="john_doe",
                email="invalid-email",  # 不是有效的邮箱
                password="SecurePass123!",
                password_confirm="SecurePass123!",
            )


class TestProductOrderValidation:
    """订单数据验证测试"""
    
    def test_valid_order(self):
        """测试有效的订单"""
        order = ProductOrder(
            product_id=1,
            quantity=10,
            original_price=100.0,
            discount_percent=10,
        )
        assert order.product_id == 1
        assert order.quantity == 10
    
    def test_quantity_range_validation(self):
        """测试数量范围校验"""
        # ✅ 数量可以是1
        order = ProductOrder(
            product_id=1,
            quantity=1,
            original_price=100.0,
        )
        assert order.quantity == 1
        
        # ✅ 数量可以是1000（模型没有上限限制）
        order = ProductOrder(
            product_id=1,
            quantity=1000,
            original_price=100.0,
        )
        assert order.quantity == 1000
        
        # ❌ 数量不能为0（ge=1约束）
        with pytest.raises(ValidationError):
            ProductOrder(
                product_id=1,
                quantity=0,
                original_price=100.0,
            )
        
        # ❌ 数量不能为负数
        with pytest.raises(ValidationError):
            ProductOrder(
                product_id=1,
                quantity=-1,
                original_price=100.0,
            )
    
    def test_discount_validation(self):
        """测试折扣校验"""
        # ❌ 数量超过100且折扣超过50%
        with pytest.raises(ValidationError) as exc_info:
            ProductOrder(
                product_id=1,
                quantity=101,
                original_price=100.0,
                discount_percent=60,  # 超过50%
            )
        assert "折扣不能超过50%" in str(exc_info.value)
        
        # ✅ 数量超过100但折扣不超过50%
        order = ProductOrder(
            product_id=1,
            quantity=101,
            original_price=100.0,
            discount_percent=50,
        )
        assert order.discount_percent == 50


class TestConditionalValidation:
    """条件校验测试"""
    
    def test_student_info_required(self):
        """测试学生信息为必需的条件"""
        # ❌ 标记为学生但没有提供学校名
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(
                name="John",
                is_student=True,
                school_name=None,  # 缺少学校名
            )
        assert "学生必须提供学校名称" in str(exc_info.value)
        
        # ❌ 标记为学生但没有提供毕业年份
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(
                name="John",
                is_student=True,
                school_name="Harvard",
                graduation_year=None,  # 缺少毕业年份
            )
        assert "学生必须提供毕业年份" in str(exc_info.value)
        
        # ✅ 完整的学生信息
        profile = UserProfile(
            name="John",
            is_student=True,
            school_name="Harvard",
            graduation_year=2025,
        )
        assert profile.is_student is True
        assert profile.school_name == "Harvard"
    
    def test_non_student_ignores_school_info(self):
        """测试非学生不需要学校信息"""
        # ✅ 非学生不提供学校信息是可以的
        profile = UserProfile(
            name="John",
            is_student=False,
            # school_name 和 graduation_year 都是 None
        )
        assert profile.is_student is False
        assert profile.school_name is None


class TestValidationErrorMessages:
    """验证错误信息测试"""
    
    def test_validation_error_detail(self):
        """测试验证错误的详细信息"""
        try:
            ImprovedUserCreate(
                username="123",  # 格式错误
                email="invalid",  # 邮箱格式错误
                password="weak",  # 密码太弱
                password_confirm="weak",
            )
        except ValidationError as e:
            # 可以获取所有错误的详细信息
            errors = e.errors()
            assert len(errors) > 0
            
            # 每个错误都有位置、类型和消息
            for error in errors:
                assert 'loc' in error  # 错误位置
                assert 'type' in error  # 错误类型
                assert 'msg' in error  # 错误消息
    
    def test_error_json_serialization(self):
        """测试错误信息的JSON序列化"""
        try:
            ImprovedUserCreate(
                username="123invalid",
                email="invalid-email",
                password="weak123",
                password_confirm="weak123",
            )
        except ValidationError as e:
            # ValidationError 可以直接转换为JSON
            error_json = e.json()
            assert isinstance(error_json, str)
            
            # 或者转换为字典
            errors_dict = e.errors()
            assert isinstance(errors_dict, list)


# ============================================================================
# 异步验证测试（在实际应用中）
# ============================================================================

"""
对于异步验证（如检查用户名是否已存在），测试会更复杂：

@pytest.mark.asyncio
async def test_username_exists_async():
    '''测试异步验证：检查用户名是否已存在'''
    # 1. 先创建一个用户
    existing_user = await User.create(
        username="john_doe",
        email="john@example.com",
        hashed_password="hashed",
    )
    
    # 2. 在客户端进行异步验证
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/register",
            json={
                "username": "john_doe",  # 已存在
                "email": "another@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
            }
        )
        
        # 应该返回 "用户名已存在" 的错误
        assert response.status_code == 400
        assert "已存在" in response.json()["message"]
"""


if __name__ == "__main__":
    # 运行测试
    # pytest -v tests/test_validation.py
    pass
