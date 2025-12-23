from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """创建用户模型"""
    username: str
    email: EmailStr
    password: str
    is_active: bool = True


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str