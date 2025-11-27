#!/usr/bin/env python3
"""
测试用户注册、登录和权限检查功能
"""

import requests
import json
from datetime import datetime

def test_user_flow():
    # 测试注册
    email = f'test{int(datetime.now().timestamp())}@test.com'
    register_data = {
        'email': email,
        'password': 'test123456'
    }

    print('=== 测试注册 ===')
    print(f'注册邮箱: {email}')

    try:
        response = requests.post('http://localhost:5000/api/auth/register', 
                               json=register_data, 
                               headers={'Content-Type': 'application/json'})
        
        print(f'注册状态码: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print('注册成功!')
            print(f'用户ID: {result.get("user_id")}')
            print(f'计划: {result.get("plan")}')
            
            # 测试登录
            print('\n=== 测试登录 ===')
            login_data = {'email': email, 'password': 'test123456'}
            
            login_response = requests.post('http://localhost:5000/api/auth/login',
                                        json=login_data,
                                        headers={'Content-Type': 'application/json'})
            
            print(f'登录状态码: {login_response.status_code}')
            if login_response.status_code == 200:
                login_result = login_response.json()
                print('登录成功!')
                print(f'Token: {login_result.get("token")[:50]}...')
                
                # 测试获取用户信息
                print('\n=== 测试获取用户信息 ===')
                headers = {'Authorization': f'Bearer {login_result.get("token")}'}
                
                profile_response = requests.get('http://localhost:5000/api/auth/profile',
                                              headers=headers)
                
                print(f'用户信息状态码: {profile_response.status_code}')
                if profile_response.status_code == 200:
                    profile = profile_response.json()
                    print('用户信息获取成功!')
                    print(f'完整响应: {json.dumps(profile, indent=2, ensure_ascii=False)}')
                    
                    # 检查用户信息
                    user_info = profile.get('user', {})
                    usage_stats = profile.get('usage_stats', {})
                    
                    print(f'用户计划: {user_info.get("plan")}')
                    print(f'每日限制: {user_info.get("daily_limit")}')
                    print(f'今日使用: {usage_stats.get("today_usage")}')
                    print(f'剩余次数: {usage_stats.get("remaining_daily")}')
                    
                    # 检查是否还显示"无限制"
                    daily_limit = user_info.get("daily_limit", 0)
                    if daily_limit == 0:
                        print('❌ 问题：仍然显示无限制')
                    else:
                        print('✅ 修复成功：显示正确的限制')
                        
                else:
                    print('获取用户信息失败:', profile_response.text)
            else:
                print('登录失败:', login_response.text)
        else:
            print('注册失败:', response.text)
            
    except Exception as e:
        print(f'测试异常: {e}')

if __name__ == '__main__':
    test_user_flow()