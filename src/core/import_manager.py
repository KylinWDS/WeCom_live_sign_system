import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.models.live_booking import LiveBooking
from src.models.live_viewer import LiveViewer, UserSource
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ImportManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def import_live_data(self, file_path: str) -> Dict[str, Any]:
        """导入直播数据
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            Dict[str, Any]: 导入结果统计
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证必要字段
            required_fields = ["标题", "主播ID", "主播姓名", "开始时间", "结束时间"]
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                raise ValueError(f"Excel文件缺少必要字段: {', '.join(missing_fields)}")
                
            # 统计数据
            total_count = len(df)
            success_count = 0
            error_count = 0
            error_records = []
            
            # 导入数据
            with self.db_manager.get_session() as session:
                for _, row in df.iterrows():
                    try:
                        # 创建直播预约
                        live_booking = LiveBooking(
                            title=str(row["标题"]),
                            anchor_id=str(row["主播ID"]),
                            anchor_name=str(row["主播姓名"]),
                            start_time=row["开始时间"],
                            end_time=row["结束时间"],
                            status="未开始",
                            creator_id=str(row.get("创建者ID", "")),
                            creator_name=str(row.get("创建者姓名", ""))
                        )
                        
                        session.add(live_booking)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_records.append({
                            "标题": row["标题"],
                            "主播ID": row["主播ID"],
                            "错误信息": str(e)
                        })
                        
                session.commit()
                
            return {
                "total": total_count,
                "success": success_count,
                "error": error_count,
                "error_records": error_records
            }
            
        except Exception as e:
            logger.error(f"导入直播数据失败: {str(e)}")
            raise
            
    def import_viewer_data(self, file_path: str, living_id: int) -> Dict[str, Any]:
        """导入观众数据
        
        Args:
            file_path: Excel文件路径
            living_id: 直播ID
            
        Returns:
            Dict[str, Any]: 导入结果统计
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证必要字段
            required_fields = ["用户ID", "用户名", "观看时长"]
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                raise ValueError(f"Excel文件缺少必要字段: {', '.join(missing_fields)}")
                
            # 统计数据
            total_count = len(df)
            success_count = 0
            error_count = 0
            error_records = []
            
            # 导入数据
            with self.db_manager.get_session() as session:
                for _, row in df.iterrows():
                    try:
                        # 创建观众记录
                        viewer = LiveViewer(
                            living_id=living_id,
                            userid=str(row["用户ID"]),
                            name=str(row["用户名"]),
                            user_source=UserSource.INTERNAL if row.get("用户类型", 1) == 2 else UserSource.EXTERNAL,
                            user_type=int(row.get("用户类型", 1)),
                            department=str(row.get("部门", "")),
                            watch_time=int(float(row["观看时长"]))
                        )
                        
                        session.add(viewer)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_records.append({
                            "用户ID": row["用户ID"],
                            "用户名": row["用户名"],
                            "错误信息": str(e)
                        })
                        
                session.commit()
                
            return {
                "total": total_count,
                "success": success_count,
                "error": error_count,
                "error_records": error_records
            }
            
        except Exception as e:
            logger.error(f"导入观众数据失败: {str(e)}")
            raise
            
    def import_sign_data(self, file_path: str, living_id: int) -> Dict[str, Any]:
        """导入签到数据
        
        Args:
            file_path: Excel文件路径
            living_id: 直播ID
            
        Returns:
            Dict[str, Any]: 导入结果统计
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证必要字段
            required_fields = ["用户ID", "用户名", "签到时间"]
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                raise ValueError(f"Excel文件缺少必要字段: {', '.join(missing_fields)}")
                
            # 统计数据
            total_count = len(df)
            success_count = 0
            error_count = 0
            error_records = []
            
            # 导入数据
            with self.db_manager.get_session() as session:
                for _, row in df.iterrows():
                    try:
                        # 创建签到记录
                        live_viewer = LiveViewer(
                            living_id=living_id,
                            userid=str(row["用户ID"]),
                            name=str(row["用户名"]),
                            user_source=UserSource.INTERNAL if row.get("用户类型", 1) == 2 else UserSource.EXTERNAL,
                            user_type=int(row.get("用户类型", 1)),
                            is_signed=True,
                            sign_time=row["签到时间"],
                            sign_type="import"
                        )
                        
                        session.add(live_viewer)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_records.append({
                            "用户ID": row["用户ID"],
                            "用户名": row["用户名"],
                            "错误信息": str(e)
                        })
                        
                session.commit()
                
            return {
                "total": total_count,
                "success": success_count,
                "error": error_count,
                "error_records": error_records
            }
            
        except Exception as e:
            logger.error(f"导入签到数据失败: {str(e)}")
            raise 