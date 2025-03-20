from sqlalchemy import create_engine, text
from src.utils.logger import get_logger
import os

logger = get_logger(__name__)

def check_database():
    # 使用用户指定的数据库路径
    db_path = r'C:\Users\pc\Desktop\lsy\WeCom_live_sign_system-feature_20250314_run_from_main\database\data.db'
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        return
    
    logger.info(f"正在检查数据库: {db_path}")
    logger.info(f"数据库文件大小: {os.path.getsize(db_path)} 字节")
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    with engine.connect() as conn:
        # 获取所有表名
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        logger.info(f"\n数据库中的表: {tables}")
        
        # 检查users表
        logger.info("\n=== Users表信息 ===")
        # 获取表结构
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
        logger.info(f"表结构: {columns}")
        
        # 获取用户数据
        result = conn.execute(text("SELECT * FROM users"))
        rows = result.fetchall()
        logger.info(f"\n总用户数: {len(rows)}")
        
        for row in rows:
            user_data = dict(zip(columns, row))
            logger.info("\n用户详细信息:")
            for key, value in user_data.items():
                logger.info(f"  {key}: {value}")
            
        # 检查root-admin用户
        result = conn.execute(text("SELECT is_admin, is_active, role FROM users WHERE login_name = 'root-admin'"))
        root_admin = result.fetchone()
        if root_admin:
            logger.info("\nroot-admin用户状态:")
            logger.info(f"  is_admin: {root_admin[0]}")
            logger.info(f"  is_active: {root_admin[1]}")
            logger.info(f"  role: {root_admin[2]}")
        else:
            logger.warning("未找到root-admin用户!")

if __name__ == "__main__":
    check_database() 