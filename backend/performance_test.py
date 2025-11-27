"""
性能测试脚本 - 分析背景移除处理时间
"""

import time
import base64
import io
from PIL import Image
from rembg import new_session, remove
import requests
import json

def test_local_performance():
    """测试本地rembg性能"""
    print("🔍 测试本地rembg性能...")
    
    # 创建测试图片
    test_image = Image.new('RGB', (512, 512), color='red')
    buffer = io.BytesIO()
    test_image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()
    
    # 测试不同模型的性能
    models = ['u2net', 'u2netp', 'silueta', 'isnet-general-use']
    
    for model_name in models:
        print(f"\n📊 测试模型: {model_name}")
        
        # 模型加载时间
        start_time = time.time()
        session = new_session(model_name)
        load_time = time.time() - start_time
        print(f"  模型加载时间: {load_time:.2f}秒")
        
        # 处理时间
        start_time = time.time()
        result = remove(image_bytes, session=session)
        process_time = time.time() - start_time
        print(f"  图片处理时间: {process_time:.2f}秒")
        print(f"  总时间: {load_time + process_time:.2f}秒")

def test_api_performance():
    """测试API性能"""
    print("\n🌐 测试API性能...")
    
    # 创建测试图片
    test_image = Image.new('RGB', (512, 512), color='blue')
    buffer = io.BytesIO()
    test_image.save(buffer, format='PNG')
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # 测试数据
    test_data = {
        'image': image_base64,
        'model': 'u2net'
    }
    
    # 发送请求
    start_time = time.time()
    try:
        response = requests.post(
            'http://localhost:5000/api/tools/background-remover',
            json=test_data,
            headers={
                'Authorization': 'Bearer dev-token-test-user',
                'Content-Type': 'application/json'
            },
            timeout=60
        )
        
        total_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"  API总响应时间: {total_time:.2f}秒")
            print(f"  服务器处理时间: {result.get('processing_info', {}).get('processing_time', 'N/A')}秒")
            print(f"  网络传输时间: {total_time - result.get('processing_info', {}).get('processing_time', 0):.2f}秒")
        else:
            print(f"  API请求失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            
    except requests.exceptions.Timeout:
        print("  ❌ 请求超时（超过60秒）")
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")

def test_image_size_impact():
    """测试不同图片尺寸对性能的影响"""
    print("\n📏 测试不同图片尺寸的性能影响...")
    
    sizes = [(256, 256), (512, 512), (1024, 1024), (2048, 2048)]
    
    for width, height in sizes:
        print(f"\n📐 测试尺寸: {width}x{height}")
        
        # 创建测试图片
        test_image = Image.new('RGB', (width, height), color='green')
        buffer = io.BytesIO()
        test_image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # 测试处理时间
        start_time = time.time()
        session = new_session('u2net')
        result = remove(image_bytes, session=session)
        process_time = time.time() - start_time
        
        print(f"  处理时间: {process_time:.2f}秒")
        print(f"  像素数量: {width * height:,}")
        print(f"  每百万像素处理时间: {process_time / (width * height / 1000000):.2f}秒")

def analyze_performance_bottlenecks():
    """分析性能瓶颈"""
    print("\n🔍 性能瓶颈分析...")
    
    print("主要性能影响因素:")
    print("1. 模型加载时间 - 每次请求都会重新加载模型")
    print("2. 图片尺寸 - 更大的图片需要更长的处理时间")
    print("3. 模型复杂度 - 不同模型的处理速度差异很大")
    print("4. 硬件性能 - CPU和内存限制")
    print("5. 网络传输 - base64编码增加约33%的数据量")
    
    print("\n💡 优化建议:")
    print("1. 模型缓存 - 避免重复加载模型")
    print("2. 图片预处理 - 限制输入图片尺寸")
    print("3. 异步处理 - 使用队列处理大图片")
    print("4. 模型选择 - 根据需求选择合适的模型")
    print("5. 硬件升级 - 使用GPU加速")

if __name__ == "__main__":
    print("🚀 开始性能测试...")
    
    # 本地性能测试
    test_local_performance()
    
    # API性能测试
    test_api_performance()
    
    # 图片尺寸影响测试
    test_image_size_impact()
    
    # 性能瓶颈分析
    analyze_performance_bottlenecks()
    
    print("\n✅ 性能测试完成!")