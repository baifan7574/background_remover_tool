from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

print(f'连接到: {supabase_url}')
supabase = create_client(supabase_url, supabase_key)

# 检查用户表是否有数据
try:
    response = supabase.table('user_profiles').select('*').execute()
    print(f'用户表记录数: {len(response.data) if response.data else 0}')
    if response.data:
        for user in response.data[-3:]:  # 显示最近3个用户
            email = user.get('email', 'N/A')
            credits = user.get('credits', 0)
            created_at = user.get('created_at', 'N/A')
            print(f'用户: {email} - 积分: {credits} - 创建时间: {created_at}')
    
    # 检查工具使用记录
    usage_response = supabase.table('tool_usage').select('*').execute()
    print(f'工具使用记录数: {len(usage_response.data) if usage_response.data else 0}')
    
    print('✅ 数据库连接正常，数据写入成功')
    
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')