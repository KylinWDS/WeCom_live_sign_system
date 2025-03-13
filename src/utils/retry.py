import time
import functools
from typing import TypeVar, Callable, Any, Type, Union, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟时间的增长因子
        exceptions: 需要重试的异常类型
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            current_delay = delay
            
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(
                            f"函数 {func.__name__} 执行失败，"
                            f"已重试 {max_retries} 次: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"函数 {func.__name__} 执行失败，"
                        f"第 {retries} 次重试: {str(e)}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
        return wrapper
    return decorator 