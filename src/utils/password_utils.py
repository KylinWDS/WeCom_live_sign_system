import hashlib
import os
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> Tuple[str, str]:
    """对密码进行哈希处理
    
    Args:
        password: 原始密码
        
    Returns:
        Tuple[str, str]: (密码哈希值, 盐值)
    """
    # 生成随机盐值
    salt = os.urandom(16).hex()
    
    # 将密码和盐值组合并进行哈希
    salted_password = password.encode() + salt.encode()
    hashed = hashlib.sha256(salted_password).hexdigest()
    
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """验证密码是否正确
    
    Args:
        password: 待验证的密码
        hashed: 存储的密码哈希值
        salt: 盐值
        
    Returns:
        bool: 密码是否正确
    """
    # 检查参数是否为空
    if not password or not hashed or not salt:
        return False
        
    try:
        # 使用相同的盐值对密码进行哈希
        salted_password = password.encode() + salt.encode()
        new_hashed = hashlib.sha256(salted_password).hexdigest()
        
        # 比较哈希值
        return new_hashed == hashed
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        return False 