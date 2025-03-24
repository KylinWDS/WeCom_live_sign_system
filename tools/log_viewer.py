#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import click
import os
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)

@click.group()
def main():
    """日志查看工具"""
    pass

@main.command()
@click.option('--lines', default=100, help='显示的行数')
@click.option('--level', default='INFO', help='日志级别')
@click.option('--date', help='日期 (YYYY-MM-DD)')
def view(lines, level, date):
    """查看日志"""
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            logger.error("日志目录不存在")
            sys.exit(1)
            
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if not log_files:
            logger.error("没有找到日志文件")
            sys.exit(1)
            
        # 如果指定了日期，查找对应日期的日志文件
        if date:
            try:
                datetime.strptime(date, '%Y-%m-%d')
                log_files = [f for f in log_files if date in f]
            except ValueError:
                logger.error("日期格式错误，请使用YYYY-MM-DD格式")
                sys.exit(1)
        
        for log_file in log_files:
            file_path = os.path.join(log_dir, log_file)
            logger.info(f"查看日志文件: {log_file}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines_list = f.readlines()
                
            # 过滤日志级别
            if level:
                lines_list = [line for line in lines_list if level in line]
            
            # 显示最后N行
            for line in lines_list[-lines:]:
                print(line.strip())
                
    except Exception as e:
        logger.error(f"查看日志时发生错误: {e}")
        sys.exit(1)

@main.command()
@click.option('--days', default=30, help='保留的天数')
def clean(days):
    """清理旧日志"""
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            logger.error("日志目录不存在")
            sys.exit(1)
            
        current_time = datetime.now()
        for log_file in os.listdir(log_dir):
            if log_file.endswith('.log'):
                file_path = os.path.join(log_dir, log_file)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if (current_time - file_time).days > days:
                    os.remove(file_path)
                    logger.info(f"删除旧日志文件: {log_file}")
                    
    except Exception as e:
        logger.error(f"清理日志时发生错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 