"""
优化版背景移除功能 - 解决性能问题
主要优化：
1. 模型缓存 - 避免重复加载
2. 图片预处理 - 限制输入尺寸
3. 异步处理 - 支持进度回调
4. 内存优化 - 减少内存占用
"""

import os
import time
import threading
from datetime import datetime
from PIL import Image
import io
import base64
import rembg
from rembg import new_session, remove

# 全局模型缓存
model_cache = {}
cache_lock = threading.Lock()

def get_cached_session(model_name='u2net'):
    """获取缓存的模型会话"""
    global model_cache
    
    with cache_lock:
        if model_name not in model_cache:
            print(f"🔄 首次加载模型: {model_name}")
            start_time = time.time()
            model_cache[model_name] = new_session(model_name)
            load_time = time.time() - start_time
            print(f"✅ 模型加载完成: {model_name} (耗时: {load_time:.2f}秒)")
        else:
            print(f"📦 使用缓存模型: {model_name}")
    
    return model_cache[model_name]

def preprocess_image(image, max_size=1024):
    """图片预处理 - 限制尺寸以提高处理速度"""
    original_size = image.size
    
    # 如果图片过大，进行缩放
    if max(image.size) > max_size:
        # 计算缩放比例
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        
        print(f"📏 图片缩放: {original_size} -> {new_size}")
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    return image

def optimized_remove_background(image_data, model_name='u2net', alpha_matting=False, 
                               progress_callback=None, max_size=1024):
    """优化版背景移除"""
    try:
        total_start = time.time()
        
        # 1. 图片解码和预处理
        if progress_callback:
            progress_callback(10, "解码图片...")
        
        if isinstance(image_data, str):
            # base64字符串
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
        elif isinstance(image_data, bytes):
            # 字节数据
            image = Image.open(io.BytesIO(image_data))
        else:
            # PIL Image对象
            image = image_data
        
        original_size = image.size
        print(f"📸 原始图片尺寸: {original_size}")
        
        # 2. 图片预处理
        if progress_callback:
            progress_callback(20, "预处理图片...")
        
        image = preprocess_image(image, max_size)
        processed_size = image.size
        
        # 3. 模型加载（使用缓存）
        if progress_callback:
            progress_callback(30, "加载AI模型...")
        
        session_start = time.time()
        session = get_cached_session(model_name)
        session_time = time.time() - session_start
        
        # 4. 背景移除处理
        if progress_callback:
            progress_callback(50, "移除背景中...")
        
        process_start = time.time()
        output_image = remove(
            image, 
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        process_time = time.time() - process_start
        
        # 5. 结果编码
        if progress_callback:
            progress_callback(90, "生成结果...")
        
        buffer = io.BytesIO()
        output_image.save(buffer, format='PNG', optimize=True)
        result_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        total_time = time.time() - total_start
        
        # 6. 清理内存
        if progress_callback:
            progress_callback(100, "完成")
        
        # 释放图片对象
        image.close()
        output_image.close()
        buffer.close()
        
        return {
            'success': True,
            'processed_image': result_base64,
            'performance_info': {
                'total_time': round(total_time, 2),
                'model_load_time': round(session_time, 2),
                'process_time': round(process_time, 2),
                'original_size': f"{original_size[0]}x{original_size[1]}",
                'processed_size': f"{processed_size[0]}x{processed_size[1]}",
                'model_used': model_name,
                'optimization': 'enabled'
            }
        }
        
    except Exception as e:
        print(f"❌ 背景移除失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def clear_model_cache():
    """清理模型缓存"""
    global model_cache
    
    with cache_lock:
        model_cache.clear()
        print("🗑️ 模型缓存已清理")

def get_cache_info():
    """获取缓存信息"""
    global model_cache
    
    with cache_lock:
        return {
            'cached_models': list(model_cache.keys()),
            'cache_size': len(model_cache)
        }

# 性能测试函数
def performance_test():
    """性能测试"""
    print("🚀 开始性能测试...")
    
    # 创建测试图片
    test_image = Image.new('RGB', (1024, 1024), color='red')
    buffer = io.BytesIO()
    test_image.save(buffer, format='PNG')
    test_data = base64.b64encode(buffer.getvalue()).decode()
    
    # 测试不同模型
    models = ['u2net', 'u2netp', 'silueta']
    
    for model in models:
        print(f"\n📊 测试模型: {model}")
        
        # 第一次处理（包含模型加载）
        result1 = optimized_remove_background(test_data, model)
        if result1['success']:
            info = result1['performance_info']
            print(f"  首次处理: {info['total_time']}秒 (包含模型加载)")
        
        # 第二次处理（使用缓存）
        result2 = optimized_remove_background(test_data, model)
        if result2['success']:
            info = result2['performance_info']
            print(f"  缓存处理: {info['total_time']}秒 (模型已缓存)")
    
    # 缓存信息
    cache_info = get_cache_info()
    print(f"\n📦 缓存信息: {cache_info}")

if __name__ == "__main__":
    performance_test()