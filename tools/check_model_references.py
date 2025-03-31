#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查代码中对旧模型(WatchStat, SignRecord)的引用，生成修改建议
"""

import os
import re
import sys
import argparse
from typing import Dict, List, Tuple

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="检查对旧模型的引用")
    parser.add_argument('--path', type=str, default='src', help='要检查的目录路径')
    parser.add_argument('--fix', action='store_true', help='自动修复简单的引用问题')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')
    return parser.parse_args()

def collect_files(path: str) -> List[str]:
    """收集指定目录下的所有Python文件"""
    files = []
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))
    return files

def analyze_file(file_path: str) -> Dict[str, List[Tuple[int, str]]]:
    """分析文件中的模型引用
    
    返回:
        Dict[str, List[Tuple[int, str]]]: 按模型名称分组的行号和内容
    """
    references = {
        'SignRecord': [],
        'WatchStat': []
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f.readlines()):
            if 'SignRecord' in line:
                references['SignRecord'].append((i+1, line.strip()))
            if 'WatchStat' in line:
                references['WatchStat'].append((i+1, line.strip()))
                
    return references

def generate_fix_suggestions(file_path: str, references: Dict[str, List[Tuple[int, str]]]) -> Dict[str, str]:
    """生成修复建议"""
    suggestions = {}
    
    # 检查导入语句
    import_patterns = {
        r'from\s+.*\.models\.sign_record\s+import\s+SignRecord': 'from src.models.live_viewer import LiveViewer',
        r'from\s+.*\.models\.watch_stat\s+import\s+WatchStat': 'from src.models.living import Living, WatchStat 或 from src.models.live_viewer import LiveViewer',
        r'from\s+.*\.models\s+import\s+.*,\s*SignRecord': '移除 SignRecord 导入，改用 LiveViewer',
        r'from\s+.*\.models\s+import\s+.*,\s*WatchStat': '移除 WatchStat 导入，改用 LiveViewer 或从 living 导入'
    }
    
    # 检查查询语句
    query_patterns = {
        r'query\s*\(\s*SignRecord\s*\)': 'query(LiveViewer).filter(LiveViewer.is_signed == True)',
        r'filter.*SignRecord\.': '将 SignRecord 替换为 LiveViewer，并相应调整字段名',
        r'query\s*\(\s*WatchStat\s*\)': 'query(LiveViewer)',
        r'filter.*WatchStat\.': '将 WatchStat 替换为 LiveViewer，并相应调整字段名'
    }
    
    for model, lines in references.items():
        for line_num, line in lines:
            for pattern, suggestion in import_patterns.items():
                if re.search(pattern, line):
                    suggestions[f"{file_path}:{line_num}"] = f"导入替换: {suggestion}"
            
            for pattern, suggestion in query_patterns.items():
                if re.search(pattern, line):
                    suggestions[f"{file_path}:{line_num}"] = f"查询替换: {suggestion}"
    
    return suggestions

def fix_simple_references(file_path: str, references: Dict[str, List[Tuple[int, str]]]) -> int:
    """尝试修复简单的引用问题
    
    返回:
        int: 修复的引用数量
    """
    if not references['SignRecord'] and not references['WatchStat']:
        return 0
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 简单替换导入语句
    replacements = {
        'from src.models.sign_record import SignRecord': 'from src.models.live_viewer import LiveViewer',
        'from models.sign_record import SignRecord': 'from models.live_viewer import LiveViewer',
        'from src.models import SignRecord': 'from src.models import LiveViewer',
        'from models import SignRecord': 'from models import LiveViewer',
    }
    
    fixed_count = 0
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            fixed_count += 1
            
    # 只有在有修改时才写入文件
    if fixed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    return fixed_count

def main():
    """主函数"""
    args = parse_args()
    
    if not os.path.exists(args.path):
        print(f"错误: 路径 {args.path} 不存在")
        return 1
        
    print(f"检查目录: {args.path}")
    files = collect_files(args.path)
    print(f"找到 {len(files)} 个Python文件")
    
    total_refs = {
        'SignRecord': 0,
        'WatchStat': 0
    }
    
    total_fixed = 0
    files_with_refs = []
    
    for file_path in files:
        if args.verbose:
            print(f"检查文件: {file_path}")
            
        references = analyze_file(file_path)
        
        # 更新总引用计数
        for model, refs in references.items():
            total_refs[model] += len(refs)
            
        # 如果有引用，记录文件
        if references['SignRecord'] or references['WatchStat']:
            files_with_refs.append(file_path)
            
            # 尝试自动修复
            if args.fix:
                fixed = fix_simple_references(file_path, references)
                total_fixed += fixed
                if fixed > 0 and args.verbose:
                    print(f"  - 已修复 {fixed} 处简单引用")
            
            # 生成修复建议
            suggestions = generate_fix_suggestions(file_path, references)
            for loc, suggestion in suggestions.items():
                print(f"{loc}: {suggestion}")
    
    print("\n摘要:")
    print(f"检查的文件: {len(files)}")
    print(f"包含旧模型引用的文件: {len(files_with_refs)}")
    print(f"SignRecord 引用数: {total_refs['SignRecord']}")
    print(f"WatchStat 引用数: {total_refs['WatchStat']}")
    
    if args.fix:
        print(f"自动修复的引用数: {total_fixed}")
    
    if files_with_refs:
        print("\n需要检查的文件:")
        for file_path in files_with_refs:
            print(f"  - {file_path}")
            
    return 0

if __name__ == "__main__":
    sys.exit(main()) 