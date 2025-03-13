import hashlib
import hmac
import time
import random
import string
from typing import Tuple, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

def generate_random_string(length: int = 32) -> str:
    """生成随机字符串
    
    Args:
        length: 字符串长度
        
    Returns:
        str: 随机字符串
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_admin_token() -> str:
    """生成管理员令牌
    
    Returns:
        str: 管理员令牌
    """
    try:
        # 生成随机字符串
        random_str = generate_random_string()
        
        # 获取当前时间戳
        timestamp = str(int(time.time()))
        
        # 生成签名
        message = f"{random_str}:{timestamp}"
        secret = "wecom_live_sign_admin_secret"  # 在实际应用中应该使用更安全的密钥
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 组合令牌
        token = f"{random_str}.{timestamp}.{signature}"
        
        logger.info("生成管理员令牌成功")
        return token
        
    except Exception as e:
        logger.error(f"生成管理员令牌失败: {str(e)}")
        raise

def verify_admin_token(token: str) -> Tuple[bool, str]:
    """验证管理员令牌
    
    Args:
        token: 管理员令牌
        
    Returns:
        Tuple[bool, str]: (是否有效, 消息)
    """
    try:
        # 解析令牌
        parts = token.split(".")
        if len(parts) != 3:
            return False, "令牌格式无效"
            
        random_str, timestamp, signature = parts
        
        # 验证时间戳
        try:
            token_time = int(timestamp)
            current_time = int(time.time())
            
            # 令牌有效期24小时
            if current_time - token_time > 24 * 3600:
                return False, "令牌已过期"
                
        except ValueError:
            return False, "令牌时间戳无效"
            
        # 验证签名
        message = f"{random_str}:{timestamp}"
        secret = "wecom_live_sign_admin_secret"  # 在实际应用中应该使用更安全的密钥
        expected_signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if signature != expected_signature:
            return False, "令牌签名无效"
            
        logger.info("管理员令牌验证成功")
        return True, "令牌有效"
        
    except Exception as e:
        logger.error(f"验证管理员令牌失败: {str(e)}")
        return False, "令牌验证失败"

def hash_password(password: str) -> Tuple[str, str]:
    """密码哈希
    
    Args:
        password: 原始密码
        
    Returns:
        Tuple[str, str]: (哈希后的密码, 盐值)
    """
    try:
        # 生成随机盐值
        salt = generate_random_string(16)
        
        # 使用PBKDF2进行密码哈希
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000  # 迭代次数
        ).hex()
        
        return key, salt
        
    except Exception as e:
        logger.error(f"密码哈希失败: {str(e)}")
        raise

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """验证密码
    
    Args:
        password: 原始密码
        hashed: 哈希后的密码
        salt: 盐值
        
    Returns:
        bool: 是否匹配
    """
    try:
        # 使用相同的参数重新计算哈希
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000  # 迭代次数
        ).hex()
        
        return key == hashed
        
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        return False

def check_password_strength(password: str) -> Tuple[bool, str]:
    """检查密码强度
    
    Args:
        password: 密码
        
    Returns:
        Tuple[bool, str]: (是否满足要求, 错误信息)
    """
    try:
        # 检查长度
        if len(password) < 8:
            return False, "密码长度不能少于8位"
            
        # 检查是否包含数字
        if not any(c.isdigit() for c in password):
            return False, "密码必须包含数字"
            
        # 检查是否包含小写字母
        if not any(c.islower() for c in password):
            return False, "密码必须包含小写字母"
            
        # 检查是否包含大写字母
        if not any(c.isupper() for c in password):
            return False, "密码必须包含大写字母"
            
        # 检查是否包含特殊字符
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "密码必须包含特殊字符"
            
        return True, "密码强度符合要求"
        
    except Exception as e:
        logger.error(f"检查密码强度失败: {str(e)}")
        return False, "检查密码强度失败"