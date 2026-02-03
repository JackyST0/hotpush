"""
认证中间件
使用 JWT Token 进行用户认证和权限控制
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.utils.logger import logger


# JWT 配置
JWT_ALGORITHM = "HS256"

# 不需要认证的路径
PUBLIC_PATHS = [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/check",
    "/static",
    "/bg.jpg",
    "/favicon.ico",
]

# 支持 query 参数验证 token 的路径（SSE 不支持自定义 header）
TOKEN_QUERY_PATHS = [
    "/api/hot/stream",
]


def is_auth_enabled() -> bool:
    """检查是否启用了认证（需要设置 admin_password）"""
    return bool(settings.admin_password)


def create_token(data: dict) -> str:
    """创建 JWT Token"""
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_public_path(path: str) -> bool:
    """检查是否为公开路径"""
    for public_path in PUBLIC_PATHS:
        if path == public_path or path.startswith(public_path + "/"):
            return True
    # 静态文件
    if path.startswith("/static"):
        return True
    return False


def is_token_query_path(path: str) -> bool:
    """检查是否为支持 query 参数验证的路径"""
    for query_path in TOKEN_QUERY_PATHS:
        if path == query_path or path.startswith(query_path + "/"):
            return True
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    async def dispatch(self, request: Request, call_next):
        # 如果未启用认证，则不需要验证
        if not is_auth_enabled():
            return await call_next(request)

        path = request.url.path

        # 公开路径不需要认证
        if is_public_path(path):
            return await call_next(request)

        token = None

        # 检查 Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # 解析 Bearer Token
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    token = None
            except ValueError:
                token = None

        # 对于 SSE 等特殊路径，支持从 query 参数获取 token
        if not token and is_token_query_path(path):
            token = request.query_params.get("token")

        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "未登录，请先登录"}
            )

        # 验证 Token
        payload = verify_token(token)
        if not payload:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token 已过期或无效，请重新登录"}
            )

        # 将用户信息添加到请求状态
        request.state.user = payload

        return await call_next(request)


# FastAPI 依赖项

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[dict]:
    """获取当前用户（可选认证）"""
    # 如果未启用认证，返回默认用户
    if not is_auth_enabled():
        return {"authenticated": True, "no_auth": True, "role": "admin"}

    if not credentials:
        return None

    payload = verify_token(credentials.credentials)
    return payload


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """要求认证（必须登录）"""
    # 如果未启用认证，返回默认用户（管理员权限）
    if not is_auth_enabled():
        return {"authenticated": True, "no_auth": True, "role": "admin"}

    if not credentials:
        raise HTTPException(status_code=401, detail="未登录，请先登录")

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 已过期或无效，请重新登录")

    return payload


async def require_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """要求管理员权限"""
    # 如果未启用认证，返回默认用户（管理员权限）
    if not is_auth_enabled():
        return {"authenticated": True, "no_auth": True, "role": "admin"}

    if not credentials:
        raise HTTPException(status_code=401, detail="未登录，请先登录")

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 已过期或无效，请重新登录")

    # 检查角色
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="权限不足，需要管理员权限")

    return payload
