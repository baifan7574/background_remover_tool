import requests
import json

def test_user_display_fix():
    """测试用户显示修复效果"""
    base_url = "http://localhost:5000"
    
    print("=== 测试用户显示修复效果 ===")
    
    # 使用已存在的测试用户
    test_email = "test1763348878@test.com"
    test_password = "test123456"
    
    print(f"\n1. 使用已存在用户登录: {test_email}")
    
    try:
        # 登录
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
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
                
                print(f"\n=== API返回的完整数据 ===")
                print(json.dumps(profile_data, indent=2, ensure_ascii=False))
                
                # 检查前端期望的数据结构
                if 'user' in profile_data and 'usage_stats' in profile_data:
                    user_info = profile_data['user']
                    usage_stats = profile_data['usage_stats']
                    
                    print(f"\n=== 前端显示需要的数据 ===")
                    print(f"用户计划: {user_info.get('plan')}")
                    print(f"每日限制: {user_info.get('daily_limit')}")
                    print(f"使用统计: {usage_stats}")
                    
                    # 模拟前端显示逻辑
                    daily_limit = usage_stats.get('daily_limit', 0)
                    today_usage = usage_stats.get('today_usage', 0)
                    
                    if daily_limit > 0:
                        display_text = f"今日已用 {today_usage}/{daily_limit}"
                        print(f"\n✅ 前端应该显示: {display_text}")
                    else:
                        display_text = "无限制"
                        print(f"\n❌ 前端会显示: {display_text}")
                        
                    print(f"\n=== 修复验证结果 ===")
                    if daily_limit == 3 and today_usage >= 0:
                        print("✅ 修复成功：免费用户每日3次限制正确显示")
                    else:
                        print(f"❌ 仍有问题：限制={daily_limit}, 已用={today_usage}")
                        
                else:
                    print("❌ 数据结构不正确")
                    
            else:
                print(f"获取用户信息失败: {profile_response.text}")
        else:
            print(f"登录失败: {login_response.text}")
            
    except Exception as e:
        print(f"请求异常: {e}")

if __name__ == "__main__":
    test_user_display_fix()