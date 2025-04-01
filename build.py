#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信直播签到系统打包工具
集成所有平台打包功能，支持命令行和被调用两种方式
作者: Kylin
邮箱: kylin_wds@163.com
"""

import os
import sys
import shutil
import argparse
import platform
import subprocess
import time
import json
import logging
import tempfile
import re
import glob
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('PackageBuilder')

# 全局变量
APP_NAME = "企业微信直播签到系统"
APP_VERSION = "1.0.0"  # 可从setup.py或其他地方动态获取
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 工具函数
def run_command(cmd: List[str], shell: bool = False, cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """执行shell命令并返回结果"""
    logger.debug(f"执行命令: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
        cwd=cwd,
        text=True,
        encoding='utf-8'
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def is_tool_installed(name: str) -> bool:
    """检查系统中是否安装了指定工具"""
    try:
        devnull = open(os.devnull, 'w')
        if platform.system() == "Windows":
            subprocess.Popen([name], stdout=devnull, stderr=devnull, shell=True).communicate()
        else:
            subprocess.Popen([f"command -v {name}"], stdout=devnull, stderr=devnull, shell=True).communicate()
    except OSError:
        return False
    return True

def get_python_version() -> str:
    """获取Python版本信息"""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

class ResourceManager:
    """资源文件管理类"""
    
    def __init__(self, base_dir: str = SCRIPT_DIR):
        self.base_dir = base_dir
        self.src_dir = os.path.join(base_dir, 'src')
        self.tools_dir = os.path.join(base_dir, 'tools')
        self.assets_dir = os.path.join(self.tools_dir, 'assets')
        
    def ensure_icon_exists(self) -> str:
        """确保图标文件存在，返回图标路径"""
        icon_path = os.path.join(self.assets_dir, 'app.png')
        if not os.path.exists(icon_path):
            logger.info("图标文件不存在，尝试创建默认图标")
            try:
                # 如果目录不存在，先创建
                os.makedirs(self.assets_dir, exist_ok=True)
                
                # 尝试使用create_icon.py创建
                icon_creator = os.path.join(self.tools_dir, 'create_icon.py')
                if os.path.exists(icon_creator):
                    logger.info("使用create_icon.py创建图标")
                    run_command([sys.executable, icon_creator], cwd=self.base_dir)
                else:
                    logger.warning("未找到create_icon.py，将使用空白图标")
                    # 创建一个简单的图标文件
                    with open(icon_path, 'wb') as f:
                        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x06bKGD\x00\xff\x00\xff\x00\xff\xa0\xbd\xa7\x93\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xe5\x05\x07\n\x1c\x12\xc3G\xef\xbd\x00\x00\x00\x1diTXtComment\x00\x00\x00\x00\x00Created with GIMPd.e\x07\x00\x00\x00\x0eIDATx\xda\xed\xc1\x01\x01\x00\x00\x00\x80\x90\xfe\xaf\xb6\xfb\x01\x00\x00\x00\x00\x00\x00\x00\x00\xec\r\x00\x00\xff\xff\x03\x00\x18\xe3\x00\x01\x82\xb3\x9c\xb2\x00\x00\x00\x00IEND\xaeB`\x82')
            except Exception as e:
                logger.error(f"创建图标失败: {e}")
                raise
        return icon_path
    
    def collect_data_files(self) -> List[Tuple[str, str]]:
        """收集数据文件"""
        data_files = []
        
        # 收集src目录下的所有非Python文件
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                if not file.endswith('.py') and not file.endswith('.pyc'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(os.path.dirname(full_path), self.base_dir)
                    data_files.append((full_path, rel_path))
        
        # 收集其他可能需要的配置文件
        config_files = []
        for config_file in config_files:
            if os.path.exists(config_file):
                data_files.append((config_file, os.path.dirname(config_file)))
                
        logger.info(f"收集了 {len(data_files)} 个数据文件")
        return data_files

class PlatformHandler:
    """平台特定功能处理类"""
    
    def __init__(self):
        self.system = platform.system()
        self.machine = platform.machine()
        self.is_windows = self.system == "Windows"
        self.is_macos = self.system == "Darwin"
        self.is_linux = self.system == "Linux"
        
        # 检测是否是M系列Mac
        self.is_apple_silicon = False
        if self.is_macos:
            try:
                output = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True).decode('utf-8')
                self.is_apple_silicon = "Apple" in output
            except:
                self.is_apple_silicon = platform.processor() == "arm"
    
    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息"""
        return {
            "system": self.system,
            "machine": self.machine,
            "processor": platform.processor(),
            "is_64bit": platform.architecture()[0] == "64bit",
            "is_apple_silicon": self.is_apple_silicon if self.is_macos else False
        }
    
    def create_macos_fix_script(self) -> str:
        """创建macOS特定的修复脚本"""
        if not self.is_macos:
            return ""
            
        fix_script_path = os.path.join(SCRIPT_DIR, "fix_macos_crash.py")
        with open(fix_script_path, "w", encoding="utf-8") as f:
            f.write("""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
macOS应用修复脚本
修复打包后的macOS应用无法启动的问题
\"\"\"

import os
import sys
import subprocess
import glob
import shutil
from pathlib import Path

def fix_app_bundle(app_path):
    \"\"\"修复应用包\"\"\"
    if not os.path.exists(app_path):
        print(f"错误: 应用 {app_path} 不存在")
        return False
        
    print(f"正在修复应用: {app_path}")
    
    # 修复Info.plist
    info_plist = os.path.join(app_path, "Contents", "Info.plist")
    if os.path.exists(info_plist):
        # 使用PlistBuddy修复
        subprocess.run(["/usr/libexec/PlistBuddy", "-c", "Add :NSHighResolutionCapable bool true", info_plist], 
                       stderr=subprocess.PIPE)
        subprocess.run(["/usr/libexec/PlistBuddy", "-c", "Add :NSSupportsAutomaticGraphicsSwitching bool true", info_plist],
                       stderr=subprocess.PIPE)
        print("已修复Info.plist")
    
    # 设置执行权限
    macos_dir = os.path.join(app_path, "Contents", "MacOS")
    if os.path.exists(macos_dir):
        for executable in glob.glob(os.path.join(macos_dir, "*")):
            if os.path.isfile(executable):
                os.chmod(executable, 0o755)
        print("已设置可执行权限")
    
    return True

if __name__ == "__main__":
    # 查找dist目录下的.app文件
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "企业微信直播签到系统.app")
    if os.path.exists(app_path):
        fix_app_bundle(app_path)
    else:
        print("未找到应用包，请确认打包是否成功")
""")
        os.chmod(fix_script_path, 0o755)
        logger.info(f"创建macOS修复脚本: {fix_script_path}")
        return fix_script_path
            
    def create_memory_hook(self, level: str = "medium") -> str:
        """创建内存优化钩子脚本"""
        levels = {
            "low": 1024,
            "medium": 2048,
            "high": 4096
        }
        memory_limit = levels.get(level.lower(), 2048)
        
        hook_path = os.path.join(SCRIPT_DIR, "memory_hook.py")
        with open(hook_path, "w", encoding="utf-8") as f:
            f.write(f"""# -*- coding: utf-8 -*-
\"\"\"
内存优化钩子脚本 - 内存级别: {level}
\"\"\"

def warn_on_low_memory():
    \"\"\"在内存不足时警告\"\"\"
    import psutil
    import sys
    import os
    
    # 检查系统内存
    memory = psutil.virtual_memory()
    available_mb = memory.available / (1024 * 1024)
    
    if available_mb < {memory_limit}:
        print(f"警告: 系统可用内存不足 ({{available_mb:.1f}}MB < {memory_limit}MB)")
        print("应用可能运行缓慢或不稳定")
        # 可以在这里添加更多处理逻辑
        
warn_on_low_memory()
""")
        logger.info(f"创建内存优化钩子: {hook_path}，内存级别: {level}")
        return hook_path

class PackageBuilder:
    """应用程序打包器"""
    
    def __init__(self):
        """初始化打包器"""
        self.resources = ResourceManager()
        self.platform = PlatformHandler()
        self.workdir = SCRIPT_DIR
        self.dist_dir = os.path.join(self.workdir, "dist")
        self.build_dir = os.path.join(self.workdir, "build")
        
    def check_dependencies(self) -> bool:
        """检查依赖项"""
        # 检查Python版本
        if sys.version_info < (3, 7):
            logger.error(f"Python版本过低: {get_python_version()}, 需要3.7+")
            return False
            
        # 检查PyInstaller
        try:
            import PyInstaller
            logger.info(f"PyInstaller版本: {PyInstaller.__version__}")
        except ImportError:
            logger.error("未安装PyInstaller，请先执行: pip install pyinstaller")
            return False
            
        # 检查其他依赖
        missing_deps = []
        try:
            import psutil
        except ImportError:
            missing_deps.append("psutil")
            
        if missing_deps:
            logger.error(f"缺少依赖: {', '.join(missing_deps)}")
            logger.info("请执行: pip install " + " ".join(missing_deps))
            return False
            
        return True
        
    def clean_build(self):
        """清理构建目录"""
        logger.info("清理构建目录...")
        for path in [self.build_dir, self.dist_dir]:
            if os.path.exists(path):
                shutil.rmtree(path)
                logger.info(f"已删除: {path}")
        
        # 删除临时文件
        for pattern in ["*.spec", "memory_hook*.py", "fast_start_hook.py"]:
            for path in glob.glob(os.path.join(self.workdir, pattern)):
                os.remove(path)
                logger.info(f"已删除: {path}")
                
    def prepare_build(self, options: Dict[str, Any]):
        """准备构建环境"""
        # 确保目录存在
        os.makedirs(self.dist_dir, exist_ok=True)
        
        # 确保图标存在
        icon_path = self.resources.ensure_icon_exists()
        options["icon_path"] = icon_path
        
        # 准备平台特定文件
        if self.platform.is_macos:
            options["fix_script"] = self.platform.create_macos_fix_script()
            
        # 准备内存优化钩子
        if options.get("memory_level"):
            options["memory_hook"] = self.platform.create_memory_hook(options["memory_level"])
            
        return options
        
    def build_application(self, options: Dict[str, Any]) -> bool:
        """构建应用程序"""
        if not self.check_dependencies():
            return False
            
        # 准备构建环境
        options = self.prepare_build(options)
        
        # 构建PyInstaller命令
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name", APP_NAME,
            "--icon", options["icon_path"],
        ]
        
        # 添加模式选项
        if options.get("onefile", False):
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")
            
        # 添加窗口选项
        if not options.get("console", False):
            cmd.append("--windowed")
            
        # 添加调试选项
        if options.get("debug", False):
            cmd.append("--debug")
            
        # 添加架构选项 (仅Mac)
        if self.platform.is_macos:
            target_arch = options.get("target_arch", "")
            if target_arch == "universal":
                cmd.extend(["--target-architecture", "universal2"])
            elif target_arch == "intel":
                cmd.extend(["--target-architecture", "x86_64"])
            elif target_arch == "arm":
                cmd.extend(["--target-architecture", "arm64"])
        
        # 添加钩子和数据文件
        if options.get("memory_hook"):
            cmd.extend(["--additional-hooks-dir", os.path.dirname(options["memory_hook"])])
            
        # 收集数据文件
        data_files = self.resources.collect_data_files()
        for src, dest in data_files:
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])
            
        # 添加入口点
        launcher_path = os.path.join(self.workdir, "launcher.py")
        cmd.append(launcher_path)
        
        # 执行构建
        logger.info(f"开始构建: {' '.join(cmd)}")
        returncode, stdout, stderr = run_command(cmd)
        
        if returncode != 0:
            logger.error(f"构建失败: {stderr}")
            return False
            
        logger.info("构建成功!")
        
        # 执行平台特定修复
        if self.platform.is_macos and options.get("fix_script"):
            logger.info("执行macOS特定修复...")
            fix_script = options["fix_script"]
            run_command([sys.executable, fix_script])
            
        return True
        
    def create_launcher_scripts(self):
        """创建启动脚本"""
        if self.platform.is_windows:
            # 创建Windows启动脚本
            bat_path = os.path.join(self.dist_dir, f"启动{APP_NAME}.bat")
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(f'@echo off\ncd /d "%~dp0"\nstart "" "{APP_NAME}\\{APP_NAME}.exe"\n')
            logger.info(f"创建启动脚本: {bat_path}")
        elif self.platform.is_macos:
            # 创建macOS启动脚本
            sh_path = os.path.join(self.dist_dir, f"启动{APP_NAME}.command")
            app_path = os.path.join(self.dist_dir, f"{APP_NAME}.app")
            with open(sh_path, "w", encoding="utf-8") as f:
                f.write(f'#!/bin/bash\ncd "$(dirname "$0")"\nopen "{APP_NAME}.app"\n')
            os.chmod(sh_path, 0o755)
            logger.info(f"创建启动脚本: {sh_path}")
        elif self.platform.is_linux:
            # 创建Linux启动脚本
            sh_path = os.path.join(self.dist_dir, f"启动{APP_NAME}.sh")
            with open(sh_path, "w", encoding="utf-8") as f:
                f.write(f'#!/bin/bash\ncd "$(dirname "$0")"\n./{APP_NAME}/{APP_NAME}\n')
            os.chmod(sh_path, 0o755)
            logger.info(f"创建启动脚本: {sh_path}")
            
    def package(self, options: Dict[str, Any]) -> bool:
        """完整打包流程"""
        # 清理旧的构建文件
        if options.get("clean", True):
            self.clean_build()
            
        # 构建应用
        if not self.build_application(options):
            return False
            
        # 创建启动脚本
        self.create_launcher_scripts()
        
        # 显示完成信息
        logger.info(f"\n打包完成! 输出位置: {self.dist_dir}")
        if self.platform.is_macos:
            logger.info(f"应用程序: {os.path.join(self.dist_dir, f'{APP_NAME}.app')}")
        elif self.platform.is_windows:
            if options.get("onefile", False):
                logger.info(f"应用程序: {os.path.join(self.dist_dir, f'{APP_NAME}.exe')}")
            else:
                logger.info(f"应用程序: {os.path.join(self.dist_dir, APP_NAME, f'{APP_NAME}.exe')}")
                
        return True 

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description=f"企业微信直播签到系统打包工具 v{APP_VERSION}")
    
    # 基本选项
    parser.add_argument("--onefile", action="store_true", help="打包为单个文件")
    parser.add_argument("--console", action="store_true", help="显示控制台窗口")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--no-clean", dest="clean", action="store_false", help="不清理旧的构建文件")
    parser.set_defaults(clean=True)
    
    # 内存优化选项
    parser.add_argument("--memory-level", choices=["low", "medium", "high"], default="medium",
                       help="内存优化级别: low=1024MB, medium=2048MB, high=4096MB")
    
    # macOS特定选项
    if platform.system() == "Darwin":
        parser.add_argument("--target-arch", choices=["auto", "intel", "arm", "universal"],
                            default="auto", help="目标架构 (仅macOS)")
    
    args = parser.parse_args()
    
    # 处理自动架构选择
    if platform.system() == "Darwin" and args.target_arch == "auto":
        # 检测Mac芯片类型
        try:
            output = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True).decode('utf-8')
            if "Apple" in output:
                args.target_arch = "arm"
            else:
                args.target_arch = "intel"
        except:
            args.target_arch = "intel"
    
    return args

def main():
    """主函数"""
    print(f"企业微信直播签到系统打包工具 v{APP_VERSION}")
    print(f"系统: {platform.system()} {platform.machine()}")
    print(f"Python: {get_python_version()}")
    print("-" * 50)
    
    # 解析命令行参数
    args = parse_args()
    
    # 配置选项
    options = vars(args)
    
    # 创建打包器并执行打包
    builder = PackageBuilder()
    success = builder.package(options)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 