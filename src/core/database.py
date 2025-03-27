import sqlite3
import os
import shutil
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import json
import threading
from src.utils.logger import get_logger
from src.models.base import Base
from src.models import User, UserRole
from src.models.living import Living, WatchStat
from src.models.live_booking import LiveBooking
from src.models.live_viewer import LiveViewer
from src.models.sign_record import SignRecord
from src.models.sign import Sign
from contextlib import contextmanager
from src.config.database import get_default_paths
from sqlalchemy import inspect

logger = get_logger(__name__)

def get_db_connection_config() -> Dict[str, Any]:
    """获取数据库连接参数配置
    注意：不包含路径配置，路径配置由配置管理器提供
    """
    return {
        "type": "sqlite",
        "pool_size": 5,
        "timeout": 30,
        "echo": False,
        "pool_recycle": 3600,
        "pool_pre_ping": True
    }

class DatabaseManager:
    """数据库管理器"""
    
    # 单例模式支持
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        # 防止重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.engine = None
        self.Session = None
        self.initialized = False
        self.db_config = None
        
        # 添加会话计数和线程锁
        self._active_sessions = 0
        self._session_lock = threading.Lock()
        
        self._initialized = True
        
    def initialize(self, db_config: Dict[str, Any]) -> bool:
        """初始化数据库
        
        Args:
            db_config: 数据库配置
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 合并默认配置和用户配置
            default_config = get_db_connection_config()
            self.db_config = {**default_config, **db_config}  # 用户配置会覆盖默认配置
            
            # 获取数据库路径
            db_path = self.db_config.get("path")
            if not db_path:
                logger.error("数据库路径未配置")
                return False
                
            logger.info(f"数据库路径: {db_path}")
            
            # 确保数据库目录存在
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                logger.info(f"创建数据库目录: {db_dir}")
                os.makedirs(db_dir, exist_ok=True)
            
            # 确保备份路径存在于配置中
            backup_path = self.db_config.get("backup_path")
            if not backup_path:
                logger.error("备份路径未配置")
                return False
                
            logger.info(f"备份路径: {backup_path}")
            
            # 确保备份目录存在
            if not os.path.exists(backup_path):
                logger.info(f"创建备份目录: {backup_path}")
                os.makedirs(backup_path, exist_ok=True)
            
            # 创建数据库引擎
            logger.info("创建数据库引擎...")
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                poolclass=QueuePool,
                pool_size=self.db_config.get("pool_size", 5),
                pool_recycle=self.db_config.get("pool_recycle", 3600),
                pool_timeout=self.db_config.get("timeout", 30),
                echo=self.db_config.get("echo", False)
            )
            
            # 创建会话工厂 - 兼容SQLAlchemy 2.0的方式
            logger.info("创建会话工厂...")
            self.Session = sessionmaker(
                autocommit=False,
                autoflush=True,
                expire_on_commit=True,
                class_=Session,
                bind=self.engine
            )
            
            # 标记为已初始化
            self.initialized = True
            logger.info(f"数据库管理器初始化成功: {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"初始化数据库失败: {str(e)}")
            return False
            
    def create_tables(self) -> bool:
        """创建数据库表
        
        Returns:
            bool: 是否成功创建表
        """
        try:
            if not self.initialized:
                logger.error("数据库未初始化")
                return False
            
            # 导入所有模型类以确保Base.metadata包含所有表定义
            from src.models.base import Base
            from src.models.user import User
            from src.models.live_booking import LiveBooking
            from src.models.live_viewer import LiveViewer
            from src.models.sign_record import SignRecord
            from src.models.living import Living
            from src.models.watch_stat import WatchStat
            from src.models.ip_record import IPRecord
            from src.models.setting import Setting
            from src.models.corporation import Corporation
            from src.models.config_change import ConfigChange
            from src.models.operation_log import OperationLog
            
            # 动态获取所有模型表
            # 使用Base.metadata.tables获取所有注册的表
            tables = Base.metadata.tables
            
            # 检查表是否已存在
            inspector = inspect(self.engine)
            created_tables = inspector.get_table_names()
            
            # 创建未存在的表
            for table_name, table_obj in tables.items():
                if table_name not in created_tables:
                    table_obj.create(self.engine, checkfirst=True)
                    logger.info(f"创建表: {table_name}")
            
            # 再次检查表是否都已创建
            created_tables = inspector.get_table_names()
            if set(tables.keys()).issubset(set(created_tables)):
                return True
            else:
                missing_tables = set(tables.keys()) - set(created_tables)
                logger.error(f"部分表未创建成功: {', '.join(missing_tables)}")
                return False
            
        except Exception as e:
            logger.error(f"创建数据库表失败: {str(e)}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
    
    def init_db(self, force_recreate: bool = False):
        """初始化数据库
        
        Args:
            force_recreate: 是否强制重建表，默认为False。
                          首次运行时应该设置为True以确保表结构正确。
        """
        try:
            # 导入所有模型类，确保它们被注册到Base.metadata中
            from src.models.user import User, UserRole
            from src.models.living import Living, WatchStat
            from src.models.live_booking import LiveBooking
            from src.models.live_viewer import LiveViewer
            from src.models.sign_record import SignRecord
            from src.models.sign import Sign
            
            if force_recreate:
                # 删除所有表
                logger.info("正在重建数据库表...")
                Base.metadata.drop_all(bind=self.engine)
                Base.metadata.create_all(bind=self.engine)
            else:
                # 仅创建不存在的表
                logger.info("正在检查并创建缺失的数据库表...")
                Base.metadata.create_all(bind=self.engine)
            
            # 创建默认的root-admin用户
            session = self.Session()
            try:
                # 检查是否已存在root-admin用户
                existing_user = session.query(User).filter_by(login_name="root-admin").first()
                if not existing_user:
                    # 创建root-admin用户
                    root_admin = User(
                        login_name="root-admin",
                        name="超级管理员",
                        role=UserRole.ROOT_ADMIN.value,  # 使用枚举值的字符串表示
                        is_active=True,
                        is_admin=True,  # 设置为管理员
                        password_hash=None,  # 初始密码为空，等待配置向导设置
                        salt=None,  # 初始盐值为空，等待配置向导设置
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    session.add(root_admin)
                    session.commit()
                    logger.info("创建默认root-admin用户成功")
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
            
            logger.info("数据库初始化成功")
            
        except Exception as e:
            logger.error(f"初始化数据库失败: {str(e)}")
            raise
    
    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器
        
        如果数据库未初始化，将抛出RuntimeError异常
        
        Yields:
            Session: 数据库会话
        
        Raises:
            RuntimeError: 数据库未初始化时抛出
        """
        if not self.initialized:
            raise RuntimeError("数据库未初始化")
            
        session = self.Session()
        
        # 为Session添加query方法以兼容SQLAlchemy 1.x API
        if not hasattr(session, 'query'):
            from sqlalchemy.orm import Query
            # 正确实现：将entities中的元素展开后传递给Query
            session.query = lambda *entities, **kwargs: Query(entities[0] if len(entities) == 1 else entities, session=session)
        
        # 增加活跃会话计数
        with self._session_lock:
            self._active_sessions += 1
            
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"会话操作出错: {str(e)}")
            raise
        finally:
            session.close()
            # 减少活跃会话计数
            with self._session_lock:
                self._active_sessions -= 1
    
    def get_active_sessions_count(self):
        """获取当前活跃会话数量
        
        Returns:
            int: 活跃会话数量
        """
        with self._session_lock:
            return self._active_sessions
    
    def merge_user(self, session, user_obj):
        """安全地合并用户对象到当前会话
        
        Args:
            session: 数据库会话
            user_obj: 用户对象或用户ID
            
        Returns:
            User: 合并后的用户对象或None
        """
        if user_obj is None:
            return None
            
        try:
            from ..models.user import User
            
            # 如果传入的是ID，则查询用户对象
            if isinstance(user_obj, int):
                return session.query(User).get(user_obj)
            
            # 否则合并到当前会话
            return session.merge(user_obj)
        except Exception as e:
            logger.error(f"合并用户对象失败: {str(e)}")
            return None
    
    def backup(self) -> str:
        """数据库备份
        
        Returns:
            str: 备份文件路径
        """
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                self.db_config['backup_path'],
                f"backup_{timestamp}.db"
            )
            
            # 关闭所有连接
            self.engine.dispose()
            
            # 复制数据库文件
            shutil.copy2(self.db_config['path'], backup_file)
            
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
            shutil.copy2(backup_file, self.db_config['path'])
            
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
            for file in os.listdir(self.db_config['backup_path']):
                if file.endswith('.db'):
                    file_path = os.path.join(self.db_config['backup_path'], file)
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
            if new_path != self.db_config['path']:
                shutil.copy2(self.db_config['path'], new_path)
            
            # 更新配置
            self.db_config['path'] = new_path
            
            # 重新创建引擎
            self.engine = create_engine(
                f"sqlite:///{new_path}",
                poolclass=QueuePool,
                pool_size=self.db_config['max_connections'],
                pool_recycle=self.db_config['pool_recycle'],
                echo=self.db_config['echo']
            )
            self.Session = sessionmaker(bind=self.engine)
            
            logger.info(f"数据库路径更新成功: {new_path}")
            return True
            
        except Exception as e:
            logger.error(f"数据库路径更新失败: {str(e)}")
            return False
    
    def execute(self, sql: str, params: tuple = None) -> Optional[List[Dict[str, Any]]]:
        """执行SQL语句"""
        try:
            # 创建数据库连接
            conn = sqlite3.connect(self.db_config['path'])
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
            sql = "SELECT * FROM users WHERE login_name = ?"
            result = self.execute(sql, (username,))
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            raise
    
    def create_user(self, username: str, password: str, salt: str, role: str) -> bool:
        """创建用户"""
        try:
            sql = """
                INSERT INTO users (login_name, name, password_hash, salt, role, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """
            self.execute(sql, (username, username, password, salt, role))
            return True
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return False
    
    def update_user(self, username: str, **kwargs) -> bool:
        """更新用户信息"""
        try:
            # 构建更新语句
            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            sql = f"UPDATE users SET {set_clause}, updated_at = datetime('now') WHERE login_name = ?"
            
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
            sql = "DELETE FROM users WHERE login_name = ?"
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
    
    def get_live_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取直播统计数据
        
        Args:
            days: 统计的天数，默认为30天
            
        Returns:
            Dict[str, Any]: 统计结果
        """
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
    
    def query_one(self, sql: str, params: tuple = None) -> Optional[tuple]:
        """执行SQL查询并返回第一条记录
        
        Args:
            sql: SQL语句
            params: 查询参数
            
        Returns:
            Optional[tuple]: 查询结果
        """
        try:
            # 创建数据库连接
            conn = sqlite3.connect(self.db_config["path"])
            cursor = conn.cursor()
            
            # 执行SQL语句
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # 获取结果
            result = cursor.fetchone()
            
            # 关闭连接
            conn.close()
            
            return result
            
        except Exception as e:
            logger.error(f"执行SQL查询失败: {str(e)}")
            raise
    
    def get_agent_id_by_user(self, user_id: str) -> int:
        """根据用户ID获取对应的企业微信应用ID
        
        Args:
            user_id: 用户ID，应该是login_name
            
        Returns:
            int: 企业微信应用ID，如果获取失败则返回默认值
        """
        try:
            with self.get_session() as session:
                # 使用login_name查找用户
                from src.models.user import User
                user = session.query(User).filter_by(login_name=user_id).first()
                
                # 如果找到了用户，且用户有agentid
                if user and user.agentid:
                    try:
                        return int(user.agentid)
                    except (ValueError, TypeError):
                        logger.warning(f"用户 {user_id} 的agentid '{user.agentid}'不是有效的整数")
                
                # 如果找到了用户，且用户有corpid，则尝试获取对应企业的agentid
                if user and user.corpid:
                    from src.models.corporation import Corporation
                    corp = session.query(Corporation).filter_by(corp_id=user.corpid).first()
                    if corp and corp.agent_id:
                        try:
                            return int(corp.agent_id)
                        except (ValueError, TypeError):
                            logger.warning(f"企业 {user.corpid} 的agent_id '{corp.agent_id}'不是有效的整数")
                
                # 如果找到了用户，且用户有corpname，则尝试获取对应企业的agentid
                if user and user.corpname:
                    from src.models.corporation import Corporation
                    corp = session.query(Corporation).filter_by(name=user.corpname).first()
                    if corp and corp.agent_id:
                        try:
                            return int(corp.agent_id)
                        except (ValueError, TypeError):
                            logger.warning(f"企业 {user.corpname} 的agent_id '{corp.agent_id}'不是有效的整数")
                
                # 如果以上方法都失败，则获取当前激活的企业的agentid
                from src.models.corporation import Corporation
                corp = session.query(Corporation).filter_by(status=1).first()
                if corp and corp.agent_id:
                    try:
                        return int(corp.agent_id)
                    except (ValueError, TypeError):
                        logger.warning(f"当前激活企业的agent_id '{corp.agent_id}'不是有效的整数")
                
                # 如果所有方法都失败，返回默认值
                return 1000002  # 默认企业微信应用ID
        except Exception as e:
            logger.error(f"获取用户对应的企业微信应用ID失败: {str(e)}")
            return 1000002  # 出错时返回默认ID