#!/usr/bin/env python3
"""
深入调查外键约束问题
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# 加载环境变量 - 从项目根目录加载
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

def get_service_role_client():
    """获取服务角色客户端（有更高权限）"""
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    if not url or not service_key:
        print("❌ 缺少Supabase服务角色配置")
        return None
    return create_client(url, service_key)

def investigate_foreign_key():
    """调查外键约束问题"""
    client = get_service_role_client()
    if not client:
        return False
    
    print("=== 深入调查外键约束问题 ===")
    
    # 1. 检查用户表中所有ID相关字段
    try:
        print("\n1. 检查user_profiles表中的ID字段...")
        
        # 查询用户的所有ID信息
        test_user_id = "c4bbd285-4006-4fd4-a225-3f76d055bc6d"
        
        # 查询user_id字段
        user_id_result = client.table('user_profiles').select('id, user_id').eq('user_id', test_user_id).execute()
        print(f"按user_id查询结果: {len(user_id_result.data)} 条记录")
        if user_id_result.data:
            for user in user_id_result.data:
                print(f"  - id: {user.get('id')}")
                print(f"  - user_id: {user.get('user_id')}")
        
        # 查询id字段
        id_result = client.table('user_profiles').select('id, user_id').eq('id', test_user_id).execute()
        print(f"\n按id查询结果: {len(id_result.data)} 条记录")
        if id_result.data:
            for user in id_result.data:
                print(f"  - id: {user.get('id')}")
                print(f"  - user_id: {user.get('user_id')}")
        
        # 获取所有用户，看看ID字段的实际情况
        all_users_result = client.table('user_profiles').select('id, user_id, email').limit(5).execute()
        print(f"\n前5个用户的ID信息:")
        for i, user in enumerate(all_users_result.data):
            print(f"  用户{i+1}:")
            print(f"    - id: {user.get('id')}")
            print(f"    - user_id: {user.get('user_id')}")
            print(f"    - email: {user.get('email')}")
            
    except Exception as e:
        print(f"❌ 查询用户信息失败: {e}")
    
    # 2. 尝试用不同的用户ID创建订单
    try:
        print("\n2. 尝试用不同的用户ID创建订单...")
        
        if all_users_result.data:
            # 尝试用第一个用户的id字段
            first_user_id = all_users_result.data[0].get('id')
            first_user_user_id = all_users_result.data[0].get('user_id')
            
            print(f"尝试用id字段: {first_user_id}")
            test_order_1 = {
                'user_id': first_user_id,  # 使用id字段
                'order_no': f'test_id_field_{int(__import__("time").time())}',
                'membership_type': 'basic',
                'amount': 9.9,
                'original_price': 9.9,  # 添加缺失的字段
                'payment_method': 'alipay',
                'status': 'pending',
                'membership_duration': 30
            }
            
            try:
                result = client.table('payment_records').insert(test_order_1).execute()
                print("✅ 使用id字段插入成功!")
                if result.data:
                    record_id = result.data[0].get('id')
                    client.table('payment_records').delete().eq('id', record_id).execute()
                    print("✅ 测试记录已清理")
            except Exception as e:
                print(f"❌ 使用id字段插入失败: {e}")
            
            print(f"\n尝试用user_id字段: {first_user_user_id}")
            test_order_2 = {
                'user_id': first_user_user_id,  # 使用user_id字段
                'order_no': f'test_user_id_field_{int(__import__("time").time())}',
                'membership_type': 'basic',
                'amount': 9.9,
                'original_price': 9.9,  # 添加缺失的字段
                'payment_method': 'alipay',
                'status': 'pending',
                'membership_duration': 30
            }
            
            try:
                result = client.table('payment_records').insert(test_order_2).execute()
                print("✅ 使用user_id字段插入成功!")
                if result.data:
                    record_id = result.data[0].get('id')
                    client.table('payment_records').delete().eq('id', record_id).execute()
                    print("✅ 测试记录已清理")
            except Exception as e:
                print(f"❌ 使用user_id字段插入失败: {e}")
                
    except Exception as e:
        print(f"❌ 测试不同用户ID失败: {e}")
    
    # 3. 检查payment_records表结构
    try:
        print("\n3. 检查payment_records表结构...")
        
        # 尝试获取一条记录来了解字段结构
        records_result = client.table('payment_records').select('*').limit(1).execute()
        if records_result.data:
            print("payment_records表字段:")
            for field in records_result.data[0].keys():
                print(f"  - {field}")
        else:
            print("payment_records表为空，无法获取字段结构")
            
    except Exception as e:
        print(f"❌ 检查payment_records表结构失败: {e}")

if __name__ == "__main__":
    investigate_foreign_key()