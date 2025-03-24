#!/usr/bin/env python3
import os
import sys
import argparse
import json
from datetime import datetime
from src.utils.security import generate_admin_token, verify_admin_token
from src.utils.logger import get_logger
from src.core.database import DatabaseManager
from src.core.auth_manager import AuthManager

logger = get_logger(__name__)

def generate_reset_token():
    """生成重置令牌"""
    try:
        # 生成令牌
        token = generate_admin_token()
        
        # 获取当前时间
        now = datetime.now()
        
        print("\n=== 超级管理员密码重置令牌 ===")
        print(f"令牌: {token}")
        print(f"生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n使用说明:")
        print("1. 复制上面的令牌")
        print("2. 打开系统登录界面")
        print("3. 点击'忘记密码'按钮")
        print("4. 粘贴令牌并设置新密码")
        print("\n安全提示:")
        print("- 令牌有效期为24小时")
        print("- 请妥善保管令牌，不要泄露给他人")
        print("- 重置密码后请立即修改为新的密码")
        print("- 建议定期更换密码")
        print("- 密码应包含大小写字母、数字和特殊字符")
        
        # 记录日志
        logger.info("生成管理员令牌成功")
        
    except Exception as e:
        logger.error(f"生成管理员令牌失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1)

def reset_password(token: str, new_password: str):
    """重置密码
    
    Args:
        token: 管理员令牌
        new_password: 新密码
    """
    try:
        # 初始化数据库和认证管理器
        db_manager = DatabaseManager()
        auth_manager = AuthManager(db_manager)
        
        # 验证令牌
        is_valid, error_msg = verify_admin_token(token)
        if not is_valid:
            print(f"错误: {error_msg}")
            sys.exit(1)
            
        # 重置密码
        success, error_msg = auth_manager.reset_admin_password(token, new_password)
        if success:
            print("\n密码重置成功!")
            print("请使用新密码登录系统")
            logger.info("管理员密码重置成功")
        else:
            print(f"错误: {error_msg}")
            logger.error(f"重置密码失败: {error_msg}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"重置密码失败: {str(e)}")
        print(f"错误: {str(e)}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="超级管理员密码重置工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 生成令牌命令
    token_parser = subparsers.add_parser("token", help="生成管理员令牌")
    
    # 重置密码命令
    reset_parser = subparsers.add_parser("reset", help="重置管理员密码")
    reset_parser.add_argument("token", help="管理员令牌")
    reset_parser.add_argument("password", help="新密码")
    
    args = parser.parse_args()
    
    if args.command == "token":
        generate_reset_token()
    elif args.command == "reset":
        reset_password(args.token, args.password)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 