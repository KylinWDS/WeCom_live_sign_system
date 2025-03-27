#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据迁移工具：将旧模型（WatchStat、SignRecord）的数据迁移到新的 LiveViewer 模型
"""

import os
import sys
import argparse
from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import datetime

# 添加项目根目录到系统路径，确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager
from src.models.live_viewer import LiveViewer, UserSource
from src.models.living import Living
from src.utils.logger import get_logger

logger = get_logger("data_migration")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="数据迁移工具：将旧模型数据迁移到新模型")
    parser.add_argument('--dry-run', action='store_true', help='只模拟执行但不实际修改数据库')
    parser.add_argument('--force', action='store_true', help='强制执行，即使已经有迁移数据')
    parser.add_argument('--limit', type=int, default=None, help='限制处理的记录数')
    parser.add_argument('--living-id', type=int, help='只处理特定的直播ID')
    return parser.parse_args()

def get_old_model_counts(session: Session) -> Dict[str, int]:
    """获取旧模型中数据的数量"""
    counts = {}
    
    # 尝试获取 WatchStat 记录数
    try:
        # 动态导入，如果模块不存在则忽略
        WatchStat = None
        try:
            from src.models.watch_stat import WatchStat
            counts['watch_stat'] = session.query(WatchStat).count()
            logger.info(f"找到 {counts['watch_stat']} 条 WatchStat 记录")
        except ImportError:
            logger.warning("WatchStat 模型不存在或已删除")
            counts['watch_stat'] = 0
    except Exception as e:
        logger.error(f"查询 WatchStat 记录失败: {str(e)}")
        counts['watch_stat'] = 0

    # 尝试获取 SignRecord 记录数
    try:
        # 动态导入，如果模块不存在则忽略
        SignRecord = None
        try:
            from src.models.sign_record import SignRecord
            counts['sign_record'] = session.query(SignRecord).count()
            logger.info(f"找到 {counts['sign_record']} 条 SignRecord 记录")
        except ImportError:
            logger.warning("SignRecord 模型不存在或已删除")
            counts['sign_record'] = 0
    except Exception as e:
        logger.error(f"查询 SignRecord 记录失败: {str(e)}")
        counts['sign_record'] = 0
        
    # 获取 LiveViewer 记录数
    counts['live_viewer'] = session.query(LiveViewer).count()
    logger.info(f"找到 {counts['live_viewer']} 条 LiveViewer 记录")
    
    return counts

def migrate_watch_stats(session: Session, args) -> int:
    """迁移 WatchStat 数据到 LiveViewer"""
    try:
        # 动态导入，如果模块不存在则返回
        try:
            from src.models.watch_stat import WatchStat
        except ImportError:
            logger.warning("WatchStat 模型不存在或已删除，跳过数据迁移")
            return 0
    except Exception as e:
        logger.error(f"导入 WatchStat 模型失败: {str(e)}")
        return 0
    
    query = session.query(WatchStat)
    
    # 如果指定了直播ID，则只处理该直播的数据
    if args.living_id:
        query = query.filter(WatchStat.living_id == args.living_id)
    
    # 如果指定了数量限制，则应用限制
    if args.limit:
        query = query.limit(args.limit)
    
    watch_stats = query.all()
    migrated_count = 0
    
    for watch_stat in watch_stats:
        # 检查是否已存在对应的 LiveViewer 记录
        existing = session.query(LiveViewer).filter(
            LiveViewer.living_id == watch_stat.living_id,
            LiveViewer.userid == watch_stat.userid
        ).first()
        
        if existing and not args.force:
            logger.debug(f"跳过已存在的 LiveViewer 记录：直播ID {watch_stat.living_id}，用户ID {watch_stat.userid}")
            continue
        
        # 确定用户来源
        user_source = UserSource.INTERNAL if watch_stat.user_type == 2 else UserSource.EXTERNAL
        
        # 创建新的 LiveViewer 记录
        if existing:
            # 更新现有记录
            existing.watch_time = watch_stat.watch_time
            existing.is_comment = watch_stat.is_comment
            existing.is_mic = watch_stat.is_mic
            existing.invitor_userid = watch_stat.invitor_userid
            existing.invitor_name = watch_stat.invitor_name
            existing.ip = watch_stat.ip
            existing.location = watch_stat.location
            existing.device_info = watch_stat.device_info
        else:
            new_viewer = LiveViewer(
                living_id=watch_stat.living_id,
                userid=watch_stat.userid,
                name=watch_stat.name,
                user_source=user_source,
                user_type=watch_stat.user_type,
                watch_time=watch_stat.watch_time,
                is_comment=watch_stat.is_comment,
                is_mic=watch_stat.is_mic,
                invitor_userid=watch_stat.invitor_userid,
                invitor_name=watch_stat.invitor_name,
                ip=watch_stat.ip,
                location=watch_stat.location,
                device_info=watch_stat.device_info
            )
            if not args.dry_run:
                session.add(new_viewer)
        
        migrated_count += 1
        
        if migrated_count % 100 == 0:
            logger.info(f"已处理 {migrated_count}/{len(watch_stats)} 条 WatchStat 记录")
            if not args.dry_run:
                session.commit()  # 每处理100条提交一次，避免事务过大
    
    if not args.dry_run and migrated_count % 100 != 0:
        session.commit()  # 提交剩余的更改
    
    logger.info(f"已将 {migrated_count} 条 WatchStat 记录迁移到 LiveViewer")
    return migrated_count

def migrate_sign_records(session: Session, args) -> int:
    """迁移 SignRecord 数据到 LiveViewer"""
    try:
        # 动态导入，如果模块不存在则返回
        try:
            from src.models.sign_record import SignRecord
        except ImportError:
            logger.warning("SignRecord 模型不存在或已删除，跳过数据迁移")
            return 0
    except Exception as e:
        logger.error(f"导入 SignRecord 模型失败: {str(e)}")
        return 0
    
    query = session.query(SignRecord)
    
    # 如果指定了直播ID，则只处理该直播的数据
    if args.living_id:
        query = query.filter(SignRecord.living_id == args.living_id)
    
    # 如果指定了数量限制，则应用限制
    if args.limit:
        query = query.limit(args.limit)
    
    sign_records = query.all()
    migrated_count = 0
    
    for sign_record in sign_records:
        # 查找对应的 LiveViewer 记录
        viewer = session.query(LiveViewer).filter(
            LiveViewer.living_id == sign_record.living_id,
            LiveViewer.userid == sign_record.userid
        ).first()
        
        # 确定用户来源
        user_source = UserSource.INTERNAL if sign_record.user_type == 2 else UserSource.EXTERNAL
        
        if viewer:
            # 更新已存在的记录
            viewer.is_signed = True
            viewer.sign_time = sign_record.sign_time
            viewer.sign_type = sign_record.sign_type
            viewer.sign_location = sign_record.sign_location
            
            # 如果还没有部门信息，则更新
            if not viewer.department and sign_record.department:
                viewer.department = sign_record.department
        else:
            # 创建新的记录
            new_viewer = LiveViewer(
                living_id=sign_record.living_id,
                userid=sign_record.userid,
                name=sign_record.name,
                user_source=user_source,
                user_type=sign_record.user_type,
                department=sign_record.department,
                is_signed=True,
                sign_time=sign_record.sign_time,
                sign_type=sign_record.sign_type,
                sign_location=sign_record.sign_location
            )
            if not args.dry_run:
                session.add(new_viewer)
        
        migrated_count += 1
        
        if migrated_count % 100 == 0:
            logger.info(f"已处理 {migrated_count}/{len(sign_records)} 条 SignRecord 记录")
            if not args.dry_run:
                session.commit()  # 每处理100条提交一次，避免事务过大
    
    if not args.dry_run and migrated_count % 100 != 0:
        session.commit()  # 提交剩余的更改
    
    logger.info(f"已将 {migrated_count} 条 SignRecord 记录迁移到 LiveViewer")
    return migrated_count

def update_living_stats(session: Session, args):
    """更新直播统计数据"""
    logger.info("开始更新直播统计数据...")
    
    query = session.query(Living)
    
    # 如果指定了直播ID，则只处理该直播
    if args.living_id:
        query = query.filter(Living.id == args.living_id)
    
    livings = query.all()
    updated_count = 0
    
    for living in livings:
        # 获取该直播的观众数据
        viewers = session.query(LiveViewer).filter(LiveViewer.living_id == living.id).all()
        
        # 更新统计数据
        viewer_count = len(viewers)
        signed_count = len([v for v in viewers if v.is_signed])
        comment_count = len([v for v in viewers if v.is_comment])
        
        # 检查是否需要更新
        if (living.viewer_num != viewer_count or
            living.sign_num != signed_count or
            living.comment_num != comment_count):
            
            # 更新直播统计数据
            living.viewer_num = viewer_count
            living.sign_num = signed_count
            living.comment_num = comment_count
            
            updated_count += 1
            
            logger.debug(f"已更新直播 {living.id} 的统计数据: 观众数={viewer_count}, 签到数={signed_count}, 评论数={comment_count}")
    
    if not args.dry_run and updated_count > 0:
        session.commit()
    
    logger.info(f"已更新 {updated_count}/{len(livings)} 个直播的统计数据")
    return updated_count

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 初始化数据库管理器
    db_manager = DatabaseManager()
    
    # 创建会话
    with db_manager.get_session() as session:
        # 获取旧模型数据数量
        counts = get_old_model_counts(session)
        
        if counts['live_viewer'] > 0 and not args.force:
            logger.warning(f"数据库中已存在 {counts['live_viewer']} 条 LiveViewer 记录")
            logger.warning("如果要强制执行数据迁移，请使用 --force 参数")
            if not args.force:
                return
        
        if args.dry_run:
            logger.info("执行模拟迁移 (--dry-run)...")
        
        # 开始迁移
        migrated_watch_stats = migrate_watch_stats(session, args)
        migrated_sign_records = migrate_sign_records(session, args)
        
        # 更新直播统计数据
        updated_livings = update_living_stats(session, args)
        
        # 输出迁移结果
        logger.info("=== 数据迁移结果 ===")
        logger.info(f"- 迁移 WatchStat 记录: {migrated_watch_stats} 条")
        logger.info(f"- 迁移 SignRecord 记录: {migrated_sign_records} 条")
        logger.info(f"- 更新直播统计数据: {updated_livings} 个直播")
        
        if args.dry_run:
            logger.info("这是模拟运行，没有对数据库进行实际修改")
        else:
            logger.info("数据迁移已完成")

if __name__ == "__main__":
    main()