#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import click
from src.utils.logger import get_logger
from src.core.database import DatabaseManager

logger = get_logger(__name__)

@click.group()
def main():
    """数据库管理工具"""
    pass

@main.command()
def init():
    """初始化数据库"""
    try:
        logger.info("开始初始化数据库...")
        db_manager = DatabaseManager()
        db_manager.init_database()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"初始化数据库时发生错误: {e}")
        sys.exit(1)

@main.command()
def migrate():
    """运行数据库迁移"""
    try:
        logger.info("开始数据库迁移...")
        db_manager = DatabaseManager()
        db_manager.run_migrations()
        logger.info("数据库迁移完成")
    except Exception as e:
        logger.error(f"数据库迁移时发生错误: {e}")
        sys.exit(1)

@main.command()
def backup():
    """备份数据库"""
    try:
        logger.info("开始备份数据库...")
        db_manager = DatabaseManager()
        db_manager.backup_database()
        logger.info("数据库备份完成")
    except Exception as e:
        logger.error(f"备份数据库时发生错误: {e}")
        sys.exit(1)

@main.command()
def restore():
    """恢复数据库"""
    try:
        logger.info("开始恢复数据库...")
        db_manager = DatabaseManager()
        db_manager.restore_database()
        logger.info("数据库恢复完成")
    except Exception as e:
        logger.error(f"恢复数据库时发生错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 