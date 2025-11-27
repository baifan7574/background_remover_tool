#!/usr/bin/env python3
"""
检查数据库表结构
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def check_table_structure():
    """检查表结构"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        supabase = create_client(supabase_url, supabase_key)
        
        # 查看payment_records表的结构
        print("=== 检查payment_records表结构 ===")
        try:
            # 尝试查询表结构信息
            response = supabase.rpc('get_table_columns', {'table_name': 'payment_records'}).execute()
            print(f"payment_records表结构: {response.data}")
        except Exception as e:
            print(f"无法获取表结构: {e}")
        
        # 查看user_profiles表的结构
        print("\n=== 检查user_profiles表结构 ===")
        try:
            response = supabase.rpc('get_table_columns', {'table_name': 'user_profiles'}).execute()
            print(f"user_profiles表结构: {response.data}")
        except Exception as e:
            print(f"无法获取表结构: {e}")
        
        # 检查外键约束
        print("\n=== 检查外键约束 ===")
        try:
            # 尝试查看约束信息
            response = supabase.table('information_schema.table_constraints').select('*').eq('table_name', 'payment_records').execute()
            print(f"payment_records表约束: {response.data}")
        except Exception as e:
            print(f"无法获取约束信息: {e}")
        
        # 尝试直接插入一条记录来测试
        print("\n=== 测试直接插入 ===")
        try:
            test_data = {
                'order_no': 'TEST_ORDER_001',
                'user_id': 'c4bbd285-4006-4fd4-a225-3f76d055bc6d',
                'membership_type': 'basic',
                'membership_duration': 1,
                'payment_method': 'alipay',
                'amount': 1900,
                'original_price': 1900,
                'status': 'pending'
            }
            
            response = supabase.table('payment_records').insert(test_data).execute()
            print(f"直接插入结果: {response.data}")
            
            # 如果成功，删除测试记录
            if response.data:
                supabase.table('payment_records').delete().eq('order_no', 'TEST_ORDER_001').execute()
                print("测试记录已删除")
                
        except Exception as e:
            print(f"直接插入失败: {e}")
        
    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == "__main__":
    check_table_structure()