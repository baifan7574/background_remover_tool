import requests
import json

# 测试货币转换工具
try:
    # 获取token
    login_data = {
        'email': 'testuser789@example.com',
        'password': '123456'
    }
    
    login_response = requests.post('http://localhost:5000/api/auth/login', json=login_data)
    if login_response.status_code == 200:
        token = login_response.json()['token']
        print('登录成功，获取到token')
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试货币转换
        currency_data = {
            'amount': 100,
            'from_currency': 'USD',
            'to_currency': 'CNY'
        }
        
        currency_response = requests.post('http://localhost:5000/api/tools/currency-converter', json=currency_data, headers=headers)
        print(f'货币转换状态码: {currency_response.status_code}')
        if currency_response.status_code == 200:
            result = currency_response.json()
            print(f'货币转换结果: {result}')
        else:
            print(f'货币转换失败: {currency_response.text}')
            
        # 测试运费计算
        shipping_data = {
            'weight': 5,
            'from_country': 'CN',
            'to_country': 'US'
        }
        
        shipping_response = requests.post('http://localhost:5000/api/tools/shipping-calculator', json=shipping_data, headers=headers)
        print(f'运费计算状态码: {shipping_response.status_code}')
        if shipping_response.status_code == 200:
            result = shipping_response.json()
            print(f'运费计算结果: {result}')
        else:
            print(f'运费计算失败: {shipping_response.text}')
            
        # 查看最终使用记录
        usage_response = requests.get('http://localhost:5000/api/user/usage', headers=headers)
        if usage_response.status_code == 200:
            usage = usage_response.json()
            print(f'总使用记录数: {usage["total_records"]}')
            for record in usage['usage_records']:
                print(f'- {record["tool_name"]}: {record["created_at"]}')
        
    else:
        print(f'登录失败: {login_response.text}')
        
except Exception as e:
    print(f'测试异常: {e}')