#!/usr/bin/env python3
"""
检查和修复RLS策略问题
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

def get_service_role_client():
    """获取服务角色客户端（有更高权限）"""
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    if not url or not service_key:
        print("❌ 缺少Supabase服务角色配置")
        return None
    return create_client(url, service_key)

def check_rls_policies():
    """检查RLS策略"""
    client = get_supabase_client()
    service_client = get_service_role_client()
    
    if not client or not service_client:
        return False
    
    print("=== 检查RLS策略 ===")
    
    # 1. 检查payment_records表的RLS状态
    try:
        print("\n1. 检查payment_records表的RLS状态...")
        
        # 使用服务角色查询RLS状态
        rls_check_sql = """
        SELECT 
            schemaname,
            tablename,
            rowsecurity
        FROM pg_tables 
        WHERE tablename = 'payment_records';
        """
        
        # 由于没有execute_sql函数，我们直接尝试插入来测试
        test_data = {
            'user_id': 'c4bbd285-4006-4fd4-a225-3f76d055bc6d',
            'order_no': f'test_rls_{int(__import__("time").time())}',
            'membership_type': 'basic',
            'amount': 9.9,
            'payment_method': 'alipay',
            'status': 'pending',
            'membership_duration': 30
        }
        
        # 尝试用普通用户插入
        print("尝试用普通用户插入...")
        try:
            result = client.table('payment_records').insert(test_data).execute()
            print("✅ 普通用户插入成功!")
            if result.data:
                # 清理测试数据
                record_id = result.data[0].get('id')
                client.table('payment_records').delete().eq('id', record_id).execute()
                print("✅ 测试数据已清理")
        except Exception as e:
            print(f"❌ 普通用户插入失败: {e}")
            
        # 尝试用服务角色插入
        print("\n尝试用服务角色插入...")
        try:
            result = service_client.table('payment_records').insert(test_data).execute()
            print("✅ 服务角色插入成功!")
            if result.data:
                record_id = result.data[0].get('id')
                print(f"插入记录ID: {record_id}")
                
                # 验证插入的数据
                verify_result = service_client.table('payment_records').select('*').eq('id', record_id).execute()
                if verify_result.data:
                    print("插入的数据:")
                    for key, value in verify_result.data[0].items():
                        print(f"  {key}: {value}")
                
                # 清理测试数据
                service_client.table('payment_records').delete().eq('id', record_id).execute()
                print("✅ 测试数据已清理")
                
        except Exception as e:
            print(f"❌ 服务角色插入也失败: {e}")
            
    except Exception as e:
        print(f"❌ 检查RLS状态失败: {e}")
    
    # 2. 测试OrderManager
    try:
        print("\n2. 测试OrderManager...")
        sys.path.append(os.path.dirname(__file__))
        from order_manager import OrderManager
        
        service_client = get_service_role_client()
        if not service_client:
            print("❌ 无法获取服务角色客户端")
            return
            
        manager = OrderManager(service_client)
        result = manager.create_order(
            user_id='c4bbd285-4006-4fd4-a225-3f76d055bc6d',
            plan='basic',
            payment_method='alipay'
        )
        
        if result.get('success'):
            print("✅ OrderManager创建订单成功!")
            print(f"订单号: {result.get('order_no')}")
            
            # 清理测试订单
            service_client = get_service_role_client()
            if service_client:
                delete_result = service_client.table('payment_records').delete().eq('order_no', result.get('order_no')).execute()
                print("✅ 测试订单已清理")
        else:
            print(f"❌ OrderManager创建订单失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ OrderManager测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_rls_policies()