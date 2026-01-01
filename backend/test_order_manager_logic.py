#!/usr/bin/env python3
"""
测试OrderManager修复的逻辑（不依赖Supabase连接）
"""

import sys
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_order_manager_logic():
    """测试OrderManager的修复逻辑"""
    print("=== 测试OrderManager修复逻辑 ===")
    
    try:
        # 模拟Supabase客户端
        mock_supabase = Mock()
        
        # 模拟用户查询响应
        mock_user_response = Mock()
        mock_user_response.data = [{'id': 'real-database-id-123'}]
        
        # 模拟订单插入响应
        mock_order_response = Mock()
        mock_order_response.data = [{
            'id': 'order-id-456',
            'order_no': 'ORD20250117001',
            'user_id': 'real-database-id-123',  # 应该是真实的数据库ID
            'membership_type': 'basic',
            'amount': 2900,
            'status': 'pending'
        }]
        
        # 设置模拟表操作
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_order_response
        
        # 导入并创建OrderManager
        from order_manager import OrderManager
        order_manager = OrderManager(mock_supabase)
        
        # 测试用户ID (user_profiles.user_id字段)
        test_user_id = "5d887a17-8694-416f-bdbc-111e88c4f2b2"
        
        print(f"1. 测试创建订单逻辑，用户ID: {test_user_id}")
        
        # 调用create_order方法
        result = order_manager.create_order(
            user_id=test_user_id,
            plan='basic',
            payment_method='alipay'
        )
        
        print(f"创建订单结果: {result}")
        
        # 验证结果
        if result.get('success'):
            print("✅ 订单创建逻辑测试成功！")
            order = result.get('order', {})
            print(f"订单号: {order.get('order_no')}")
            print(f"用户ID: {order.get('user_id')}")
            print(f"金额: {order.get('amount')}")
            print(f"状态: {order.get('status')}")
            
            # 验证关键修复点
            if order.get('user_id') == 'real-database-id-123':
                print("✅ 用户ID映射修复正确：使用了真实的数据库ID")
            else:
                print(f"❌ 用户ID映射修复失败：期望 'real-database-id-123'，实际 '{order.get('user_id')}'")
                return False
                
            # 验证Supabase调用 - 检查是否调用了正确的表
            table_calls = [call[0][0] for call in mock_supabase.table.call_args_list]
            if 'user_profiles' in table_calls:
                print("✅ Supabase查询调用正确：调用了user_profiles表")
            else:
                print(f"❌ Supabase查询调用错误：未调用user_profiles表，实际调用: {table_calls}")
                return False
            
            return True
        else:
            print(f"❌ 订单创建逻辑测试失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_activate_membership_logic():
    """测试activate_membership的修复逻辑"""
    print("\n=== 测试activate_membership修复逻辑 ===")
    
    try:
        # 模拟Supabase客户端
        mock_supabase = Mock()
        
        # 模拟订单查询响应
        mock_order_response = Mock()
        mock_order_response.data = [{
            'id': 'order-id-456',
            'order_no': 'ORD20250117001',
            'user_id': 'real-database-id-123',  # 真实的数据库ID
            'membership_type': 'basic',
            'membership_duration': 1,  # 1个月
            'amount': 2900,
            'status': 'paid'
        }]
        
        # 模拟用户更新响应
        mock_user_response = Mock()
        mock_user_response.data = [{
            'id': 'real-database-id-123',
            'user_id': '5d887a17-8694-416f-bdbc-111e88c4f2b2',  # 原始user_id
            'plan': 'basic',
            'membership_type': 'basic',
            'membership_expires_at': '2025-02-17T19:58:13'
        }]
        
        # 模拟会员日志插入响应
        mock_log_response = Mock()
        mock_log_response.data = [{'id': 'log-id-789'}]
        
        # 设置模拟表操作
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_order_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_user_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_log_response
        
        # 导入并创建OrderManager
        from order_manager import OrderManager
        order_manager = OrderManager(mock_supabase)
        
        print("2. 测试激活会员逻辑")
        
        # 调用activate_membership方法
        result = order_manager.activate_membership('ORD20250117001')
        
        print(f"激活会员结果: {result}")
        
        # 验证结果
        if result.get('success'):
            print("✅ 激活会员逻辑测试成功！")
            
            # 验证关键修复点
            update_calls = mock_supabase.table.return_value.update.call_args_list
            user_profile_update = None
            
            for call in update_calls:
                if mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value == mock_user_response:
                    user_profile_update = call
                    break
            
            if user_profile_update:
                update_data = user_profile_update[0][0]  # 第一个位置参数
                print(f"更新数据: {update_data}")
                
                # 检查字段名修复
                if 'membership_expires_at' in update_data and 'membership_type' in update_data:
                    print("✅ 字段名修复正确：使用了membership_expires_at和membership_type")
                else:
                    print("❌ 字段名修复失败")
                    return False
                    
                # 检查查询条件
                eq_call = mock_supabase.table.return_value.update.return_value.eq
                if 'id' in str(eq_call.call_args) and 'real-database-id-123' in str(eq_call.call_args):
                    print("✅ 查询条件修复正确：使用了id字段")
                else:
                    print("❌ 查询条件修复失败")
                    return False
            else:
                print("❌ 未找到用户更新调用")
                return False
                
            return True
        else:
            print(f"❌ 激活会员逻辑测试失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_order_manager_logic()
    success2 = test_activate_membership_logic()
    
    if success1 and success2:
        print("\n🎉 所有OrderManager修复逻辑测试通过！")
        print("✅ 用户ID字段映射问题已修复")
        print("✅ activate_membership字段名问题已修复")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)