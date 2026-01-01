#!/usr/bin/env python3
"""
检查数据库结构和现有用户
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 从项目根目录加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from supabase import create_client

def check_database_structure():
    """检查数据库结构和现有用户"""
    print("=== 检查数据库结构和现有用户 ===")
    
    # 初始化Supabase客户端
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ 缺少Supabase配置")
        return
    
    try:
        # 使用服务角色客户端
        service_client = create_client(supabase_url, supabase_key)
        
        print("1. 检查user_profiles表结构...")
        try:
            # 尝试获取表结构信息
            response = service_client.table('user_profiles').select('*').limit(1).execute()
            if response.data:
                user = response.data[0]
                print("✅ user_profiles表字段:")
                for key, value in user.items():
                    print(f"  - {key}: {type(value).__name__} = {value}")
            else:
                print("❌ user_profiles表为空")
        except Exception as e:
            print(f"❌ 检查user_profiles表失败: {str(e)}")
        
        print("\n2. 检查现有用户...")
        try:
            response = service_client.table('user_profiles').select('*').limit(2).execute()
            if response.data:
                print("✅ 现有用户完整字段:")
                for user in response.data:
                    print(f"  用户 {user.get('email')}:")
                    for key, value in user.items():
                        if 'membership' in key.lower() or key in ['plan', 'expires_at', 'start_at']:
                            print(f"    - {key}: {value}")
                    break  # 只显示第一个用户的详细信息
            else:
                print("❌ 没有找到用户")
        except Exception as e:
            print(f"❌ 检查现有用户失败: {str(e)}")
        
        print("\n3. 检查payment_records表结构...")
        try:
            response = service_client.table('payment_records').select('*').limit(1).execute()
            if response.data:
                record = response.data[0]
                print("✅ payment_records表字段:")
                for key, value in record.items():
                    print(f"  - {key}: {type(value).__name__} = {value}")
            else:
                print("❌ payment_records表为空")
        except Exception as e:
            print(f"❌ 检查payment_records表失败: {str(e)}")
            
    except Exception as e:
        print(f"❌ 检查异常: {str(e)}")

if __name__ == "__main__":
    check_database_structure()