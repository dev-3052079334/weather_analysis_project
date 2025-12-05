#!/usr/bin/env python3
"""
创建PWA图标的脚本
运行: python create_icon.py
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_pwa_icons():
    """创建PWA所需的图标文件"""
    
    # 确保当前目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🎨 开始创建PWA图标...")
    
    # 创建512×512图标
    print("🖼️ 创建512×512图标...")
    img_512 = Image.new('RGBA', (512, 512), color=(102, 126, 234, 255))  # #667eea
    draw = ImageDraw.Draw(img_512)
    
    # 绘制中心圆形
    circle_margin = 80
    circle_coords = (circle_margin, circle_margin, 
                     512 - circle_margin, 512 - circle_margin)
    draw.ellipse(circle_coords, fill=(255, 255, 255, 255))
    
    # 绘制天气图标（简单的云和太阳）
    # 云朵
    cloud_coords = (180, 180, 330, 280)
    draw.ellipse(cloud_coords, fill=(240, 248, 255, 255))
    cloud_coords2 = (230, 150, 380, 250)
    draw.ellipse(cloud_coords2, fill=(240, 248, 255, 255))
    
    # 太阳
    sun_coords = (360, 360, 450, 450)
    draw.ellipse(sun_coords, fill=(255, 215, 0, 255))
    
    # 保存512图标
    img_512.save('icon-512.png', 'PNG')
    print("✅ 已创建: icon-512.png")
    
    # 创建192×192图标（从512缩放）
    print("🖼️ 创建192×192图标...")
    img_192 = img_512.resize((192, 192), Image.Resampling.LANCZOS)
    img_192.save('icon-192.png', 'PNG')
    print("✅ 已创建: icon-192.png")
    
    print("\n🎉 图标创建完成！")
    print("📁 生成的文件:")
    print("   - icon-512.png (512×512)")
    print("   - icon-192.png (192×192)")
    print("\n📱 现在可以测试PWA安装功能了！")

if __name__ == "__main__":
    create_pwa_icons()
