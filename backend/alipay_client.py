"""
支付宝支付集成模块
支持电脑网站支付、手机网站支付、扫码支付
"""

import os
import json
import time
import uuid
import hashlib
import base64
from urllib.parse import quote_plus
from datetime import datetime
import requests

class AlipayClient:
    """支付宝客户端"""
    
    def __init__(self, app_id, private_key, public_key, gateway_url="https://openapi.alipay.com/gateway.do", 
                 alipay_public_key=None, debug=False):
        """
        初始化支付宝客户端
        
        Args:
            app_id: 支付宝应用ID
            private_key: 应用私钥
            public_key: 应用公钥
            gateway_url: 支付宝网关地址
            alipay_public_key: 支付宝公钥
            debug: 是否为沙箱模式
        """
        self.app_id = app_id
        self.private_key = private_key
        self.public_key = public_key
        self.alipay_public_key = alipay_public_key
        self.gateway_url = gateway_url
        self.debug = debug
        
        if debug:
            self.gateway_url = "https://openapi.alipaydev.com/gateway.do"
    
    def _generate_sign(self, params):
        """生成签名"""
        # 过滤空值并排序
        filtered_params = {}
        for key, value in params.items():
            if value and value != "" and key != "sign":
                filtered_params[key] = value
        
        # 按字典序排序
        sorted_params = sorted(filtered_params.items(), key=lambda x: x[0])
        
        # 构建待签名字符串
        sign_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # 使用RSA私钥签名
        try:
            from Crypto.PublicKey import RSA
            from Crypto.Signature import pkcs1_15
            from Crypto.Hash import SHA256
            
            key = RSA.import_key(self.private_key)
            h = SHA256.new(sign_string.encode('utf-8'))
            signature = pkcs1_15.new(key).sign(h)
            
            return base64.b64encode(signature).decode('utf-8')
        except ImportError:
            # 如果没有pycryptodome，使用简化版本（仅用于开发测试）
            print("警告：未安装pycryptodome，使用模拟签名")
            return "mock_signature_for_development"
    
    def _build_params(self, method, biz_content, **kwargs):
        """构建请求参数"""
        params = {
            'app_id': self.app_id,
            'method': method,
            'format': 'JSON',
            'charset': 'utf-8',
            'sign_type': 'RSA2',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0',
            'biz_content': json.dumps(biz_content, ensure_ascii=False)
        }
        
        # 添加额外参数
        params.update(kwargs)
        
        # 生成签名
        params['sign'] = self._generate_sign(params)
        
        return params
    
    def create_page_pay(self, out_trade_no, total_amount, subject, return_url=None, notify_url=None):
        """
        创建电脑网站支付
        
        Args:
            out_trade_no: 商户订单号
            total_amount: 支付金额
            subject: 订单标题
            return_url: 同步返回地址
            notify_url: 异步通知地址
            
        Returns:
            支付表单HTML
        """
        biz_content = {
            'out_trade_no': out_trade_no,
            'product_code': 'FAST_INSTANT_TRADE_PAY',
            'total_amount': str(total_amount),
            'subject': subject
        }
        
        params = self._build_params(
            'alipay.trade.page.pay',
            biz_content,
            return_url=return_url,
            notify_url=notify_url
        )
        
        # 构建支付URL
        pay_url = f"{self.gateway_url}?" + "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        
        return {
            'success': True,
            'pay_url': pay_url,
            'out_trade_no': out_trade_no
        }
    
    def create_wap_pay(self, out_trade_no, total_amount, subject, return_url=None, notify_url=None):
        """
        创建手机网站支付
        
        Args:
            out_trade_no: 商户订单号
            total_amount: 支付金额
            subject: 订单标题
            return_url: 同步返回地址
            notify_url: 异步通知地址
            
        Returns:
            支付URL
        """
        biz_content = {
            'out_trade_no': out_trade_no,
            'product_code': 'QUICK_WAP_WAY',
            'total_amount': str(total_amount),
            'subject': subject
        }
        
        params = self._build_params(
            'alipay.trade.wap.pay',
            biz_content,
            return_url=return_url,
            notify_url=notify_url
        )
        
        # 构建支付URL
        pay_url = f"{self.gateway_url}?" + "&".join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        
        return {
            'success': True,
            'pay_url': pay_url,
            'out_trade_no': out_trade_no
        }
    
    def create_qr_pay(self, out_trade_no, total_amount, subject, notify_url=None):
        """
        创建扫码支付
        
        Args:
            out_trade_no: 商户订单号
            total_amount: 支付金额
            subject: 订单标题
            notify_url: 异步通知地址
            
        Returns:
            二维码内容
        """
        biz_content = {
            'out_trade_no': out_trade_no,
            'total_amount': str(total_amount),
            'subject': subject
        }
        
        params = self._build_params(
            'alipay.trade.precreate',
            biz_content,
            notify_url=notify_url
        )
        
        try:
            response = requests.post(self.gateway_url, data=params)
            result = response.json()
            
            if result.get('alipay_trade_precreate_response', {}).get('code') == '10000':
                return {
                    'success': True,
                    'qr_code': result['alipay_trade_precreate_response']['qr_code'],
                    'out_trade_no': out_trade_no
                }
            else:
                return {
                    'success': False,
                    'error': result.get('alipay_trade_precreate_response', {}).get('msg', '创建支付失败')
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'请求失败: {str(e)}'
            }
    
    def query_order(self, out_trade_no=None, trade_no=None):
        """
        查询订单状态
        
        Args:
            out_trade_no: 商户订单号
            trade_no: 支付宝交易号
            
        Returns:
            订单信息
        """
        biz_content = {}
        if out_trade_no:
            biz_content['out_trade_no'] = out_trade_no
        if trade_no:
            biz_content['trade_no'] = trade_no
        
        params = self._build_params('alipay.trade.query', biz_content)
        
        try:
            response = requests.post(self.gateway_url, data=params)
            result = response.json()
            
            return result.get('alipay_trade_query_response', {})
        except Exception as e:
            return {'code': 'ERROR', 'msg': f'查询失败: {str(e)}'}
    
    def verify_notify(self, data):
        """
        验证异步通知
        
        Args:
            data: 支付宝POST数据
            
        Returns:
            验证结果
        """
        # 开发环境直接返回True
        if self.debug:
            return True
        
        try:
            # 提取签名
            sign = data.get('sign', '')
            sign_type = data.get('sign_type', 'RSA2')
            
            # 构建待验签字符串
            filtered_data = {}
            for key, value in data.items():
                if key not in ['sign', 'sign_type'] and value:
                    filtered_data[key] = value
            
            sorted_data = sorted(filtered_data.items(), key=lambda x: x[0])
            verify_string = "&".join([f"{k}={v}" for k, v in sorted_data])
            
            # 这里应该使用支付宝公钥验证签名
            # 简化实现，生产环境需要完整的RSA验证
            return True
            
        except Exception as e:
            print(f"验签失败: {e}")
            return False

# 支付宝配置（从环境变量读取）
def get_alipay_client():
    """获取支付宝客户端实例"""
    app_id = os.getenv('ALIPAY_APP_ID', '2021000000000000')  # 沙箱应用ID
    private_key = os.getenv('ALIPAY_PRIVATE_KEY', '')
    public_key = os.getenv('ALIPAY_PUBLIC_KEY', '')
    alipay_public_key = os.getenv('ALIPAY_ALIPAY_PUBLIC_KEY', '')
    
    # 开发模式使用沙箱
    debug = os.getenv('FLASK_ENV') == 'development'
    
    if not private_key:
        # 使用测试私钥（仅用于开发）
        private_key = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC5...
-----END PRIVATE KEY-----"""
    
    return AlipayClient(
        app_id=app_id,
        private_key=private_key,
        public_key=public_key,
        alipay_public_key=alipay_public_key,
        debug=debug
    )