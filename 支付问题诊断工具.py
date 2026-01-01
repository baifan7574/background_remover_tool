"""
支付问题诊断工具
用于诊断码支付配置和接口调用问题
"""

import requests
import hashlib
import json
from datetime import datetime

class PaymentDiagnostic:
    """支付诊断工具"""
    
    def __init__(self, merchant_id, merchant_key):
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.api_url = "https://pay.mzfpay.com/xpay/epay/mapi.php"
    
    def generate_sign(self, params):
        """生成签名（与mzfpay_client.py保持一致）"""
        filtered_params = {}
        for k, v in params.items():
            if k not in ['sign', 'sign_type'] and v is not None and str(v).strip():
                filtered_params[k] = str(v).strip()
        
        sorted_params = sorted(filtered_params.items(), key=lambda x: x[0])
        sign_parts = []
        for k, v in sorted_params:
            sign_parts.append(f"{k}={v}")
        
        sign_str = '&'.join(sign_parts)
        sign_str += f"&key={self.merchant_key}"
        
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
    
    def test_connection(self):
        """测试1: 检查网络连接"""
        print("\n" + "="*60)
        print("🔍 测试1: 检查网络连接")
        print("="*60)
        
        try:
            response = requests.get(self.api_url, timeout=5)
            print(f"✅ 网络连接正常")
            print(f"   状态码: {response.status_code}")
            return True
        except requests.exceptions.Timeout:
            print(f"❌ 连接超时 - 码支付服务器可能无法访问")
            return False
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接失败 - 请检查网络或码支付服务器地址")
            return False
        except Exception as e:
            print(f"❌ 连接异常: {str(e)}")
            return False
    
    def test_merchant_config(self):
        """测试2: 检查商户配置"""
        print("\n" + "="*60)
        print("🔍 测试2: 检查商户配置")
        print("="*60)
        
        if not self.merchant_id:
            print("❌ 商户ID为空")
            return False
        
        if not self.merchant_key:
            print("❌ 商户密钥为空")
            return False
        
        print(f"✅ 商户ID: {self.merchant_id}")
        print(f"✅ 商户密钥: {self.merchant_key[:10]}...{self.merchant_key[-10:]}")
        
        # 检查格式
        if len(self.merchant_id) < 3:
            print("⚠️ 商户ID长度异常，可能不正确")
            return False
        
        if len(self.merchant_key) < 10:
            print("⚠️ 商户密钥长度异常，可能不正确")
            return False
        
        return True
    
    def test_sign_generation(self):
        """测试3: 测试签名生成"""
        print("\n" + "="*60)
        print("🔍 测试3: 测试签名生成")
        print("="*60)
        
        # 测试参数
        test_params = {
            'pid': self.merchant_id,
            'type': 'alipay',
            'out_trade_no': 'TEST' + datetime.now().strftime('%Y%m%d%H%M%S'),
            'name': '测试商品',
            'money': '0.01',
            'sign_type': 'MD5'
        }
        
        print("测试参数:")
        for k, v in test_params.items():
            print(f"   {k}: {v}")
        
        sign = self.generate_sign(test_params)
        print(f"\n✅ 生成的签名: {sign}")
        print(f"   签名长度: {len(sign)} (应该是32位)")
        
        if len(sign) != 32:
            print("⚠️ 签名长度异常，应该是32位MD5值")
            return False
        
        return True
    
    def test_create_order(self):
        """测试4: 测试创建支付订单"""
        print("\n" + "="*60)
        print("🔍 测试4: 测试创建支付订单")
        print("="*60)
        
        # 构建测试订单
        order_no = 'TEST' + datetime.now().strftime('%Y%m%d%H%M%S')
        params = {
            'pid': self.merchant_id,
            'type': 'alipay',
            'out_trade_no': order_no,
            'name': '诊断测试订单',
            'money': '0.01',
            'sign_type': 'MD5',
            'notify_url': 'https://example.com/notify',
            'return_url': 'https://example.com/return'
        }
        
        params['sign'] = self.generate_sign(params)
        
        print("发送的参数:")
        for k, v in params.items():
            if k == 'sign':
                print(f"   {k}: {v[:20]}...")
            else:
                print(f"   {k}: {v}")
        
        try:
            print(f"\n📤 发送请求到: {self.api_url}")
            response = requests.post(
                self.api_url,
                data=params,
                timeout=10,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            print(f"📥 响应状态码: {response.status_code}")
            print(f"📥 响应内容: {response.text[:500]}")
            
            if response.status_code != 200:
                print(f"❌ HTTP状态码错误: {response.status_code}")
                return False
            
            # 尝试解析JSON
            try:
                result = response.json()
                print(f"\n📋 解析后的JSON:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if result.get('code') == 1:
                    print("\n✅ 订单创建成功！")
                    print(f"   支付链接: {result.get('payurl', '无')}")
                    return True
                else:
                    error_msg = result.get('msg', '未知错误')
                    print(f"\n❌ 订单创建失败: {error_msg}")
                    
                    # 常见错误分析
                    if '签名' in error_msg or 'sign' in error_msg.lower():
                        print("\n💡 可能原因: 签名验证失败")
                        print("   1. 检查商户密钥是否正确")
                        print("   2. 检查签名生成算法是否正确")
                        print("   3. 检查参数是否完整")
                    elif '商户' in error_msg or 'pid' in error_msg.lower():
                        print("\n💡 可能原因: 商户ID错误或未激活")
                        print("   1. 检查商户ID是否正确")
                        print("   2. 登录码支付平台确认商户状态")
                    elif '金额' in error_msg or 'money' in error_msg.lower():
                        print("\n💡 可能原因: 金额格式错误")
                        print("   1. 金额必须是数字，保留2位小数")
                        print("   2. 金额不能为0或负数")
                    
                    return False
                    
            except ValueError:
                print(f"\n❌ 响应不是JSON格式")
                print(f"   原始响应: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"\n❌ 请求超时")
            return False
        except Exception as e:
            print(f"\n❌ 请求异常: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🚀 开始支付问题诊断")
        print("="*60)
        
        results = []
        
        # 测试1: 网络连接
        results.append(("网络连接", self.test_connection()))
        
        # 测试2: 商户配置
        results.append(("商户配置", self.test_merchant_config()))
        
        # 测试3: 签名生成
        results.append(("签名生成", self.test_sign_generation()))
        
        # 测试4: 创建订单（需要网络和配置都正常）
        if results[0][1] and results[1][1]:
            results.append(("创建订单", self.test_create_order()))
        else:
            print("\n⚠️ 跳过订单创建测试（前置条件不满足）")
            results.append(("创建订单", False))
        
        # 汇总结果
        print("\n" + "="*60)
        print("📊 诊断结果汇总")
        print("="*60)
        
        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{name}: {status}")
        
        all_passed = all(r[1] for r in results)
        
        if all_passed:
            print("\n✅ 所有测试通过！支付配置正常。")
        else:
            print("\n❌ 部分测试失败，请根据上述提示检查配置。")
            print("\n💡 建议:")
            print("   1. 检查商户ID和密钥是否正确")
            print("   2. 登录码支付平台确认商户状态")
            print("   3. 检查网络连接")
            print("   4. 如果问题持续，考虑更换支付平台")
        
        return all_passed


def main():
    """主函数"""
    print("="*60)
    print("💳 支付问题诊断工具")
    print("="*60)
    
    # 从代码中读取配置（与sk_app.py保持一致）
    MERCHANT_ID = '10294'
    MERCHANT_KEY = 'X0cJyf2G0EjDKtQe9NMf'
    
    print(f"\n当前配置:")
    print(f"  商户ID: {MERCHANT_ID}")
    print(f"  商户密钥: {MERCHANT_KEY[:10]}...{MERCHANT_KEY[-10:]}")
    
    # 创建诊断工具
    diagnostic = PaymentDiagnostic(MERCHANT_ID, MERCHANT_KEY)
    
    # 运行诊断
    diagnostic.run_all_tests()


if __name__ == '__main__':
    main()

