#!/usr/bin/env python3
"""
创建测试用户脚本
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# 加载环境变量
load_dotenv()

# Supabase配置
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("❌ 错误：请设置SUPABASE_URL和SUPABASE_SERVICE_KEY环境变量")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

def create_test_user():
    """创建测试用户"""
    try:
        user_id = "test-user-123"
        email = "test@example.com"
        
        # 检查用户是否已存在
        existing_user = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if existing_user.data:
            print(f"✅ 测试用户已存在: {user_id}")
            return user_id
        
        # 创建新用户
        user_data = {
            "user_id": user_id,
            "email": email,
            "plan": "pro",  # 专业版，避免次数限制
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table('user_profiles').insert(user_data).execute()
        
        if result.data:
            print(f"✅ 成功创建测试用户: {user_id}")
            print(f"📧 邮箱: {email}")
            print(f"🎯 计划: 专业版")
            return user_id
        else:
            print(f"❌ 创建用户失败: {result}")
            return None
            
    except Exception as e:
        print(f"❌ 创建测试用户异常: {e}")
        return None

if __name__ == "__main__":
    user_id = create_test_user()
    if user_id:
        print(f"\n🔑 开发Token: dev-token-{user_id}")
        print("📝 使用方法: 在请求头中添加 Authorization: Bearer dev-token-{user_id}")
    else:
        print("❌ 无法创建测试用户")
        exit(1)