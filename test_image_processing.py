#!/usr/bin/env python3
"""
图片处理功能测试脚本
测试所有第3周开发的图片处理功能
"""

import requests
import base64
import json
import time
from PIL import Image
import io
import os

# API基础URL
BASE_URL = "http://localhost:5000"

def create_test_image():
    """创建测试图片"""
    # 创建一个简单的测试图片
    img = Image.new('RGB', (400, 300), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return base64.b64encode(img_bytes.read()).decode()

def test_api_endpoint(endpoint, data, description):
    """测试API端点"""
    print(f"\n🧪 测试: {description}")
    print(f"📍 端点: {endpoint}")
    
    try:
        response = requests.post(f"{BASE_URL}{endpoint}", 
                                json=data, 
                                headers={'Content-Type': 'application/json'},
                                timeout=30)
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功: {result.get('message', 'N/A')}")
            return True, result
        else:
            print(f"❌ 失败: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False, None

def main():
    """主测试函数"""
    print("🚀 开始测试第3周图片处理模块功能")
    print("=" * 60)
    
    # 创建测试图片
    test_image = create_test_image()
    print(f"📷 已创建测试图片 (base64长度: {len(test_image)})")
    
    test_results = []
    
    # 1. 测试背景移除功能
    print("\n" + "="*40)
    print("🎨 测试背景移除功能")
    print("="*40)
    
    # 测试不同模型
    models = ['u2net', 'u2netp', 'u2net_human_seg', 'silueta', 'isnet-general-use']
    for model in models:
        data = {
            "image": test_image,
            "model": model,
            "alpha_matting": model == 'isnet-general-use'
        }
        success, result = test_api_endpoint("/api/tools/remove-background", data, f"背景移除 - {model}")
        test_results.append(("背景移除", model, success))
        time.sleep(1)  # 避免请求过快
    
    # 2. 测试图片压缩功能
    print("\n" + "="*40)
    print("🗜️ 测试图片压缩功能")
    print("="*40)
    
    compress_tests = [
        {"quality": 90, "max_size": 1024*1024, "description": "高质量压缩"},
        {"quality": 70, "max_size": 500*1024, "description": "中等质量压缩"},
        {"quality": 50, "max_size": 200*1024, "description": "低质量压缩"}
    ]
    
    for test in compress_tests:
        data = {
            "image": test_image,
            "quality": test["quality"],
            "max_size": test["max_size"]
        }
        success, result = test_api_endpoint("/api/tools/compress-image", data, test["description"])
        test_results.append(("图片压缩", test["description"], success))
        time.sleep(1)
    
    # 3. 测试格式转换功能
    print("\n" + "="*40)
    print("🔄 测试格式转换功能")
    print("="*40)
    
    formats = ['JPEG', 'PNG', 'WebP', 'BMP']
    for fmt in formats:
        data = {
            "image": test_image,
            "target_format": fmt,
            "quality": 90
        }
        success, result = test_api_endpoint("/api/tools/convert-format", data, f"转换为{fmt}")
        test_results.append(("格式转换", fmt, success))
        time.sleep(1)
    
    # 4. 测试图片裁剪功能
    print("\n" + "="*40)
    print("✂️ 测试图片裁剪功能")
    print("="*40)
    
    crop_tests = [
        {
            "crop_type": "preset",
            "crop_data": {"preset": "instagram_square"},
            "description": "Instagram正方形裁剪"
        },
        {
            "crop_type": "aspect_ratio",
            "crop_data": {"aspect": "16:9"},
            "description": "16:9宽高比裁剪"
        },
        {
            "crop_type": "custom",
            "crop_data": {"x": 50, "y": 50, "width": 200, "height": 150},
            "description": "自定义裁剪"
        }
    ]
    
    for test in crop_tests:
        data = {
            "image": test_image,
            "crop_type": test["crop_type"],
            "crop_data": test["crop_data"]
        }
        success, result = test_api_endpoint("/api/tools/crop-image", data, test["description"])
        test_results.append(("图片裁剪", test["description"], success))
        time.sleep(1)
    
    # 5. 测试移动端优化功能
    print("\n" + "="*40)
    print("📱 测试移动端优化功能")
    print("="*40)
    
    mobile_tests = [
        {
            "target_device": "mobile",
            "quality_level": "high",
            "description": "移动端高质量优化"
        },
        {
            "target_device": "tablet",
            "quality_level": "balanced",
            "description": "平板端平衡优化"
        },
        {
            "target_device": "desktop",
            "quality_level": "fast",
            "description": "桌面端快速优化"
        }
    ]
    
    for test in mobile_tests:
        data = {
            "image": test_image,
            "target_device": test["target_device"],
            "quality_level": test["quality_level"]
        }
        success, result = test_api_endpoint("/api/tools/mobile-optimize", data, test["description"])
        test_results.append(("移动端优化", test["description"], success))
        time.sleep(1)
    
    # 6. 测试批量处理功能
    print("\n" + "="*40)
    print("📦 测试批量处理功能")
    print("="*40)
    
    # 创建多个测试图片
    test_images = [create_test_image() for _ in range(3)]
    
    batch_tests = [
        {
            "operation": "compress",
            "settings": {"quality": 80, "max_size": 500*1024},
            "description": "批量压缩"
        },
        {
            "operation": "convert",
            "settings": {"target_format": "JPEG", "quality": 85},
            "description": "批量格式转换"
        },
        {
            "operation": "mobile_optimize",
            "settings": {"target_device": "mobile", "quality_level": "balanced"},
            "description": "批量移动端优化"
        }
    ]
    
    for test in batch_tests:
        data = {
            "images": test_images,
            "operation": test["operation"],
            "settings": test["settings"]
        }
        success, result = test_api_endpoint("/api/tools/batch-process", data, test["description"])
        test_results.append(("批量处理", test["description"], success))
        time.sleep(2)  # 批量处理需要更多时间
    
    # 7. 测试错误处理
    print("\n" + "="*40)
    print("⚠️ 测试错误处理")
    print("="*40)
    
    error_tests = [
        {
            "endpoint": "/api/tools/remove-background",
            "data": {},
            "description": "缺少图片数据"
        },
        {
            "endpoint": "/api/tools/compress-image",
            "data": {"image": "invalid_base64"},
            "description": "无效的base64数据"
        },
        {
            "endpoint": "/api/tools/crop-image",
            "data": {"image": test_image, "crop_type": "invalid"},
            "description": "无效的裁剪类型"
        },
        {
            "endpoint": "/api/tools/batch-process",
            "data": {"images": [], "operation": "compress"},
            "description": "空批量处理"
        }
    ]
    
    for test in error_tests:
        success, result = test_api_endpoint(test["endpoint"], test["data"], test["description"])
        # 错误测试应该返回失败，这是正确的
        test_results.append(("错误处理", test["description"], not success))
        time.sleep(0.5)
    
    # 输出测试结果汇总
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, _, success in test_results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"📈 总测试数: {total_tests}")
    print(f"✅ 通过测试: {passed_tests}")
    print(f"❌ 失败测试: {failed_tests}")
    print(f"📊 成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    # 按功能分组显示结果
    print("\n📋 详细结果:")
    categories = {}
    for category, test_name, success in test_results:
        if category not in categories:
            categories[category] = []
        categories[category].append((test_name, success))
    
    for category, tests in categories.items():
        print(f"\n🔸 {category}:")
        for test_name, success in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}")
    
    print("\n🎉 测试完成!")
    
    if failed_tests == 0:
        print("🌟 所有测试通过！第3周图片处理模块功能完整。")
    else:
        print(f"⚠️ 有{failed_tests}个测试失败，需要检查相关功能。")
    
    return passed_tests, failed_tests

if __name__ == "__main__":
    try:
        passed, failed = main()
        exit(0 if failed == 0 else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n💥 测试脚本异常: {str(e)}")
        exit(1)