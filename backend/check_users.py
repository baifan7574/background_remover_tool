import os
from dotenv import load_dotenv
from supabase import create_client

# 加载环境变量
load_dotenv()

# Supabase配置
supabase_url = 'https://jzgwzualserijpsbdrke.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6Z3d6dWFsc2VyaWpwc2JkcmtlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE0MzM3MywiZXhwIjoyMDc4NzE5MzczfQ.-ERsHnuwdGY_6hyJ5mIeeaQtXKhP_dJZ56Bk0X9enN0'

supabase = create_client(supabase_url, supabase_key)

try:
    # 查询用户
    response = supabase.table('user_profiles').select('*').limit(5).execute()
    if response.data:
        print('找到用户:')
        for user in response.data:
            print(f'  用户ID: {user.get("user_id")}')
            print(f'  邮箱: {user.get("email")}')
            print(f'  姓名: {user.get("name")}')
            print('---')
    else:
        print('没有找到用户，创建测试用户...')
        # 创建测试用户
        test_user = {
            'user_id': '00000000-0000-0000-0000-000000000001',
            'email': 'test@example.com',
            'name': '测试用户',
            'plan': 'free',
            'credits': 10
        }
        create_response = supabase.table('user_profiles').insert(test_user).execute()
        print('创建结果:', create_response.data)
        
except Exception as e:
    print('查询失败:', str(e))