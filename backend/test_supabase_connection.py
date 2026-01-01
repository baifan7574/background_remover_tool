#!/usr/bin/env python3
"""
测试Supabase连接
"""

import os
from dotenv import load_dotenv
from supabase import create_client

def test_supabase_connection():
    """测试Supabase连接"""
    print("=== 测试Supabase连接 ===")
    
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取配置
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        print(f"Supabase URL: {supabase_url}")
        print(f"Supabase Key: {supabase_key[:20]}..." if supabase_key else "None")
        
        if not supabase_url or not supabase_key:
            print("❌ 缺少Supabase配置")
            return False
            
        # 创建客户端
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase客户端创建成功")
        
        # 测试连接 - 查询用户表
        print("1. 测试查询user_profiles表...")
        try:
            response = supabase.table('user_profiles').select('id, user_id, plan').limit(5).execute()
            print(f"✅ 查询成功，返回 {len(response.data)} 条记录")
            for user in response.data:
                print(f"   ID: {user['id']}, User_ID: {user['user_id']}, Plan: {user.get('plan', 'None')}")
        except Exception as e:
            print(f"❌ 查询user_profiles表失败: {str(e)}")
            return False
        
        # 测试查询特定用户
        test_user_id = "5d887a17-8694-416f-bdbc-111e88c4f2b2"
        print(f"2. 测试查询特定用户 {test_user_id}...")
        try:
            response = supabase.table('user_profiles').select('id').eq('user_id', test_user_id).execute()
            if response.data:
                print(f"✅ 找到用户，数据库ID: {response.data[0]['id']}")
            else:
                print(f"❌ 用户不存在")
                return False
        except Exception as e:
            print(f"❌ 查询特定用户失败: {str(e)}")
            return False
        
        # 测试查询payment_records表
        print("3. 测试查询payment_records表...")
        try:
            response = supabase.table('payment_records').select('*').limit(1).execute()
            print(f"✅ 查询成功，返回 {len(response.data)} 条记录")
            if response.data:
                print(f"   示例记录: {response.data[0]}")
        except Exception as e:
            print(f"❌ 查询payment_records表失败: {str(e)}")
        
        print("✅ Supabase连接测试完成")
        return True
        
    except Exception as e:
        print(f"❌ Supabase连接测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    exit(0 if success else 1)