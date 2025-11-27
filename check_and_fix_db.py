"""
检查并修复Supabase数据库表结构
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# 加载环境变量
load_dotenv()

# Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print("=== 检查user_profiles表结构 ===")

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 尝试查询表结构
    result = supabase.table('user_profiles').select('*').limit(1).execute()
    
    if result.data:
        print("✓ 表中现有数据:", result.data)
        print("✓ 现有列名:", list(result.data[0].keys()) if result.data else "表为空")
    else:
        print("表为空，无法获取列信息")
        
    print("\n=== 需要添加的列 ===")
    print("请在Supabase SQL编辑器中执行以下命令（只执行缺失的列）：")
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS user_id UUID;")
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS name TEXT;")
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 10;")
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free';")
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();")
    print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();")

except Exception as e:
    print(f"检查失败: {e}")