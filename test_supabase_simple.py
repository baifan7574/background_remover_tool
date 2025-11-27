"""
Supabase集成测试脚本 - 简化版
用于测试基本的API功能，不需要真实的Supabase连接
"""

import requests
import json
import time
from datetime import datetime

class SupabaseIntegrationTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.auth_token = None
        self.test_user = {
            'email': f'test_{int(time.time())}@example.com',
            'password': 'test123456',
            'name': '测试用户'
        }
    
    def test_health_check(self):
        """测试健康检查"""
        print("🔍 测试健康检查...")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查成功: {data.get('status')}")
                print(f"   版本: {data.get('version')}")
                print(f"   时间: {data.get('timestamp')}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_user_registration(self):
        """测试用户注册"""
        print("\n🔍 测试用户注册...")
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=self.test_user
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 用户注册成功: {data.get('message')}")
                print(f"   用户ID: {data.get('user_id')}")
                print(f"   邮箱: {data.get('email')}")
                return True
            else:
                print(f"❌ 用户注册失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 用户注册异常: {e}")
            return False
    
    def test_user_login(self):
        """测试用户登录"""
        print("\n🔍 测试用户登录...")
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={
                    'email': self.test_user['email'],
                    'password': self.test_user['password']
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 用户登录成功: {data.get('message')}")
                user_info = data.get('user', {})
                print(f"   用户ID: {user_info.get('id')}")
                print(f"   邮箱: {user_info.get('email')}")
                print(f"   积分: {user_info.get('credits')}")
                print(f"   套餐: {user_info.get('plan')}")
                
                self.auth_token = data.get('token')
                return True
            else:
                print(f"❌ 用户登录失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 用户登录异常: {e}")
            return False
    
    def test_get_profile(self):
        """测试获取用户资料"""
        print("\n🔍 测试获取用户资料...")
        if not self.auth_token:
            print("❌ 没有认证令牌，跳过测试")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = requests.get(
                f"{self.base_url}/api/auth/profile",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                user_info = data.get('user', {})
                print(f"✅ 获取用户资料成功")
                print(f"   用户ID: {user_info.get('id')}")
                print(f"   邮箱: {user_info.get('email')}")
                print(f"   姓名: {user_info.get('name')}")
                print(f"   积分: {user_info.get('credits')}")
                print(f"   套餐: {user_info.get('plan')}")
                return True
            else:
                print(f"❌ 获取用户资料失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 获取用户资料异常: {e}")
            return False
    
    def test_currency_converter(self):
        """测试汇率转换工具"""
        print("\n🔍 测试汇率转换工具...")
        if not self.auth_token:
            print("❌ 没有认证令牌，跳过测试")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = requests.post(
                f"{self.base_url}/api/tools/currency-converter",
                headers=headers,
                json={
                    'amount': 100,
                    'from_currency': 'USD',
                    'to_currency': 'CNY'
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 汇率转换成功")
                print(f"   转换结果: {data.get('result')}")
                print(f"   汇率: {data.get('exchange_rate')}")
                print(f"   积分消耗: {data.get('credits_used')}")
                print(f"   消息: {data.get('message')}")
                return True
            else:
                print(f"❌ 汇率转换失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 汇率转换异常: {e}")
            return False
    
    def test_unit_converter(self):
        """测试单位转换工具"""
        print("\n🔍 测试单位转换工具...")
        if not self.auth_token:
            print("❌ 没有认证令牌，跳过测试")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = requests.post(
                f"{self.base_url}/api/tools/unit-converter",
                headers=headers,
                json={
                    'value': 10,
                    'from_unit': 'kg',
                    'to_unit': 'lb'
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 单位转换成功")
                print(f"   转换结果: {data.get('result')}")
                print(f"   转换率: {data.get('conversion_rate')}")
                print(f"   积分消耗: {data.get('credits_used')}")
                print(f"   消息: {data.get('message')}")
                return True
            else:
                print(f"❌ 单位转换失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 单位转换异常: {e}")
            return False
    
    def test_shipping_calculator(self):
        """测试运费计算工具"""
        print("\n🔍 测试运费计算工具...")
        if not self.auth_token:
            print("❌ 没有认证令牌，跳过测试")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = requests.post(
                f"{self.base_url}/api/tools/shipping-calculator",
                headers=headers,
                json={
                    'weight': 2.5,
                    'from_country': 'CN',
                    'to_country': 'US'
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 运费计算成功")
                print(f"   运费: {data.get('shipping_cost')}")
                print(f"   基础费率: {data.get('base_rate')}")
                print(f"   积分消耗: {data.get('credits_used')}")
                print(f"   消息: {data.get('message')}")
                return True
            else:
                print(f"❌ 运费计算失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 运费计算异常: {e}")
            return False
    
    def test_usage_stats(self):
        """测试使用统计"""
        print("\n🔍 测试使用统计...")
        if not self.auth_token:
            print("❌ 没有认证令牌，跳过测试")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_token}'}
            response = requests.get(
                f"{self.base_url}/api/tools/usage-stats",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 获取使用统计成功")
                print(f"   总使用次数: {data.get('total_usage')}")
                print(f"   总积分消耗: {data.get('total_credits_used')}")
                print(f"   工具使用明细: {data.get('tool_breakdown')}")
                return True
            else:
                print(f"❌ 获取使用统计失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 获取使用统计异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Supabase集成功能测试")
        print("=" * 50)
        
        tests = [
            ("健康检查", self.test_health_check),
            ("用户注册", self.test_user_registration),
            ("用户登录", self.test_user_login),
            ("获取用户资料", self.test_get_profile),
            ("汇率转换", self.test_currency_converter),
            ("单位转换", self.test_unit_converter),
            ("运费计算", self.test_shipping_calculator),
            ("使用统计", self.test_usage_stats)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                results.append((test_name, False))
            
            time.sleep(0.5)  # 避免请求过快
        
        # 输出测试结果汇总
        print("\n" + "=" * 50)
        print("📊 测试结果汇总")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<20} {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n总计: {len(results)} 项测试")
        print(f"通过: {passed} 项")
        print(f"失败: {failed} 项")
        print(f"成功率: {passed/len(results)*100:.1f}%")
        
        if failed > 0:
            print(f"\n⚠️  有 {failed} 项测试失败，请检查配置和代码。")
        else:
            print(f"\n🎉 所有测试通过！Supabase集成功能正常。")
        
        return passed == len(results)

def main():
    """主函数"""
    print("🧪 Supabase集成功能测试工具")
    print("请确保Flask应用已启动：python backend/app_supabase_simple.py")
    print()
    
    # 等待用户确认
    input("按回车键开始测试...")
    
    # 运行测试
    tester = SupabaseIntegrationTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 测试完成，所有功能正常！")
        exit(0)
    else:
        print("\n❌ 测试失败，请修复问题后重新测试。")
        exit(1)

if __name__ == "__main__":
    main()