#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信直播签到系统启动器
作者: Kylin
邮箱: kylin_wds@163.com
"""

import os
import sys
import time
import platform
import logging
import traceback
import importlib

# 设置全局变量
APP_NAME = "企业微信直播签到系统"
APP_VERSION = "1.0.0"  # 可从其他文件动态获取
DEBUG_MODE = os.environ.get("DEBUG_MODE", "0") == "1"

# 配置日志 - 开发环境下仅输出到控制台
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("Launcher")

class SplashScreen:
    """启动画面"""
    
    def __init__(self, app_name=APP_NAME):
        self.app_name = app_name
        self.window = None
        self._running = False
        self.progress = None
        self.status_label = None
        
    def show(self):
        """显示启动画面"""
        if self._running:
            return
            
        self._running = True
        # 不再使用线程，直接在主线程中初始化窗口但不阻塞
        self._init_splash()
        
    def _init_splash(self):
        """初始化启动画面但不运行主循环"""
        try:
            # 尝试导入tkinter
            import tkinter as tk
            from tkinter import ttk
            
            # 创建窗口
            self.window = tk.Tk()
            self.window.title(f"{self.app_name} - 启动中")
            self.window.geometry("400x200")
            self.window.configure(bg="#f0f0f0")
            self.window.attributes("-topmost", True)
            
            # 居中窗口
            self.window.update_idletasks()
            width = self.window.winfo_width()
            height = self.window.winfo_height()
            x = (self.window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.window.winfo_screenheight() // 2) - (height // 2)
            self.window.geometry(f"{width}x{height}+{x}+{y}")
            
            # 添加内容
            main_frame = tk.Frame(self.window, bg="#f0f0f0")
            main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
            
            title_label = tk.Label(
                main_frame, 
                text=self.app_name, 
                font=("Arial", 16, "bold"),
                bg="#f0f0f0"
            )
            title_label.pack(pady=(0, 10))
            
            self.status_label = tk.Label(
                main_frame, 
                text="正在启动中，请稍候...", 
                font=("Arial", 10),
                bg="#f0f0f0"
            )
            self.status_label.pack(pady=(0, 20))
            
            # 进度条 - 确定模式
            self.progress = ttk.Progressbar(
                main_frame, 
                orient="horizontal", 
                length=350, 
                mode="determinate"
            )
            self.progress.pack(pady=10)
            
            # 添加进度百分比标签
            self.percent_label = tk.Label(
                main_frame,
                text="0%",
                font=("Arial", 9),
                bg="#f0f0f0"
            )
            self.percent_label.pack(pady=(0, 5))
            
            # 版本信息
            version_label = tk.Label(
                main_frame, 
                text=f"版本: v{APP_VERSION}", 
                font=("Arial", 8),
                fg="#888888",
                bg="#f0f0f0"
            )
            version_label.pack(side=tk.BOTTOM, anchor=tk.SE)
            
            # 更新窗口但不阻塞主线程
            self.set_progress(0, "正在初始化...")
            self.window.update()
            
        except ImportError:
            logger.warning("未找到tkinter模块，将不显示启动画面")
        except Exception as e:
            logger.error(f"创建启动画面时出错: {e}")
    
    def set_progress(self, value, status_text=None):
        """设置进度条的值和状态文本"""
        if not self._running or not self.window:
            return
            
        try:
            if self.progress:
                self.progress["value"] = value
                if self.percent_label:
                    self.percent_label.config(text=f"{int(value)}%")
                
            if status_text and self.status_label:
                self.status_label.config(text=status_text)
                
            self.update()
        except Exception as e:
            logger.error(f"更新进度条时出错: {e}")
    
    def update(self):
        """更新启动画面"""
        if self.window and self._running:
            try:
                self.window.update()
            except:
                pass
            
    def close(self):
        """关闭启动画面"""
        if not self._running:
            return
            
        self._running = False
        
        if self.window:
            try:
                self.window.destroy()
            except:
                pass

def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    # 记录异常信息
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.error(f"未捕获的异常:\n{error_msg}")
    
    # 显示错误对话框
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "应用程序错误",
            f"很抱歉，应用程序遇到了一个错误，需要关闭。\n\n错误: {exc_value}\n\n详细信息已记录到日志文件。"
        )
        root.destroy()
    except:
        print(f"错误: {exc_value}")
        print("详细错误信息:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # 标准异常处理器
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def main():
    """主函数"""
    # 设置全局异常处理器
    sys.excepthook = handle_exception
    
    # 记录启动信息
    logger.info(f"启动 {APP_NAME} v{APP_VERSION}")
    logger.info(f"平台: {platform.system()} {platform.machine()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"工作目录: {os.getcwd()}")
    
    # 启动时间
    start_time = time.time()
    
    # 创建启动画面
    splash = SplashScreen()
    
    try:
        # 显示启动画面
        splash.show()
        
        # 更新进度
        splash.set_progress(30, "准备加载模块...")
        
        # 导入主模块
        logger.info("正在加载主模块...")
        splash.set_progress(60, "正在加载主模块...")
        
        try:
            import src.main
            logger.info("成功导入主模块")
        except ImportError as e:
            logger.error(f"导入主模块失败: {e}")
            
            # 尝试修复导入路径
            if "No module named 'src'" in str(e):
                logger.info("尝试修复导入路径...")
                
                # 如果是打包的应用，将资源目录添加到sys.path
                if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
                    resource_path = sys._MEIPASS
                    if resource_path not in sys.path:
                        sys.path.insert(0, resource_path)
                
                # 添加当前目录到sys.path
                current_dir = os.path.abspath(".")
                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                    
                # 再次尝试导入
                import src.main
                logger.info("成功导入主模块")
        
        # 准备启动主程序
        splash.set_progress(90, "准备启动应用程序...")
        time.sleep(0.3)  # 短暂停顿以显示进度
        
        # 最终准备
        splash.set_progress(100, "准备就绪，即将启动...")
        time.sleep(0.5)  # 短暂停顿以显示100%
        
        # 关闭启动画面（在调用main之前关闭，避免多个Tk实例）
        splash.close()
        
        # 执行主程序
        result = src.main.main()
        
        # 记录执行时间
        elapsed_time = time.time() - start_time
        logger.info(f"应用程序执行完成，耗时: {elapsed_time:.2f}秒")
        
        return result
        
    except Exception as e:
        # 记录异常
        logger.error(f"启动失败: {e}")
        logger.error(traceback.format_exc())
        
        # 关闭启动画面
        splash.close()
        
        # 显示错误信息
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "启动错误",
                f"应用程序启动失败。\n\n错误: {e}\n\n详细信息已记录到日志文件。"
            )
            root.destroy()
        except:
            print(f"启动错误: {e}")
            traceback.print_exc()
            
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(0) 