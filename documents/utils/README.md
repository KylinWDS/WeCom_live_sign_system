# 工具模块文档

## 概述
工具模块提供了一系列通用工具函数和类，用于简化系统各个模块的开发，提高代码复用性和可维护性。该模块包含了日志、加密、文件操作、数据处理、格式转换等多种工具。

## 与启动器的集成

工具模块的日志功能与启动器深度整合，提供了从启动初期就能正常工作的日志记录能力。错误处理工具被启动器用于捕获和展示全局异常，提升用户体验。

## 目录结构

### 1. 日志工具 (logger/)
日志记录相关工具。

主要内容：
- 日志配置 (LogConfig)
- 日志记录器 (Logger)
- 日志格式化器 (Formatter)
- 日志处理器 (Handler)
- 日志过滤器 (Filter)
- 日志轮转 (Rotator)

### 2. 加密工具 (crypto/)
数据加密解密相关工具。

主要内容：
- AES加密 (AESCipher)
- 哈希工具 (HashUtils)
- Base64工具 (Base64Utils)
- 密码工具 (PasswordUtils)
- 令牌工具 (TokenUtils)
- 随机数生成器 (RandomGenerator)

### 3. 文件工具 (file/)
文件操作相关工具。

主要内容：
- 文件读写 (FileIO)
- 目录操作 (DirectoryUtils)
- 文件监控 (FileWatcher)
- 临时文件 (TempFileManager)
- 文件备份 (BackupUtils)
- 文件类型检测 (FileTypeDetector)

### 4. 数据工具 (data/)
数据处理相关工具。

主要内容：
- JSON工具 (JSONUtils)
- CSV工具 (CSVUtils)
- Excel工具 (ExcelUtils)
- 数据验证 (Validator)
- 数据转换 (Converter)
- 数据过滤 (Filter)

### 5. 网络工具 (network/)
网络操作相关工具。

主要内容：
- HTTP客户端 (HTTPClient)
- URL工具 (URLUtils)
- IP工具 (IPUtils)
- 请求限流 (RateLimiter)
- 网络检测 (NetworkDetector)
- 代理设置 (ProxySettings)

### 6. 时间工具 (time/)
时间处理相关工具。

主要内容：
- 时间格式化 (TimeFormatter)
- 日期计算 (DateCalculator)
- 定时器 (Timer)
- 时区转换 (TimeZoneConverter)
- 日历工具 (CalendarUtils)
- 定时任务 (ScheduledTask)

### 7. 系统工具 (system/)
系统相关工具。

主要内容：
- 进程管理 (ProcessManager)
- 资源监控 (ResourceMonitor)
- 系统信息 (SystemInfo)
- 环境变量 (EnvironmentUtils)
- 命令执行 (CommandExecutor)
- 平台检测 (PlatformDetector)

### 8. 错误处理 (error/)
错误处理相关工具。

主要内容：
- 异常捕获 (ExceptionCatcher)
- 错误日志 (ErrorLogger)
- 用户提示 (UserNotifier)
- 错误恢复 (ErrorRecovery)
- 重试机制 (Retrier)
- 错误码 (ErrorCodes)

### 9. UI工具 (ui_utils/)
UI相关工具。

主要内容：
- 颜色工具 (ColorUtils)
- 图标工具 (IconUtils)
- 消息框 (MessageBox)
- 对话框 (DialogUtils)
- 界面缩放 (ScalingUtils)
- 文本处理 (TextUtils)

### 10. 国际化工具 (i18n/)
国际化相关工具。

主要内容：
- 翻译工具 (Translator)
- 语言设置 (LanguageSettings)
- 本地化 (Localizer)
- 文本资源 (TextResources)
- 语言检测 (LanguageDetector)
- 区域设置 (LocaleSettings)

## 主要功能

### 1. 日志记录

日志模块提供了灵活的日志记录功能，支持多种输出方式和格式化选项。

```python
# 日志初始化
def setup_logger(self, level="INFO", log_file=None, console=True):
    """设置日志记录器"""
    logger = logging.getLogger("wecom_live")
    logger.setLevel(getattr(logging, level))
    
    # 清除已有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] - %(message)s"
    )
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
```

### 2. 加密工具

加密模块提供了多种加密算法和工具，用于保护敏感数据。

```python
class AESCipher:
    """AES加密解密工具"""
    
    def __init__(self, key):
        """初始化AES加密器"""
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()
    
    def encrypt(self, raw):
        """加密数据"""
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode())).decode('utf-8')
    
    def decrypt(self, enc):
        """解密数据"""
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
    
    def _pad(self, s):
        """填充数据"""
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
    
    @staticmethod
    def _unpad(s):
        """去除填充"""
        return s[:-ord(s[len(s)-1:])]
```

### 3. 文件操作

文件操作模块提供了一系列简化文件和目录操作的工具。

```python
class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(directory):
        """确保目录存在，如不存在则创建"""
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return directory
    
    @staticmethod
    def clean_dir(directory):
        """清空目录内容但保留目录"""
        if os.path.exists(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
    
    @staticmethod
    def copy_file(src, dst, overwrite=True):
        """复制文件"""
        if not os.path.exists(src):
            raise FileNotFoundError(f"源文件不存在: {src}")
        
        # 确保目标目录存在
        dst_dir = os.path.dirname(dst)
        FileUtils.ensure_dir(dst_dir)
        
        # 检查是否可以覆盖
        if os.path.exists(dst) and not overwrite:
            return False
        
        shutil.copy2(src, dst)
        return True
    
    @staticmethod
    def safe_filename(filename):
        """生成安全的文件名，去除非法字符"""
        # 替换Windows/Unix文件系统中的非法字符
        return re.sub(r'[\\/*?:"<>|]', "_", filename)
```

### 4. 数据处理

数据处理模块提供了处理各种格式数据的工具。

```python
class ExcelUtils:
    """Excel文件处理工具"""
    
    @staticmethod
    def export_to_excel(data, sheet_name="数据", file_path=None):
        """导出数据到Excel文件"""
        # 创建工作簿和工作表
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        # 写入表头
        if data and isinstance(data[0], dict):
            headers = list(data[0].keys())
            for col_idx, header in enumerate(headers, 1):
                ws.cell(row=1, column=col_idx, value=header)
            
            # 写入数据
            for row_idx, row_data in enumerate(data, 2):
                for col_idx, header in enumerate(headers, 1):
                    ws.cell(row=row_idx, column=col_idx, value=row_data.get(header))
        
        # 自动调整列宽
        for column in ws.columns:
            max_length = 0
            column_letter = openpyxl.utils.get_column_letter(column[0].column)
            for cell in column:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            adjusted_width = max_length + 2
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # 保存文件
        if file_path:
            wb.save(file_path)
            return file_path
        else:
            # 生成临时文件
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".xlsx", prefix="export_"
            )
            temp_file.close()
            wb.save(temp_file.name)
            return temp_file.name
```

### 5. 错误处理

错误处理模块提供了用于捕获、记录和恢复异常的工具。

```python
class ExceptionHandler:
    """全局异常处理器"""
    
    def __init__(self, logger, show_error_dialog=True):
        """初始化异常处理器"""
        self.logger = logger
        self.show_dialog = show_error_dialog
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            # 正常退出，不处理键盘中断异常
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 记录异常信息
        self.logger.error(
            "未捕获的异常", 
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # 格式化错误信息
        error_msg = str(exc_value)
        tb_info = ''.join(traceback.format_tb(exc_traceback))
        
        # 显示错误对话框
        if self.show_dialog:
            msg = (
                f"程序遇到了一个错误:\n\n"
                f"{error_msg}\n\n"
                f"详细信息已记录到日志文件。"
            )
            self._show_error_dialog("程序错误", msg, tb_info)
    
    def _show_error_dialog(self, title, message, details=None):
        """显示错误对话框"""
        try:
            from PySide6.QtWidgets import QMessageBox, QApplication
            
            # 确保有QApplication实例
            app = QApplication.instance()
            if not app:
                app = QApplication(sys.argv)
            
            # 创建错误对话框
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            
            if details:
                msg_box.setDetailedText(details)
            
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        except Exception as e:
            # 如果无法显示QT对话框，回退到控制台输出
            print(f"\n{title}: {message}")
            if details:
                print(f"\n详细信息: {details}")
```

### 6. 时间工具

时间工具模块提供了处理日期时间的便捷函数。

```python
class TimeUtils:
    """时间工具类"""
    
    @staticmethod
    def timestamp_to_str(timestamp, format="%Y-%m-%d %H:%M:%S"):
        """将时间戳转换为字符串"""
        if not timestamp:
            return ""
        return datetime.fromtimestamp(timestamp).strftime(format)
    
    @staticmethod
    def str_to_timestamp(time_str, format="%Y-%m-%d %H:%M:%S"):
        """将字符串转换为时间戳"""
        if not time_str:
            return 0
        return int(datetime.strptime(time_str, format).timestamp())
    
    @staticmethod
    def get_today_range():
        """获取今天的起止时间戳"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return (int(today.timestamp()), int(tomorrow.timestamp() - 1))
    
    @staticmethod
    def get_date_range(days=7):
        """获取最近几天的起止时间戳"""
        end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        start = end - timedelta(days=days-1)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        return (int(start.timestamp()), int(end.timestamp()))
    
    @staticmethod
    def get_month_range(year=None, month=None):
        """获取指定月份的起止时间戳"""
        today = datetime.now()
        year = year or today.year
        month = month or today.month
        
        # 月初
        start = datetime(year, month, 1, 0, 0, 0)
        
        # 下月初
        if month == 12:
            end = datetime(year + 1, 1, 1, 0, 0, 0)
        else:
            end = datetime(year, month + 1, 1, 0, 0, 0)
        
        # 月末
        end = end - timedelta(seconds=1)
        
        return (int(start.timestamp()), int(end.timestamp()))
```

### 7. 系统工具

系统工具模块提供了与操作系统交互的功能。

```python
class SystemUtils:
    """系统工具类"""
    
    @staticmethod
    def get_platform():
        """获取当前平台名称"""
        if sys.platform.startswith('win'):
            return 'windows'
        elif sys.platform.startswith('darwin'):
            return 'macos'
        elif sys.platform.startswith('linux'):
            return 'linux'
        return 'unknown'
    
    @staticmethod
    def get_free_space(path):
        """获取指定路径的可用空间(字节)"""
        if os.path.exists(path):
            return shutil.disk_usage(path).free
        return 0
    
    @staticmethod
    def get_memory_usage():
        """获取当前进程内存使用情况(MB)"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    @staticmethod
    def get_cpu_usage():
        """获取当前进程CPU使用率(%)"""
        process = psutil.Process(os.getpid())
        return process.cpu_percent(interval=0.1)
    
    @staticmethod
    def get_application_path():
        """获取应用程序根路径"""
        if getattr(sys, 'frozen', False):
            # PyInstaller打包后的情况
            return os.path.dirname(sys.executable)
        else:
            # 普通Python环境
            return os.path.dirname(os.path.abspath(__file__))
    
    @staticmethod
    def is_admin():
        """检查当前是否具有管理员权限"""
        try:
            if SystemUtils.get_platform() == 'windows':
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
```

### 8. IP工具

IP工具模块提供了IP地址相关的功能。

```python
class IPUtils:
    """IP工具类"""
    
    @staticmethod
    def get_local_ip():
        """获取本机IP地址"""
        try:
            # 创建一个UDP套接字
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接一个公共IP，不需要真正发送数据
            s.connect(("8.8.8.8", 80))
            # 获取本地IP
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    @staticmethod
    def get_public_ip():
        """获取公网IP地址"""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        try:
            response = requests.get('https://ip.sb', timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        
        return None
    
    @staticmethod
    def is_valid_ip(ip):
        """验证IP地址格式是否有效"""
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False
    
    @staticmethod
    def is_private_ip(ip):
        """检查是否为私有IP地址"""
        # 解析IP
        parts = ip.split('.')
        if len(parts) != 4:
            return False
            
        # 检查是否为私有IP范围
        # 10.0.0.0 - 10.255.255.255
        if parts[0] == '10':
            return True
            
        # 172.16.0.0 - 172.31.255.255
        if parts[0] == '172' and 16 <= int(parts[1]) <= 31:
            return True
            
        # 192.168.0.0 - 192.168.255.255
        if parts[0] == '192' and parts[1] == '168':
            return True
            
        return False
```

## 使用示例

### 1. 使用日志记录
```python
from src.utils.logger import LogManager

# 初始化日志管理器
log_manager = LogManager(log_level="INFO", log_file="logs/app.log")
logger = log_manager.get_logger()

# 记录日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")

# 使用上下文记录额外信息
with logger.contextualize(user="admin", operation="login"):
    logger.info("用户登录成功")
```

### 2. 使用加密工具
```python
from src.utils.crypto import AESCipher, PasswordUtils

# AES加密
cipher = AESCipher("my-secret-key")
encrypted = cipher.encrypt("敏感数据")
decrypted = cipher.decrypt(encrypted)

# 密码加密和验证
hashed = PasswordUtils.hash_password("user-password")
is_valid = PasswordUtils.verify_password("user-password", hashed)
```

### 3. 使用文件工具
```python
from src.utils.file import FileUtils

# 确保目录存在
data_dir = FileUtils.ensure_dir("data/exports")

# 生成安全文件名
filename = FileUtils.safe_filename("企业微信直播数据 2023/05/30.xlsx")

# 复制文件
FileUtils.copy_file("templates/report.xlsx", f"exports/{filename}")
```

### 4. 使用数据导出工具
```python
from src.utils.data import ExcelUtils

# 导出数据到Excel
data = [
    {"姓名": "张三", "部门": "技术部", "观看时长": 3600},
    {"姓名": "李四", "部门": "市场部", "观看时长": 1800}
]
file_path = ExcelUtils.export_to_excel(
    data, 
    sheet_name="观看记录", 
    file_path="exports/观看记录.xlsx"
)
```

### 5. 使用时间工具
```python
from src.utils.time import TimeUtils

# 获取时间范围
today_start, today_end = TimeUtils.get_today_range()
week_start, week_end = TimeUtils.get_date_range(7)
month_start, month_end = TimeUtils.get_month_range()

# 时间格式转换
now_str = TimeUtils.timestamp_to_str(time.time())
timestamp = TimeUtils.str_to_timestamp("2023-05-30 14:30:00")
```

## 线程安全

工具模块设计时充分考虑了多线程环境下的使用：

1. **线程安全的日志记录**: 使用线程锁保护日志写入操作
2. **无状态工具函数**: 大多数工具函数设计为无状态，避免线程冲突
3. **线程本地存储**: 对于需要保持状态的工具，使用线程本地存储
4. **原子操作**: 重要操作实现为原子操作
5. **并发控制**: 提供并发限制机制

```python
class ThreadSafeCounter:
    """线程安全的计数器"""
    
    def __init__(self, initial_value=0):
        self.value = initial_value
        self.lock = threading.RLock()
        
    def increment(self, amount=1):
        """增加计数"""
        with self.lock:
            self.value += amount
            return self.value
            
    def decrement(self, amount=1):
        """减少计数"""
        with self.lock:
            self.value -= amount
            return self.value
            
    def get(self):
        """获取当前值"""
        with self.lock:
            return self.value
```

## 日志规范

工具模块对日志记录格式和内容进行了规范：

1. **级别准则**:
   - DEBUG: 详细的开发调试信息
   - INFO: 正常操作的信息
   - WARNING: 需要注意但不是错误的情况
   - ERROR: 发生错误但不影响系统继续运行
   - CRITICAL: 严重错误可能导致系统无法继续运行

2. **格式规范**:
   - 记录时间戳
   - 记录日志级别
   - 记录模块名和行号
   - 对于重要操作记录用户信息
   - 对于错误记录完整异常信息

3. **敏感信息处理**:
   - 密码等敏感信息不直接记录
   - 令牌、密钥等信息记录前脱敏处理

## 注意事项
1. 使用日志工具时注意选择合适的日志级别
2. 加密数据时妥善保管加密密钥
3. 处理大文件时注意内存使用
4. 网络操作添加超时机制
5. 文件操作前检查路径和权限
6. 长时间操作使用线程避免阻塞UI
7. 注意处理和记录可能的异常
8. 涉及用户数据的操作确保安全和隐私 