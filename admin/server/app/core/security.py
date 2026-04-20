"""
Security Utilities - 密码哈希和 JWT 处理
"""
from datetime import datetime, timedelta
from typing import Optional, Any
import bcrypt
from jose import jwt, JWTError

from app.core.config import get_settings


def hash_password(password: str) -> str:
    """对密码进行哈希处理"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT access token

    Args:
        data: 要编码到 token 中的数据
        expires_delta: 过期时间增量

    Returns:
        JWT token 字符串
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    解析 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        解析后的数据字典，失败返回 None
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    """hash_password 的别名，保持兼容性"""
    return hash_password(password)
