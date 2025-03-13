from loguru import logger
import logging

# 定义get_logger函数

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return logger.bind(name=name) 