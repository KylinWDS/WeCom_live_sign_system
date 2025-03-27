import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from src.utils.logger import get_logger
from src.models.live_viewer import LiveViewer, UserSource
from src.models.live_booking import LiveBooking
from src.models.living import Living
from src.models.live_sign_record import LiveSignRecord
import time
import concurrent.futures
import threading
import queue
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger(__name__)

class SignImportManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.batch_size = 1000  # 每次批量提交的记录数
        self.max_workers = 5    # 最大线程数
        
    def import_sign_data(self, excel_path, living_id):
        """导入签到数据
        
        Args:
            excel_path: Excel文件路径
            living_id: 直播ID
            
        Returns:
            tuple: (成功导入数量, 失败数量, 跳过数量)
        """
        session = None
        try:
            # 创建会话
            session = self.db_manager.get_session().__enter__()
            
            # 添加调试日志
            logger.info(f"===== 开始导入签到数据 =====")
            logger.info(f"文件路径: {excel_path}")
            logger.info(f"尝试查询直播记录，living_id={living_id}，类型={type(living_id)}")
            
            # 验证直播是否存在
            from src.models.living import Living
            live = session.query(Living).filter_by(id=living_id).first()
            logger.info(f"查询结果：{live}")
            
            if not live:
                raise ValueError(f"直播ID {living_id} 不存在")
            
            # 读取Excel文件
            logger.info(f"正在读取Excel文件: {excel_path}")
            excel = pd.ExcelFile(excel_path)
            sheet_names = excel.sheet_names
            logger.info(f"Excel文件包含以下sheet: {sheet_names}")
            
            # 从数据库获取当前直播的已有签到记录
            existing_records = session.query(LiveViewer).filter_by(living_id=live.id).all()
            logger.info(f"当前直播已有 {len(existing_records)} 条签到记录")
            
            # 创建姓名到记录的映射，方便查找（不区分大小写）
            existing_name_map = {record.name.lower(): record for record in existing_records}
            
            # 获取当前直播的所有签到明细记录
            existing_sign_records = session.query(LiveSignRecord).filter_by(living_id=live.livingid).all()
            logger.info(f"当前直播已有 {len(existing_sign_records)} 条签到明细记录")
            
            # 如果有已存在的签到明细记录，先删除它们 - 覆盖模式
            if existing_sign_records:
                logger.info(f"删除当前直播的 {len(existing_sign_records)} 条签到明细记录")
                session.query(LiveSignRecord).filter_by(living_id=live.livingid).delete()
                session.commit()
            
            # 重置所有签到用户的签到次数计数
            for record in existing_records:
                record.sign_count = 0
            session.commit()
            
            # 准备结果
            results = {
                'success_count': 0,
                'error_count': 0,
                'skipped_count': 0
            }
            result_lock = threading.Lock()  # 用于保护结果计数
            
            # 共享资源
            shared_data = {
                'live': live,
                'existing_name_map': existing_name_map,
                'result_lock': result_lock,
                'sheet_names': sheet_names,
                'excel': excel
            }
            
            # 计算每个sheet的处理线程数
            worker_count = min(self.max_workers, len(sheet_names))
            logger.info(f"使用 {worker_count} 个线程处理 {len(sheet_names)} 个sheet")
            
            # 使用线程池处理每个sheet
            with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
                # 为每个sheet创建一个任务
                futures = []
                for sheet_index, sheet_name in enumerate(sheet_names):
                    futures.append(
                        executor.submit(
                            self._process_sheet, 
                            excel_path, 
                            sheet_name, 
                            sheet_index,
                            shared_data,
                            results
                        )
                    )
                
                # 等待所有任务完成
                for future in concurrent.futures.as_completed(futures):
                    try:
                        # 获取任务结果
                        sheet_result = future.result()
                        logger.info(f"Sheet处理完成: {sheet_result}")
                    except Exception as exc:
                        logger.error(f"处理sheet时出错: {exc}")
                        results['error_count'] += 1
            
            # 更新记录到数据库
            for record in existing_records:
                if record.sign_count > 0:
                    record.is_signed = True
            session.commit()
            
            return results['success_count'], results['error_count'], results['skipped_count']
            
        except Exception as e:
            # 记录错误
            logger.error(f"导入签到数据时出错: {str(e)}")
            if session:
                session.rollback()
            raise
            
        finally:
            # 关闭会话
            if session:
                session.__exit__(None, None, None)
                
    def _process_sheet(self, excel_path, sheet_name, sheet_index, shared_data, results):
        """处理单个sheet
        
        Args:
            excel_path: Excel文件路径
            sheet_name: sheet名称
            sheet_index: sheet索引
            shared_data: 共享数据
            results: 结果统计
            
        Returns:
            dict: 处理结果
        """
        # 在方法开头就导入需要的类，确保在线程中可用
        from src.models.live_viewer import LiveViewer, UserSource
        from src.models.live_sign_record import LiveSignRecord
        
        sheet_result = {
            'sheet_name': sheet_name,
            'success_count': 0,
            'error_count': 0,
            'skipped_count': 0
        }
        
        # 获取线程专用的数据库会话
        session = None
        try:
            session = self.db_manager.get_session().__enter__()
            
            # 获取共享数据
            live = shared_data['live']
            existing_name_map = shared_data['existing_name_map'].copy()  # 复制一份，避免多线程修改冲突
            result_lock = shared_data['result_lock']
            
            # 读取sheet数据
            logger.info(f"线程{threading.current_thread().name} 开始处理Sheet: {sheet_name}")
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            # 打印基本信息
            logger.info(f"Sheet '{sheet_name}' 包含 {len(df)} 行, {df.shape[1]} 列")
            
            # 为DataFrame添加sheet名称属性，方便后续解析时间
            df.name = sheet_name
            
            # 验证数据格式
            if not self._validate_sheet_data(df):
                logger.warning(f"Sheet {sheet_name} 数据格式不正确")
                sheet_result['error_count'] += 1
                return sheet_result
            
            # 解析签到时间
            try:
                sign_time = self._parse_sign_time(df)
                logger.info(f"获取到签到时间: {sign_time}")
            except ValueError as e:
                logger.error(f"解析签到时间失败: {str(e)}")
                sheet_result['error_count'] += 1
                return sheet_result

            # 解析已签到人数
            try:
                signed_count = df.iloc[2, 1]  # 第3行第2列
                if pd.notna(signed_count):
                    signed_count = int(signed_count)
                    logger.info(f"已签到人数: {signed_count}")
                else:
                    signed_count = 0
                    logger.warning("未找到有效的已签到人数，默认为0")
            except Exception as e:
                logger.warning(f"解析已签到人数失败: {str(e)}，使用默认值0")
                signed_count = 0

            # 获取当前sheet对应的签到次数（按sheet索引计算）
            sign_sequence = sheet_index + 1  # 从1开始计数
            logger.info(f"当前sheet '{sheet_name}' 对应的签到次数: {sign_sequence}")
            
            # 存储批量处理的记录
            viewer_batch = []
            sign_record_batch = []
            viewer_update_ids = set()  # 需要更新的LiveViewer ID集合
            
            # 从第7行开始处理签到数据
            sheet_success_count = 0
            skipped_count = 0
            
            for i in range(6, len(df)):  # 从第7行开始
                try:
                    # 检查是否有有效的成员名称
                    if pd.isna(df.iloc[i, 0]):
                        continue
                    
                    member_name = str(df.iloc[i, 0]).strip()
                    if not member_name:
                        continue
                        
                    # 获取部门信息
                    department = ""
                    if df.shape[1] > 1 and pd.notna(df.iloc[i, 1]):  # 第2列是部门
                        department = str(df.iloc[i, 1]).strip()
                    
                    # 处理微信用户名称，去除@微信后缀
                    processed_member_name = LiveViewer.process_wechat_name(member_name)
                    
                    # 使用本地会话查询数据
                    existing_record = None
                    
                    # 检查本地映射中是否有这个用户
                    record_key = processed_member_name.lower()
                    if record_key in existing_name_map:
                        existing_record = session.query(LiveViewer).get(existing_name_map[record_key].id)
                    
                    # 如果没有在映射中找到，尝试在数据库中查询
                    if not existing_record:
                        existing_record = session.query(LiveViewer).filter(
                            LiveViewer.living_id == live.id,
                            LiveViewer.name.ilike(processed_member_name)
                        ).first()
                        
                        # 如果在数据库中找到了，添加到本地映射
                        if existing_record:
                            existing_name_map[record_key] = existing_record
                    
                    if existing_record:
                        # 记录ID，后续批量更新
                        viewer_update_ids.add(existing_record.id)
                        
                        # 创建新的签到明细记录
                        sign_record = LiveSignRecord(
                            viewer_id=existing_record.id,
                            living_id=live.livingid,
                            sign_time=sign_time,
                            sign_type="import",
                            sign_remark=f"Excel批量导入，表格：{sheet_name}",
                            sign_sequence=sign_sequence,
                            sheet_name=sheet_name
                        )
                        sign_record_batch.append(sign_record)
                        
                        sheet_success_count += 1
                    else:
                        # 生成唯一的userid，使用成员名称
                        # 为避免重复，添加时间戳和行号
                        userid = f"wx_{processed_member_name}_{int(time.time())}_{i}"
                        
                        # 创建新的观众记录
                        viewer = LiveViewer(
                            living_id=live.id,
                            userid=userid,
                            name=processed_member_name,
                            user_source=UserSource.EXTERNAL,  # 导入的签到数据默认为外部用户
                            user_type=1,  # 微信用户
                            department=department,
                            is_signed=True,
                            sign_time=sign_time,
                            sign_count=1
                        )
                        viewer_batch.append(viewer)
                        
                        # 需要先提交获取ID，所以不能批量处理签到记录
                        sheet_success_count += 1
                    
                    # 批量处理
                    if len(viewer_batch) >= self.batch_size:
                        try:
                            # 批量添加LiveViewer记录
                            session.bulk_save_objects(viewer_batch)
                            session.flush()
                            
                            # 为每个新添加的viewer创建签到记录
                            new_sign_records = []
                            for viewer in viewer_batch:
                                sign_record = LiveSignRecord(
                                    viewer_id=viewer.id,
                                    living_id=live.livingid,
                                    sign_time=sign_time,
                                    sign_type="import",
                                    sign_remark=f"Excel批量导入，表格：{sheet_name}",
                                    sign_sequence=sign_sequence,
                                    sheet_name=sheet_name
                                )
                                new_sign_records.append(sign_record)
                            
                            sign_record_batch.extend(new_sign_records)
                            
                            # 批量添加签到记录
                            if sign_record_batch:
                                session.bulk_save_objects(sign_record_batch)
                                session.flush()
                                
                            # 更新已存在用户的签到次数
                            if viewer_update_ids:
                                session.query(LiveViewer).filter(
                                    LiveViewer.id.in_(viewer_update_ids)
                                ).update(
                                    {LiveViewer.sign_count: LiveViewer.sign_count + 1,
                                     LiveViewer.sign_time: sign_time,
                                     LiveViewer.is_signed: True},
                                    synchronize_session=False
                                )
                                session.flush()
                            
                            # 清空批次
                            viewer_batch = []
                            sign_record_batch = []
                            viewer_update_ids = set()
                            
                            # 提交事务
                            session.commit()
                            
                        except SQLAlchemyError as e:
                            logger.error(f"批量处理数据时出错: {str(e)}")
                            session.rollback()
                            sheet_result['error_count'] += len(viewer_batch)
                            
                except Exception as e:
                    logger.error(f"处理第{i+1}行时出错: {str(e)}")
                    sheet_result['error_count'] += 1
            
            # 处理剩余的批次
            if viewer_batch or sign_record_batch or viewer_update_ids:
                try:
                    # 批量添加LiveViewer记录
                    if viewer_batch:
                        session.bulk_save_objects(viewer_batch)
                        session.flush()
                        
                        # 为每个新添加的viewer创建签到记录
                        new_sign_records = []
                        for viewer in viewer_batch:
                            sign_record = LiveSignRecord(
                                viewer_id=viewer.id,
                                living_id=live.livingid,
                                sign_time=sign_time,
                                sign_type="import",
                                sign_remark=f"Excel批量导入，表格：{sheet_name}",
                                sign_sequence=sign_sequence,
                                sheet_name=sheet_name
                            )
                            new_sign_records.append(sign_record)
                        
                        sign_record_batch.extend(new_sign_records)
                    
                    # 批量添加签到记录
                    if sign_record_batch:
                        session.bulk_save_objects(sign_record_batch)
                        session.flush()
                    
                    # 更新已存在用户的签到次数
                    if viewer_update_ids:
                        session.query(LiveViewer).filter(
                            LiveViewer.id.in_(viewer_update_ids)
                        ).update(
                            {LiveViewer.sign_count: LiveViewer.sign_count + 1,
                             LiveViewer.sign_time: sign_time,
                             LiveViewer.is_signed: True},
                            synchronize_session=False
                        )
                        session.flush()
                    
                    # 提交事务
                    session.commit()
                    
                except SQLAlchemyError as e:
                    logger.error(f"处理剩余批次时出错: {str(e)}")
                    session.rollback()
                    sheet_result['error_count'] += len(viewer_batch)
            
            # 更新sheet_result
            sheet_result['success_count'] = sheet_success_count
            sheet_result['skipped_count'] = skipped_count
            
            # 同步更新全局结果
            with result_lock:
                results['success_count'] += sheet_success_count
                results['error_count'] += sheet_result['error_count']
                results['skipped_count'] += skipped_count
                
            logger.info(f"Sheet '{sheet_name}' 处理完成，成功导入 {sheet_success_count} 条记录")
            return sheet_result
            
        except Exception as e:
            logger.error(f"处理Sheet {sheet_name} 时出错: {str(e)}")
            with result_lock:
                results['error_count'] += 1
            return sheet_result
        finally:
            # 关闭会话
            if session:
                session.__exit__(None, None, None)

    def _validate_sheet_data(self, df: pd.DataFrame) -> bool:
        """验证sheet数据格式
        
        Args:
            df: DataFrame对象
            
        Returns:
            bool: 是否有效
        """
        try:
            sheet_name = getattr(df, 'name', 'unknown')
            logger.info(f"===== 开始验证Sheet '{sheet_name}' 格式 =====")
            
            # 打印每行的内容 - 前10行
            for i in range(min(10, len(df))):
                row_content = []
                for j in range(min(5, df.shape[1])):
                    value = df.iloc[i, j] if j < df.shape[1] else None
                    row_content.append(f"'{value}'" if pd.notna(value) else "None")
                logger.info(f"行{i+1}内容: {', '.join(row_content)}")  # 注意：这里i+1是人类可读的行号
            
            # 检查DataFrame是否有足够的行
            min_rows = 7  # 至少需要6行（第6行才是第一条签到数据，索引为5）
            if len(df) < min_rows:
                logger.warning(f"Sheet '{sheet_name}' 行数不足，至少需要{min_rows}行，实际为{len(df)}行")
                return False
            
            # 确保DataFrame至少有2列
            if df.shape[1] < 2:
                logger.warning(f"Sheet '{sheet_name}' 列数不足，至少需要2列，实际为{df.shape[1]}列")
                return False
                
            # 查找"签到发起时间"和"已签到人数"标题所在的行
            time_row_idx = -1
            time_col_idx = -1
            count_col_idx = -1
            
            # 搜索前3行来查找标题
            for i in range(min(3, len(df))):
                row_text = ' '.join([str(x) for x in df.iloc[i].tolist() if pd.notna(x)])
                logger.info(f"检查索引{i}行(第{i+1}行)是否包含标题: '{row_text}'")
                
                # 在同一行检查是否同时存在"签到发起时间"和"已签到人数"
                if "签到发起时间" in row_text and "已签到人数" in row_text:
                    time_row_idx = i
                    # 找到具体的列索引
                    for j in range(df.shape[1]):
                        cell_value = str(df.iloc[i, j]) if pd.notna(df.iloc[i, j]) else ""
                        if "签到发起时间" in cell_value:
                            time_col_idx = j
                        if "已签到人数" in cell_value:
                            count_col_idx = j
                    break
            
            if time_row_idx == -1:
                logger.warning(f"Sheet '{sheet_name}' 未找到包含'签到发起时间'和'已签到人数'的行")
                return False
                
            # 确保找到了"签到发起时间"和"已签到人数"的列
            if time_col_idx == -1:
                logger.warning(f"Sheet '{sheet_name}' 未找到'签到发起时间'列")
                return False
                
            if count_col_idx == -1:
                logger.warning(f"Sheet '{sheet_name}' 未找到'已签到人数'列")
                return False
                
            logger.info(f"找到标题行索引：{time_row_idx}(第{time_row_idx+1}行)，" +
                        f"时间列索引：{time_col_idx}(第{time_col_idx+1}列)，" +
                        f"人数列索引：{count_col_idx}(第{count_col_idx+1}列)")
            
            # 检查下一行是否有数据（时间和人数）
            if time_row_idx + 1 >= len(df):
                logger.warning(f"Sheet '{sheet_name}' 标题行后没有数据行")
                return False
                
            if pd.isna(df.iloc[time_row_idx + 1, time_col_idx]) or pd.isna(df.iloc[time_row_idx + 1, count_col_idx]):
                logger.warning(f"Sheet '{sheet_name}' 索引{time_row_idx+1}行(第{time_row_idx+2}行)缺少签到时间或人数数据")
                return False
                
            # 查找"签到明细"标题
            detail_row_idx = -1
            for i in range(time_row_idx + 1, min(time_row_idx + 5, len(df))):
                row_text = ' '.join([str(x) for x in df.iloc[i].tolist() if pd.notna(x)])
                logger.info(f"检查索引{i}行(第{i+1}行)是否包含'签到明细': '{row_text}'")
                if "签到明细" in row_text:
                    detail_row_idx = i
                    break
            
            if detail_row_idx == -1:
                logger.warning(f"Sheet '{sheet_name}' 未找到'签到明细'标题行")
                return False
                
            logger.info(f"找到签到明细行索引：{detail_row_idx}(第{detail_row_idx+1}行)")
            
            # 查找"已签到成员"和"所在部门"标题
            member_row_idx = -1
            member_col_idx = -1
            dept_col_idx = -1
            
            for i in range(detail_row_idx + 1, min(detail_row_idx + 3, len(df))):
                row_text = ' '.join([str(x) for x in df.iloc[i].tolist() if pd.notna(x)])
                logger.info(f"检查索引{i}行(第{i+1}行)是否包含'已签到成员': '{row_text}'")
                
                if "已签到成员" in row_text:
                    member_row_idx = i
                    # 找到具体的列索引
                    for j in range(df.shape[1]):
                        cell_value = str(df.iloc[i, j]) if pd.notna(df.iloc[i, j]) else ""
                        if "已签到成员" in cell_value:
                            member_col_idx = j
                        if "所在部门" in cell_value:
                            dept_col_idx = j
                    break
            
            if member_row_idx == -1 or member_col_idx == -1:
                logger.warning(f"Sheet '{sheet_name}' 未找到'已签到成员'标题")
                return False
                
            logger.info(f"找到成员标题行索引：{member_row_idx}(第{member_row_idx+1}行)，" +
                        f"成员列索引：{member_col_idx}(第{member_col_idx+1}列)，" +
                        f"部门列索引：{dept_col_idx}(第{dept_col_idx+1}列)")
            
            # 检查是否有成员数据
            has_member_data = False
            for i in range(member_row_idx + 1, len(df)):
                if pd.notna(df.iloc[i, member_col_idx]):
                    member_name = str(df.iloc[i, member_col_idx]).strip()
                    logger.info(f"在索引{i}行(第{i+1}行)找到成员数据: '{member_name}'")
                    has_member_data = True
                    break
                    
            if not has_member_data:
                logger.warning(f"Sheet '{sheet_name}' 没有有效的成员数据")
                return False
                
            # 存储找到的行列索引，供其他方法使用
            df.time_row_idx = time_row_idx
            df.time_col_idx = time_col_idx
            df.count_col_idx = count_col_idx
            df.detail_row_idx = detail_row_idx
            df.member_row_idx = member_row_idx
            df.member_col_idx = member_col_idx
            df.dept_col_idx = dept_col_idx
                
            logger.info(f"===== Sheet '{sheet_name}' 格式验证通过 =====")
            return True
            
        except Exception as e:
            logger.error(f"验证签到文件格式失败: {str(e)}")
            return False
        
    def _parse_sign_time(self, df: pd.DataFrame) -> datetime:
        """解析签到时间，从表格中动态查找
        
        Args:
            df: DataFrame对象
            
        Returns:
            datetime: 签到时间
            
        Raises:
            ValueError: 如果无法从表格内提取签到时间
        """
        try:
            sheet_name = getattr(df, 'name', 'unknown')
            logger.info(f"===== 开始解析Sheet '{sheet_name}' 的签到时间 =====")
            
            # 获取之前在_validate_sheet_data中找到的时间单元格位置
            time_row_idx = getattr(df, 'time_row_idx', 0) 
            time_col_idx = getattr(df, 'time_col_idx', 0)
            
            # 时间值在标题的下一行
            time_value = df.iloc[time_row_idx + 1, time_col_idx]
            logger.info(f"从索引{time_row_idx+1}行(第{time_row_idx+2}行)索引{time_col_idx}列(第{time_col_idx+1}列)获取签到时间值: '{time_value}'")
            
            # 如果没有找到任何时间值，抛出异常
            if time_value is None or pd.isna(time_value):
                logger.error(f"Sheet '{sheet_name}' 中未找到有效的签到时间")
                raise ValueError("无法从表格中找到有效的签到时间")
            
            logger.info(f"获取到原始签到时间值: '{time_value}', 类型: {type(time_value)}")
                
            # 处理不同类型的时间值
            if isinstance(time_value, pd.Timestamp):
                logger.info(f"时间值是pd.Timestamp类型，转换为: {time_value.to_pydatetime()}")
                return time_value.to_pydatetime()
            elif isinstance(time_value, datetime):
                logger.info(f"时间值已经是datetime类型: {time_value}")
                return time_value
            elif isinstance(time_value, str):
                logger.info(f"时间值是字符串类型，尝试解析: '{time_value}'")
                # 尝试多种常见的日期时间格式
                formats = [
                    "%Y.%m.%d %H:%M",       # 2023.01.01 12:30
                    "%Y.%m.%d %H:%M:%S",    # 2023.01.01 12:30:00
                    "%Y.%-m.%-d %H:%M",     # 2023.3.26 12:30 (没有前导零)
                    "%Y.%-m.%-d %H:%M:%S",  # 2023.3.26 12:30:00 (没有前导零)
                    "%Y-%m-%d %H:%M",       # 2023-01-01 12:30
                    "%Y-%m-%d %H:%M:%S",    # 2023-01-01 12:30:00
                    "%Y-%-m-%-d %H:%M",     # 2023-3-26 12:30 (没有前导零)
                    "%Y-%-m-%-d %H:%M:%S",  # 2023-3-26 12:30:00 (没有前导零)
                    "%Y/%m/%d %H:%M",       # 2023/01/01 12:30
                    "%Y/%m/%d %H:%M:%S",    # 2023/01/01 12:30:00
                    "%Y/%-m/%-d %H:%M",     # 2023/3/26 12:30 (没有前导零)
                    "%Y/%-m/%-d %H:%M:%S",  # 2023/3/26 12:30:00 (没有前导零)
                ]
                
                for fmt in formats:
                    try:
                        parsed_time = datetime.strptime(time_value, fmt)
                        logger.info(f"使用格式 '{fmt}' 成功解析时间: {parsed_time}")
                        return parsed_time
                    except ValueError:
                        continue

                # 如果标准格式失败，尝试使用更灵活的解析方法
                try:
                    # 处理常见的各种格式，如 "2025.3.26 18:17"
                    import re
                    pattern = r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?'
                    match = re.search(pattern, time_value)
                    if match:
                        year, month, day, hour, minute = map(int, match.groups()[:5])
                        second = int(match.group(6)) if match.group(6) else 0
                        parsed_time = datetime(year, month, day, hour, minute, second)
                        logger.info(f"使用正则表达式成功解析时间: {parsed_time}")
                        return parsed_time
                except Exception as e:
                    logger.warning(f"灵活解析日期时间失败: {str(e)}")
            
            # 如果所有解析方法都失败，抛出异常
            error_msg = f"无法解析签到时间: {time_value}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        except Exception as e:
            logger.error(f"解析签到时间失败: {str(e)}")
            # 将错误上抛给调用者处理
            raise ValueError(f"无法从表格中解析有效的签到时间: {str(e)}") 