#!/usr/bin/env python3
"""
检查payment_records表结构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
import json

def check_table_structure():
    """检查payment_records表结构"""
    try:
        # 从环境变量或配置中获取Supabase配置 - 使用与主应用相同的配置
        supabase_url = "https://jzgwzualserijpsbdrke.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp6Z3d6dWFsc2VyaWpwc2JkcmtlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzE0MzM3MywiZXhwIjoyMDc4NzE5MzczfQ.-ERsHnuwdGY_6hyJ5mIeeaQtXKhP_dJZ56Bk0X9enN0"
        
        # 创建Supabase客户端
        supabase = create_client(supabase_url, supabase_key)
        
        # 尝试查询表结构（通过查询一条记录来了解字段）
        try:
            response = supabase.table('payment_records').select('*').limit(1).execute()
            
            if response.data:
                print("✅ payment_records表存在，包含以下字段:")
                fields = list(response.data[0].keys()) if response.data else []
                for field in fields:
                    print(f"  - {field}")
                
                print(f"\n📊 示例记录:")
                print(json.dumps(response.data[0], indent=2, ensure_ascii=False))
            else:
                print("✅ payment_records表存在但为空")
                
        except Exception as e:
            print(f"❌ 查询payment_records表失败: {str(e)}")
            
            # 尝试查询其他可能的表
            try:
                response = supabase.table('payment_orders').select('*').limit(1).execute()
                if response.data:
                    print("✅ payment_orders表存在，包含以下字段:")
                    fields = list(response.data[0].keys()) if response.data else []
                    for field in fields:
                        print(f"  - {field}")
            except:
                print("❌ payment_orders表也不存在")
                
        # 查询所有表
        try:
            print("\n🔍 查询所有可能的支付相关表...")
            # 这里我们尝试一些常见的表名
            tables_to_check = [
                'payment_records', 'payment_orders', 'orders', 
                'transactions', 'payments', 'user_orders'
            ]
            
            for table in tables_to_check:
                try:
                    response = supabase.table(table).select('*').limit(1).execute()
                    if response.data is not None:
                        print(f"✅ {table} 表存在")
                        if response.data:
                            fields = list(response.data[0].keys())
                            print(f"   字段: {', '.join(fields)}")
                except:
                    print(f"❌ {table} 表不存在或无权限访问")
                    
        except Exception as e:
            print(f"❌ 查询表列表失败: {str(e)}")
            
    except Exception as e:
        print(f"❌ 连接Supabase失败: {str(e)}")

if __name__ == "__main__":
    check_table_structure()