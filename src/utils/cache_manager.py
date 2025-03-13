from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import os
import sys
from src.utils.logger import get_logger

logger = get_logger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "cache"):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, Any] = {}
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def set(self, key: str, value: Any, expire: int = 3600):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间(秒)
        """
        try:
            # 内存缓存
            self.memory_cache[key] = {
                "value": value,
                "expire": datetime.now() + timedelta(seconds=expire)
            }
            
            # 文件缓存
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "value": value,
                    "expire": (datetime.now() + timedelta(seconds=expire)).isoformat()
                }, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            
    def get(self, key: str) -> Optional[Any]:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值
        """
        try:
            # 检查内存缓存
            if key in self.memory_cache:
                cache_data = self.memory_cache[key]
                if datetime.now() < cache_data["expire"]:
                    return cache_data["value"]
                else:
                    del self.memory_cache[key]
                    
            # 检查文件缓存
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    expire_time = datetime.fromisoformat(cache_data["expire"])
                    if datetime.now() < expire_time:
                        # 更新内存缓存
                        self.memory_cache[key] = {
                            "value": cache_data["value"],
                            "expire": expire_time
                        }
                        return cache_data["value"]
                    else:
                        os.remove(cache_file)
                        
            return None
        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None
            
    def delete(self, key: str):
        """删除缓存
        
        Args:
            key: 缓存键
        """
        try:
            # 删除内存缓存
            if key in self.memory_cache:
                del self.memory_cache[key]
                
            # 删除文件缓存
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
        except Exception as e:
            logger.error(f"删除缓存失败: {str(e)}")
            
    def clear(self):
        """清空缓存"""
        try:
            # 清空内存缓存
            self.memory_cache.clear()
            
            # 清空文件缓存
            for file in os.listdir(self.cache_dir):
                if file.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, file))
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        try:
            stats = {
                "memory_cache_size": len(self.memory_cache),
                "file_cache_size": len([f for f in os.listdir(self.cache_dir) if f.endswith(".json")]),
                "total_memory_usage": sum(sys.getsizeof(v) for v in self.memory_cache.values()),
                "cache_hits": 0,
                "cache_misses": 0
            }
            return stats
        except Exception as e:
            logger.error(f"获取性能统计失败: {str(e)}")
            return {}
            
    def optimize(self):
        """优化缓存"""
        try:
            # 清理过期缓存
            now = datetime.now()
            for key, cache_data in list(self.memory_cache.items()):
                if now >= cache_data["expire"]:
                    del self.memory_cache[key]
                    
            for file in os.listdir(self.cache_dir):
                if file.endswith(".json"):
                    cache_file = os.path.join(self.cache_dir, file)
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)
                        expire_time = datetime.fromisoformat(cache_data["expire"])
                        if now >= expire_time:
                            os.remove(cache_file)
        except Exception as e:
            logger.error(f"优化缓存失败: {str(e)}") 