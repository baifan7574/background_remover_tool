"""
码支付（易支付接口）客户端
支持支付宝、微信支付等多种支付方式
"""

import hashlib
import requests
from urllib.parse import urlencode, quote

class MzfPayClient:
    """码支付客户端"""
    
    def __init__(self, merchant_id, merchant_key):
        """
        初始化码支付客户端
        
        Args:
            merchant_id: 商户ID
            merchant_key: 商户密钥
        """
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        # 易支付接口地址（推荐）
        self.api_url = "https://pay.mzfpay.com/xpay/epay/mapi.php"  # API调用接口
        self.submit_url = "https://pay.mzfpay.com/xpay/epay/submit.php"  # 表单提交接口
    
    def generate_sign(self, params):
        """
        生成签名（MD5）
        
        根据易支付文档，签名规则：
        1. 将所有参数（除sign和sign_type）按照参数名ASCII码从小到大排序
        2. URL类型的参数值不需要URL编码（易支付特殊要求）
        3. 拼接成字符串：key1=value1&key2=value2
        4. 在末尾加上&key=商户密钥
        5. MD5加密，转小写或大写（根据平台要求）
        
        Args:
            params: 参数字典
        
        Returns:
            签名字符串（小写）
        """
        # 排除sign和sign_type，并过滤空值
        filtered_params = {}
        for k, v in params.items():
            if k not in ['sign', 'sign_type'] and v is not None and str(v).strip():
                # 参数值转为字符串，但不进行URL编码（易支付要求原始值参与签名）
                filtered_params[k] = str(v).strip()
        
        # 按参数名ASCII码排序（使用键名排序）
        sorted_params = sorted(filtered_params.items(), key=lambda x: x[0])
        
        # 拼接成字符串：key1=value1&key2=value2
        # 易支付签名规则：参数值不需要URL编码，但需要保持原始值
        sign_parts = []
        for k, v in sorted_params:
            # 确保值是字符串格式
            v_str = str(v).strip()
            sign_parts.append(f"{k}={v_str}")
        
        sign_str = '&'.join(sign_parts)
        
        # 在末尾加上&key=商户密钥
        sign_str += f"&key={self.merchant_key}"
        
        # 打印调试信息
        print(f"🔐 签名原始字符串: {sign_str}")
        
        # MD5加密
        # 易支付可能要求小写或大写，先尝试小写
        sign_lower = hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
        sign_upper = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
        
        print(f"🔐 签名原始字符串: {sign_str}")
        print(f"🔐 MD5(小写): {sign_lower}")
        print(f"🔐 MD5(大写): {sign_upper}")
        
        # 默认返回小写（大多数易支付平台要求小写）
        # 如果小写失败，可以尝试大写
        return sign_lower
    
    def verify_sign(self, params):
        """
        验证签名
        
        Args:
            params: 接收到的参数字典（包含sign字段）
        
        Returns:
            True/False
        """
        if 'sign' not in params:
            return False
        
        received_sign = params.get('sign', '').lower()
        calculated_sign = self.generate_sign(params)
        
        return received_sign == calculated_sign
    
    def create_payment(self, order_no, amount, product_name, payment_type='alipay',
                      notify_url=None, return_url=None, method='api'):
        """
        创建支付订单
        
        Args:
            order_no: 商户订单号（必须唯一）
            amount: 支付金额（元，如 19.00）
            product_name: 商品名称
            payment_type: 支付方式
                - 'alipay': 支付宝
                - 'wxpay': 微信支付
                - 'qqpay': QQ钱包
                - 'bank': 网银支付
            notify_url: 异步通知地址（支付成功后回调）
            return_url: 同步返回地址（支付完成后跳转）
            method: 调用方式
                - 'api': API调用，返回JSON
                - 'submit': 表单提交，返回HTML表单
        
        Returns:
            {
                'success': True/False,
                'pay_url': '支付链接（method=api时）',
                'form_html': '表单HTML（method=submit时）',
                'qr_code': '二维码链接',
                'error': '错误信息'
            }
        """
        # 构建参数
        params = {
            'pid': self.merchant_id,
            'type': payment_type,  # 支付方式
            'out_trade_no': order_no,  # 商户订单号
            'name': product_name,  # 商品名称
            'money': f"{float(amount):.2f}",  # 金额（保留2位小数）
            'sign_type': 'MD5',  # 签名类型
        }
        
        # 添加通知地址（如果提供）
        # 注意：易支付可能要求URL类型的参数不包含查询参数，或需要特殊处理
        if notify_url:
            params['notify_url'] = notify_url
        if return_url:
            # 简化return_url，移除查询参数（在订单号中已经包含了必要信息）
            # 如果return_url包含查询参数，可能会影响签名验证
            # 先尝试使用原始URL，如果失败再简化
            params['return_url'] = return_url
        
        # 生成签名
        params['sign'] = self.generate_sign(params)
        
        try:
            if method == 'api':
                # API调用方式，返回JSON
                print(f"📤 调用码支付API: {self.api_url}")
                print(f"   参数: {params}")
                
                response = requests.post(
                    self.api_url,
                    data=params,
                    timeout=10,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                )
                
                print(f"📥 码支付响应状态码: {response.status_code}")
                print(f"   响应内容: {response.text[:500]}")
                
                # 检查响应状态
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'码支付接口返回错误状态码: {response.status_code}'
                    }
                
                # 尝试解析JSON
                try:
                    result = response.json()
                except ValueError as e:
                    # 如果不是JSON格式，返回原始文本
                    print(f"⚠️ 响应不是JSON格式: {response.text}")
                    return {
                        'success': False,
                        'error': f'码支付接口返回格式错误: {response.text[:200]}'
                    }
                
                print(f"📋 解析后的结果: {result}")
                
                # 码支付返回格式通常是：
                # {"code": 1, "msg": "success", "payurl": "...", "qrcode": "..."}
                # 或 {"code": 0, "msg": "错误信息"}
                
                if result.get('code') == 1 or result.get('status') == 'success':
                    pay_url = result.get('payurl') or result.get('pay_url') or result.get('url', '')
                    qr_code = result.get('qrcode') or result.get('qr_code') or result.get('qrcode_url', '')
                    print(f"✅ 支付链接生成成功: {pay_url[:100] if pay_url else '无'}")
                    return {
                        'success': True,
                        'pay_url': pay_url,
                        'qr_code': qr_code,
                        'order_no': order_no,
                        'trade_no': result.get('trade_no', ''),  # 码支付订单号
                    }
                else:
                    error_msg = result.get('msg') or result.get('message') or result.get('error') or '创建支付订单失败'
                    print(f"❌ 码支付返回错误: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg
                    }
                    
            else:
                # 表单提交方式，返回表单HTML
                # 这里返回参数，前端构建表单
                form_html = f"""
                <form id="mzfpay_form" method="post" action="{self.submit_url}">
                    {''.join([f'<input type="hidden" name="{k}" value="{v}">' for k, v in params.items()])}
                </form>
                <script>document.getElementById('mzfpay_form').submit();</script>
                """
                
                return {
                    'success': True,
                    'form_html': form_html,
                    'submit_url': self.submit_url,
                    'form_data': params,
                    'order_no': order_no
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': '请求超时，请稍后重试'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'网络请求失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'创建支付订单异常: {str(e)}'
            }
    
    def query_order(self, order_no):
        """
        查询订单状态
        
        Args:
            order_no: 商户订单号
        
        Returns:
            {
                'success': True/False,
                'status': '订单状态（paid/unpaid/expired）',
                'trade_no': '码支付订单号',
                'amount': '支付金额',
                'error': '错误信息'
            }
        """
        # 码支付可能没有单独的查询接口，需要通过订单管理页面查询
        # 或者使用异步通知来判断订单状态
        # 这里先返回一个基础结构，后续根据实际情况补充
        
        return {
            'success': False,
            'error': '订单查询功能待实现，建议通过异步通知获取订单状态'
        }



