#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的每日次数限制功能
验证所有工具都使用统一的每日免费次数而非积分系统
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:5000"

def test_login():
    """测试登录获取token"""
    print("🔐 测试用户登录...")
    
    login_data = {
        "email": "testuser789@example.com",
        "password": "123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ 登录成功，获取到token")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 登录请求异常: {e}")
        return None

def test_tool_with_daily_limit(token, tool_name, tool_data, tool_url):
    """测试工具的每日次数限制功能"""
    print(f"\n🔧 测试 {tool_name} 工具...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"{BASE_URL}{tool_url}", json=tool_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success', False)
            
            if success:
                current_usage = data.get('current_usage', 0)
                daily_limit = data.get('daily_limit', 0)
                remaining_usage = data.get('remaining_usage', 0)
                message = data.get('message', '')
                
                print(f"✅ {tool_name} 使用成功")
                print(f"   当前使用次数: {current_usage}")
                print(f"   每日限制: {daily_limit}")
                print(f"   剩余次数: {remaining_usage}")
                print(f"   消息: {message}")
                
                # 检查返回信息中是否包含积分相关内容（应该不包含）
                if 'credits' in str(data).lower():
                    print(f"⚠️  警告: {tool_name} 仍然包含积分相关内容")
                    return False
                else:
                    print(f"✅ {tool_name} 已正确使用每日次数限制")
                    return True
            else:
                print(f"❌ {tool_name} 使用失败: {data}")
                return False
        else:
            print(f"❌ {tool_name} API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {tool_name} 请求异常: {e}")
        return False

def test_usage_records(token):
    """测试使用记录查询"""
    print(f"\n📊 测试使用记录查询...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/user/usage", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            usage_records = data.get('usage_records', [])
            total_records = data.get('total_records', 0)
            
            print(f"✅ 使用记录查询成功")
            print(f"   总记录数: {total_records}")
            
            # 显示最近的使用记录
            for i, record in enumerate(usage_records[:3]):
                tool_name = record.get('tool_name', 'unknown')
                created_at = record.get('created_at', 'unknown')
                print(f"   记录 {i+1}: {tool_name} - {created_at}")
            
            return True
        else:
            print(f"❌ 使用记录查询失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 使用记录查询异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 测试修复后的每日次数限制功能")
    print("=" * 50)
    
    # 1. 登录获取token
    token = test_login()
    if not token:
        print("❌ 无法获取token，测试终止")
        return
    
    # 2. 测试各种工具
    tools_to_test = [
        {
            'name': 'currency_converter',
            'url': '/api/tools/currency-converter',
            'data': {
                'amount': 100,
                'from_currency': 'CNY',
                'to_currency': 'USD'
            }
        },
        {
            'name': 'unit_converter',
            'url': '/api/tools/unit-converter',
            'data': {
                'value': 10,
                'from_unit': 'kg',
                'to_unit': 'lb'
            }
        },
        {
            'name': 'shipping_calculator',
            'url': '/api/tools/shipping-calculator',
            'data': {
                'weight': 2,
                'from_country': 'CN',
                'to_country': 'US'
            }
        },
        {
            'name': 'send_email',
            'url': '/api/tools/send-email',
            'data': {
                'to': 'test@example.com',
                'subject': '测试邮件',
                'body': '这是一个测试邮件内容'
            }
        }
    ]
    
    all_passed = True
    results = []
    
    for tool in tools_to_test:
        success = test_tool_with_daily_limit(
            token, 
            tool['name'], 
            tool['data'], 
            tool['url']
        )
        results.append((tool['name'], success))
        if not success:
            all_passed = False
        
        # 短暂延迟，避免请求过快
        time.sleep(0.5)
    
    # 3. 测试使用记录查询
    usage_success = test_usage_records(token)
    if not usage_success:
        all_passed = False
    
    # 4. 总结测试结果
    print(f"\n📋 测试结果总结")
    print("=" * 50)
    
    for tool_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{tool_name}: {status}")
    
    print(f"使用记录查询: {'✅ 通过' if usage_success else '❌ 失败'}")
    
    if all_passed:
        print(f"\n🎉 所有测试通过！系统已成功修复为每日次数限制模式")
    else:
        print(f"\n⚠️  部分测试失败，需要进一步检查")
    
    print(f"\n📊 免费用户每日限制:")
    print(f"   - 背景移除: 3次")
    print(f"   - 图片压缩/格式转换/图片裁剪: 5次")
    print(f"   - 邮件发送: 5次")
    print(f"   - 货币转换/单位转换/运费计算: 10次")

if __name__ == "__main__":
    main()