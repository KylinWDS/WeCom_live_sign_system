#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为企业微信直播签到系统创建默认图标
"""
import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageColor, ImageEnhance

def create_app_icon(output_path, size=1024):
    """
    创建简单明了的应用图标
    
    Args:
        output_path: 输出路径
        size: 图标大小
    """
    # 如果输出文件已存在，则不覆盖
    if os.path.exists(output_path):
        print(f"图标文件已存在: {output_path}，将不会覆盖")
        return True
        
    try:
        # 创建一个正方形画布
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 设置颜色
        main_color = (52, 152, 219)  # 鲜明的蓝色
        secondary_color = (41, 128, 185)  # 深蓝色
        accent_color = (231, 76, 60)  # 红色，用于强调
        
        # 绘制圆形背景
        draw.ellipse((0, 0, size, size), fill=main_color)
        
        # 绘制内环装饰
        ring_width = size // 20
        inner_size = size - (ring_width * 2)
        draw.ellipse(
            (ring_width, ring_width, size - ring_width, size - ring_width),
            fill=secondary_color
        )
        
        # 绘制中心圆形
        center_padding = size // 6
        draw.ellipse(
            (center_padding, center_padding, size - center_padding, size - center_padding),
            fill=(255, 255, 255)  # 白色中心
        )
        
        # 尝试加载字体，如果失败则使用备选方案
        font = None
        font_size = size // 5
        
        # 尝试几种常见字体路径
        font_paths = []
        
        if sys.platform == 'darwin':  # macOS
            font_paths = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
            ]
        elif sys.platform == 'win32':  # Windows
            font_paths = [
                'C:\\Windows\\Fonts\\msyh.ttc',
                'C:\\Windows\\Fonts\\arial.ttf',
                'C:\\Windows\\Fonts\\simhei.ttf'
            ]
        else:  # Linux或其他
            font_paths = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            ]
        
        # 尝试加载字体
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except:
                    continue
        
        # 在中心绘制简单的"QD"文字（签到拼音首字母）
        text = "ZBQD\nKylin"
        text_color = accent_color  # 使用红色作为强调色
        
        # 计算文本位置 - 使用更简单可靠的方法
        if font:
            try:
                # 尝试使用新API
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                # 回退到固定大小
                text_width = font_size * len(text) * 0.6
                text_height = font_size
        else:
            # 无字体时的回退方案
            font = ImageFont.load_default()
            text_width = font_size * 0.5
            text_height = font_size * 0.5
        
        # 计算居中位置
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        # 绘制文本
        draw.text((x, y), text, fill=text_color, font=font, stroke_width=5, stroke_fill=(255,255,255))
        
        # 添加简单红点标记 - 确保有可见元素
        dot_size = size // 15
        draw.ellipse(
            (
                (size * 3) // 4 - dot_size,
                (size * 3) // 4 - dot_size,
                (size * 3) // 4 + dot_size,
                (size * 3) // 4 + dot_size
            ),
            fill=accent_color
        )
        
        # 应用轻微的阴影效果增加深度感
        shadow = img.copy().filter(ImageFilter.GaussianBlur(5))
        shadow_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        shadow_img.paste(shadow, (5, 5), shadow)
        
        # 合并图层
        final_img = Image.alpha_composite(shadow_img, img)
        
        # 保存图标
        final_img.save(output_path)
        print(f"图标已保存到: {output_path}")
        return True
    except Exception as e:
        print(f"创建图标时出错: {e}")
        return False

def create_icns_from_png(png_path, icns_path):
    """从PNG创建ICNS图标文件"""
    if not os.path.exists(png_path):
        print(f"错误: PNG图标文件不存在: {png_path}")
        return False
        
    if os.path.exists(icns_path):
        print(f"ICNS图标文件已存在: {icns_path}，将不会覆盖")
        return True
        
    try:
        # 检查操作系统是否为macOS
        if sys.platform != 'darwin':
            print("警告: 只有macOS支持直接创建ICNS文件")
            return False
            
        # 创建临时iconset目录
        iconset_path = os.path.join(os.path.dirname(icns_path), "AppIcon.iconset")
        if os.path.exists(iconset_path):
            import shutil
            shutil.rmtree(iconset_path)
        os.makedirs(iconset_path, exist_ok=True)
        
        # 打开PNG图像
        img = Image.open(png_path)
        
        # 生成不同尺寸的图标
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            # 根据PIL/Pillow版本选择适当的缩放方法
            if hasattr(Image, 'Resampling'):
                # 新版本Pillow (9.0.0+)
                resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            else:
                # 旧版本
                resized_img = img.resize((size, size), Image.LANCZOS)
                
            resized_img.save(os.path.join(iconset_path, f"icon_{size}x{size}.png"))
            
            # 对于Retina显示屏，创建@2x版本
            if size <= 512:
                if hasattr(Image, 'Resampling'):
                    resized_img = img.resize((size*2, size*2), Image.Resampling.LANCZOS)
                else:
                    resized_img = img.resize((size*2, size*2), Image.LANCZOS)
                resized_img.save(os.path.join(iconset_path, f"icon_{size}x{size}@2x.png"))
        
        # 使用iconutil命令创建icns文件
        import subprocess
        result = subprocess.run(['iconutil', '-c', 'icns', iconset_path, '-o', icns_path], 
                               capture_output=True, text=True)
        
        # 清理临时文件
        import shutil
        shutil.rmtree(iconset_path)
        
        if result.returncode == 0:
            print(f"ICNS图标已保存到: {icns_path}")
            return True
        else:
            print(f"创建ICNS图标时出错: {result.stderr}")
            return False
    except Exception as e:
        print(f"创建ICNS图标时出错: {e}")
        return False

def main():
    """主函数"""
    # 确定图标保存路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    assets_dir = os.path.join(current_dir, "assets")
    
    # 确保assets目录存在
    os.makedirs(assets_dir, exist_ok=True)
    
    # 创建不同格式的图标
    png_path = os.path.join(assets_dir, "app.png")
    icns_path = os.path.join(assets_dir, "app.icns")
    
    # 检查PNG文件是否已存在
    png_exists = os.path.exists(png_path)
    icns_exists = os.path.exists(icns_path)
    
    # 如果PNG不存在，则创建
    if not png_exists:
        success = create_app_icon(png_path)
    else:
        print(f"使用现有PNG图标: {png_path}")
        success = True
    
    # 如果PNG创建成功或已存在，但ICNS不存在，则创建ICNS
    if success and not icns_exists:
        if sys.platform == 'darwin':
            create_icns_from_png(png_path, icns_path)
    
    # 在Windows上，尝试创建ICO文件
    if success and sys.platform == 'win32':
        try:
            ico_path = os.path.join(assets_dir, "app.ico")
            
            # 如果ICO文件已存在，则不覆盖
            if os.path.exists(ico_path):
                print(f"ICO图标已存在: {ico_path}")
                return
                
            img = Image.open(png_path)
            
            # 准备不同尺寸的图标
            sizes = [16, 32, 48, 64, 128, 256]
            icons = []
            for size in sizes:
                # 根据PIL/Pillow版本选择适当的缩放方法
                if hasattr(Image, 'Resampling'):
                    icon = img.resize((size, size), Image.Resampling.LANCZOS)
                else:
                    icon = img.resize((size, size), Image.LANCZOS)
                icons.append(icon)
                
            # 保存为ICO文件
            icons[0].save(ico_path, format='ICO', sizes=[(s, s) for s in sizes], 
                         append_images=icons[1:])
            
            print(f"ICO图标已保存到: {ico_path}")
        except Exception as e:
            print(f"创建ICO图标时出错: {e}")

if __name__ == "__main__":
    main() 