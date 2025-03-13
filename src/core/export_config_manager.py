from datetime import datetime
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.models.export_config import ExportConfig

logger = get_logger(__name__)

class ExportConfigManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def save_config(self, user_id, config_name, config_type, selected_fields, filter_conditions=None, sort_conditions=None):
        """保存导出配置
        
        Args:
            user_id: 用户ID
            config_name: 配置名称
            config_type: 配置类型
            selected_fields: 选中的字段列表
            filter_conditions: 筛选条件
            sort_conditions: 排序条件
            
        Returns:
            bool: 是否保存成功
        """
        session = self.db_manager.get_session()
        try:
            config = ExportConfig(
                user_id=user_id,
                config_name=config_name,
                config_type=config_type,
                selected_fields=selected_fields,
                filter_conditions=filter_conditions,
                sort_conditions=sort_conditions
            )
            session.add(config)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"保存导出配置失败: {str(e)}")
            return False
        finally:
            session.close()
            
    def get_user_configs(self, user_id, config_type=None):
        """获取用户的导出配置列表
        
        Args:
            user_id: 用户ID
            config_type: 配置类型（可选）
            
        Returns:
            list: 配置列表
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(ExportConfig).filter_by(user_id=user_id)
            if config_type:
                query = query.filter_by(config_type=config_type)
            return query.all()
        except Exception as e:
            logger.error(f"获取导出配置失败: {str(e)}")
            return []
        finally:
            session.close()
            
    def get_config(self, user_id, config_name, config_type):
        """获取指定的导出配置
        
        Args:
            user_id: 用户ID
            config_name: 配置名称
            config_type: 配置类型
            
        Returns:
            ExportConfig: 配置对象
        """
        session = self.db_manager.get_session()
        try:
            return session.query(ExportConfig).filter_by(
                user_id=user_id,
                config_name=config_name,
                config_type=config_type
            ).first()
        except Exception as e:
            logger.error(f"获取导出配置失败: {str(e)}")
            return None
        finally:
            session.close()
            
    def update_config(self, user_id, config_name, config_type, selected_fields, filter_conditions=None, sort_conditions=None):
        """更新导出配置
        
        Args:
            user_id: 用户ID
            config_name: 配置名称
            config_type: 配置类型
            selected_fields: 选中的字段列表
            filter_conditions: 筛选条件
            sort_conditions: 排序条件
            
        Returns:
            bool: 是否更新成功
        """
        session = self.db_manager.get_session()
        try:
            config = self.get_config(user_id, config_name, config_type)
            if config:
                config.selected_fields = selected_fields
                config.filter_conditions = filter_conditions
                config.sort_conditions = sort_conditions
                config.updated_at = datetime.now()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"更新导出配置失败: {str(e)}")
            return False
        finally:
            session.close()
            
    def delete_config(self, user_id, config_name, config_type):
        """删除导出配置
        
        Args:
            user_id: 用户ID
            config_name: 配置名称
            config_type: 配置类型
            
        Returns:
            bool: 是否删除成功
        """
        session = self.db_manager.get_session()
        try:
            config = self.get_config(user_id, config_name, config_type)
            if config:
                session.delete(config)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除导出配置失败: {str(e)}")
            return False
        finally:
            session.close()
            
    def get_available_fields(self, config_type):
        """获取可用的导出字段列表
        
        Args:
            config_type: 配置类型
            
        Returns:
            list: 字段列表
        """
        # 根据不同的配置类型返回对应的可用字段
        field_maps = {
            "viewer_stats": [
                {"name": "user_name", "label": "用户名"},
                {"name": "department", "label": "部门"},
                {"name": "total_watch_time", "label": "观看时长"},
                {"name": "watch_percentage", "label": "观看比例"},
                {"name": "is_signed", "label": "是否签到"},
                {"name": "sign_count", "label": "签到次数"},
                {"name": "comment_count", "label": "评论次数"},
                {"name": "is_mic", "label": "是否连麦"},
                {"name": "mic_duration", "label": "连麦时长"},
                {"name": "invitor_name", "label": "邀请人"}
            ],
            "sign_records": [
                {"name": "user_name", "label": "用户名"},
                {"name": "department", "label": "部门"},
                {"name": "sign_time", "label": "签到时间"},
                {"name": "sign_count", "label": "签到次数"}
            ],
            "live_details": [
                {"name": "living_id", "label": "直播ID"},
                {"name": "title", "label": "直播标题"},
                {"name": "start_time", "label": "开始时间"},
                {"name": "end_time", "label": "结束时间"},
                {"name": "status", "label": "状态"},
                {"name": "creator_name", "label": "创建人"}
            ]
        }
        return field_maps.get(config_type, []) 