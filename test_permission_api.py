#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试权限检查API
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_permission_check():
    """测试权限检查API"""
    print("=== 测试权限检查API ===")
    
    # 1. 先注册一个新用户
    print("\n1. 注册新用户...")
    register_data = {
        "email": "test_permission@example.com",
        "password": "test123456",
        "name": "权限测试用户"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        print(f"注册响应状态: {response.status_code}")
        if response.status_code == 200:
            register_result = response.json()
            token = register_result.get('token')
            user_id = register_result.get('user', {}).get('id')
            print(f"注册成功，用户ID: {user_id}")
            print(f"Token: {token}")
        else:
            print(f"注册失败: {response.text}")
            return
    except Exception as e:
        print(f"注册请求异常: {e}")
        return
    
    # 2. 测试权限检查API
    print("\n2. 测试权限检查API...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试背景移除工具权限
    try:
        response = requests.get(f"{BASE_URL}/api/auth/check-permission/background_remover", headers=headers)
        print(f"权限检查响应状态: {response.status_code}")
        print(f"权限检查响应内容: {response.text}")
        
        if response.status_code == 200:
            permission_data = response.json()
            print(f"权限检查结果:")
            print(f"  - 有权限: {permission_data.get('has_permission')}")
            print(f"  - 当前使用: {permission_data.get('current_usage')}")
            print(f"  - 每日限制: {permission_data.get('daily_limit')}")
            print(f"  - 剩余次数: {permission_data.get('remaining_usage')}")
            print(f"  - 用户计划: {permission_data.get('plan')}")
            print(f"  - 消息: {permission_data.get('message')}")
        else:
            print(f"权限检查失败: {response.text}")
    except Exception as e:
        print(f"权限检查请求异常: {e}")
    
    # 3. 测试用户信息API
    print("\n3. 测试用户信息API...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/profile", headers=headers)
        print(f"用户信息响应状态: {response.status_code}")
        print(f"用户信息响应内容: {response.text}")
    except Exception as e:
        print(f"用户信息请求异常: {e}")

if __name__ == "__main__":
    test_permission_check()