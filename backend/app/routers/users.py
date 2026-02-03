"""
用户管理路由
仅管理员可访问
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, List

from app.services.database import db
from app.middleware.auth import require_admin


router = APIRouter()


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

    @field_validator('username')
    @classmethod
    def username_valid(cls, v):
        if v is not None:
            if len(v.strip()) < 3:
                raise ValueError('用户名至少3个字符')
            if len(v) > 32:
                raise ValueError('用户名最多32个字符')
        return v.strip() if v else v

    @field_validator('password')
    @classmethod
    def password_valid(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('密码至少6个字符')
        return v

    @field_validator('role')
    @classmethod
    def role_valid(cls, v):
        if v is not None and v not in ['admin', 'user']:
            raise ValueError('角色必须是 admin 或 user')
        return v


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    role: str
    created_at: Optional[str] = None
    last_login: Optional[str] = None


@router.get("")
async def get_users(admin: dict = Depends(require_admin)):
    """获取用户列表"""
    users = db.get_all_users()
    return {
        "users": users,
        "count": len(users)
    }


@router.get("/{user_id}")
async def get_user(user_id: int, admin: dict = Depends(require_admin)):
    """获取单个用户信息"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"],
        "last_login": user["last_login"]
    }


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    admin: dict = Depends(require_admin)
):
    """更新用户信息"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 如果要更改用户名，检查是否已存在
    if user_update.username and user_update.username != user["username"]:
        existing = db.get_user_by_username(user_update.username)
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")

    # 如果要将管理员降级为普通用户，检查是否是最后一个管理员
    if user_update.role == "user" and user["role"] == "admin":
        admin_count = db.get_admin_count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="不能将唯一的管理员降级为普通用户")

    success = db.update_user(
        user_id=user_id,
        username=user_update.username,
        password=user_update.password,
        role=user_update.role
    )

    if not success:
        raise HTTPException(status_code=500, detail="更新失败")

    return {"success": True, "message": "用户信息已更新"}


@router.delete("/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    """删除用户"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能删除最后一个管理员
    if user["role"] == "admin":
        admin_count = db.get_admin_count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="不能删除唯一的管理员账户")

    # 不能删除自己（可选，根据需求）
    current_user_id = admin.get("user_id")
    if current_user_id and current_user_id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")

    success = db.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")

    return {"success": True, "message": f"用户 {user['username']} 已删除"}
