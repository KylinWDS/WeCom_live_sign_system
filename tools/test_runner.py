#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
from src.utils.logger import get_logger

logger = get_logger(__name__)

def run_tests():
    """运行测试"""
    try:
        logger.info("开始运行测试...")
        # 运行pytest
        result = subprocess.run(
            ["pytest", "-v", "--cov=src", "--cov-report=term-missing"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        logger.info("测试运行完成")
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"测试运行失败: {e}")
        print(e.stderr)
        return 1
    except Exception as e:
        logger.error(f"运行测试时发生错误: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests()) 