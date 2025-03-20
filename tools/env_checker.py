#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from importlib.metadata import version, PackageNotFoundError
from typing import List, Dict, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

def check_tools_structure() -> bool:
    """检查工具目录结构"""
    try:
        # 检查tools目录是否存在
        if not os.path.exists('tools'):
            logger.error("错误: tools目录不存在")
            return False
            
        # 检查__init__.py是否存在
        init_file = os.path.join('tools', '__init__.py')
        if not os.path.exists(init_file):
            logger.info("创建tools/__init__.py...")
            with open(init_file, 'w') as f:
                f.write('# tools package\n')
            logger.info("tools/__init__.py创建成功")
            
        return True
    except Exception as e:
        logger.error(f"检查工具目录结构时出错: {e}")
        return False

def check_pip_version() -> bool:
    """检查pip版本是否满足要求"""
    try:
        import pip
        required_version = (21, 0)
        current_version = tuple(map(int, pip.__version__.split('.')))
        return current_version >= required_version
    except Exception:
        return False

def check_python_version() -> bool:
    """检查Python版本是否满足要求"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    return current_version >= required_version

def check_venv() -> bool:
    """检查是否在虚拟环境中"""
    return hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix

def create_venv() -> bool:
    """创建虚拟环境"""
    try:
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"创建虚拟环境失败: {e}")
        return False

def activate_venv() -> bool:
    """激活虚拟环境"""
    if sys.platform == 'win32':
        activate_script = 'venv\\Scripts\\activate.bat'
    else:
        activate_script = 'venv/bin/activate'
    
    if not os.path.exists(activate_script):
        logger.error(f"错误: 虚拟环境激活脚本不存在: {activate_script}")
        return False
    
    try:
        # 获取当前Python解释器路径
        python_path = os.path.join(os.path.dirname(activate_script), 'python')
        if sys.platform == 'win32':
            python_path += '.exe'
        
        # 使用新的Python解释器运行程序
        if os.path.exists(python_path):
            sys.executable = python_path
            return True
        logger.error(f"错误: 虚拟环境Python解释器不存在: {python_path}")
        return False
    except Exception as e:
        logger.error(f"激活虚拟环境时出错: {e}")
        return False

def check_project_package() -> bool:
    """检查项目包是否已安装"""
    try:
        version('wecom_live_sign_system')
        return True
    except PackageNotFoundError:
        logger.info("正在安装项目包...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"项目包安装失败: {e}")
            return False

def check_dependencies() -> Dict[str, bool]:
    """检查依赖是否已安装"""
    try:
        # 读取requirements.txt文件
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        # 检查每个依赖是否已安装
        result = {}
        for req in requirements:
            # 移除版本号信息，只保留包名
            pkg_name = req.split('>=')[0].split('<=')[0].split('==')[0].strip()
            try:
                version(pkg_name)
                result[pkg_name] = True
            except PackageNotFoundError:
                result[pkg_name] = False
        return result
    except Exception as e:
        logger.error(f"检查依赖时出错: {e}")
        return {}

def install_dependencies() -> bool:
    """安装依赖"""
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"安装依赖失败: {e}")
        return False

def check_environment() -> bool:
    """检查环境并返回结果"""
    logger.info("开始环境检查...")
    
    # 检查工具目录结构
    if not check_tools_structure():
        logger.error("错误: 工具目录结构检查失败")
        return False
    
    # 检查pip版本
    if not check_pip_version():
        logger.info("正在升级pip...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
            logger.info("pip升级成功")
        except subprocess.CalledProcessError as e:
            logger.warning(f"警告: pip升级失败: {e}")
    
    # 检查Python版本
    if not check_python_version():
        logger.error("错误: Python版本必须 >= 3.8")
        return False
    
    # 检查虚拟环境
    if not check_venv():
        logger.info("未检测到虚拟环境，正在创建...")
        if not create_venv():
            logger.error("错误: 创建虚拟环境失败")
            return False
        logger.info("正在激活虚拟环境...")
        if not activate_venv():
            logger.error("错误: 激活虚拟环境失败")
            return False
    
    logger.info("检查项目包...")
    # 检查项目包是否已安装
    if not check_project_package():
        logger.error("错误: 项目包安装失败")
        return False
    
    logger.info("检查依赖...")
    # 检查依赖
    dependencies = check_dependencies()
    missing_deps = [dep for dep, installed in dependencies.items() if not installed]
    
    if missing_deps:
        logger.warning(f"发现缺失依赖: {', '.join(missing_deps)}")
        logger.info("正在安装依赖...")
        if not install_dependencies():
            logger.error("错误: 安装依赖失败")
            return False
    
    logger.info("环境检查完成")
    return True

if __name__ == '__main__':
    if not check_environment():
        sys.exit(1)
    sys.exit(0) 