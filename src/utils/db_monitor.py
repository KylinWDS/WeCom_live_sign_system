from sqlalchemy import event
from src.core.database import DatabaseManager
from src.utils.logger import get_logger
import time

logger = get_logger(__name__)

def setup_db_monitoring(db_manager: DatabaseManager):
    """设置数据库监控
    
    Args:
        db_manager: 数据库管理器实例
    """
    @event.listens_for(db_manager.engine, 'connect')
    def receive_connect(dbapi_connection, connection_record):
        logger.info("数据库连接建立")
        
    @event.listens_for(db_manager.engine, 'disconnect')
    def receive_disconnect(dbapi_connection, connection_record):
        logger.info("数据库连接断开")
        
    @event.listens_for(db_manager.engine, 'cursor')
    def receive_cursor(cursor):
        start_time = time.time()
        
        def after_cursor_execute(session, cursor, statement, parameters, context, executemany):
            total = time.time() - start_time
            logger.debug(f"SQL执行时间: {total:.3f}秒")
            logger.debug(f"SQL语句: {statement}")
            if parameters:
                logger.debug(f"参数: {parameters}")
                
        event.listen(cursor, 'after_execute', after_cursor_execute) 