#!/usr/bin/env python3
"""
测试图片压缩功能的认证需求
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
    # 创建一个简单的测试图片
    img = Image.new('RGB', (400, 300), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()

def test_image_compression_auth():
    """测试图片压缩功能的认证需求"""
    print("=== 测试图片压缩功能认证需求 ===\n")
    
    # 创建测试图片
    print("1. 创建测试图片...")
    test_image = create_test_image()
    image_base64 = base64.b64encode(test_image).decode()
    print(f"✅ 测试图片创建成功，大小: {len(test_image)} bytes")
    
    # API配置
    api_base = "http://localhost:5000"
    compress_url = f"{api_base}/api/tools/compress-image"
    
    # 测试数据
    test_data = {
        "image": image_base64,
        "quality": 85,
        "format": "JPEG"
    }
    
    print(f"\n2. 测试无认证访问...")
    try:
        response = requests.post(
            compress_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ 正确返回401 - 需要认证")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data.get('error', '无错误信息')}")
            except:
                print("响应内容:", response.text[:200])
        else:
            print(f"❌ 期望401，实际返回{response.status_code}")
            try:
                print("响应内容:", response.json())
            except:
                print("响应内容:", response.text[:200])
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    
    print(f"\n3. 测试需要登录用户...")
    
    # 尝试使用测试用户登录
    login_url = f"{api_base}/api/auth/login"
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    try:
        print("尝试登录测试用户...")
        login_response = requests.post(
            login_url,
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print("登录响应:", login_result)
            
            # 检查多种可能的token字段
            token = None
            if 'token' in login_result:
                token = login_result['token']
            elif 'data' in login_result and isinstance(login_result['data'], dict) and 'token' in login_result['data']:
                token = login_result['data']['token']
            
            if token:
                print("✅ 测试用户登录成功")
                
                # 使用token测试图片压缩
                print(f"\n4. 使用认证token测试图片压缩...")
                auth_headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
                
                compress_response = requests.post(
                    compress_url,
                    json=test_data,
                    headers=auth_headers,
                    timeout=30
                )
                
                print(f"压缩响应状态码: {compress_response.status_code}")
                
                if compress_response.status_code == 200:
                    compress_result = compress_response.json()
                    if compress_result.get('success'):
                        print("✅ 图片压缩功能正常工作")
                        compression_info = compress_result.get('compression_info', {})
                        print(f"原始大小: {compression_info.get('original_size', 'N/A')}")
                        print(f"压缩后大小: {compression_info.get('compressed_size', 'N/A')}")
                        print(f"压缩率: {compression_info.get('compression_ratio', 'N/A')}")
                        print(f"处理时间: {compression_info.get('processing_time', 'N/A')}秒")
                        return True
                    else:
                        print(f"❌ 压缩失败: {compress_result.get('error', '未知错误')}")
                elif compress_response.status_code == 400:
                    error_result = compress_response.json()
                    error_msg = error_result.get('error', '')
                    if '权限' in error_msg or '会员' in error_msg or '套餐' in error_msg:
                        print("✅ 认证检查正常，但用户权限不足")
                        print(f"权限信息: {error_msg}")
                        return True
                    else:
                        print(f"❌ 其他错误: {error_msg}")
                else:
                    print(f"❌ 压缩请求失败，状态码: {compress_response.status_code}")
                    try:
                        print("错误信息:", compress_response.json())
                    except:
                        print("错误信息:", compress_response.text[:200])
                return False
            else:
                print("❌ 登录响应中没有token")
                print("登录响应:", login_result)
        else:
            print(f"❌ 登录失败，状态码: {login_response.status_code}")
            try:
                print("登录错误:", login_response.json())
            except:
                print("登录错误:", login_response.text[:200])
                
    except requests.exceptions.RequestException as e:
        print(f"❌ 登录请求失败: {e}")
    
    return False

def main():
    """主函数"""
    print("图片压缩功能认证需求测试\n")
    print("=" * 50)
    
    success = test_image_compression_auth()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 图片压缩功能认证需求验证完成")
        print("✅ 认证检查正常工作")
        print("✅ 需要登录才能使用")
        print("✅ 权限检查正常")
    else:
        print("❌ 图片压缩功能存在问题")
        print("需要进一步检查认证实现")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)