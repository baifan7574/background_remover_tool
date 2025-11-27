import requests
import json

# 测试邮件功能
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
        
        # 测试发送邮件
        email_data = {
            'to': 'test@example.com',
            'subject': '测试邮件',
            'body': '这是一封测试邮件，用于验证邮件功能是否正常工作。'
        }
        
        email_response = requests.post('http://localhost:5000/api/tools/send-email', json=email_data, headers=headers)
        print(f'邮件发送状态码: {email_response.status_code}')
        
        if email_response.status_code == 200:
            result = email_response.json()
            print(f'邮件发送结果: {result}')
        else:
            print(f'邮件发送失败: {email_response.text}')
        
    else:
        print(f'登录失败: {login_response.text}')
        
except Exception as e:
    print(f'测试异常: {e}')