#!/usr/bin/env python3
"""
直接使用SQL查询检查外键约束
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("=== 尝试使用SQL查询外键约束 ===")

# 由于Supabase REST API不支持直接SQL查询，我们尝试其他方法
# 让我们检查是否有其他用户相关的表

print("检查所有可能的用户表...")
tables_to_check = [
    'users', 'auth.users', 'user_profiles', 'profiles', 'accounts', 
    'user_accounts', 'customers', 'members'
]

for table in tables_to_check:
    try:
        response = supabase.table(table).select('*').limit(1).execute()
        if response.data:
            print(f"✅ 表 '{table}' 存在，字段: {list(response.data[0].keys())}")
            # 检查是否有user_id字段
            if 'user_id' in response.data[0]:
                # 查看是否有我们测试的用户ID
                user_id = 'c4bbd285-4006-4fd4-a225-3f76d055bc6d'
                user_check = supabase.table(table).select('user_id').eq('user_id', user_id).execute()
                if user_check.data:
                    print(f"   -> 在表 '{table}' 中找到用户 {user_id}")
        else:
            print(f"❌ 表 '{table}' 不存在或无权限访问")
    except Exception as e:
        print(f"❌ 表 '{table}' 错误: {str(e)[:50]}...")

print("\n=== 检查payment_records表是否可以临时禁用外键约束 ===")

# 尝试查看是否可以通过其他方式创建记录
# 我们先检查payment_records表的完整结构
try:
    # 获取表中的所有记录（应该为空）
    response = supabase.table('payment_records').select('*').limit(1).execute()
    print(f"payment_records表当前记录数: {len(response.data) if response.data else 0}")
    
    if response.data:
        print(f"payment_records字段: {list(response.data[0].keys())}")
        
except Exception as e:
    print(f"查询payment_records表失败: {e}")

print("\n=== 尝试创建一个新用户来测试 ===")

# 创建一个测试用户
try:
    import uuid
    test_user_id = str(uuid.uuid4())
    
    new_user = {
        'user_id': test_user_id,
        'email': f'test_{test_user_id[:8]}@example.com',
        'password_hash': 'test_hash',
        'plan': 'free',
        'name': '测试用户'
    }
    
    response = supabase.table('user_profiles').insert(new_user).execute()
    if response.data:
        print(f"✅ 创建测试用户成功: {test_user_id}")
        
        # 现在尝试为这个用户创建订单
        test_order = {
            'order_no': f'TEST_{test_user_id[:8]}',
            'user_id': test_user_id,
            'membership_type': 'basic',
            'membership_duration': 1,
            'payment_method': 'alipay',
            'amount': 1900,
            'original_price': 1900,
            'status': 'pending'
        }
        
        try:
            order_response = supabase.table('payment_records').insert(test_order).execute()
            if order_response.data:
                print(f"✅ 为新用户创建订单成功")
                
                # 清理测试数据
                supabase.table('payment_records').delete().eq('order_no', test_order['order_no']).execute()
                supabase.table('user_profiles').delete().eq('user_id', test_user_id).execute()
                print("✅ 测试数据已清理")
            else:
                print("❌ 为新用户创建订单失败")
        except Exception as order_error:
            print(f"❌ 为新用户创建订单异常: {order_error}")
    else:
        print("❌ 创建测试用户失败")
        
except Exception as user_error:
    print(f"❌ 创建测试用户异常: {user_error}")