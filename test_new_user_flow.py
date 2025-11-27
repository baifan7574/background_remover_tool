#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新注册用户完整流程
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_new_user_flow():
    """测试新注册用户完整流程"""
    print("=== 测试新注册用户完整流程 ===")
    
    # 1. 注册新用户
    print("\n1. 注册新用户...")
    register_data = {
        "email": "new_user_test@example.com",
        "password": "test123456",
        "name": "新用户测试"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        print(f"注册响应状态: {response.status_code}")
        if response.status_code == 200:
            register_result = response.json()
            token = register_result.get('token')
            user_id = register_result.get('user', {}).get('id')
            print(f"✅ 注册成功，用户ID: {user_id}")
            print(f"Token: {token}")
        else:
            print(f"❌ 注册失败: {response.text}")
            return
    except Exception as e:
        print(f"❌ 注册请求异常: {e}")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 2. 获取用户信息
    print("\n2. 获取用户信息...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/profile", headers=headers)
        print(f"用户信息响应状态: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ 用户信息获取成功")
            print(f"  - 用户计划: {user_data.get('user', {}).get('plan')}")
            print(f"  - 今日日期: {user_data.get('today')}")
            
            # 显示使用统计
            usage_stats = user_data.get('usage_stats', {})
            bg_stats = usage_stats.get('background_remover', {})
            print(f"  - 背景移除工具: {bg_stats.get('current_usage')}/{bg_stats.get('daily_limit')} 次")
        else:
            print(f"❌ 获取用户信息失败: {response.text}")
    except Exception as e:
        print(f"❌ 获取用户信息异常: {e}")
    
    # 3. 检查背景移除工具权限
    print("\n3. 检查背景移除工具权限...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/check-permission/background_remover", headers=headers)
        print(f"权限检查响应状态: {response.status_code}")
        if response.status_code == 200:
            permission_data = response.json()
            print(f"✅ 权限检查成功")
            print(f"  - 有权限: {permission_data.get('has_permission')}")
            print(f"  - 当前使用: {permission_data.get('current_usage')}")
            print(f"  - 每日限制: {permission_data.get('daily_limit')}")
            print(f"  - 剩余次数: {permission_data.get('remaining_usage')}")
            print(f"  - 消息: {permission_data.get('message')}")
            
            if permission_data.get('has_permission'):
                print("✅ 新用户应该可以正常使用背景移除工具")
            else:
                print("❌ 新用户无法使用背景移除工具")
        else:
            print(f"❌ 权限检查失败: {response.text}")
    except Exception as e:
        print(f"❌ 权限检查异常: {e}")
    
    # 4. 模拟使用背景移除工具
    print("\n4. 模拟使用背景移除工具...")
    try:
        # 创建一个模拟的图片文件
        files = {
            'file': ('test.jpg', b'fake_image_data', 'image/jpeg')
        }
        response = requests.post(f"{BASE_URL}/api/tools/remove-background", 
                               files=files, headers=headers)
        print(f"背景移除响应状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 背景移除成功")
            print(f"  - 处理结果: {result.get('success')}")
        else:
            print(f"❌ 背景移除失败: {response.text}")
    except Exception as e:
        print(f"❌ 背景移除异常: {e}")
    
    # 5. 再次检查权限（使用次数应该减少）
    print("\n5. 再次检查权限（使用后）...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/check-permission/background_remover", headers=headers)
        print(f"权限检查响应状态: {response.status_code}")
        if response.status_code == 200:
            permission_data = response.json()
            print(f"✅ 使用后权限检查")
            print(f"  - 当前使用: {permission_data.get('current_usage')}")
            print(f"  - 剩余次数: {permission_data.get('remaining_usage')}")
            print(f"  - 消息: {permission_data.get('message')}")
        else:
            print(f"❌ 使用后权限检查失败: {response.text}")
    except Exception as e:
        print(f"❌ 使用后权限检查异常: {e}")

if __name__ == "__main__":
    test_new_user_flow()