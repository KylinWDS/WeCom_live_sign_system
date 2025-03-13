import time
import functools
from datetime import datetime
from typing import Dict, Any, Callable
from utils.logger import get_logger

logger = get_logger(__name__)

class PerformanceManager:
    """性能管理器，用于监控和记录各种操作的性能数据"""
    
    _instance = None
    _performance_data: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._performance_data = {}
            logger.info("性能管理器初始化完成")
    
    @classmethod
    def measure_operation(cls, operation_name: str) -> Callable:
        """性能监控装饰器
        
        Args:
            operation_name: 操作名称
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    cls._record_performance(operation_name, time.time() - start_time)
                    return result
                except Exception as e:
                    cls._record_performance(operation_name, time.time() - start_time, success=False)
                    raise e
            return wrapper
        return decorator
    
    @classmethod
    def _record_performance(cls, operation_name: str, duration: float, success: bool = True):
        """记录性能数据
        
        Args:
            operation_name: 操作名称
            duration: 执行时间（秒）
            success: 是否执行成功
        """
        if operation_name not in cls._performance_data:
            cls._performance_data[operation_name] = {
                "count": 0,
                "total_time": 0,
                "max_time": 0,
                "min_time": float('inf'),
                "success_count": 0,
                "fail_count": 0,
                "last_execution": None
            }
            
        stats = cls._performance_data[operation_name]
        duration_ms = duration * 1000  # 转换为毫秒
        
        stats["count"] += 1
        stats["total_time"] += duration_ms
        stats["max_time"] = max(stats["max_time"], duration_ms)
        stats["min_time"] = min(stats["min_time"], duration_ms)
        if success:
            stats["success_count"] += 1
        else:
            stats["fail_count"] += 1
        stats["last_execution"] = datetime.now()
        
        # 记录日志
        logger.debug(f"操作 {operation_name} 执行完成，耗时: {duration_ms:.2f}ms, 成功: {success}")
    
    def get_performance_stats(self, start_time: datetime = None, end_time: datetime = None) -> Dict[str, Dict[str, Any]]:
        """获取性能统计数据
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            性能统计数据
        """
        stats = {}
        for operation, data in self._performance_data.items():
            # 如果指定了时间范围，只返回该范围内的数据
            if start_time and end_time and data["last_execution"]:
                if not (start_time <= data["last_execution"] <= end_time):
                    continue
                    
            if data["count"] > 0:
                stats[operation] = {
                    "count": data["count"],
                    "avg": data["total_time"] / data["count"],
                    "max": data["max_time"],
                    "min": data["min_time"],
                    "success_rate": (data["success_count"] / data["count"]) * 100,
                    "last_execution": data["last_execution"]
                }
                
        return stats
    
    def reset_stats(self):
        """重置性能统计数据"""
        self._performance_data.clear()
        logger.info("性能统计数据已重置") 