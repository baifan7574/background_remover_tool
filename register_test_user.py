#!/usr/bin/env python3
"""
注册测试用户
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:5000"

def register_test_user():
    """注册测试用户"""
    print("🔐 注册测试用户...")
    
    register_data = {
        "email": "test@example.com",
        "password": "test123",
        "name": "测试用户"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应内容: {response.text}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ 注册成功: {data.get('message', '')}")
            return True
        else:
            print(f"❌ 注册失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 注册请求异常: {e}")
        return False

if __name__ == "__main__":
    register_test_user()