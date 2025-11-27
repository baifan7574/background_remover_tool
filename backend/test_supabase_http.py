#!/usr/bin/env python3
"""
测试Supabase HTTP连接
"""

import requests
import os
from dotenv import load_dotenv

def test_supabase_http():
    """测试Supabase HTTP连接"""
    print("=== 测试Supabase HTTP连接 ===")
    
    try:
        # 加载环境变量
        load_dotenv()
        
        # 获取配置
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        print(f"Supabase URL: {supabase_url}")
        
        if not supabase_url or not supabase_key:
            print("❌ 缺少Supabase配置")
            return False
            
        # 测试基本连接
        print("1. 测试基本HTTP连接...")
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        try:
            response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=10)
            print(f"响应状态码: {response.status_code}")
            if response.status_code == 200:
                print("✅ 基本连接成功")
            else:
                print(f"❌ 基本连接失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 基本连接异常: {str(e)}")
            return False
        
        # 测试查询user_profiles表
        print("2. 测试查询user_profiles表...")
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{supabase_url}/rest/v1/user_profiles?select=id,user_id,plan&limit=5",
                headers=headers,
                timeout=30
            )
            print(f"响应状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 查询成功，返回 {len(data)} 条记录")
                for user in data:
                    print(f"   ID: {user['id']}, User_ID: {user['user_id']}, Plan: {user.get('plan', 'None')}")
            else:
                print(f"❌ 查询失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 查询异常: {str(e)}")
            return False
        
        print("✅ Supabase HTTP连接测试完成")
        return True
        
    except Exception as e:
        print(f"❌ Supabase HTTP连接测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_supabase_http()
    exit(0 if success else 1)