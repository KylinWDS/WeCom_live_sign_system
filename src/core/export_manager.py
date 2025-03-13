import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.models.live_booking import LiveBooking
from src.models.live_viewer import LiveViewer
from src.models.sign_record import SignRecord
from src.core.viewer_stats_manager import ViewerStatsManager
from src.utils.cache import Cache
import matplotlib.pyplot as plt
import os
from PIL import Image

logger = get_logger(__name__)
cache = Cache()

class ExportManager:
    """导出管理器"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.viewer_stats_manager = ViewerStatsManager(db_manager)
        self.chunk_size = 5000  # 分块大小
        
    async def export_live_data(self, living_id: str, file_path: str, include_charts: bool = True):
        """导出直播数据
        
        Args:
            living_id: 直播ID
            file_path: 导出文件路径
            include_charts: 是否包含图表
        """
        try:
            # 获取直播数据
            with self.db_manager.get_session() as session:
                live = session.query(LiveBooking).filter_by(livingid=living_id).first()
                if not live:
                    raise Exception("直播不存在")
                    
                # 获取观看记录
                viewers = session.query(LiveViewer).filter_by(living_id=living_id).all()
                
                # 获取签到记录
                sign_records = session.query(SignRecord).filter_by(living_id=living_id).all()
                
            # 创建Excel写入器
            with pd.ExcelWriter(file_path) as writer:
                # 导出基本信息
                self._export_basic_info(live, writer)
                
                # 导出观看记录
                self._export_viewer_data(viewers, writer)
                
                # 导出签到记录
                self._export_sign_data(sign_records, writer)
                
                # 导出图表
                if include_charts:
                    self._export_charts(live, viewers, sign_records, writer)
                    
            return True
            
        except Exception as e:
            logger.error(f"导出直播数据失败: {str(e)}")
            raise
            
    def _export_basic_info(self, live: LiveBooking, writer: pd.ExcelWriter):
        """导出基本信息"""
        data = {
            "直播主题": [live.theme],
            "开始时间": [live.living_start.strftime("%Y-%m-%d %H:%M:%S")],
            "结束时间": [(live.living_start + timedelta(seconds=live.living_duration)).strftime("%Y-%m-%d %H:%M:%S")],
            "主播ID": [live.anchor_userid],
            "直播类型": [{
                0: "通用直播",
                1: "小班课",
                2: "大班课",
                3: "企业培训",
                4: "活动直播"
            }.get(live.type, "未知")],
            "状态": [{
                0: "预约中",
                1: "直播中",
                2: "已结束",
                3: "已过期",
                4: "已取消"
            }.get(live.status, "未知")],
            "观看人数": [live.viewer_num or 0],
            "签到人数": [live.sign_count or 0]
        }
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="基本信息", index=False)
        
    def _export_viewer_data(self, viewers: List[LiveViewer], writer: pd.ExcelWriter):
        """导出观看记录"""
        data = []
        for viewer in viewers:
            data.append({
                "用户ID": viewer.user_id,
                "用户名称": viewer.user_name or "",
                "用户类型": "企业成员" if viewer.user_type == 1 else "外部用户",
                "首次进入时间": viewer.first_enter_time.strftime("%Y-%m-%d %H:%M:%S") if viewer.first_enter_time else "",
                "最后离开时间": viewer.last_leave_time.strftime("%Y-%m-%d %H:%M:%S") if viewer.last_leave_time else "",
                "观看时长(秒)": viewer.total_watch_time,
                "观看时长占比(%)": f"{viewer.watch_percentage:.2f}",
                "是否评论": "是" if viewer.is_comment else "否",
                "评论次数": viewer.comment_count,
                "是否连麦": "是" if viewer.is_mic else "否",
                "连麦时长(秒)": viewer.mic_duration,
                "邀请人ID": viewer.invitor_id or "",
                "邀请人名称": viewer.invitor_name or "",
                "邀请人类型": "企业成员" if viewer.invitor_type == 1 else "外部用户"
            })
            
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="观看记录", index=False)
        
    def _export_sign_data(self, sign_records: List[SignRecord], writer: pd.ExcelWriter):
        """导出签到记录"""
        data = []
        for record in sign_records:
            data.append({
                "用户ID": record.user_id,
                "用户名称": record.user_name or "",
                "签到时间": record.sign_time.strftime("%Y-%m-%d %H:%M:%S"),
                "签到类型": "正常签到" if record.sign_type == 1 else "补签",
                "签到状态": "成功" if record.status == 1 else "失败",
                "备注": record.remark or ""
            })
            
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="签到记录", index=False)
        
    def _export_charts(self, live: LiveBooking, viewers: List[LiveViewer], 
                      sign_records: List[SignRecord], writer: pd.ExcelWriter):
        """导出图表"""
        try:
            # 创建观看人数趋势图
            self._create_viewer_trend_chart(live, viewers, writer)
            
            # 创建用户类型分布图
            self._create_user_type_chart(viewers, writer)
            
            # 创建签到时间分布图
            self._create_sign_time_chart(sign_records, writer)
            
            # 创建观看时长分布图
            self._create_watch_time_chart(viewers, writer)
            
        except Exception as e:
            logger.error(f"创建图表失败: {str(e)}")
            
    def _create_viewer_trend_chart(self, live: LiveBooking, viewers: List[LiveViewer], writer: pd.ExcelWriter):
        """创建观看人数趋势图"""
        try:
            # 按时间统计观看人数
            time_slots = {}
            for viewer in viewers:
                if not viewer.first_enter_time or not viewer.last_leave_time:
                    continue
                    
                current_time = viewer.first_enter_time
                while current_time <= viewer.last_leave_time:
                    slot_key = current_time.strftime("%H:%M")
                    time_slots[slot_key] = time_slots.get(slot_key, 0) + 1
                    current_time += timedelta(minutes=5)
                    
            # 创建图表
            plt.figure(figsize=(12, 6))
            plt.plot(list(time_slots.keys()), list(time_slots.values()))
            plt.title("观看人数趋势")
            plt.xlabel("时间")
            plt.ylabel("观看人数")
            plt.xticks(rotation=45)
            plt.grid(True)
            
            # 保存图表
            plt.savefig("viewer_trend.png")
            plt.close()
            
            # 插入Excel
            img = Image.open("viewer_trend.png")
            img.save("viewer_trend.png", "PNG")
            worksheet = writer.sheets["基本信息"]
            worksheet.insert_image("A12", "viewer_trend.png")
            
            # 删除临时文件
            os.remove("viewer_trend.png")
            
        except Exception as e:
            logger.error(f"创建观看人数趋势图失败: {str(e)}")
            
    def _create_user_type_chart(self, viewers: List[LiveViewer], writer: pd.ExcelWriter):
        """创建用户类型分布图"""
        try:
            # 统计用户类型
            internal_count = len([v for v in viewers if v.user_type == 1])
            external_count = len([v for v in viewers if v.user_type == 2])
            
            # 创建饼图
            plt.figure(figsize=(8, 8))
            plt.pie([internal_count, external_count], 
                   labels=["企业成员", "外部用户"],
                   autopct="%1.1f%%")
            plt.title("用户类型分布")
            
            # 保存图表
            plt.savefig("user_type.png")
            plt.close()
            
            # 插入Excel
            img = Image.open("user_type.png")
            img.save("user_type.png", "PNG")
            worksheet = writer.sheets["基本信息"]
            worksheet.insert_image("A25", "user_type.png")
            
            # 删除临时文件
            os.remove("user_type.png")
            
        except Exception as e:
            logger.error(f"创建用户类型分布图失败: {str(e)}")
            
    def _create_sign_time_chart(self, sign_records: List[SignRecord], writer: pd.ExcelWriter):
        """创建签到时间分布图"""
        try:
            # 按小时统计签到人数
            hour_slots = {}
            for record in sign_records:
                hour = record.sign_time.hour
                hour_slots[hour] = hour_slots.get(hour, 0) + 1
                
            # 创建柱状图
            plt.figure(figsize=(10, 6))
            plt.bar(list(hour_slots.keys()), list(hour_slots.values()))
            plt.title("签到时间分布")
            plt.xlabel("小时")
            plt.ylabel("签到人数")
            plt.grid(True)
            
            # 保存图表
            plt.savefig("sign_time.png")
            plt.close()
            
            # 插入Excel
            img = Image.open("sign_time.png")
            img.save("sign_time.png", "PNG")
            worksheet = writer.sheets["签到记录"]
            worksheet.insert_image("A12", "sign_time.png")
            
            # 删除临时文件
            os.remove("sign_time.png")
            
        except Exception as e:
            logger.error(f"创建签到时间分布图失败: {str(e)}")
            
    def _create_watch_time_chart(self, viewers: List[LiveViewer], writer: pd.ExcelWriter):
        """创建观看时长分布图"""
        try:
            # 统计观看时长分布
            time_ranges = {
                "0-30分钟": 0,
                "30-60分钟": 0,
                "60-90分钟": 0,
                "90分钟以上": 0
            }
            
            for viewer in viewers:
                minutes = viewer.total_watch_time / 60
                if minutes <= 30:
                    time_ranges["0-30分钟"] += 1
                elif minutes <= 60:
                    time_ranges["30-60分钟"] += 1
                elif minutes <= 90:
                    time_ranges["60-90分钟"] += 1
                else:
                    time_ranges["90分钟以上"] += 1
                    
            # 创建柱状图
            plt.figure(figsize=(10, 6))
            plt.bar(list(time_ranges.keys()), list(time_ranges.values()))
            plt.title("观看时长分布")
            plt.xlabel("时长范围")
            plt.ylabel("人数")
            plt.grid(True)
            
            # 保存图表
            plt.savefig("watch_time.png")
            plt.close()
            
            # 插入Excel
            img = Image.open("watch_time.png")
            img.save("watch_time.png", "PNG")
            worksheet = writer.sheets["观看记录"]
            worksheet.insert_image("A12", "watch_time.png")
            
            # 删除临时文件
            os.remove("watch_time.png")
            
        except Exception as e:
            logger.error(f"创建观看时长分布图失败: {str(e)}")
            
    def export_charts(self, living_id: str) -> List[str]:
        """导出数据可视化图表
        
        Args:
            living_id: 直播ID
            
        Returns:
            List[str]: 图表文件路径列表
        """
        try:
            # 获取统计数据
            from core.stats_manager import StatsManager
            stats_manager = StatsManager(self.db_manager)
            stats = stats_manager.get_live_stats(living_id)
            profile = stats_manager.get_user_profile(living_id)
            
            # 生成图表
            chart_files = []
            
            # 1. 观看人数趋势图
            self._create_viewer_trend_chart(living_id, stats)
            chart_files.append(f"viewer_trend_{living_id}.png")
            
            # 2. 用户画像图
            self._create_user_profile_chart(living_id, profile)
            chart_files.append(f"user_profile_{living_id}.png")
            
            # 3. 签到统计图
            self._create_sign_stats_chart(living_id, stats)
            chart_files.append(f"sign_stats_{living_id}.png")
            
            return chart_files
            
        except Exception as e:
            logger.error(f"导出图表失败: {str(e)}")
            return []
            
    def _create_user_profile_chart(self, living_id: str, profile: Dict):
        """创建用户画像图"""
        try:
            # 准备数据
            labels = ["内部用户", "外部用户"]
            sizes = [
                profile["viewer_stats"]["internal_viewers"],
                profile["viewer_stats"]["external_viewers"]
            ]
            
            # 创建饼图
            plt.figure(figsize=(8, 8))
            plt.pie(sizes, labels=labels, autopct="%1.1f%%")
            plt.title("用户类型分布")
            
            # 保存图表
            plt.savefig(f"user_profile_{living_id}.png")
            plt.close()
            
        except Exception as e:
            logger.error(f"创建用户画像图失败: {str(e)}")
            
    def _create_sign_stats_chart(self, living_id: str, stats: Dict):
        """创建签到统计图"""
        try:
            # 准备数据
            labels = ["正常签到", "补签"]
            sizes = [
                stats["sign_stats"]["normal_signs"],
                stats["sign_stats"]["makeup_signs"]
            ]
            
            # 创建饼图
            plt.figure(figsize=(8, 8))
            plt.pie(sizes, labels=labels, autopct="%1.1f%%")
            plt.title("签到类型分布")
            
            # 保存图表
            plt.savefig(f"sign_stats_{living_id}.png")
            plt.close()
            
        except Exception as e:
            logger.error(f"创建签到统计图失败: {str(e)}")
            
    def export_sign_data(self, living_id: int, selected_fields: List[str]) -> pd.DataFrame:
        """导出签到数据
        
        Args:
            living_id: 直播ID
            selected_fields: 选中的字段列表
            
        Returns:
            pd.DataFrame: 导出的数据
        """
        try:
            with self.db_manager.get_session() as session:
                # 获取签到记录
                sign_records = session.query(SignRecord).filter_by(
                    living_id=living_id
                ).all()
                
                # 构建数据
                data = []
                for record in sign_records:
                    record_data = {
                        "直播ID": record.living_id,
                        "用户ID": record.user_id,
                        "用户名": record.user_name,
                        "签到时间": record.sign_time,
                        "状态": record.status,
                        "创建时间": record.created_at,
                        "更新时间": record.updated_at
                    }
                    data.append({k: v for k, v in record_data.items() if k in selected_fields})
                    
                return pd.DataFrame(data)
                
        except Exception as e:
            logger.error(f"导出签到数据失败: {str(e)}")
            raise
            
    def export_user_analysis(self, living_id: int, selected_fields: List[str]) -> pd.DataFrame:
        """导出用户分析数据
        
        Args:
            living_id: 直播ID
            selected_fields: 选中的字段列表
            
        Returns:
            pd.DataFrame: 导出的数据
        """
        try:
            # 获取观众统计数据
            viewer_stats = self.viewer_stats_manager.get_viewer_stats(living_id)
            
            # 获取部门统计数据
            dept_stats = self.viewer_stats_manager.get_department_stats(living_id)
            
            # 获取观看时长分布数据
            time_dist = self.viewer_stats_manager.get_time_distribution(living_id)
            
            # 创建Excel写入器
            with pd.ExcelWriter("temp_stats.xlsx") as writer:
                # 写入观众统计数据
                if "观众统计" in selected_fields:
                    viewer_stats.to_excel(writer, sheet_name="观众统计", index=False)
                    
                # 写入部门统计数据
                if "部门统计" in selected_fields:
                    dept_stats.to_excel(writer, sheet_name="部门统计", index=False)
                    
                # 写入观看时长分布数据
                if "时长分布" in selected_fields:
                    time_dist.to_excel(writer, sheet_name="时长分布", index=False)
                    
            return pd.read_excel("temp_stats.xlsx")
            
        except Exception as e:
            logger.error(f"导出用户分析数据失败: {str(e)}")
            raise
            
    def save_to_excel(self, df: pd.DataFrame, file_path: str, chart_data: Dict[str, pd.DataFrame] = None):
        """保存数据到Excel文件
        
        Args:
            df: 要保存的数据
            file_path: 保存路径
            chart_data: 图表数据
        """
        try:
            # 创建Excel写入器
            with pd.ExcelWriter(file_path) as writer:
                # 写入主数据
                df.to_excel(writer, sheet_name="数据", index=False)
                
                # 写入图表数据
                if chart_data:
                    for sheet_name, chart_df in chart_data.items():
                        chart_df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
        except Exception as e:
            logger.error(f"保存Excel文件失败: {str(e)}")
            raise 