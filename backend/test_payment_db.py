#!/usr/bin/env python3
"""
测试支付API的数据库连接
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_supabase_connection():
    """测试Supabase连接"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        print(f"Supabase URL: {supabase_url}")
        print(f"Supabase Key: {supabase_key[:20]}...")
        
        # 创建客户端
        supabase = create_client(supabase_url, supabase_key)
        
        # 测试连接 - 查询用户表
        print("测试用户表连接...")
        response = supabase.table('user_profiles').select('count').execute()
        print(f"用户表查询成功: {response.data}")
        
        # 测试支付记录表
        print("测试支付记录表连接...")
        response = supabase.table('payment_records').select('count').execute()
        print(f"支付记录表查询成功: {response.data}")
        
        return True
        
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

def test_order_creation():
    """测试订单创建"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        supabase = create_client(supabase_url, supabase_key)
        
        # 测试创建订单
        from order_manager import OrderManager
        order_manager = OrderManager(supabase)
        
        result = order_manager.create_order(
            user_id='c4bbd285-4006-4fd4-a225-3f76d055bc6d',
            plan='basic',
            payment_method='alipay'
        )
        
        print(f"订单创建结果: {result}")
        return result['success']
        
    except Exception as e:
        print(f"订单创建失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 测试Supabase连接 ===")
    if test_supabase_connection():
        print("✅ 数据库连接正常")
        
        print("\n=== 测试订单创建 ===")
        if test_order_creation():
            print("✅ 订单创建成功")
        else:
            print("❌ 订单创建失败")
    else:
        print("❌ 数据库连接失败")