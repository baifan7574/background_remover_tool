#!/usr/bin/env python3
"""
测试认证登录
"""

import requests
import json

def test_auth():
    """测试认证登录"""
    api_base = "http://localhost:5000"
    login_url = f"{api_base}/api/auth/login"
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    print("🔐 测试登录...")
    print(f"📍 URL: {login_url}")
    print(f"📤 数据: {login_data}")
    
    try:
        response = requests.post(
            login_url,
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📥 响应头: {dict(response.headers)}")
        print(f"📄 响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功!")
            print(f"🔑 Token: {result.get('token', 'N/A')}")
            return result.get('token')
        else:
            print(f"❌ 登录失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

if __name__ == "__main__":
    token = test_auth()
    if token:
        print(f"\n🎉 获取到token: {token[:20]}...")
    else:
        print("\n❌ 未能获取token")