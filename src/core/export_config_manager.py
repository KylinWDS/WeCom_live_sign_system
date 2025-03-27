from datetime import datetime
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
# from src.models.export_config import ExportConfig  -- 已删除

logger = get_logger(__name__)

class ExportConfigManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        logger.info("导出配置管理器已初始化，但ExportConfig模型已移除")
        
    def save_config(self, user_id, config_name, config_type, selected_fields, filter_conditions=None, sort_conditions=None):
        """保存导出配置（已弃用）
        
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
        logger.warning("试图保存导出配置，但ExportConfig模型已移除")
        logger.debug(f"配置信息: {user_id}, {config_name}, {config_type}, {len(selected_fields) if selected_fields else 0}个字段")
        return False
            
    def get_user_configs(self, user_id, config_type=None):
        """获取用户的导出配置列表（已弃用）
        
        Args:
            user_id: 用户ID
            config_type: 配置类型（可选）
            
        Returns:
            list: 配置列表
        """
        logger.warning("试图获取导出配置列表，但ExportConfig模型已移除")
        return []
            
    def get_config(self, user_id, config_name, config_type):
        """获取指定的导出配置（已弃用）
        
        Args:
            user_id: 用户ID
            config_name: 配置名称
            config_type: 配置类型
            
        Returns:
            ExportConfig: 配置对象
        """
        logger.warning("试图获取导出配置，但ExportConfig模型已移除")
        return None
            
    def update_config(self, user_id, config_name, config_type, selected_fields, filter_conditions=None, sort_conditions=None):
        """更新导出配置（已弃用）
        
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
        logger.warning("试图更新导出配置，但ExportConfig模型已移除")
        return False
            
    def delete_config(self, user_id, config_name, config_type):
        """删除导出配置（已弃用）
        
        Args:
            user_id: 用户ID
            config_name: 配置名称
            config_type: 配置类型
            
        Returns:
            bool: 是否删除成功
        """
        logger.warning("试图删除导出配置，但ExportConfig模型已移除")
        return False
            
    def get_available_fields(self, config_type):
        """获取可用的导出字段列表
        
        Args:
            config_type: 配置类型
            
        Returns:
            list: 字段列表
        """
        # 这个方法可以保留，因为它不依赖于ExportConfig模型
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