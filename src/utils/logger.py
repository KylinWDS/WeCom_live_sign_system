import os
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger
from src.core.config_manager import ConfigManager

class Logger:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        """初始化日志管理器
        
        Args:
            log_dir: 日志目录
        """
        self.config_manager = ConfigManager()
        self.log_dir = Path(self.config_manager.get("system.log_path", log_dir))
        self.log_level = self.config_manager.get("system.log_level", "INFO")
        self.log_retention = self.config_manager.get("system.log_retention", 30)
        self._ensure_log_dir()
        self._setup_logger()
        
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        self.log_dir.mkdir(exist_ok=True)
        
    def _setup_logger(self):
        """设置日志记录器"""
        # 配置loguru
        logger.remove()  # 移除默认处理器
        
        # 添加文件处理器
        log_file = self.log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
        logger.add(
            str(log_file),
            rotation="00:00",  # 每天午夜轮换
            retention=f"{self.log_retention} days",  # 保留天数
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            encoding="utf-8"
        )
        
        # 添加控制台处理器
        logger.add(
            lambda msg: print(msg),
            level=self.log_level,
            format="{time:HH:mm:ss} | {level} | {message}",
            colorize=True
        )
        
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            logging.Logger: 日志记录器
        """
        return logger.bind(name=name)
        
    def log_operation(self, user: str, operation: str, details: Optional[str] = None):
        """记录用户操作
        
        Args:
            user: 用户名
            operation: 操作类型
            details: 详细信息
        """
        log_message = f"用户 {user} 执行了 {operation}"
        if details:
            log_message += f": {details}"
            
        logger.info(log_message)
        self._write_to_file("operations.log", log_message)
        
    def log_performance(self, operation: str, start_time: float):
        """记录性能日志
        
        Args:
            operation: 操作类型
            start_time: 开始时间
        """
        duration = time.time() - start_time
        log_message = f"操作: {operation} - 耗时: {duration:.2f}秒"
        logger.info(log_message)
        self._write_to_file("performance.log", log_message)
        
    def log_error(self, error: Exception, user: Optional[str] = None,
                  operation: Optional[str] = None, context: Optional[str] = None):
        """记录错误
        
        Args:
            error: 异常对象
            user: 用户名
            operation: 操作类型
            context: 上下文信息
        """
        log_message = f"发生错误: {str(error)}"
        if user:
            log_message += f" (用户: {user})"
        if operation:
            log_message += f" (操作: {operation})"
        if context:
            log_message += f" (上下文: {context})"
            
        logger.error(log_message, exc_info=True)
        self._write_to_file("errors.log", log_message)
        
    def log_system_event(self, event: str, details: Optional[str] = None):
        """记录系统事件
        
        Args:
            event: 事件类型
            details: 详细信息
        """
        log_message = f"系统事件: {event}"
        if details:
            log_message += f" - {details}"
            
        logger.info(log_message)
        self._write_to_file("system.log", log_message)
        
    def _write_to_file(self, filename: str, message: str):
        """写入日志文件
        
        Args:
            filename: 日志文件名
            message: 日志消息
        """
        filepath = self.log_dir / filename
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except Exception as e:
            logger.error(f"写入日志文件失败: {str(e)}")
            
    def get_operation_logs(self, start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         user: Optional[str] = None) -> List[str]:
        """获取操作日志
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            user: 用户名
            
        Returns:
            List[str]: 日志列表
        """
        logs = []
        log_file = self.log_dir / "operations.log"
        if not log_file.exists():
            return logs
            
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    timestamp = datetime.strptime(
                        line.split(" - ")[0],
                        "%Y-%m-%d %H:%M:%S,%f"
                    )
                    log_user = line.split("用户: ")[1].split(" - ")[0]
                    
                    if start_time and timestamp < start_time:
                        continue
                    if end_time and timestamp > end_time:
                        continue
                    if user and log_user != user:
                        continue
                        
                    logs.append(line.strip())
                except:
                    continue
        return logs
        
    def get_performance_stats(self, operation: Optional[str] = None,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """获取性能统计
        
        Args:
            operation: 操作类型
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        stats = {
            "total_count": 0,
            "avg_duration": 0,
            "max_duration": 0,
            "min_duration": float("inf")
        }
        
        total_duration = 0
        log_file = self.log_dir / "performance.log"
        if not log_file.exists():
            return stats
            
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    timestamp = datetime.strptime(
                        line.split(" - ")[0],
                        "%Y-%m-%d %H:%M:%S,%f"
                    )
                    log_operation = line.split("操作: ")[1].split(" - ")[0]
                    duration = float(line.split("耗时: ")[1].split("秒")[0])
                    
                    if start_time and timestamp < start_time:
                        continue
                    if end_time and timestamp > end_time:
                        continue
                    if operation and log_operation != operation:
                        continue
                        
                    stats["total_count"] += 1
                    total_duration += duration
                    stats["max_duration"] = max(stats["max_duration"], duration)
                    stats["min_duration"] = min(stats["min_duration"], duration)
                except:
                    continue
                    
        if stats["total_count"] > 0:
            stats["avg_duration"] = total_duration / stats["total_count"]
            
        return stats
        
    def export_logs(self, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   log_type: Optional[str] = None) -> str:
        """导出日志
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            log_type: 日志类型
            
        Returns:
            str: 导出文件路径
        """
        try:
            # 创建导出目录
            export_dir = self.log_dir / "exports"
            export_dir.mkdir(exist_ok=True)
            
            # 生成导出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = export_dir / f"logs_{timestamp}.txt"
            
            # 写入日志内容
            with open(export_file, "w", encoding="utf-8") as f:
                f.write("=== 日志导出 ===\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if start_date:
                    f.write(f"开始日期: {start_date.strftime('%Y-%m-%d')}\n")
                if end_date:
                    f.write(f"结束日期: {end_date.strftime('%Y-%m-%d')}\n")
                if log_type:
                    f.write(f"日志类型: {log_type}\n")
                f.write("\n")
                
                # 读取并写入日志内容
                log_files = {
                    "operations": "operations.log",
                    "errors": "errors.log",
                    "system": "system.log",
                    "performance": "performance.log"
                }
                
                if log_type and log_type in log_files:
                    files = [log_files[log_type]]
                else:
                    files = log_files.values()
                    
                for filename in files:
                    filepath = self.log_dir / filename
                    if filepath.exists():
                        f.write(f"\n=== {filename} ===\n")
                        with open(filepath, "r", encoding="utf-8") as log_file:
                            content = log_file.read()
                            # 按日期范围过滤
                            filtered_content = self._filter_logs_by_date(
                                content, start_date, end_date
                            )
                            f.write(filtered_content)
                            
            return str(export_file)
            
        except Exception as e:
            logger.error(f"导出日志失败: {str(e)}")
            raise
            
    def _filter_logs_by_date(self, content: str, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> str:
        """按日期范围过滤日志
        
        Args:
            content: 日志内容
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            str: 过滤后的日志内容
        """
        if not start_date and not end_date:
            return content
            
        filtered_lines = []
        for line in content.split("\n"):
            if not line.strip():
                continue
                
            try:
                # 解析日志时间戳
                timestamp_str = line[1:20]  # 格式: [YYYY-MM-DD HH:MM:SS]
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # 检查是否在日期范围内
                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue
                    
                filtered_lines.append(line)
            except:
                # 如果解析失败,保留该行
                filtered_lines.append(line)
                
        return "\n".join(filtered_lines)
        
    def cleanup_old_logs(self):
        """清理旧日志文件"""
        try:
            # 获取所有日志文件
            log_files = []
            for file_path in self.log_dir.glob("*.log"):
                log_files.append((file_path, file_path.stat().st_mtime))
                
            # 按修改时间排序
            log_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除过期日志
            current_time = datetime.now().timestamp()
            for file_path, mtime in log_files:
                if current_time - mtime > self.log_retention * 24 * 3600:
                    try:
                        file_path.unlink()
                        logger.info(f"删除过期日志: {file_path}")
                    except Exception as e:
                        logger.error(f"删除过期日志失败: {str(e)}")
                        
        except Exception as e:
            logger.error(f"清理旧日志失败: {str(e)}")
            
# 创建全局日志管理器实例
logger_manager = Logger()

# 导出get_logger函数
def get_logger(name: str) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return logger_manager.get_logger(name) 