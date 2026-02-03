"""
认证路由
处理登录、注册、登出和认证检查
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional

from app.config import settings
from app.middleware.auth import create_token, get_current_user, require_auth, is_auth_enabled
from app.services.database import db


router = APIRouter()


class LoginRequest(BaseModel):
    """登录请求"""
    username: Optional[str] = None
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def username_valid(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('用户名至少3个字符')
        if len(v) > 32:
            raise ValueError('用户名最多32个字符')
        return v.strip()

    @field_validator('password')
    @classmethod
    def password_valid(cls, v):
        if not v or len(v) < 6:
            raise ValueError('密码至少6个字符')
        return v


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    token: Optional[str] = None
    message: str
    user: Optional[dict] = None


class AuthCheckResponse(BaseModel):
    """认证检查响应"""
    authenticated: bool
    auth_required: bool
    auth_mode: str = "none"  # "none", "password", "user"
    user: Optional[dict] = None


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    role: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    登录接口
    使用用户名+密码登录
    """
    # 如果未启用认证
    if not is_auth_enabled():
        return LoginResponse(
            success=True,
            token=None,
            message="系统未启用认证，无需登录"
        )

    # 用户名+密码登录
    if not request.username:
        raise HTTPException(status_code=400, detail="请输入用户名")

    user = db.verify_password(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 更新最后登录时间
    db.update_last_login(user["id"])

    # 生成 Token
    token = create_token({
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "authenticated": True
    })

    return LoginResponse(
        success=True,
        token=token,
        message="登录成功",
        user={
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    )


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    """
    注册接口
    创建普通用户账户
    """
    # 检查是否启用了用户认证模式
    if not settings.admin_password:
        raise HTTPException(status_code=400, detail="系统未启用用户注册功能")

    # 检查用户名是否已存在
    if db.get_user_by_username(request.username):
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户
    user_id = db.create_user(
        username=request.username,
        password=request.password,
        role="user"
    )

    # 生成 Token
    token = create_token({
        "user_id": user_id,
        "username": request.username,
        "role": "user",
        "authenticated": True
    })

    return LoginResponse(
        success=True,
        token=token,
        message="注册成功",
        user={
            "id": user_id,
            "username": request.username,
            "role": "user"
        }
    )


@router.post("/logout")
async def logout():
    """
    登出接口
    客户端删除本地存储的 Token 即可
    """
    return {"success": True, "message": "登出成功"}


@router.get("/check", response_model=AuthCheckResponse)
async def check_auth(user: Optional[dict] = Depends(get_current_user)):
    """
    检查认证状态
    返回是否已认证以及系统是否需要认证
    """
    auth_required = is_auth_enabled()

    if not auth_required:
        return AuthCheckResponse(
            authenticated=True,
            auth_required=False,
            auth_mode="none"
        )

    if user:
        return AuthCheckResponse(
            authenticated=True,
            auth_required=True,
            auth_mode="user",
            user={
                "id": user.get("user_id"),
                "username": user.get("username"),
                "role": user.get("role", "admin")
            } if user.get("username") else None
        )

    return AuthCheckResponse(
        authenticated=False,
        auth_required=True,
        auth_mode="user"
    )


@router.get("/me")
async def get_current_user_info(user: dict = Depends(require_auth)):
    """
    获取当前用户信息
    """
    if user.get("no_auth"):
        return {
            "id": 0,
            "username": "admin",
            "role": "admin"
        }

    return {
        "id": user.get("user_id"),
        "username": user.get("username"),
        "role": user.get("role", "admin")
    }
