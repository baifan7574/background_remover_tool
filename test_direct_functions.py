
import sys
import os
from PIL import Image
import io
import base64
from datetime import datetime

# 直接导入PIL进行测试，避免复杂的Flask导入

# 创建模拟用户
class MockUser:
    def __init__(self):
        self.id = "test-user-123"
        self.email = "test@example.com"
        self.user_metadata = {}

def create_test_image():
    """创建测试图片"""
    img = Image.new('RGB', (400, 300), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return base64.b64encode(img_bytes.read()).decode()

def test_image_functions():
    """直接测试图片处理函数"""
    print("🚀 开始直接测试图片处理功能")
    
    # 创建测试图片
    test_image = create_test_image()
    print(f"📷 已创建测试图片")
    
    # 测试图片解码
    try:
        image_bytes = base64.b64decode(test_image)
        img = Image.open(io.BytesIO(image_bytes))
        print(f"✅ 图片解码成功: {img.width}x{img.height}")
    except Exception as e:
        print(f"❌ 图片解码失败: {e}")
        return
    
    # 测试图片压缩逻辑
    try:
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=80, optimize=True)
        compressed_size = len(buffer.getvalue())
        original_size = len(test_image)
        compression_ratio = (1 - compressed_size / original_size) * 100
        print(f"✅ 压缩测试成功: {original_size} -> {compressed_size} bytes ({compression_ratio:.1f}% 压缩)")
    except Exception as e:
        print(f"❌ 压缩测试失败: {e}")
    
    # 测试格式转换
    try:
        formats = ['JPEG', 'PNG', 'WebP', 'BMP']
        for fmt in formats:
            buffer = io.BytesIO()
            if fmt == 'PNG':
                img.save(buffer, format=fmt, optimize=True)
            else:
                img.save(buffer, format=fmt, quality=90, optimize=True)
            print(f"✅ {fmt}格式转换成功: {len(buffer.getvalue())} bytes")
    except Exception as e:
        print(f"❌ 格式转换测试失败: {e}")
    
    # 测试裁剪
    try:
        # 测试居中裁剪
        width, height = img.size
        target_width, target_height = 200, 200
        
        # 计算裁剪区域（居中裁剪）
        aspect_ratio = width / height
        target_aspect = target_width / target_height
        
        if aspect_ratio > target_aspect:
            # 原图更宽，裁剪宽度
            new_height = height
            new_width = int(new_height * target_aspect)
            x = (width - new_width) // 2
            y = 0
        else:
            # 原图更高，裁剪高度
            new_width = width
            new_height = int(new_width / target_aspect)
            x = 0
            y = (height - new_height) // 2
        
        crop_box = (x, y, x + new_width, y + new_height)
        cropped = img.crop(crop_box)
        resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        print(f"✅ 裁剪测试成功: {crop_box} -> {target_width}x{target_height}")
    except Exception as e:
        print(f"❌ 裁剪测试失败: {e}")
    
    # 测试移动端优化
    try:
        # 移动端配置
        max_width, max_height = 1080, 1920
        
        if width > max_width or height > max_height:
            aspect_ratio = width / height
            
            if width > height:
                new_width = min(width, max_width)
                new_height = int(new_width / aspect_ratio)
                
                if new_height > max_height:
                    new_height = max_height
                    new_width = int(new_height * aspect_ratio)
            else:
                new_height = min(height, max_height)
                new_width = int(new_height / aspect_ratio)
                
                if new_width > max_width:
                    new_width = max_width
                    new_height = int(new_width / aspect_ratio)
            
            optimized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"✅ 移动端优化成功: {width}x{height} -> {new_width}x{new_height}")
        else:
            print(f"✅ 图片尺寸已适合移动端: {width}x{height}")
    except Exception as e:
        print(f"❌ 移动端优化测试失败: {e}")
    
    print("🎉 直接功能测试完成！")

if __name__ == "__main__":
    test_image_functions()
