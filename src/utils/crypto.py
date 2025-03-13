import hashlib
import os
from typing import Optional

def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """对密码进行哈希处理
    
    Args:
        password: 原始密码
        salt: 盐值，如果为None则生成新的盐值
        
    Returns:
        tuple[bytes, bytes]: (盐值, 哈希后的密码)
    """
    if salt is None:
        salt = os.urandom(32)
    
    # 使用PBKDF2算法进行密码哈希
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # 迭代次数
    )
    
    return salt, key

def verify_password(password: str, salt: bytes, key: bytes) -> bool:
    """验证密码
    
    Args:
        password: 待验证的密码
        salt: 盐值
        key: 哈希后的密码
        
    Returns:
        bool: 密码是否正确
    """
    _, new_key = hash_password(password, salt)
    return new_key == key 