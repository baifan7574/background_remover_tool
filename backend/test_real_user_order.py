#!/usr/bin/env python3
"""
使用真实用户测试OrderManager修复
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 从项目根目录加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from supabase import create_client
from order_manager import OrderManager

def test_with_real_user():
    """使用真实用户测试OrderManager"""
    print("=== 使用真实用户测试OrderManager修复 ===")
    
    # 初始化Supabase客户端
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ 缺少Supabase配置")
        return
    
    try:
        # 使用服务角色客户端
        service_client = create_client(supabase_url, supabase_key)
        
        # 创建OrderManager实例
        manager = OrderManager(service_client)
        
        # 使用真实存在的用户ID (user_profiles.user_id)
        test_user_id = "5d887a17-8694-416f-bdbc-111e88c4f2b2"  # 对应email: final_success_test@example.com
        
        print(f"1. 测试创建订单，用户ID: {test_user_id}")
        
        # 创建订单
        result = manager.create_order(
            user_id=test_user_id,
            plan='basic',
            payment_method='alipay'
        )
        
        print(f"创建订单结果: {result}")
        
        if result['success']:
            print("✅ 订单创建成功！")
            order = result['order']
            print(f"订单号: {order['order_no']}")
            print(f"用户ID: {order['user_id']}")
            print(f"会员类型: {order['membership_type']}")
            print(f"金额: {order['amount']}")
            print(f"状态: {order['status']}")
            
            # 测试会员激活
            print("\n2. 测试会员激活...")
            activation_result = manager.activate_membership(order['order_no'])
            print(f"会员激活结果: {activation_result}")
            
            if activation_result['success']:
                print("✅ 会员激活成功！")
                print(f"会员到期时间: {activation_result['membership_end']}")
            else:
                print(f"❌ 会员激活失败: {activation_result['error']}")
                
        else:
            print(f"❌ 订单创建失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_with_real_user()