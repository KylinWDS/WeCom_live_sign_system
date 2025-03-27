import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.models.live_viewer import LiveViewer
from src.models.live_booking import LiveBooking
from src.core.token_manager import TokenManager

logger = get_logger(__name__)

class SignImportManager:
    def __init__(self, db_manager, corpid: str, corpsecret: str):
        self.db_manager = db_manager
        self.token_manager = TokenManager()
        self.token_manager.set_credentials(corpid, corpsecret)
        
    def import_from_excel(self, file_path: str, living_id: int) -> Dict[str, Any]:
        """从Excel文件导入签到数据
        
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
                
            # 验证直播是否存在
            living = self.db_manager.get_living_by_id(living_id)
            if not living:
                raise ValueError(f"直播ID {living_id} 不存在")
                
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
                            user_id=str(row["用户ID"]),
                            username=str(row["用户名"]),
                            sign_time=row["签到时间"],
                            is_signed=True,
                            sign_count=1
                        )
                        
                        # 检查是否已存在
                        existing = session.query(LiveViewer).filter_by(
                            living_id=living_id,
                            user_id=live_viewer.user_id
                        ).first()
                        
                        if existing:
                            # 更新现有记录
                            existing.sign_time = live_viewer.sign_time
                            existing.is_signed = True
                            existing.sign_count += 1
                        else:
                            # 添加新记录
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
            
    def validate_excel_format(self, file_path: str) -> bool:
        """验证Excel文件格式
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            bool: 格式是否有效
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 验证必要字段
            required_fields = ["用户ID", "用户名", "签到时间"]
            missing_fields = [field for field in required_fields if field not in df.columns]
            if missing_fields:
                return False
                
            # 验证数据类型
            if not pd.api.types.is_numeric_dtype(df["用户ID"]):
                return False
                
            if not pd.api.types.is_string_dtype(df["用户名"]):
                return False
                
            if not pd.api.types.is_datetime64_any_dtype(df["签到时间"]):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"验证Excel格式失败: {str(e)}")
            return False

    def import_sign_data(self, excel_path, living_id):
        """导入签到数据
        
        Args:
            excel_path: Excel文件路径
            living_id: 直播ID
            
        Returns:
            tuple: (成功导入数量, 失败数量)
        """
        try:
            # 验证直播是否存在
            session = self.db_manager.get_session()
            live = session.query(LiveBooking).filter_by(living_id=living_id).first()
            if not live:
                raise ValueError(f"直播ID {living_id} 不存在")
            
            success_count = 0
            error_count = 0
            
            # 读取Excel文件
            excel = pd.ExcelFile(excel_path)
            
            # 处理每个sheet
            for sheet_name in excel.sheet_names:
                try:
                    # 读取sheet数据
                    df = pd.read_excel(excel, sheet_name=sheet_name)
                    
                    # 验证数据格式
                    if not self._validate_sheet_data(df):
                        logger.warning(f"Sheet {sheet_name} 数据格式不正确")
                        error_count += 1
                        continue
                    
                    # 获取签到时间
                    sign_time = self._parse_sign_time(df)
                    
                    # 处理签到明细
                    if "签到明细" in df.columns:
                        sign_details = df[df["签到明细"].notna()]
                        for _, row in sign_details.iterrows():
                            try:
                                # 解析用户信息
                                user_name = row["已签到成员"].split("@")[0].strip()
                                department = row.get("所在部门", "")
                                user_id = self._get_user_id(user_name)
                                
                                # 检查是否已存在签到记录
                                existing_record = session.query(LiveViewer).filter_by(
                                    living_id=living_id,
                                    user_id=user_id
                                ).first()
                                
                                if existing_record:
                                    # 更新现有记录
                                    existing_record.sign_count += 1
                                    existing_record.sign_time = sign_time
                                    existing_record.department = department
                                    existing_record.updated_at = datetime.now()
                                    existing_record.is_signed = True
                                else:
                                    # 创建新记录
                                    live_viewer = LiveViewer(
                                        living_id=living_id,
                                        user_id=user_id,
                                        username=user_name,
                                        department=department,
                                        is_signed=True,
                                        sign_time=sign_time,
                                        sign_count=1,
                                        sign_type=1,
                                        sign_status=1,
                                        created_at=datetime.now(),
                                        updated_at=datetime.now()
                                    )
                                    session.add(live_viewer)
                                
                                success_count += 1
                                
                            except Exception as e:
                                logger.error(f"处理签到记录失败: {str(e)}")
                                error_count += 1
                                
                except Exception as e:
                    logger.error(f"处理sheet {sheet_name} 失败: {str(e)}")
                    error_count += 1
                    
            session.commit()
            return success_count, error_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"导入签到数据失败: {str(e)}")
            raise
        finally:
            session.close()
            
    def _validate_sheet_data(self, df: pd.DataFrame) -> bool:
        """验证sheet数据格式
        
        Args:
            df: DataFrame对象
            
        Returns:
            bool: 是否有效
        """
        required_columns = ["已签到成员", "签到时间"]
        return all(col in df.columns for col in required_columns)
        
    def _parse_sign_time(self, df: pd.DataFrame) -> datetime:
        """解析签到时间
        
        Args:
            df: DataFrame对象
            
        Returns:
            datetime: 签到时间
        """
        try:
            # 尝试从"签到时间"列获取
            if "签到时间" in df.columns:
                time_str = df["签到时间"].iloc[0]
                if isinstance(time_str, str):
                    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                elif isinstance(time_str, pd.Timestamp):
                    return time_str.to_pydatetime()
                    
            # 尝试从sheet名称获取
            try:
                return datetime.strptime(df.index.name, "%Y-%m-%d")
            except:
                pass
                
            # 默认使用当前时间
            return datetime.now()
            
        except Exception as e:
            logger.error(f"解析签到时间失败: {str(e)}")
            return datetime.now()
            
    def _get_user_id(self, user_name: str) -> str:
        """获取用户ID
        
        Args:
            user_name: 用户名称
            
        Returns:
            str: 用户ID
        """
        try:
            # 从企业微信API获取用户ID
            token = self.token_manager.get_token()
            url = "https://qyapi.weixin.qq.com/cgi-bin/user/list"
            params = {
                "access_token": token,
                "department_id": 1,  # 从根部门开始搜索
                "fetch_child": 1
            }
            
            import requests
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get("errcode") == 0:
                for user in result.get("userlist", []):
                    if user.get("name") == user_name:
                        return user.get("userid", user_name)
            else:
                logger.warning(f"获取用户ID失败: {result.get('errmsg')}")
                
            return user_name
            
        except Exception as e:
            logger.error(f"获取用户ID异常: {str(e)}")
            return user_name 