#!/usr/bin/env python3
"""
检查数据库表和字段
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

# 检查user_profiles表的实际字段
print('=== 检查user_profiles表字段 ===')
try:
    response = supabase.table('user_profiles').select('*').limit(1).execute()
    if response.data:
        print(f'user_profiles字段: {list(response.data[0].keys())}')
        print(f'示例数据: {response.data[0]}')
    else:
        print('user_profiles表为空')
except Exception as e:
    print(f'查询user_profiles失败: {e}')

# 检查是否有users表
print('\n=== 检查是否有users表 ===')
try:
    response = supabase.table('users').select('*').limit(1).execute()
    if response.data:
        print(f'users表存在，字段: {list(response.data[0].keys())}')
    else:
        print('users表为空')
except Exception as e:
    print(f'users表不存在或无权限访问: {e}')

# 检查payment_records表结构
print('\n=== 检查payment_records表字段 ===')
try:
    response = supabase.table('payment_records').select('*').limit(1).execute()
    if response.data:
        print(f'payment_records字段: {list(response.data[0].keys())}')
    else:
        print('payment_records表为空，尝试插入测试数据...')
        
        # 尝试插入最小化的测试数据
        test_data = {
            'order_no': 'TEST_001',
            'user_id': 'c4bbd285-4006-4fd4-a225-3f76d055bc6d',
            'membership_type': 'basic',
            'payment_method': 'alipay',
            'amount': 1900,
            'status': 'pending'
        }
        
        try:
            response = supabase.table('payment_records').insert(test_data).execute()
            print(f'插入成功: {response.data}')
            
            # 删除测试数据
            supabase.table('payment_records').delete().eq('order_no', 'TEST_001').execute()
            print('测试数据已删除')
        except Exception as insert_error:
            print(f'插入失败: {insert_error}')
            
except Exception as e:
    print(f'查询payment_records失败: {e}')