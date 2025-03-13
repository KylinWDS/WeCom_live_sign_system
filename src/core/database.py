import sqlite3
import os
import shutil
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
from src.utils.logger import get_logger
from src.models.base import Base
from src.models import User, UserRole
from src.models.living import Living, WatchStat
from src.models.live_booking import LiveBooking
from src.models.live_viewer import LiveViewer
from src.models.sign_record import SignRecord
from src.models.sign import Sign
from src.config.database import DB_CONFIG, MIGRATION_CONFIG
from contextlib import contextmanager

logger = get_logger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        """初始化数据库管理器"""
        self.engine = create_engine(
            f"sqlite:///{DB_CONFIG['db_path']}",
            poolclass=QueuePool,
            pool_size=DB_CONFIG['max_connections'],
            pool_recycle=DB_CONFIG['pool_recycle'],
            echo=DB_CONFIG['echo']
        )
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        try:
            # 删除所有表
            Base.metadata.drop_all(bind=self.engine)
            
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            
            # 创建会话
            with self.get_session() as session:
                # 检查是否已存在root-admin用户
                root_admin = session.query(User).filter(User.userid == "root-admin").first()
                if not root_admin:
                    # 创建root-admin用户
                    root_admin = User(
                        userid="root-admin",
                        name="系统超级管理员",
                        role=UserRole.ROOT_ADMIN,
                        is_active=True,
                        # 初始密码为空，需要首次登录时设置
                        password_hash=None
                    )
                    session.add(root_admin)
                    session.commit()
                    logger.info("创建root-admin用户成功")
            
            logger.info("数据库初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def backup(self) -> str:
        """数据库备份
        
        Returns:
            str: 备份文件路径
        """
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                DB_CONFIG['backup_path'],
                f"backup_{timestamp}.db"
            )
            
            # 关闭所有连接
            self.engine.dispose()
            
            # 复制数据库文件
            shutil.copy2(DB_CONFIG['db_path'], backup_file)
            
            logger.info(f"数据库备份成功: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"数据库备份失败: {str(e)}")
            raise
    
    def restore(self, backup_file: str) -> bool:
        """从备份文件恢复数据库
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            bool: 是否恢复成功
        """
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
            # 关闭所有连接
            self.engine.dispose()
            
            # 复制备份文件到数据库位置
            shutil.copy2(backup_file, DB_CONFIG['db_path'])
            
            logger.info(f"数据库恢复成功: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"数据库恢复失败: {str(e)}")
            return False
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """获取备份文件列表
        
        Returns:
            List[Dict[str, Any]]: 备份文件信息列表
        """
        try:
            backups = []
            for file in os.listdir(DB_CONFIG['backup_path']):
                if file.endswith('.db'):
                    file_path = os.path.join(DB_CONFIG['backup_path'], file)
                    backups.append({
                        'name': file,
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'created_at': datetime.fromtimestamp(
                            os.path.getctime(file_path)
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    })
            return sorted(backups, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"获取备份列表失败: {str(e)}")
            return []
    
    def delete_backup(self, backup_file: str) -> bool:
        """删除备份文件
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if os.path.exists(backup_file):
                os.remove(backup_file)
                logger.info(f"删除备份文件成功: {backup_file}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"删除备份文件失败: {str(e)}")
            return False
    
    def update_db_path(self, new_path: str) -> bool:
        """更新数据库路径
        
        Args:
            new_path: 新的数据库路径
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 检查新路径是否可写
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            # 关闭所有连接
            self.engine.dispose()
            
            # 如果新路径与原路径不同,复制数据库文件
            if new_path != DB_CONFIG['db_path']:
                shutil.copy2(DB_CONFIG['db_path'], new_path)
            
            # 更新配置
            DB_CONFIG['db_path'] = new_path
            
            # 重新创建引擎
            self.engine = create_engine(
                f"sqlite:///{new_path}",
                poolclass=QueuePool,
                pool_size=DB_CONFIG['max_connections'],
                pool_recycle=DB_CONFIG['pool_recycle'],
                echo=DB_CONFIG['echo']
            )
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            
            logger.info(f"数据库路径更新成功: {new_path}")
            return True
            
        except Exception as e:
            logger.error(f"数据库路径更新失败: {str(e)}")
            return False
    
    def execute(self, sql: str, params: tuple = None) -> Optional[List[Dict[str, Any]]]:
        """执行SQL语句"""
        try:
            # 创建数据库连接
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 执行SQL语句
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # 获取结果
            if sql.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
                return [dict(row) for row in result]
            else:
                conn.commit()
                return None
            
            # 关闭连接
            conn.close()
            
        except Exception as e:
            logger.error(f"执行SQL语句失败: {str(e)}")
            raise
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        try:
            sql = "SELECT * FROM users WHERE username = ?"
            result = self.execute(sql, (username,))
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            raise
    
    def create_user(self, username: str, password: str, salt: str, role: str) -> bool:
        """创建用户"""
        try:
            sql = """
                INSERT INTO users (username, password, salt, role, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """
            self.execute(sql, (username, password, salt, role))
            return True
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return False
    
    def update_user(self, username: str, **kwargs) -> bool:
        """更新用户信息"""
        try:
            # 构建更新语句
            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            sql = f"UPDATE users SET {set_clause}, updated_at = datetime('now') WHERE username = ?"
            
            # 执行更新
            params = list(kwargs.values()) + [username]
            self.execute(sql, tuple(params))
            return True
            
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """删除用户"""
        try:
            sql = "DELETE FROM users WHERE username = ?"
            self.execute(sql, (username,))
            return True
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return False
    
    def get_all_lives(self) -> List[Living]:
        """获取所有直播"""
        try:
            self.cursor.execute("SELECT * FROM livings ORDER BY created_at DESC")
            rows = self.cursor.fetchall()
            return [
                Living(
                    id=row[0],
                    name=row[1],
                    start_time=row[2],
                    end_time=row[3],
                    status=row[4],
                    created_at=row[5],
                    updated_at=row[6]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"获取直播列表失败: {str(e)}")
            raise
    
    def get_all_signs(self) -> List[Sign]:
        """获取所有签到记录"""
        try:
            self.cursor.execute("SELECT * FROM signs ORDER BY sign_time DESC")
            rows = self.cursor.fetchall()
            return [
                Sign(
                    id=row[0],
                    user_id=row[1],
                    live_id=row[2],
                    sign_time=row[3],
                    status=row[4],
                    created_at=row[5]
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"获取签到记录失败: {str(e)}")
            raise
    
    def get_live_stats(self) -> Dict[str, Any]:
        """获取直播统计数据"""
        try:
            stats = {}
            
            # 总直播数
            self.cursor.execute("SELECT COUNT(*) FROM livings")
            stats["total_lives"] = self.cursor.fetchone()[0]
            
            # 总观看人数
            self.cursor.execute("SELECT COUNT(DISTINCT user_id) FROM signs")
            stats["total_viewers"] = self.cursor.fetchone()[0]
            
            # 总签到人数
            self.cursor.execute("SELECT COUNT(*) FROM signs")
            stats["total_signs"] = self.cursor.fetchone()[0]
            
            # 平均观看时长
            self.cursor.execute("""
                SELECT AVG(
                    strftime('%s', end_time) - strftime('%s', start_time)
                ) / 60
                FROM livings
                WHERE status = 'ended'
            """)
            avg_duration = self.cursor.fetchone()[0]
            stats["avg_duration"] = round(avg_duration, 2) if avg_duration else 0
            
            return stats
        except Exception as e:
            logger.error(f"获取直播统计数据失败: {str(e)}")
            raise
    
    def get_living_by_id(self, living_id: int) -> LiveBooking:
        """根据ID获取直播信息
        
        Args:
            living_id: 直播ID
            
        Returns:
            LiveBooking: 直播信息
        """
        try:
            with self.get_session() as session:
                return session.query(LiveBooking).filter_by(id=living_id).first()
        except Exception as e:
            logger.error(f"获取直播信息失败: {str(e)}")
            raise
    
    def get_all_livings(self) -> List[LiveBooking]:
        """获取所有直播信息
        
        Returns:
            List[LiveBooking]: 直播信息列表
        """
        try:
            with self.get_session() as session:
                return session.query(LiveBooking).all()
        except Exception as e:
            logger.error(f"获取直播列表失败: {str(e)}")
            raise
    
    def get_all_sign_records(self) -> List[SignRecord]:
        """获取所有签到记录
        
        Returns:
            List[SignRecord]: 签到记录列表
        """
        try:
            with self.get_session() as session:
                return session.query(SignRecord).all()
        except Exception as e:
            logger.error(f"获取签到记录失败: {str(e)}")
            raise
    
    def get_live_rankings(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取直播排行数据
        
        Args:
            days: 统计天数
            
        Returns:
            List[Dict[str, Any]]: 排行数据
        """
        session = self.get_session()
        try:
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取直播排行
            rankings = session.query(
                Living.id,
                Living.title,
                func.count(WatchStat.id).label("watch_count"),
                func.count(SignRecord.id).label("sign_count")
            ).outerjoin(WatchStat).outerjoin(SignRecord).filter(
                Living.living_start >= start_date
            ).group_by(Living.id).order_by(
                func.count(WatchStat.id).desc()
            ).limit(10).all()
            
            return [
                {
                    "id": r.id,
                    "title": r.title,
                    "watch_count": r.watch_count,
                    "sign_count": r.sign_count
                }
                for r in rankings
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"获取直播排行数据失败: {str(e)}")
            return []
        finally:
            session.close() 