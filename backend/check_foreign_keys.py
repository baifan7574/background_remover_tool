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

def get_supabase_client():
    """获取Supabase客户端"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        print("❌ 缺少Supabase配置")
        return None
    return create_client(url, key)

def check_foreign_keys():
    """检查外键约束详情"""
    client = get_supabase_client()
    if not client:
        return False
    
    print("=== 检查外键约束详情 ===")
    
    # 1. 检查payment_records表的所有约束
    try:
        print("\n1. 检查payment_records表的约束...")
        constraints_sql = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.table_name = 'payment_records'
            AND tc.constraint_type = 'FOREIGN KEY';
        """
        
        result = client.rpc('execute_sql', {'sql_query': constraints_sql}).execute()
        if result.data:
            print("外键约束详情:")
            for constraint in result.data:
                print(f"  - 约束名: {constraint.get('constraint_name')}")
                print(f"    本地表: {constraint.get('table_name')}.{constraint.get('column_name')}")
                print(f"    引用表: {constraint.get('foreign_table_name')}.{constraint.get('foreign_column_name')}")
        else:
            print("❌ 无法获取外键约束信息")
            
    except Exception as e:
        print(f"❌ 检查约束失败: {e}")
    
    # 2. 检查user_profiles表的主键
    try:
        print("\n2. 检查user_profiles表的主键...")
        pk_sql = """
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_name = 'user_profiles'
            AND tc.constraint_type = 'PRIMARY KEY';
        """
        
        result = client.rpc('execute_sql', {'sql_query': pk_sql}).execute()
        if result.data:
            print("user_profiles表主键:")
            for pk in result.data:
                print(f"  - 主键: {pk.get('column_name')}")
        else:
            print("❌ 无法获取主键信息")
            
    except Exception as e:
        print(f"❌ 检查主键失败: {e}")
    
    # 3. 检查两个表的具体字段
    try:
        print("\n3. 检查表字段详情...")
        
        # user_profiles表字段
        profiles_result = client.table('user_profiles').select('*').limit(1).execute()
        if profiles_result.data:
            print("user_profiles表字段:")
            for field in profiles_result.data[0].keys():
                print(f"  - {field}")
        
        # payment_records表字段
        records_result = client.table('payment_records').select('*').limit(1).execute()
        if records_result.data:
            print("payment_records表字段:")
            for field in records_result.data[0].keys():
                print(f"  - {field}")
        else:
            print("payment_records表为空，无法获取字段")
            
    except Exception as e:
        print(f"❌ 检查字段失败: {e}")
    
    # 4. 测试特定用户ID
    try:
        print("\n4. 测试特定用户ID...")
        test_user_id = "c4bbd285-4006-4fd4-a225-3f76d055bc6d"
        
        # 检查user_profiles中的用户
        user_result = client.table('user_profiles').select('id, user_id').eq('user_id', test_user_id).execute()
        print(f"user_profiles中查询结果: {len(user_result.data)} 条记录")
        if user_result.data:
            for user in user_result.data:
                print(f"  - id: {user.get('id')}, user_id: {user.get('user_id')}")
        
        # 尝试插入最小化的payment_records记录
        print("\n5. 尝试插入最小化记录...")
        minimal_data = {
            'user_id': test_user_id,
            'order_no': f'test_minimal_{int(time.time())}',
            'membership_type': 'basic',
            'amount': 9.9,
            'payment_method': 'alipay',
            'status': 'pending',
            'membership_duration': 30
        }
        
        insert_result = client.table('payment_records').insert(minimal_data).execute()
        print("✅ 插入成功!")
        print(f"插入的记录ID: {insert_result.data[0].get('id') if insert_result.data else 'Unknown'}")
        
        # 立即删除测试记录
        if insert_result.data:
            record_id = insert_result.data[0].get('id')
            delete_result = client.table('payment_records').delete().eq('id', record_id).execute()
            print("✅ 测试记录已清理")
        
    except Exception as e:
        print(f"❌ 插入测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import time
    check_foreign_keys()