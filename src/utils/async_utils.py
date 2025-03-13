import asyncio
import concurrent.futures
from typing import Any, Callable, List, Optional, TypeVar, Union
from functools import wraps
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

T = TypeVar("T")

class AsyncUtils:
    """异步工具类"""
    
    def __init__(self, max_workers: int = 4):
        """初始化异步工具类
        
        Args:
            max_workers: 最大工作线程数
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.get_event_loop()
        
    def run_in_thread(self, func: Callable[..., T], *args, **kwargs) -> T:
        """在线程池中运行函数
        
        Args:
            func: 要运行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
        """
        return self.loop.run_in_executor(
            self.executor,
            lambda: func(*args, **kwargs)
        )
        
    async def run_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """异步运行函数
        
        Args:
            func: 要运行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
        """
        return await self.loop.run_in_executor(
            self.executor,
            lambda: func(*args, **kwargs)
        )
        
    async def run_batch(self, func: Callable[..., T], items: List[Any], 
                       batch_size: int = 10) -> List[T]:
        """批量异步运行函数
        
        Args:
            func: 要运行的函数
            items: 输入项列表
            batch_size: 批处理大小
            
        Returns:
            结果列表
        """
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            tasks = [self.run_async(func, item) for item in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results
        
    def run_with_timeout(self, func: Callable[..., T], timeout: float, 
                        *args, **kwargs) -> Optional[T]:
        """带超时的函数运行
        
        Args:
            func: 要运行的函数
            timeout: 超时时间(秒)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值,超时返回None
        """
        try:
            future = self.executor.submit(func, *args, **kwargs)
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.warning(f"函数执行超时: {func.__name__}")
            return None
        except Exception as e:
            logger.error(f"函数执行失败: {str(e)}")
            return None
            
    def run_with_retry(self, func: Callable[..., T], max_retries: int = 3,
                      delay: float = 1.0, *args, **kwargs) -> Optional[T]:
        """带重试的函数运行
        
        Args:
            func: 要运行的函数
            max_retries: 最大重试次数
            delay: 重试延迟(秒)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值,重试失败返回None
        """
        for i in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == max_retries - 1:
                    logger.error(f"函数执行失败: {str(e)}")
                    return None
                logger.warning(f"函数执行失败,准备重试: {str(e)}")
                asyncio.sleep(delay)
        return None
        
    def run_with_progress(self, func: Callable[..., T], total: int,
                         *args, **kwargs) -> List[T]:
        """带进度的函数运行
        
        Args:
            func: 要运行的函数
            total: 总任务数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            结果列表
        """
        results = []
        completed = 0
        
        def callback(future):
            nonlocal completed
            completed += 1
            progress = (completed / total) * 100
            logger.info(f"进度: {progress:.1f}%")
            
        futures = []
        for _ in range(total):
            future = self.executor.submit(func, *args, **kwargs)
            future.add_done_callback(callback)
            futures.append(future)
            
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"任务执行失败: {str(e)}")
                
        return results
        
    def run_with_priority(self, func: Callable[..., T], priority: int,
                         *args, **kwargs) -> T:
        """带优先级的函数运行
        
        Args:
            func: 要运行的函数
            priority: 优先级(数字越小优先级越高)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
        """
        future = self.executor.submit(func, *args, **kwargs)
        future.priority = priority
        return future.result()
        
    def run_with_callback(self, func: Callable[..., T], callback: Callable[[T], None],
                         *args, **kwargs) -> None:
        """带回调的函数运行
        
        Args:
            func: 要运行的函数
            callback: 回调函数
            *args: 位置参数
            **kwargs: 关键字参数
        """
        def wrapper():
            try:
                result = func(*args, **kwargs)
                callback(result)
            except Exception as e:
                logger.error(f"函数执行失败: {str(e)}")
                
        self.executor.submit(wrapper)
        
    def run_with_cancel(self, func: Callable[..., T], *args, **kwargs) -> tuple[concurrent.futures.Future, Callable[[], None]]:
        """可取消的函数运行
        
        Args:
            func: 要运行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            (Future对象, 取消函数)
        """
        future = self.executor.submit(func, *args, **kwargs)
        return future, future.cancel
        
    def run_with_timeout_and_retry(self, func: Callable[..., T], timeout: float,
                                 max_retries: int = 3, delay: float = 1.0,
                                 *args, **kwargs) -> Optional[T]:
        """带超时和重试的函数运行
        
        Args:
            func: 要运行的函数
            timeout: 超时时间(秒)
            max_retries: 最大重试次数
            delay: 重试延迟(秒)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值,失败返回None
        """
        for i in range(max_retries):
            try:
                future = self.executor.submit(func, *args, **kwargs)
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                if i == max_retries - 1:
                    logger.warning(f"函数执行超时: {func.__name__}")
                    return None
                logger.warning(f"函数执行超时,准备重试: {func.__name__}")
                asyncio.sleep(delay)
            except Exception as e:
                if i == max_retries - 1:
                    logger.error(f"函数执行失败: {str(e)}")
                    return None
                logger.warning(f"函数执行失败,准备重试: {str(e)}")
                asyncio.sleep(delay)
        return None
        
    def run_with_progress_and_callback(self, func: Callable[..., T], total: int,
                                     callback: Callable[[T], None],
                                     *args, **kwargs) -> None:
        """带进度和回调的函数运行
        
        Args:
            func: 要运行的函数
            total: 总任务数
            callback: 回调函数
            *args: 位置参数
            **kwargs: 关键字参数
        """
        completed = 0
        
        def wrapper():
            nonlocal completed
            try:
                result = func(*args, **kwargs)
                completed += 1
                progress = (completed / total) * 100
                logger.info(f"进度: {progress:.1f}%")
                callback(result)
            except Exception as e:
                logger.error(f"任务执行失败: {str(e)}")
                
        for _ in range(total):
            self.executor.submit(wrapper)
            
    def run_with_priority_and_timeout(self, func: Callable[..., T], priority: int,
                                    timeout: float, *args, **kwargs) -> Optional[T]:
        """带优先级和超时的函数运行
        
        Args:
            func: 要运行的函数
            priority: 优先级(数字越小优先级越高)
            timeout: 超时时间(秒)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值,超时返回None
        """
        future = self.executor.submit(func, *args, **kwargs)
        future.priority = priority
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.warning(f"函数执行超时: {func.__name__}")
            return None
        except Exception as e:
            logger.error(f"函数执行失败: {str(e)}")
            return None
            
    def run_with_retry_and_callback(self, func: Callable[..., T], max_retries: int = 3,
                                  delay: float = 1.0, callback: Callable[[T], None] = None,
                                  *args, **kwargs) -> None:
        """带重试和回调的函数运行
        
        Args:
            func: 要运行的函数
            max_retries: 最大重试次数
            delay: 重试延迟(秒)
            callback: 回调函数
            *args: 位置参数
            **kwargs: 关键字参数
        """
        def wrapper():
            for i in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    if callback:
                        callback(result)
                    return
                except Exception as e:
                    if i == max_retries - 1:
                        logger.error(f"函数执行失败: {str(e)}")
                        return
                    logger.warning(f"函数执行失败,准备重试: {str(e)}")
                    asyncio.sleep(delay)
                    
        self.executor.submit(wrapper)
        
    def run_with_progress_and_cancel(self, func: Callable[..., T], total: int,
                                   *args, **kwargs) -> tuple[List[concurrent.futures.Future], Callable[[], None]]:
        """带进度和取消的函数运行
        
        Args:
            func: 要运行的函数
            total: 总任务数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            (Future对象列表, 取消函数)
        """
        futures = []
        completed = 0
        
        def wrapper():
            nonlocal completed
            try:
                result = func(*args, **kwargs)
                completed += 1
                progress = (completed / total) * 100
                logger.info(f"进度: {progress:.1f}%")
            except Exception as e:
                logger.error(f"任务执行失败: {str(e)}")
                
        for _ in range(total):
            future = self.executor.submit(wrapper)
            futures.append(future)
            
        def cancel():
            for future in futures:
                future.cancel()
                
        return futures, cancel
        
    def run_with_priority_and_retry(self, func: Callable[..., T], priority: int,
                                  max_retries: int = 3, delay: float = 1.0,
                                  *args, **kwargs) -> Optional[T]:
        """带优先级和重试的函数运行
        
        Args:
            func: 要运行的函数
            priority: 优先级(数字越小优先级越高)
            max_retries: 最大重试次数
            delay: 重试延迟(秒)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值,失败返回None
        """
        for i in range(max_retries):
            try:
                future = self.executor.submit(func, *args, **kwargs)
                future.priority = priority
                return future.result()
            except Exception as e:
                if i == max_retries - 1:
                    logger.error(f"函数执行失败: {str(e)}")
                    return None
                logger.warning(f"函数执行失败,准备重试: {str(e)}")
                asyncio.sleep(delay)
        return None
        
    def run_with_timeout_and_callback(self, func: Callable[..., T], timeout: float,
                                    callback: Callable[[T], None],
                                    *args, **kwargs) -> None:
        """带超时和回调的函数运行
        
        Args:
            func: 要运行的函数
            timeout: 超时时间(秒)
            callback: 回调函数
            *args: 位置参数
            **kwargs: 关键字参数
        """
        def wrapper():
            try:
                future = self.executor.submit(func, *args, **kwargs)
                result = future.result(timeout=timeout)
                callback(result)
            except concurrent.futures.TimeoutError:
                logger.warning(f"函数执行超时: {func.__name__}")
            except Exception as e:
                logger.error(f"函数执行失败: {str(e)}")
                
        self.executor.submit(wrapper)
        
    def run_with_progress_and_timeout(self, func: Callable[..., T], total: int,
                                    timeout: float, *args, **kwargs) -> List[Optional[T]]:
        """带进度和超时的函数运行
        
        Args:
            func: 要运行的函数
            total: 总任务数
            timeout: 超时时间(秒)
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            结果列表
        """
        results = []
        completed = 0
        
        def wrapper():
            nonlocal completed
            try:
                future = self.executor.submit(func, *args, **kwargs)
                result = future.result(timeout=timeout)
                completed += 1
                progress = (completed / total) * 100
                logger.info(f"进度: {progress:.1f}%")
                return result
            except concurrent.futures.TimeoutError:
                logger.warning(f"任务执行超时: {func.__name__}")
                return None
            except Exception as e:
                logger.error(f"任务执行失败: {str(e)}")
                return None
                
        futures = []
        for _ in range(total):
            future = self.executor.submit(wrapper)
            futures.append(future)
            
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"获取结果失败: {str(e)}")
                results.append(None)
                
        return results 