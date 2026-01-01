"""
检查Supabase数据库表结构
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# 加载环境变量
load_dotenv()

# Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print(f"Supabase URL: {SUPABASE_URL}")
print(f"Supabase Key: {SUPABASE_KEY[:20]}...")

try:
    # 创建Supabase客户端
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n=== 检查user_profiles表结构 ===")
    # 尝试查询表结构
    try:
        result = supabase.table('user_profiles').select('*').limit(1).execute()
        print("✓ user_profiles表存在")
        if result.data:
            print(f"  列名: {list(result.data[0].keys())}")
        else:
            print("  表为空，无法获取列信息")
    except Exception as e:
        print(f"✗ user_profiles表错误: {e}")
    
    print("\n=== 检查tool_usage表结构 ===")
    try:
        result = supabase.table('tool_usage').select('*').limit(1).execute()
        print("✓ tool_usage表存在")
        if result.data:
            print(f"  列名: {list(result.data[0].keys())}")
        else:
            print("  表为空，无法获取列信息")
    except Exception as e:
        print(f"✗ tool_usage表错误: {e}")
    
    print("\n=== 检查所有表 ===")
    # 尝试获取所有表信息
    try:
        # 使用PostgREST来获取表信息
        response = supabase.rpc('get_table_info').execute()
        print("表信息:", response.data)
    except Exception as e:
        print(f"无法获取表信息: {e}")
        
    print("\n=== 尝试创建缺失的列 ===")
    # 如果credits列不存在，尝试添加
    try:
        # 使用SQL执行ALTER TABLE（需要管理员权限）
        print("注意：需要Supabase管理员权限来修改表结构")
        print("请在Supabase控制台中执行以下SQL：")
        print("ALTER TABLE user_profiles ADD COLUMN credits INTEGER DEFAULT 10;")
        print("ALTER TABLE user_profiles ADD COLUMN plan TEXT DEFAULT 'free';")
    except Exception as e:
        print(f"无法自动添加列: {e}")

except Exception as e:
    print(f"连接Supabase失败: {e}")