#!/usr/bin/env python3
"""
测试已存在用户的登录和信息获取
"""

import requests
import json

def test_existing_user():
    # 测试已存在用户的登录
    email = 'test1763348878@test.com'  # 之前成功注册的用户
    login_data = {'email': email, 'password': 'test123456'}

    print('=== 测试已存在用户登录 ===')
    print(f'登录邮箱: {email}')

    try:
        response = requests.post('http://localhost:5000/api/auth/login',
                               json=login_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f'登录状态码: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print('登录成功!')
            print(f'Token: {result.get("token")[:50]}...')
            
            # 测试获取用户信息
            print('\n=== 测试获取用户信息 ===')
            headers = {'Authorization': f'Bearer {result.get("token")}'}
            
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
            print('登录失败:', response.text)
            
    except Exception as e:
        print(f'测试异常: {e}')

if __name__ == '__main__':
    test_existing_user()