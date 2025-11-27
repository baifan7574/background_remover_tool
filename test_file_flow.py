#!/usr/bin/env python3
"""
测试完整的文件上传、处理和下载流程
"""

import requests
import json
import os
from PIL import Image
import io

# 创建测试图片
def create_test_image():
    """创建一个测试图片"""
    img = Image.new('RGB', (400, 300), color='red')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Test Image", fill='white')
    
    # 将图片保存到内存中
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer

def test_complete_flow():
    """测试完整的文件处理流程"""
    base_url = "http://localhost:5000"
    
    print("🧪 测试完整的文件上传、处理和下载流程...")
    
    # 1. 注册新用户
    print("\n1. 注册新用户...")
    register_data = {
        "email": "test_file@example.com",
        "password": "test123456"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data)
        if response.status_code == 200:
            register_result = response.json()
            token = register_result['token']
            print(f"✅ 用户注册成功: {register_result['user']['email']}")
        else:
            print(f"❌ 注册失败: {response.text}")
            return
    except Exception as e:
        print(f"❌ 注册请求失败: {e}")
        return
    
    # 2. 准备认证头
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 3. 检查权限
    print("\n2. 检查背景移除工具权限...")
    try:
        response = requests.get(f"{base_url}/api/auth/check-permission/background_remover", headers=headers)
        if response.status_code == 200:
            permission_result = response.json()
            print(f"✅ 权限检查通过: {permission_result}")
        else:
            print(f"❌ 权限检查失败: {response.text}")
            return
    except Exception as e:
        print(f"❌ 权限检查请求失败: {e}")
        return
    
    # 4. 上传文件进行处理
    print("\n3. 上传图片进行背景移除...")
    try:
        # 创建测试图片
        test_image = create_test_image()
        
        files = {
            'file': ('test_image.png', test_image, 'image/png')
        }
        
        response = requests.post(
            f"{base_url}/api/tools/remove-background",
            headers=headers,
            files=files
        )
        
        if response.status_code == 200:
            process_result = response.json()
            print(f"✅ 图片处理成功: {process_result}")
            download_url = process_result['download_url']
            output_filename = process_result['output_filename']
        else:
            print(f"❌ 图片处理失败: {response.text}")
            return
    except Exception as e:
        print(f"❌ 图片处理请求失败: {e}")
        return
    
    # 5. 下载处理后的文件
    print("\n4. 下载处理后的文件...")
    try:
        response = requests.get(f"{base_url}{download_url}", headers=headers)
        
        if response.status_code == 200:
            # 检查是否是图片文件
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                # 保存下载的文件
                with open(f"downloaded_{output_filename}", 'wb') as f:
                    f.write(response.content)
                print(f"✅ 文件下载成功，已保存为: downloaded_{output_filename}")
                print(f"   文件大小: {len(response.content)} bytes")
                print(f"   Content-Type: {content_type}")
            else:
                print(f"❌ 下载的不是图片文件，Content-Type: {content_type}")
                print(f"   响应内容: {response.text[:200]}...")
        else:
            print(f"❌ 文件下载失败: {response.text}")
    except Exception as e:
        print(f"❌ 文件下载请求失败: {e}")
        return
    
    # 6. 检查使用统计
    print("\n5. 检查使用统计...")
    try:
        response = requests.get(f"{base_url}/api/auth/user-info", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            usage_stats = user_info.get('usage_stats', {})
            print(f"✅ 使用统计: {usage_stats}")
        else:
            print(f"❌ 获取用户信息失败: {response.text}")
    except Exception as e:
        print(f"❌ 获取用户信息请求失败: {e}")
    
    print("\n🎉 完整流程测试完成！")

if __name__ == "__main__":
    test_complete_flow()