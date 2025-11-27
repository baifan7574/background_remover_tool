from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

# 查询用户
user_id = '5d887a17-8694-416f-bdbc-111e88c4f2b2'
response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()

print('查询结果:')
if response.data:
    for user in response.data:
        print(f'用户ID: {user.get("user_id")}')
        print(f'邮箱: {user.get("email")}')
        print(f'姓名: {user.get("name")}')
        print(f'计划: {user.get("plan")}')
else:
    print('用户不存在')

# 查询所有用户
print('\n所有用户:')
all_users = supabase.table('user_profiles').select('user_id, email, name').limit(5).execute()
if all_users.data:
    for user in all_users.data:
        print(f'ID: {user.get("user_id")}, 邮箱: {user.get("email")}')