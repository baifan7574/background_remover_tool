#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sk_app import users_db, user_profiles_db

def check_database():
    print('=== 当前用户数据库状态 ===')
    print(f'用户数量: {len(users_db)}')
    
    for user_id, user_data in users_db.items():
        print(f'用户ID: {user_id}')
        print(f'  邮箱: {user_data.get("email", "未知")}')
        print(f'  姓名: {user_data.get("name", "未知")}')
        print(f'  计划: {user_data.get("plan", "未知")}')
        print(f'  Token: {user_data.get("token", "未知")}')
        print('---')

    print(f'\n=== 用户资料数据库状态 ===')
    print(f'资料数量: {len(user_profiles_db)}')
    
    for user_id, profile_data in user_profiles_db.items():
        print(f'用户ID: {user_id}')
        print(f'  今日: {profile_data.get("today", "未知")}')
        if 'usage_stats' in profile_data:
            print('  使用统计:')
            for tool, stats in profile_data['usage_stats'].items():
                print(f'    {tool}: {stats}')
        print('---')

if __name__ == '__main__':
    check_database()