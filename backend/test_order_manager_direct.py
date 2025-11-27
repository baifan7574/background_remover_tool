#!/usr/bin/env python3
"""
直接测试OrderManager的create_order方法
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入模块
from supabase import create_client
from order_manager import OrderManager

def test_order_manager_direct():
    """直接测试OrderManager"""
    print("=== 直接测试OrderManager.create_order ===")
    
    try:
        # 初始化Supabase客户端
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ 缺少Supabase配置")
            return False
            
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase客户端初始化成功")
        
        # 创建OrderManager实例
        order_manager = OrderManager(supabase)
        print("✅ OrderManager实例创建成功")
        
        # 测试用户ID (user_profiles.user_id字段)
        test_user_id = "5d887a17-8694-416f-bdbc-111e88c4f2b2"
        
        # 测试创建订单
        print(f"1. 测试创建订单，用户ID: {test_user_id}")
        result = order_manager.create_order(
            user_id=test_user_id,
            plan='basic',
            payment_method='alipay'
        )
        
        print(f"创建订单结果: {result}")
        
        if result.get('success'):
            print("✅ 订单创建成功！")
            order = result.get('order', {})
            print(f"订单号: {order.get('order_no')}")
            print(f"用户ID: {order.get('user_id')}")
            print(f"金额: {order.get('amount')}")
            print(f"状态: {order.get('status')}")
            return True
        else:
            print(f"❌ 订单创建失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_order_manager_direct()
    sys.exit(0 if success else 1)