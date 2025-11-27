"""
Supabase集成功能本地测试脚本
测试用户注册、登录、工具使用等功能
"""

import os
import requests
import json
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:5000"

class SupabaseTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.access_token = None
        self.user_id = None
        
    def test_health_check(self):
        """测试健康检查"""
        print("🔍 测试健康检查...")
        try:
            response = requests.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查通过: {data}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_register(self, email, password, name):
        """测试用户注册"""
        print(f"🔍 测试用户注册: {email}")
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "name": name
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 注册成功: {data}")
                self.user_id = data.get('user_id')
                return True
            else:
                print(f"❌ 注册失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 注册异常: {e}")
            return False
    
    def test_login(self, email, password):
        """测试用户登录"""
        print(f"🔍 测试用户登录: {email}")
        try:
            response = requests.post(
                f"{self.base_url}/api/auth/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 登录成功: {data}")
                self.access_token = data.get('access_token')
                self.user_id = data.get('user_id')
                return True
            else:
                print(f"❌ 登录失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def get_auth_headers(self):
        """获取认证头"""
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def test_get_profile(self):
        """测试获取用户资料"""
        print("🔍 测试获取用户资料...")
        try:
            response = requests.get(
                f"{self.base_url}/api/user/profile",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 获取资料成功: {data}")
                return True
            else:
                print(f"❌ 获取资料失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 获取资料异常: {e}")
            return False
    
    def test_currency_converter(self):
        """测试汇率转换工具"""
        print("🔍 测试汇率转换工具...")
        try:
            response = requests.post(
                f"{self.base_url}/api/tools/currency-converter",
                json={
                    "amount": 100,
                    "from_currency": "CNY",
                    "to_currency": "USD"
                },
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 汇率转换成功: {data}")
                return True
            else:
                print(f"❌ 汇率转换失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 汇率转换异常: {e}")
            return False
    
    def test_unit_converter(self):
        """测试单位转换工具"""
        print("🔍 测试单位转换工具...")
        try:
            response = requests.post(
                f"{self.base_url}/api/tools/unit-converter",
                json={
                    "value": 100,
                    "from_unit": "cm",
                    "to_unit": "inch",
                    "conversion_type": "length"
                },
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 单位转换成功: {data}")
                return True
            else:
                print(f"❌ 单位转换失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 单位转换异常: {e}")
            return False
    
    def test_shipping_calculator(self):
        """测试运费计算工具"""
        print("🔍 测试运费计算工具...")
        try:
            response = requests.post(
                f"{self.base_url}/api/tools/shipping-calculator",
                json={
                    "weight": 1.5,
                    "length": 30,
                    "width": 20,
                    "height": 10,
                    "destination": "US",
                    "shipping_type": "standard"
                },
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 运费计算成功: {data}")
                return True
            else:
                print(f"❌ 运费计算失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 运费计算异常: {e}")
            return False
    
    def test_usage_stats(self):
        """测试使用统计"""
        print("🔍 测试使用统计...")
        try:
            response = requests.get(
                f"{self.base_url}/api/tools/usage-stats",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 使用统计成功: {data}")
                return True
            else:
                print(f"❌ 使用统计失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 使用统计异常: {e}")
            return False
    
    def test_background_remover(self, image_path):
        """测试背景移除工具"""
        print(f"🔍 测试背景移除工具: {image_path}")
        try:
            if not os.path.exists(image_path):
                print(f"❌ 测试图片不存在: {image_path}")
                return False
            
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/api/tools/background-remover",
                    files=files,
                    headers=self.get_auth_headers()
                )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 背景移除成功: {data}")
                return True
            else:
                print(f"❌ 背景移除失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 背景移除异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🚀 开始Supabase集成功能测试")
        print("=" * 60)
        
        test_results = []
        
        # 测试健康检查
        test_results.append(("健康检查", self.test_health_check()))
        
        # 测试用户注册
        test_email = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        test_results.append(("用户注册", self.test_register(test_email, "test123456", "测试用户")))
        
        # 测试用户登录
        test_results.append(("用户登录", self.test_login(test_email, "test123456")))
        
        # 测试获取用户资料
        test_results.append(("获取用户资料", self.test_get_profile()))
        
        # 测试工具功能
        test_results.append(("汇率转换", self.test_currency_converter()))
        test_results.append(("单位转换", self.test_unit_converter()))
        test_results.append(("运费计算", self.test_shipping_calculator()))
        
        # 测试使用统计
        test_results.append(("使用统计", self.test_usage_stats()))
        
        # 测试背景移除（如果有测试图片）
        test_image = "test_image.jpg"  # 需要准备测试图片
        if os.path.exists(test_image):
            test_results.append(("背景移除", self.test_background_remover(test_image)))
        else:
            print("⚠️  跳过背景移除测试（没有测试图片）")
        
        # 输出测试结果
        print("\n" + "=" * 60)
        print("📊 测试结果汇总")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:20} {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print(f"\n总计: {len(test_results)} 项测试")
        print(f"通过: {passed} 项")
        print(f"失败: {failed} 项")
        print(f"成功率: {passed/len(test_results)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 所有测试通过！Supabase集成功能正常。")
        else:
            print(f"\n⚠️  有 {failed} 项测试失败，请检查配置和代码。")
        
        return failed == 0

def main():
    """主函数"""
    print("🧪 Supabase集成功能本地测试")
    print("请确保：")
    print("1. 已配置.env文件中的Supabase连接信息")
    print("2. 已启动Flask应用 (python backend/app_supabase.py)")
    print("3. Supabase数据库和存储桶已正确配置")
    print()
    
    input("按回车键开始测试...")
    
    tester = SupabaseTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 测试完成，可以继续部署到PythonAnywhere")
    else:
        print("\n❌ 测试失败，请修复问题后重新测试")
    
    return success

if __name__ == "__main__":
    main()