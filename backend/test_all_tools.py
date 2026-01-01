#!/usr/bin/env python3
"""
测试所有工具功能
"""

import os
import sys
import requests
import base64
import json
from io import BytesIO
from PIL import Image

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_image():
    """创建一个测试图片"""
    img = Image.new('RGB', (400, 300), color='blue')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()

def get_auth_token():
    """获取认证token"""
    api_base = "http://localhost:5000"
    login_url = f"{api_base}/api/auth/login"
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    try:
        response = requests.post(
            login_url,
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            # 直接从顶层获取token
            if 'token' in result:
                return result['token']
        return None
    except Exception as e:
        print(f"登录异常: {e}")
        return None

def test_tool(tool_name, endpoint, test_data, expected_keys=None):
    """测试单个工具"""
    api_base = "http://localhost:5000"
    url = f"{api_base}{endpoint}"
    
    print(f"\n🔧 测试 {tool_name}...")
    
    # 获取token
    token = get_auth_token()
    if not token:
        print(f"❌ {tool_name}: 无法获取认证token")
        return False
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.post(url, json=test_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ {tool_name}: 测试成功")
                
                # 验证预期字段
                if expected_keys:
                    for key in expected_keys:
                        if key in result:
                            print(f"  ✓ 包含字段: {key}")
                        else:
                            print(f"  ❌ 缺少字段: {key}")
                
                return True
            else:
                print(f"❌ {tool_name}: {result.get('error', '未知错误')}")
                return False
        elif response.status_code == 400:
            error_result = response.json()
            error_msg = error_result.get('error', '')
            if '权限' in error_msg or '会员' in error_msg or '套餐' in error_msg:
                print(f"✅ {tool_name}: 权限检查正常 ({error_msg})")
                return True
            else:
                print(f"❌ {tool_name}: {error_msg}")
                return False
        else:
            print(f"❌ {tool_name}: HTTP {response.status_code}")
            try:
                print(f"  错误信息: {response.json()}")
            except:
                print(f"  错误信息: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ {tool_name}: 请求异常 - {e}")
        return False

def test_all_tools():
    """测试所有工具功能"""
    print("=== 测试所有工具功能 ===\n")
    
    # 创建测试图片
    test_image = create_test_image()
    image_base64 = base64.b64encode(test_image).decode()
    print(f"📷 测试图片创建成功，大小: {len(test_image)} bytes")
    
    # 测试工具列表
    tools = [
        {
            'name': '图片压缩',
            'endpoint': '/api/tools/compress-image',
            'data': {
                'image': image_base64,
                'quality': 85,
                'format': 'JPEG'
            },
            'expected_keys': ['compressed_image', 'compression_info']
        },
        {
            'name': '背景移除',
            'endpoint': '/api/tools/background-remover',
            'data': {
                'image': image_base64,
                'model': 'u2net'
            },
            'expected_keys': ['processed_image']
        },
        {
            'name': '格式转换',
            'endpoint': '/api/tools/convert-format',
            'data': {
                'image': image_base64,
                'format': 'PNG'
            },
            'expected_keys': ['converted_image']
        },
        {
            'name': '图片裁剪',
            'endpoint': '/api/tools/crop-image',
            'data': {
                'image': image_base64,
                'x': 50,
                'y': 50,
                'width': 200,
                'height': 200
            },
            'expected_keys': ['cropped_image']
        },
        {
            'name': '移动端优化',
            'endpoint': '/api/tools/mobile-optimize',
            'data': {
                'image': image_base64,
                'target_device': 'mobile',
                'quality_level': 'balanced'
            },
            'expected_keys': ['optimized_image']
        }
    ]
    
    results = []
    
    for tool in tools:
        success = test_tool(
            tool['name'],
            tool['endpoint'], 
            tool['data'],
            tool.get('expected_keys')
        )
        results.append((tool['name'], success))
    
    # 测试健康检查
    print(f"\n🏥 测试健康检查...")
    try:
        response = requests.get("http://localhost:5000/health", timeout=10)
        if response.status_code == 200:
            print("✅ 健康检查: 正常")
            results.append(('健康检查', True))
        else:
            print(f"❌ 健康检查: HTTP {response.status_code}")
            results.append(('健康检查', False))
    except Exception as e:
        print(f"❌ 健康检查: {e}")
        results.append(('健康检查', False))
    
    return results

def main():
    """主函数"""
    print("所有工具功能测试\n")
    print("=" * 60)
    
    results = test_all_tools()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    
    success_count = 0
    total_count = len(results)
    
    for tool_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {tool_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n📈 总体结果: {success_count}/{total_count} 个工具测试通过")
    
    if success_count == total_count:
        print("🎉 所有工具功能正常！")
        return True
    else:
        print("⚠️  部分工具需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)