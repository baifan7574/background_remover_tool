import requests
import json

def test_all_functionality():
    """全面测试所有功能"""
    print("=== 全面功能测试开始 ===\n")
    
    # 1. 登录获取token
    try:
        login_data = {
            'email': 'testuser789@example.com',
            'password': '123456'
        }
        
        login_response = requests.post('http://localhost:5000/api/auth/login', json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()['token']
            print('✅ 登录成功')
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # 2. 测试单位转换工具
            print("\n2. 测试单位转换工具...")
            unit_data = {
                'value': 10,
                'from_unit': 'kg',
                'to_unit': 'lb'
            }
            
            unit_response = requests.post('http://localhost:5000/api/tools/unit-converter', json=unit_data, headers=headers)
            if unit_response.status_code == 200:
                result = unit_response.json()
                print(f"✅ 单位转换成功: 10kg = {result['result']}lb")
            else:
                print(f"❌ 单位转换失败: {unit_response.text}")
            
            # 3. 测试货币转换工具
            print("\n3. 测试货币转换工具...")
            currency_data = {
                'amount': 100,
                'from_currency': 'USD',
                'to_currency': 'CNY'
            }
            
            currency_response = requests.post('http://localhost:5000/api/tools/currency-converter', json=currency_data, headers=headers)
            if currency_response.status_code == 200:
                result = currency_response.json()
                print(f"✅ 货币转换成功: $100 = ¥{result['result']}")
            else:
                print(f"❌ 货币转换失败: {currency_response.text}")
                
            # 4. 测试运费计算工具
            print("\n4. 测试运费计算工具...")
            shipping_data = {
                'weight': 5,
                'from_country': 'CN',
                'to_country': 'US'
            }
            
            shipping_response = requests.post('http://localhost:5000/api/tools/shipping-calculator', json=shipping_data, headers=headers)
            if shipping_response.status_code == 200:
                result = shipping_response.json()
                print(f"✅ 运费计算成功: 5kg CN→US = ${result['shipping_cost']}")
            else:
                print(f"❌ 运费计算失败: {shipping_response.text}")
                
            # 5. 测试邮件发送工具
            print("\n5. 测试邮件发送工具...")
            email_data = {
                'to': 'test@example.com',
                'subject': '功能测试邮件',
                'body': '这是一封用于测试邮件功能的邮件。'
            }
            
            email_response = requests.post('http://localhost:5000/api/tools/send-email', json=email_data, headers=headers)
            if email_response.status_code == 200:
                result = email_response.json()
                print(f"✅ 邮件发送成功: 发送到 {result['to_email']}")
            else:
                print(f"❌ 邮件发送失败: {email_response.text}")
                
            # 6. 查看使用记录
            print("\n6. 查看使用记录...")
            usage_response = requests.get('http://localhost:5000/api/user/usage', headers=headers)
            if usage_response.status_code == 200:
                usage = usage_response.json()
                print(f"✅ 总使用记录数: {usage['total_records']}")
                for i, record in enumerate(usage['usage_records'][:5], 1):
                    print(f"   {i}. {record['tool_name']} - {record['created_at']}")
            else:
                print(f"❌ 获取使用记录失败: {usage_response.text}")
                
            # 7. 测试健康检查
            print("\n7. 测试健康检查...")
            health_response = requests.get('http://localhost:5000/health')
            if health_response.status_code == 200:
                result = health_response.json()
                print(f"✅ 健康检查成功: {result['status']}")
            else:
                print(f"❌ 健康检查失败: {health_response.text}")
                
            print("\n=== 全面功能测试完成 ===")
            
        else:
            print(f"❌ 登录失败: {login_response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    test_all_functionality()