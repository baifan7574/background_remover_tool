#!/usr/bin/env python3
"""
用户数据查询工具
查看用户注册、支付、使用情况等数据
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
# import pandas as pd  # 注释掉pandas依赖

# 加载环境变量
load_dotenv()

# 连接Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # 使用服务密钥有更高权限

if not supabase_url or not supabase_key:
    print("❌ 错误：请检查.env文件中的SUPABASE_URL和SUPABASE_SERVICE_KEY")
    sys.exit(1)

supabase = create_client(supabase_url, supabase_key)

def get_all_users():
    """获取所有用户信息"""
    print("\n👥 === 所有注册用户 ===")
    try:
        response = supabase.table('user_profiles').select('*').order('created_at', desc=True).execute()
        
        if response.data:
            users = response.data
            print(f"总共注册用户数: {len(users)}")
            print("-" * 100)
            
            for i, user in enumerate(users, 1):
                created_time = user.get('created_at', 'N/A')
                if created_time != 'N/A':
                    created_time = created_time.replace('T', ' ').split('.')[0]
                
                print(f"{i:2d}. {user.get('name', 'N/A')} ({user.get('email', 'N/A')})")
                print(f"    用户ID: {user.get('user_id', 'N/A')}")
                print(f"    套餐: {user.get('plan', 'N/A')} | 积分: {user.get('credits', 0)}")
                print(f"    注册时间: {created_time}")
                print(f"    邀请者: {user.get('invited_by', '无')}")
                print("-" * 100)
                
        else:
            print("暂无注册用户")
            
    except Exception as e:
        print(f"❌ 查询用户失败: {e}")

def get_payment_records():
    """获取所有支付记录"""
    print("\n💰 === 所有支付记录 ===")
    try:
        response = supabase.table('payment_records').select('*').order('created_at', desc=True).execute()
        
        if response.data:
            payments = response.data
            total_amount = sum(p.get('amount', 0) for p in payments)
            print(f"总支付笔数: {len(payments)} | 总金额: ¥{total_amount:.2f}")
            print("-" * 100)
            
            for i, payment in enumerate(payments, 1):
                created_time = payment.get('created_at', 'N/A')
                if created_time != 'N/A':
                    created_time = created_time.replace('T', ' ').split('.')[0]
                
                print(f"{i:2d}. 支付ID: {payment.get('id', 'N/A')}")
                print(f"    用户ID: {payment.get('user_id', 'N/A')}")
                print(f"    金额: ¥{payment.get('amount', 0):.2f}")
                print(f"    支付方式: {payment.get('payment_method', 'N/A')}")
                print(f"    状态: {payment.get('status', 'N/A')}")
                print(f"    支付时间: {created_time}")
                print("-" * 100)
                
        else:
            print("暂无支付记录")
            
    except Exception as e:
        print(f"❌ 查询支付记录失败: {e}")

def get_user_statistics():
    """获取用户统计信息"""
    print("\n📊 === 用户统计信息 ===")
    try:
        # 用户套餐分布
        plan_response = supabase.table('user_profiles').select('plan').execute()
        if plan_response.data:
            plans = {}
            for user in plan_response.data:
                plan = user.get('plan', 'unknown')
                plans[plan] = plans.get(plan, 0) + 1
            
            print("套餐分布:")
            for plan, count in plans.items():
                print(f"  {plan}: {count}人")
        
        # 积分统计
        credits_response = supabase.table('user_profiles').select('credits').execute()
        if credits_response.data:
            credits_list = [user.get('credits', 0) for user in credits_response.data]
            total_credits = sum(credits_list)
            avg_credits = total_credits / len(credits_list) if credits_list else 0
            
            print(f"\n积分统计:")
            print(f"  总积分: {total_credits}")
            print(f"  平均积分: {avg_credits:.1f}")
            print(f"  最高积分: {max(credits_list) if credits_list else 0}")
            print(f"  最低积分: {min(credits_list) if credits_list else 0}")
        
        # 今日注册
        today = datetime.now().strftime('%Y-%m-%d')
        today_response = supabase.table('user_profiles').select('*').gte('created_at', today).execute()
        today_count = len(today_response.data) if today_response.data else 0
        
        print(f"\n今日注册: {today_count}人")
        
    except Exception as e:
        print(f"❌ 统计信息查询失败: {e}")

def get_tool_usage():
    """获取工具使用情况"""
    print("\n🛠️ === 工具使用统计 ===")
    try:
        response = supabase.table('tool_usage').select('*').order('created_at', desc=True).limit(20).execute()
        
        if response.data:
            usages = response.data
            print(f"最近20次使用记录:")
            print("-" * 100)
            
            for i, usage in enumerate(usages, 1):
                created_time = usage.get('created_at', 'N/A')
                if created_time != 'N/A':
                    created_time = created_time.replace('T', ' ').split('.')[0]
                
                print(f"{i:2d}. 用户: {usage.get('user_id', 'N/A')[:8]}...")
                print(f"    工具: {usage.get('tool_name', 'N/A')}")
                print(f"    消耗积分: {usage.get('credits_used', 0)}")
                print(f"    使用时间: {created_time}")
                print("-" * 100)
                
        else:
            print("暂无工具使用记录")
            
    except Exception as e:
        print(f"❌ 查询工具使用失败: {e}")

def search_user_by_email(email):
    """根据邮箱搜索用户"""
    print(f"\n🔍 === 搜索用户: {email} ===")
    try:
        response = supabase.table('user_profiles').select('*').eq('email', email).execute()
        
        if response.data and len(response.data) > 0:
            user = response.data[0]
            created_time = user.get('created_at', 'N/A')
            if created_time != 'N/A':
                created_time = created_time.replace('T', ' ').split('.')[0]
            
            print(f"✅ 找到用户:")
            print(f"  姓名: {user.get('name', 'N/A')}")
            print(f"  邮箱: {user.get('email', 'N/A')}")
            print(f"  用户ID: {user.get('user_id', 'N/A')}")
            print(f"  套餐: {user.get('plan', 'N/A')}")
            print(f"  积分: {user.get('credits', 0)}")
            print(f"  注册时间: {created_time}")
            print(f"  邀请者: {user.get('invited_by', '无')}")
            
            # 查询该用户的支付记录
            payment_response = supabase.table('payment_records').select('*').eq('user_id', user.get('user_id')).execute()
            if payment_response.data:
                print(f"\n💰 该用户的支付记录:")
                for payment in payment_response.data:
                    pay_time = payment.get('created_at', 'N/A')
                    if pay_time != 'N/A':
                        pay_time = pay_time.replace('T', ' ').split('.')[0]
                    print(f"  ¥{payment.get('amount', 0):.2f} - {payment.get('payment_method', 'N/A')} - {pay_time}")
            else:
                print("\n💰 该用户暂无支付记录")
                
        else:
            print(f"❌ 未找到邮箱为 {email} 的用户")
            
    except Exception as e:
        print(f"❌ 搜索用户失败: {e}")

def main():
    """主菜单"""
    print("🔍 跨境电商工具集 - 用户数据查询")
    print("=" * 50)
    
    while True:
        print("\n请选择查询功能:")
        print("1. 查看所有注册用户")
        print("2. 查看所有支付记录")
        print("3. 查看用户统计信息")
        print("4. 查看工具使用情况")
        print("5. 根据邮箱搜索用户")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-5): ").strip()
        
        if choice == '1':
            get_all_users()
        elif choice == '2':
            get_payment_records()
        elif choice == '3':
            get_user_statistics()
        elif choice == '4':
            get_tool_usage()
        elif choice == '5':
            email = input("请输入要搜索的邮箱: ").strip()
            if email:
                search_user_by_email(email)
        elif choice == '0':
            print("👋 再见!")
            break
        else:
            print("❌ 无效选项，请重新选择")

if __name__ == "__main__":
    main()