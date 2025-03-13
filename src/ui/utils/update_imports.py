import os
import re

def update_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新导入语句
    content = re.sub(
        r'from utils\.widget_utils import WidgetUtils',
        'from ..utils.widget_utils import WidgetUtils',
        content
    )
    content = re.sub(
        r'from utils\.animation_manager import AnimationManager',
        'from ..managers.animation import AnimationManager',
        content
    )
    content = re.sub(
        r'from utils\.style_manager import StyleManager',
        'from ..managers.style import StyleManager',
        content
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_imports(file_path)

if __name__ == '__main__':
    process_directory('src/ui') 