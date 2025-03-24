from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.models.user import User
from src.utils.security import hash_password
from src.models.user_role import UserRole

logger = get_logger(__name__)

class UserManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def reset_admin_password(self, new_password):
        """重置管理员密码
        
        Args:
            new_password: 新密码
            
        Returns:
            bool: 是否重置成功
        """
        session = self.db_manager.get_session()
        try:
            # 查找管理员用户
            admin = session.query(User).filter_by(role=UserRole.ROOT_ADMIN.value).first()
            if not admin:
                logger.error("未找到管理员用户")
                return False
                
            # 更新密码
            admin.password = hash_password(new_password)
            session.commit()
            
            logger.info("管理员密码已重置")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"重置管理员密码失败: {str(e)}")
            return False
            
        finally:
            session.close() 