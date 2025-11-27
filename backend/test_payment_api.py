#!/usr/bin/env python3
"""
测试支付API端点
"""

import requests
import json

def test_payment_api():
    """测试支付API"""
    print("=== 测试支付API端点 ===")
    
    # API基础URL
    base_url = "http://localhost:5000"
    
    # 测试用户ID (user_profiles.user_id)
    test_user_id = "5d887a17-8694-416f-bdbc-111e88c4f2b2"
    
    # 测试创建订单
    print(f"1. 测试创建订单API，用户ID: {test_user_id}")
    
    order_data = {
        "user_id": test_user_id,
        "plan": "basic",
        "payment_method": "alipay"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/payment/create-order",
            json=order_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 订单创建API测试成功！")
                order = result.get('order', {})
                print(f"订单号: {order.get('order_no')}")
                print(f"用户ID: {order.get('user_id')}")
                print(f"金额: {order.get('amount')}")
            else:
                print(f"❌ 订单创建API返回失败: {result.get('error')}")
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端API服务器")
        print("请确保后端服务器正在运行在 http://localhost:5000")
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")

if __name__ == "__main__":
    test_payment_api()