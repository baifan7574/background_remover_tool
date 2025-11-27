#!/usr/bin/env python3
"""
测试背景移除功能
"""

import requests
import json
import os

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "test123"

def test_login():
    """测试登录"""
    print("🔐 测试登录...")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 登录成功: {data.get('message', '')}")
            return data.get('token')
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求异常: {e}")
        return None

def test_background_remover(token):
    """测试背景移除功能"""
    print("\n🖼️  测试背景移除功能...")
    
    # 创建一个测试图片文件
    test_image_content = b"fake_image_content_for_testing"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    files = {
        'file': ('test_image.jpg', test_image_content, 'image/jpeg')
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/tools/remove-background", 
            files=files, 
            headers=headers
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应内容: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 背景移除成功: {data.get('message', '')}")
            print(f"💰 消耗积分: {data.get('credits_used', 0)}")
            print(f"📥 下载链接: {data.get('download_url', '')}")
            return True
        else:
            print(f"❌ 背景移除失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 背景移除请求异常: {e}")
        return False

def test_other_tools(token):
    """测试其他图片处理工具"""
    tools = [
        ("image-compressor", "图片压缩"),
        ("image-converter", "格式转换"),
        ("image-cropper", "图片裁剪")
    ]
    
    for tool_endpoint, tool_name in tools:
        print(f"\n🔧 测试{tool_name}工具...")
        
        test_image_content = b"fake_image_content_for_testing"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        files = {
            'file': ('test_image.jpg', test_image_content, 'image/jpeg')
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/tools/{tool_endpoint}", 
                files=files, 
                headers=headers
            )
            
            print(f"📊 {tool_name}响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {tool_name}成功: {data.get('message', '')}")
                print(f"💰 消耗积分: {data.get('credits_used', 0)}")
            else:
                print(f"❌ {tool_name}失败: {response.text}")
        except Exception as e:
            print(f"❌ {tool_name}请求异常: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试背景移除功能...")
    print(f"🌐 测试服务器: {BASE_URL}")
    
    # 1. 测试登录
    token = test_login()
    if not token:
        print("❌ 无法获取登录token，测试终止")
        return
    
    # 2. 测试背景移除
    background_success = test_background_remover(token)
    
    # 3. 测试其他工具
    test_other_tools(token)
    
    # 总结
    print("\n" + "="*50)
    if background_success:
        print("🎉 背景移除功能测试通过！")
        print("💡 提示：这是测试版本，实际图片处理功能需要集成真实的AI处理库")
    else:
        print("❌ 背景移除功能测试失败")
    print("="*50)

if __name__ == "__main__":
    main()