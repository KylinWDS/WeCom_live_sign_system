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
import copy

logger = get_logger(__name__)

class SignImportManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.max_workers = 5    # 最大线程数
        
        # 添加Excel解析相关的配置项，避免硬编码
        self.excel_config = {
            'min_rows': 7,                  # 最小需要的行数
            'title_search_range': 5,        # 搜索标题行的范围
            'detail_search_range': 5,       # 搜索签到明细的范围
            'member_search_range': 3,       # 搜索成员标题的范围
        }
        
        # 添加大数据处理相关配置
        self.db_config = {
            'query_batch_size': 10000,      # 查询时的批量大小
            'save_batch_size': 1000,        # 保存时的批量大小，降低为1000更合适
            'update_batch_size': 1000,      # 更新时的批量大小，降低为1000更合适
        }
        
    def import_sign_data(self, excel_path, living_id):
        """导入签到数据
        
        Args:
            excel_path: Excel文件路径或Excel文件对象
            living_id: 直播ID
            
        Returns:
            dict: 详细的导入结果
        """
        session = None
        # 用于记录详细的导入结果
        detailed_results = {
            'total_processed': 0,
            'success_details': [],
            'error_details': [],
            'skipped_details': []
        }
        try:
            # 创建会话
            session = self.db_manager.get_session().__enter__()
            
            # 添加调试日志
            logger.debug(f"===== 开始导入签到数据 =====")
            if isinstance(excel_path, str):
                logger.debug(f"文件路径: {excel_path}")
            else:
                logger.debug(f"使用传入的Excel文件对象")
            
            logger.debug(f"尝试查询直播记录，living_id={living_id}，类型={type(living_id)}")
                
            # 验证直播是否存在
            from src.models.living import Living
            live = session.query(Living).filter_by(id=living_id).first()
            logger.debug(f"查询结果：{live}")
            
            if not live:
                error_msg = f"直播ID {living_id} 不存在"
                logger.error(error_msg)
                detailed_results['error_details'].append(error_msg)
                raise ValueError(error_msg)
            
            # 获取Excel数据
            if isinstance(excel_path, str):
                logger.debug(f"正在读取Excel文件: {excel_path}")
                excel = pd.ExcelFile(excel_path)
            else:
                # 直接使用传入的Excel对象
                excel = excel_path
                logger.debug(f"使用传入的Excel文件对象")
            
            sheet_names = excel.sheet_names
            logger.debug(f"Excel文件包含以下sheet: {sheet_names}")
            
            # 一次性加载所有相关的LiveViewer记录，避免后续重复查询
            existing_records = session.query(LiveViewer).filter_by(living_id=live.id).all()
            logger.debug(f"当前直播已有 {len(existing_records)} 条签到记录")
            
            # 创建姓名到ID的映射，只传递基本数据类型（避免session对象）
            existing_name_map = {}
            for record in existing_records:
                # 只存储ID和其他必要的基本信息
                existing_name_map[record.name.lower()] = {
                    'id': record.id,
                    'name': record.name,
                    'livingid': record.living_id
                }
            
            # 获取当前直播的所有签到明细记录
            existing_sign_records = session.query(LiveSignRecord).filter_by(living_id=live.livingid).all()
            logger.debug(f"当前直播已有 {len(existing_sign_records)} 条签到明细记录")
            
            # 如果有已存在的签到明细记录，先删除它们 - 覆盖模式
            if existing_sign_records:
                logger.debug(f"删除当前直播的 {len(existing_sign_records)} 条签到明细记录")
                session.query(LiveSignRecord).filter_by(living_id=live.livingid).delete()
                session.commit()
            
            # 重置所有签到用户的签到次数计数
            for record in existing_records:
                record.is_signed = False
                record.sign_time = None
                record.sign_count = 0
            session.commit()
            
            # 重置结果字典，添加详细日志功能
            results = {
                'success_count': 0,
                'error_count': 0,
                'skipped_count': 0,
                'success_details': [],
                'error_details': [],
                'skipped_details': []
            }
            
            # 创建共享数据（只包含基本数据类型，不包含SQLAlchemy对象）
            shared_data = {
                'live_id': live.id,
                'live_livingid': live.livingid,
                'existing_name_map': existing_name_map,  # 现在只包含基本数据类型
                'sheet_names': sheet_names,
                'excel': excel
            }
            
            # 创建线程安全的队列，用于存储处理结果
            from queue import Queue
            result_queue = Queue()
            
            # 计算每个sheet的处理线程数
            worker_count = min(self.max_workers, len(sheet_names))
            logger.debug(f"使用 {worker_count} 个线程处理 {len(sheet_names)} 个sheet")
            
            # 使用线程池处理每个sheet数据解析
            with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
                # 为每个sheet创建一个任务
                futures = []
                for sheet_index, sheet_name in enumerate(sheet_names):
                    futures.append(
                        executor.submit(
                            self._parse_sheet, 
                            excel_path, 
                            sheet_name, 
                            sheet_index,
                            shared_data,
                            result_queue
                        )
                    )
                
                # 等待所有任务完成
                for future in concurrent.futures.as_completed(futures):
                    try:
                        # 获取任务结果
                        sheet_result = future.result()
                        logger.debug(f"Sheet解析完成: {sheet_result}")
                    except Exception as exc:
                        logger.error(f"解析sheet时出错: {exc}")
                        results['error_count'] += 1
                        results['error_details'].append(f"处理Sheet '{sheet_name}' 失败: {str(exc)}")
            
            # 从队列中收集所有处理结果
            all_sheet_results = []
            while not result_queue.empty():
                all_sheet_results.append(result_queue.get())
            
            # 开始统一处理数据库操作
            logger.debug(f"所有Sheet解析完成，开始处理数据库操作")
            
            # 存储要批量处理的新用户和签到记录
            all_new_viewers = []
            all_sign_records = []
            # 存储需要更新的用户ID
            all_updated_viewer_ids = set()
            
            # 使用字典来跟踪已处理的新用户，防止重复创建
            # 键为用户名（小写），值为对应的用户数据
            new_viewers_dict = {}
            
            # 从所有sheet结果中收集数据
            for sheet_result in all_sheet_results:
                # 为这个sheet创建新用户
                if 'new_viewers' in sheet_result:
                    for viewer_data in sheet_result['new_viewers']:
                        # 创建用户名的小写版本作为字典键，确保不区分大小写匹配
                        viewer_key = viewer_data['name'].lower()
                        
                        # 检查这个用户是否已经处理过
                        if viewer_key not in new_viewers_dict:
                            # 第一次看到这个用户，添加到字典
                            new_viewers_dict[viewer_key] = viewer_data
                            
                            # 根据子线程收集的数据创建LiveViewer对象
                            try:
                                viewer = LiveViewer(
                                    living_id=live.id,
                                    userid=viewer_data['userid'],
                                    name=viewer_data['name'],
                                    user_source=UserSource.EXTERNAL,
                                    user_type=1,  # 微信用户
                                    department=viewer_data.get('department', ''),
                                    is_signed=True,
                                    sign_time=sheet_result['sign_time'],
                                    sign_count=1,  # 初始设为1，后面会更新
                                    watch_time=0
                                )
                                all_new_viewers.append(viewer)
                                results['success_count'] += 1
                                results['success_details'].append(f"添加新用户: {viewer_data['name']}")
                                logger.debug(f"首次添加用户 '{viewer_data['name']}' 到新用户列表中")
                            except Exception as e:
                                logger.error(f"创建用户对象失败: {str(e)}")
                                results['error_count'] += 1
                                results['error_details'].append(f"创建用户对象失败: {viewer_data.get('name', '未知')}, 原因: {str(e)}")
                        else:
                            # 已经处理过这个用户，记录日志
                            logger.debug(f"用户 '{viewer_data['name']}' 在不同sheet中重复出现，避免重复创建")
                
                # 收集现有用户IDs，用于后续更新
                if 'updated_viewer_ids' in sheet_result:
                    all_updated_viewer_ids.update(sheet_result['updated_viewer_ids'])
                
                # 更新统计数据
                results['success_count'] += sheet_result.get('success_count', 0)
                results['error_count'] += sheet_result.get('error_count', 0)
                results['skipped_count'] += sheet_result.get('skipped_count', 0)
                
                # 更新详细信息
                if 'success_details' in sheet_result:
                    results['success_details'].extend(sheet_result['success_details'])
                if 'error_details' in sheet_result:
                    results['error_details'].extend(sheet_result['error_details'])
                if 'skipped_details' in sheet_result:
                    results['skipped_details'].extend(sheet_result['skipped_details'])
            
            # 在单一事务中批量处理所有数据库操作
            try:
                # 记录开始处理数据库操作的时间
                db_start_time = time.time()
                logger.debug(f"开始处理数据库操作，共有 {len(all_new_viewers)} 个新用户和 {sum(len(sheet_result.get('sign_records', [])) for sheet_result in all_sheet_results)} 条签到记录")
                
                # 1. 批量保存新用户
                if all_new_viewers:
                    total_new_viewers = len(all_new_viewers)
                    logger.debug(f"开始批量保存 {total_new_viewers} 个新用户")
                    
                    # 分批保存新用户
                    save_batch_size = self.db_config.get('save_batch_size', 1000)
                    for i in range(0, total_new_viewers, save_batch_size):
                        batch = all_new_viewers[i:i + save_batch_size]
                        session.bulk_save_objects(batch)
                        logger.debug(f"已保存 {i+len(batch)}/{total_new_viewers} 个新用户")
                    
                    session.flush()
                    
                    # 为新添加的用户创建签到记录
                    new_sign_records = []
                    viewer_id_map = {}  # 用于存储新用户名到ID的映射
                    
                    # 优化：分批查询所有新添加的用户
                    new_viewer_names = [viewer.name for viewer in all_new_viewers]
                    total_names = len(new_viewer_names)
                    
                    # 使用分批IN操作符查询所有新用户
                    if new_viewer_names:
                        logger.debug(f"开始批量查询 {total_names} 个新添加的用户")
                        query_batch_size = self.db_config.get('query_batch_size', 10000)
                        
                        for i in range(0, total_names, query_batch_size):
                            name_batch = new_viewer_names[i:i + query_batch_size]
                            
                            new_viewers_query = session.query(LiveViewer).filter(
                                LiveViewer.living_id == live.id,
                                LiveViewer.name.in_(name_batch),
                                LiveViewer.user_source == UserSource.EXTERNAL
                            ).all()
                            
                            # 构建名称到ID的映射
                            for viewer in new_viewers_query:
                                viewer_id_map[viewer.name.lower()] = viewer.id
                            
                            logger.debug(f"已查询 {i+len(name_batch)}/{total_names} 个新用户ID")
                    
                    # 用于记录新用户在每个sheet中的出现情况
                    user_sheet_appearances = {}
                    
                    # 为每个新用户创建签到记录
                    for sheet_result in all_sheet_results:
                        if 'sign_time' in sheet_result and 'sign_sequence' in sheet_result:
                            sheet_name = sheet_result.get('sheet_name', '')
                            
                            # 检查这个sheet中是否有新用户
                            if 'new_viewers' in sheet_result:
                                for viewer_data in sheet_result['new_viewers']:
                                    viewer_name = viewer_data['name'].lower()
                                    
                                    if viewer_name in viewer_id_map:
                                        viewer_id = viewer_id_map[viewer_name]
                                        
                                        # 记录这个用户在哪些sheet中出现了
                                        if viewer_name not in user_sheet_appearances:
                                            user_sheet_appearances[viewer_name] = []
                                        
                                        # 避免在同一个sheet中重复计数
                                        if sheet_name not in user_sheet_appearances[viewer_name]:
                                            user_sheet_appearances[viewer_name].append(sheet_name)
                                            
                                            # 创建签到记录
                                            sign_record = LiveSignRecord(
                                                viewer_id=viewer_id,
                                                living_id=live.livingid,
                                                sign_time=sheet_result['sign_time'],
                                                sign_type="import",
                                                sign_location="null",
                                                sign_remark=f"Excel批量导入，表格：{sheet_name}",
                                                sign_sequence=sheet_result['sign_sequence'],
                                                sheet_name=sheet_name,
                                                original_member_name=viewer_data.get('original_member_name', viewer_data['name'])
                                            )
                                            new_sign_records.append(sign_record)
                                            logger.debug(f"为新用户 '{viewer_data['name']}' (ID={viewer_id})在sheet '{sheet_name}' 创建签到记录")
                    
                    # 创建新用户签到次数更新字典
                    new_viewer_updates = {}
                    
                    # 计算每个新用户出现在的不同sheet数量
                    for viewer_name, sheets in user_sheet_appearances.items():
                        if viewer_name in viewer_id_map:
                            viewer_id = viewer_id_map[viewer_name]
                            sheet_count = len(sheets)
                            new_viewer_updates[viewer_id] = sheet_count
                            logger.debug(f"将更新新用户 '{viewer_name}' (ID={viewer_id})的签到次数为 {sheet_count}，基于sheet: {', '.join(sheets)}")
                    
                    # 将新用户的签到记录添加到整体签到记录列表
                    if new_sign_records:
                        logger.debug(f"为新用户创建 {len(new_sign_records)} 条签到记录")
                        all_sign_records.extend(new_sign_records)
                
                # 2. 创建现有用户的签到记录
                # 跟踪每个用户在每个sheet中的出现情况，避免重复创建签到记录
                existing_user_sheet_appearances = {}  # 格式: {user_id: [sheet_names]}
                
                for sheet_result in all_sheet_results:
                    if 'sign_records' in sheet_result:
                        sheet_name = sheet_result.get('sheet_name', '')
                        
                        for record_data in sheet_result['sign_records']:
                            viewer_id = record_data['viewer_id']
                            
                            # 初始化追踪
                            if viewer_id not in existing_user_sheet_appearances:
                                existing_user_sheet_appearances[viewer_id] = []
                            
                            # 避免在同一个sheet中重复创建记录
                            if sheet_name not in existing_user_sheet_appearances[viewer_id]:
                                existing_user_sheet_appearances[viewer_id].append(sheet_name)
                                
                                try:
                                    sign_record = LiveSignRecord(
                                        viewer_id=viewer_id,
                                        living_id=live.livingid,
                                        sign_time=sheet_result['sign_time'],
                                        sign_type="import",
                                        sign_location="null",
                                        sign_remark=f"Excel批量导入，表格：{sheet_name}",
                                        sign_sequence=sheet_result['sign_sequence'],
                                        sheet_name=sheet_name,
                                        original_member_name=record_data.get('original_member_name', '')
                                    )
                                    all_sign_records.append(sign_record)
                                    logger.debug(f"为现有用户ID={viewer_id}创建签到记录，sheet: {sheet_name}")
                                except Exception as e:
                                    logger.error(f"创建签到记录失败: {str(e)}")
                                    results['error_count'] += 1
                                    results['error_details'].append(f"创建签到记录失败: {record_data.get('original_member_name', '未知')}, 原因: {str(e)}")
                            else:
                                logger.debug(f"用户ID={viewer_id}在sheet '{sheet_name}'中已有记录，跳过重复创建")
                
                # 3. 批量保存所有签到记录
                if all_sign_records:
                    total_sign_records = len(all_sign_records)
                    logger.debug(f"开始批量保存 {total_sign_records} 条签到记录")
                    
                    # 分批保存签到记录
                    save_batch_size = self.db_config.get('save_batch_size', 1000)
                    for i in range(0, total_sign_records, save_batch_size):
                        batch = all_sign_records[i:i + save_batch_size]
                        session.bulk_save_objects(batch)
                        logger.debug(f"已保存 {i+len(batch)}/{total_sign_records} 条签到记录")
                        
                    session.flush()
                
                # 合并所有需要更新签到次数的用户（新用户和现有用户）
                all_user_updates = {}
                
                # 添加新用户的更新
                if 'new_viewer_updates' in locals() and new_viewer_updates:
                    all_user_updates.update(new_viewer_updates)
                
                # 添加现有用户的更新
                for viewer_id in all_updated_viewer_ids:
                    if viewer_id in existing_user_sheet_appearances:
                        all_user_updates[viewer_id] = len(existing_user_sheet_appearances[viewer_id])
                
                # 4. 批量更新所有用户的签到次数 (优化之前是逐个更新)
                if all_user_updates:
                    total_updates = len(all_user_updates)
                    logger.debug(f"更新 {total_updates} 个用户的签到信息")
                    
                    # 使用批量更新技术替代逐个更新
                    from sqlalchemy import case
                    
                    # 分批进行更新
                    update_batch_size = self.db_config.get('update_batch_size', 1000)
                    viewer_ids = list(all_user_updates.keys())
                    
                    for i in range(0, total_updates, update_batch_size):
                        # 获取当前批次的用户ID
                        batch_ids = viewer_ids[i:i + update_batch_size]
                        
                        # 构建case语句参数列表
                        # 修复：不再使用列表传递whens参数，而是使用*args方式展开传递
                        whens = []
                        for viewer_id in batch_ids:
                            whens.append((LiveViewer.id == viewer_id, all_user_updates[viewer_id]))
                        
                        # 一次性更新当前批次用户的签到次数
                        session.query(LiveViewer).filter(
                            LiveViewer.id.in_(batch_ids)
                        ).update(
                            {
                                # 修复：使用*whens展开参数列表，而不是传递一个列表
                                LiveViewer.sign_count: case(*whens, else_=LiveViewer.sign_count),
                                LiveViewer.sign_time: all_sign_records[0].sign_time if all_sign_records else None,
                                LiveViewer.is_signed: True
                            },
                            synchronize_session=False
                        )
                        logger.debug(f"已更新 {i+len(batch_ids)}/{total_updates} 个用户的签到次数")
                    
                # 提交事务
                logger.debug("开始提交事务...")
                commit_start_time = time.time()
                session.commit()
                commit_end_time = time.time()
                db_end_time = time.time()
                logger.debug(f"成功提交所有数据库更改，总耗时 {db_end_time - db_start_time:.2f} 秒，提交事务耗时 {commit_end_time - commit_start_time:.2f} 秒")
                
            except Exception as e:
                logger.error(f"处理数据库操作时出错: {str(e)}")
                import traceback
                logger.error(f"错误详情: {traceback.format_exc()}")
                session.rollback()
                results['error_count'] += 1
                results['error_details'].append(f"数据库操作失败: {str(e)}")
            
            # 记录详细的导入结果日志
            logger.debug(f"===== 导入签到数据完成 =====")
            logger.debug(f"成功导入: {results['success_count']} 条记录")
            logger.debug(f"导入失败: {results['error_count']} 条记录")
            logger.debug(f"跳过导入: {results['skipped_count']} 条记录")
            
            if results['success_details']:
                logger.debug(f"成功详情: {', '.join(results['success_details'][:10])}..." if len(results['success_details']) > 10 else f"成功详情: {', '.join(results['success_details'])}")
            
            if results['error_details']:
                logger.debug(f"错误详情: {', '.join(results['error_details'][:10])}..." if len(results['error_details']) > 10 else f"错误详情: {', '.join(results['error_details'])}")
            
            if results['skipped_details']:
                logger.debug(f"跳过详情: {', '.join(results['skipped_details'][:10])}..." if len(results['skipped_details']) > 10 else f"跳过详情: {', '.join(results['skipped_details'])}")
            
            # 返回详细结果信息用于UI显示
            detailed_results = {
                'success_count': results['success_count'],
                'error_count': results['error_count'],
                'skipped_count': results['skipped_count'],
                'success_details': results['success_details'][:50] if len(results['success_details']) > 50 else results['success_details'],
                'error_details': results['error_details'][:50] if len(results['error_details']) > 50 else results['error_details'],
                'skipped_details': results['skipped_details'][:50] if len(results['skipped_details']) > 50 else results['skipped_details']
            }
            
            return detailed_results
            
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
                
    def _parse_sheet(self, excel_path, sheet_name, sheet_index, shared_data, result_queue):
        """解析单个sheet的数据，不进行数据库操作，只收集数据
        
        Args:
            excel_path: Excel文件路径
            sheet_name: sheet名称
            sheet_index: sheet索引
            shared_data: 共享数据
            result_queue: 结果队列
            
        Returns:
            dict: 处理结果
        """
        # 不需要导入数据库相关的模块，只做数据采集
        sheet_result = {
            'sheet_name': sheet_name,
            'success_count': 0,
            'error_count': 0,
            'skipped_count': 0,
            'success_details': [],
            'error_details': [],
            'skipped_details': [],
            'new_viewers': [],             # 存储新用户的数据字典
            'sign_records': [],            # 存储签到记录的数据字典
            'updated_viewer_ids': set()    # 存储需要更新的用户ID
        }
        
        try:
            # 获取共享数据（只有基本数据类型，不包含SQLAlchemy对象）
            live_id = shared_data['live_id']
            live_livingid = shared_data['live_livingid']
            existing_name_map = shared_data['existing_name_map'].copy()  # 复制一份，避免多线程修改冲突
            
            # 使用共享资源中的Excel文件对象读取sheet数据，而不是重新打开文件
            logger.debug(f"线程{threading.current_thread().name} 开始处理Sheet: {sheet_name}")
            
            # 如果excel_path是字符串，则是文件路径，如果是ExcelFile对象，则直接使用
            if isinstance(excel_path, str):
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
            else:
                # 直接使用传入的Excel对象
                df = excel_path.parse(sheet_name)
            
            # 打印基本信息
            logger.debug(f"Sheet '{sheet_name}' 包含 {len(df)} 行, {df.shape[1]} 列")
            
            # 为DataFrame添加sheet名称属性，方便后续解析时间
            df.name = sheet_name
            
            # 验证数据格式
            if not self._validate_sheet_data(df):
                logger.warning(f"Sheet {sheet_name} 数据格式不正确")
                sheet_result['error_count'] += 1
                result_queue.put(sheet_result)
                return sheet_result
            
            # 解析签到时间
            try:
                sign_time = self._parse_sign_time(df)
                logger.debug(f"获取到签到时间: {sign_time}")
                sheet_result['sign_time'] = sign_time
            except ValueError as e:
                logger.error(f"解析签到时间失败: {str(e)}")
                sheet_result['error_count'] += 1
                result_queue.put(sheet_result)
                return sheet_result

            # 解析已签到人数
            try:
                # 使用动态的时间行索引，而不是硬编码的2
                time_row_idx = getattr(df, 'time_row_idx', 0)
                count_col_idx = getattr(df, 'count_col_idx', 1)
                
                # 使用动态计算的索引获取签到人数
                signed_count = df.iloc[time_row_idx + 1, count_col_idx]  # 签到人数在时间行的下一行
                
                if pd.notna(signed_count):
                    try:
                        signed_count = int(signed_count)
                        logger.debug(f"已签到人数: {signed_count}")
                    except (ValueError, TypeError):
                        logger.warning(f"签到人数 '{signed_count}' 不是有效的整数，使用默认值0")
                        signed_count = 0
                else:
                    signed_count = 0
                    logger.warning("未找到有效的已签到人数，默认为0")
            except Exception as e:
                logger.warning(f"解析已签到人数失败: {str(e)}，使用默认值0")
                signed_count = 0

            # 获取当前sheet对应的签到次数（按sheet索引计算）
            sign_sequence = sheet_index + 1  # 从1开始计数
            logger.debug(f"当前sheet '{sheet_name}' 对应的签到次数: {sign_sequence}")
            sheet_result['sign_sequence'] = sign_sequence
            
            # 获取成员标题行索引
            member_row_idx = getattr(df, 'member_row_idx', 4)  # 默认为4，如果未设置
            
            # 从成员标题行的下一行开始处理签到数据
            sheet_success_count = 0
            skipped_count = 0
            
            for i in range(member_row_idx + 1, len(df)):  # 动态确定起始行，而不是硬编码的6
                try:
                    # 打印当前正在处理的行内容
                    # 获取会员名称和部门
                    if pd.isna(df.iloc[i, 0]):
                        continue
                    
                    member_name = str(df.iloc[i, 0]).strip()
                    if not member_name:
                        continue
                        
                    # 获取部门信息
                    department = ""
                    if df.shape[1] > 1 and i < len(df) and pd.notna(df.iloc[i, 1]):  # 第2列是部门
                        try:
                            department = str(df.iloc[i, 1]).strip()
                        except (TypeError, ValueError, AttributeError) as e:
                            logger.warning(f"处理第{i+1}行部门信息出错: {str(e)}，使用空字符串代替")
                            department = ""
                    
                    # 处理微信用户名称，去除@微信后缀
                    # 注意：这里直接调用静态方法，不涉及数据库对象
                    try:
                        import re
                        if '@微信' in member_name:
                            processed_member_name = member_name.replace('@微信', '')
                        else:
                            processed_member_name = member_name
                        # 清理特殊字符
                        processed_member_name = re.sub(r'[^\w\s.\-]', '', processed_member_name).strip()
                        
                        # 记录下原始名称和处理后的名称
                        logger.debug(f"处理用户名称: '{member_name}' -> '{processed_member_name}'")
                    except Exception as e:
                        logger.warning(f"处理第{i+1}行用户名称出错: {str(e)}，使用原始名称")
                        processed_member_name = member_name
                    
                    # 只检查本地映射中是否有这个用户，不查询数据库
                    record_key = processed_member_name.lower()
                    logger.debug(f"查找用户记录，关键字: '{record_key}'")
                    
                    # 在映射中查找用户，只使用基本数据
                    if record_key in existing_name_map:
                        viewer_info = existing_name_map[record_key]
                        logger.debug(f"在缓存中找到用户: {viewer_info['name']}")
                    
                        # 用户已存在，收集签到记录所需数据（只是基础数据，不创建对象）
                        try:
                            # 记录ID，用于后续更新
                            sheet_result['updated_viewer_ids'].add(viewer_info['id'])
                            
                            # 收集创建签到记录所需的数据
                            sign_record_data = {
                                'viewer_id': viewer_info['id'],
                                'original_member_name': member_name
                            }
                            
                            # 将签到记录数据添加到结果中
                            sheet_result['sign_records'].append(sign_record_data)
                            sheet_success_count += 1
                            sheet_result['success_details'].append(f"为现有用户创建签到记录: {processed_member_name}")
                        except Exception as e:
                            logger.error(f"创建签到记录数据出错，第{i+1}行: {str(e)}")
                            sheet_result['error_count'] += 1
                            sheet_result['error_details'].append(f"创建签到记录失败: {processed_member_name}, 原因: {str(e)}")
                            continue
                    else:
                        # 用户不存在，收集创建新用户所需数据
                        logger.debug(f"未在缓存中找到用户: '{processed_member_name}'，将创建新用户")
                        
                        # 生成唯一的userid，使用成员名称
                        # 为避免重复，添加时间戳和行号
                        userid = f"wx_{processed_member_name}_{int(time.time())}_{i}"
                        
                        # 收集创建新用户所需的数据
                        try:
                            viewer_data = {
                                'userid': userid,
                                'name': processed_member_name,
                                'department': department,
                                'original_member_name': member_name
                            }
                            
                            # 将新用户数据添加到结果中
                            sheet_result['new_viewers'].append(viewer_data)
                            sheet_success_count += 1
                            sheet_result['success_details'].append(f"添加新用户: {processed_member_name}")
                                
                        except Exception as e:
                            logger.error(f"创建用户数据出错，第{i+1}行: {str(e)}")
                            sheet_result['error_count'] += 1
                            sheet_result['error_details'].append(f"创建用户数据失败: {processed_member_name}, 原因: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"处理第{i+1}行时出错: {str(e)}")
                    import traceback
                    logger.error(f"错误详情: {traceback.format_exc()}")
                    sheet_result['error_count'] += 1
                    sheet_result['error_details'].append(f"处理记录失败（行{i+1}）: {str(e)}")
            
            # 更新sheet_result
            sheet_result['success_count'] = sheet_success_count
            sheet_result['skipped_count'] = skipped_count
            
            logger.debug(f"Sheet '{sheet_name}' 处理完成，解析 {sheet_success_count} 条记录")
            
            # 将结果放入队列
            result_queue.put(sheet_result)
            return sheet_result
            
        except Exception as e:
            logger.error(f"解析Sheet {sheet_name} 时出错: {str(e)}")
            sheet_result['error_count'] += 1
            sheet_result['error_details'].append(f"解析Sheet失败: {str(e)}")
            result_queue.put(sheet_result)
            return sheet_result
            
    def _validate_sheet_data(self, df: pd.DataFrame) -> bool:
        """验证sheet数据格式
        
        Args:
            df: DataFrame对象
            
        Returns:
            bool: 是否有效
        """
        try:
            sheet_name = getattr(df, 'name', 'unknown')
            logger.debug(f"===== 开始验证Sheet '{sheet_name}' 格式 =====")
            
            # 打印每行的内容 - 前10行
            for i in range(min(10, len(df))):
                row_content = []
                for j in range(min(5, df.shape[1])):
                    value = df.iloc[i, j] if j < df.shape[1] else None
                    row_content.append(f"'{value}'" if pd.notna(value) else "None")
                logger.debug(f"行{i+1}内容: {', '.join(row_content)}")  # 注意：这里i+1是人类可读的行号
            
            # 检查DataFrame是否有足够的行
            min_rows = self.excel_config.get('min_rows', 7)  # 使用配置项，而不是硬编码
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
            
            # 使用配置项决定搜索范围，而不是硬编码
            title_search_range = min(self.excel_config.get('title_search_range', 5), len(df))
            
            # 搜索前几行来查找标题
            for i in range(title_search_range):
                row_text = ' '.join([str(x) for x in df.iloc[i].tolist() if pd.notna(x)])
                logger.debug(f"检查索引{i}行(第{i+1}行)是否包含标题: '{row_text}'")
                
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
                
            logger.debug(f"找到标题行索引：{time_row_idx}(第{time_row_idx+1}行)，" +
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
            
            # 使用配置项确定搜索范围，而不是硬编码
            detail_search_range = min(time_row_idx + self.excel_config.get('detail_search_range', 5), len(df))
            
            for i in range(time_row_idx + 1, detail_search_range):
                row_text = ' '.join([str(x) for x in df.iloc[i].tolist() if pd.notna(x)])
                logger.debug(f"检查索引{i}行(第{i+1}行)是否包含'签到明细': '{row_text}'")
                if "签到明细" in row_text:
                    detail_row_idx = i
                    break
            
            if detail_row_idx == -1:
                logger.warning(f"Sheet '{sheet_name}' 未找到'签到明细'标题行")
                return False
                
            logger.debug(f"找到签到明细行索引：{detail_row_idx}(第{detail_row_idx+1}行)")
            
            # 查找"已签到成员"和"所在部门"标题
            member_row_idx = -1
            member_col_idx = -1
            dept_col_idx = -1
            
            # 使用配置项确定搜索范围，而不是硬编码
            member_search_range = min(detail_row_idx + self.excel_config.get('member_search_range', 3), len(df))
            
            for i in range(detail_row_idx + 1, member_search_range):
                row_text = ' '.join([str(x) for x in df.iloc[i].tolist() if pd.notna(x)])
                logger.debug(f"检查索引{i}行(第{i+1}行)是否包含'已签到成员': '{row_text}'")
                
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
                
            logger.debug(f"找到成员标题行索引：{member_row_idx}(第{member_row_idx+1}行)，" +
                        f"成员列索引：{member_col_idx}(第{member_col_idx+1}列)，" +
                        f"部门列索引：{dept_col_idx}(第{dept_col_idx+1}列)")
            
            # 检查是否有成员数据
            has_member_data = False
            for i in range(member_row_idx + 1, len(df)):
                if pd.notna(df.iloc[i, member_col_idx]):
                    member_name = str(df.iloc[i, member_col_idx]).strip()
                    logger.debug(f"在索引{i}行(第{i+1}行)找到成员数据: '{member_name}'")
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
                
            logger.debug(f"===== Sheet '{sheet_name}' 格式验证通过 =====")
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
            logger.debug(f"===== 开始解析Sheet '{sheet_name}' 的签到时间 =====")
            
            # 获取之前在_validate_sheet_data中找到的时间单元格位置
            time_row_idx = getattr(df, 'time_row_idx', 0) 
            time_col_idx = getattr(df, 'time_col_idx', 0)
            
            # 时间值在标题的下一行
            time_value = df.iloc[time_row_idx + 1, time_col_idx]
            logger.debug(f"从索引{time_row_idx+1}行(第{time_row_idx+2}行)索引{time_col_idx}列(第{time_col_idx+1}列)获取签到时间值: '{time_value}'")
            
            # 如果没有找到任何时间值，抛出异常
            if time_value is None or pd.isna(time_value):
                logger.error(f"Sheet '{sheet_name}' 中未找到有效的签到时间")
                raise ValueError("无法从表格中找到有效的签到时间")
            
            logger.debug(f"获取到原始签到时间值: '{time_value}', 类型: {type(time_value)}")
                
            # 处理不同类型的时间值
            if isinstance(time_value, pd.Timestamp):
                logger.debug(f"时间值是pd.Timestamp类型，转换为: {time_value.to_pydatetime()}")
                return time_value.to_pydatetime()
            elif isinstance(time_value, datetime):
                logger.debug(f"时间值已经是datetime类型: {time_value}")
                return time_value
            elif isinstance(time_value, str):
                logger.debug(f"时间值是字符串类型，尝试解析: '{time_value}'")
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
                        logger.debug(f"使用格式 '{fmt}' 成功解析时间: {parsed_time}")
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
                        logger.debug(f"使用正则表达式成功解析时间: {parsed_time}")
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