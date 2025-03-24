#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import sys
from src.utils.logger import get_logger

logger = get_logger(__name__)

def clean_environment():
    """清理环境"""
    try:
        logger.info("开始清理环境...")
        
        # 清理Python缓存文件
        cache_dirs = [
            "__pycache__",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
            ".mypy_cache",
        ]
        
        for dir_name in cache_dirs:
            if os.path.exists(dir_name):
                logger.info(f"删除目录: {dir_name}")
                shutil.rmtree(dir_name)
        
        # 清理日志文件
        log_dir = "logs"
        if os.path.exists(log_dir):
            logger.info(f"清理日志目录: {log_dir}")
            for file in os.listdir(log_dir):
                if file.endswith(".log"):
                    os.remove(os.path.join(log_dir, file))
        
        # 清理临时文件
        temp_files = [
            ".DS_Store",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "*.so",
            "*.egg",
            "*.egg-info",
            "dist",
            "build",
        ]
        
        for pattern in temp_files:
            logger.info(f"清理临时文件: {pattern}")
            # 这里需要实现文件模式匹配和删除
        
        logger.info("环境清理完成")
        return 0
    except Exception as e:
        logger.error(f"清理环境时发生错误: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(clean_environment()) 