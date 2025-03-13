import os
import re

def replace_pyqt_imports(directory):
    """替换目录下所有Python文件中的PyQt6导入为PySide6"""
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换导入语句
                content = re.sub(r'from PyQt6\.', 'from PySide6.', content)
                content = re.sub(r'import PyQt6\.', 'import PySide6.', content)
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"已更新文件: {file_path}")

if __name__ == '__main__':
    # 替换src目录下的所有Python文件
    replace_pyqt_imports('src')
    # 替换tests目录下的所有Python文件
    replace_pyqt_imports('tests') 