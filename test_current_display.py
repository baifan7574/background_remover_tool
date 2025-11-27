import requests
import json

def test_current_user_flow():
    """测试当前用户流程，检查限制显示"""
    base_url = "http://localhost:5000"
    
    print("=== 测试当前用户限制显示 ===")
    
    # 测试注册新用户
    test_email = f"test{int(__import__('time').time())}@test.com"
    test_password = "test123456"
    
    print(f"\n1. 测试注册新用户: {test_email}")
    
    # 注册
    register_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=register_data)
        print(f"注册状态码: {response.status_code}")
        if response.status_code == 200:
            print("注册成功")
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            # 登录
            login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
            print(f"登录状态码: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                token = login_result.get('token')
                print(f"登录成功，获得token: {token[:20]}...")
                
                # 获取用户信息
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = requests.get(f"{base_url}/api/auth/profile", headers=headers)
                print(f"获取用户信息状态码: {profile_response.status_code}")
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    print(f"\n=== 完整用户信息响应 ===")
                    print(json.dumps(profile_data, indent=2, ensure_ascii=False))
                    
                    # 检查用户信息结构
                    if 'user' in profile_data:
                        user_info = profile_data['user']
                        print(f"\n=== 用户基本信息 ===")
                        print(f"邮箱: {user_info.get('email')}")
                        print(f"计划: {user_info.get('plan')}")
                        print(f"每日限制: {user_info.get('daily_limit')}")
                        print(f"今日使用: {user_info.get('usage_today')}")
                        print(f"剩余次数: {user_info.get('remaining_uses')}")
                    
                    if 'usage_stats' in profile_data:
                        usage_info = profile_data['usage_stats']
                        print(f"\n=== 使用统计信息 ===")
                        print(json.dumps(usage_info, indent=2, ensure_ascii=False))
                    
                    # 检查是否显示"无限制"
                    user_plan = user_info.get('plan') if 'user' in profile_data else None
                    daily_limit = user_info.get('daily_limit') if 'user' in profile_data else None
                    
                    print(f"\n=== 关键检查结果 ===")
                    print(f"用户计划: {user_plan}")
                    print(f"每日限制: {daily_limit}")
                    
                    if user_plan == 'free' and daily_limit == 3:
                        print("✅ 限制显示正确：免费用户每日3次")
                    elif user_plan == 'free' and daily_limit is None:
                        print("❌ 问题：免费用户但限制为None（可能显示无限制）")
                    else:
                        print(f"⚠️  意外情况：计划={user_plan}, 限制={daily_limit}")
                        
                else:
                    print(f"获取用户信息失败: {profile_response.text}")
            else:
                print(f"登录失败: {login_response.text}")
        else:
            print(f"注册失败: {response.text}")
            
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    test_current_user_flow()