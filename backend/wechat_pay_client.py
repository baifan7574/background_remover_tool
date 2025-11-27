"""
微信支付集成模块
支持JSAPI支付、Native支付、H5支付
"""

import json
import os
import time
import uuid
import hashlib
import random
import string
import requests
from datetime import datetime
import xml.etree.ElementTree as ET

class WeChatPayClient:
    """微信支付客户端"""
    
    def __init__(self, app_id, mch_id, api_key, notify_url=None, debug=False):
        """
        初始化微信支付客户端
        
        Args:
            app_id: 微信公众号/小程序AppID
            mch_id: 商户号
            api_key: API密钥
            notify_url: 支付结果通知地址
            debug: 是否为沙箱模式
        """
        self.app_id = app_id
        self.mch_id = mch_id
        self.api_key = api_key
        self.notify_url = notify_url
        self.debug = debug
        
        # API地址
        if debug:
            self.unified_order_url = "https://api.mch.weixin.qq.com/sandboxnew/pay/unifiedorder"
            self.order_query_url = "https://api.mch.weixin.qq.com/sandboxnew/pay/orderquery"
        else:
            self.unified_order_url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
            self.order_query_url = "https://api.mch.weixin.qq.com/pay/orderquery"
    
    def _generate_nonce_str(self):
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    def _generate_sign(self, params):
        """生成签名"""
        # 过滤空值并排序
        filtered_params = {}
        for key, value in params.items():
            if value and value != "":
                filtered_params[key] = str(value)
        
        # 按字典序排序
        sorted_params = sorted(filtered_params.items())
        
        # 构建待签名字符串
        sign_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        sign_string += f"&key={self.api_key}"
        
        # MD5加密
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()
    
    def _dict_to_xml(self, data):
        """字典转XML"""
        xml = ["<xml>"]
        for key, value in data.items():
            xml.append(f"<{key}>{value}</{key}>")
        xml.append("</xml>")
        return "".join(xml)
    
    def _xml_to_dict(self, xml_str):
        """XML转字典"""
        try:
            root = ET.fromstring(xml_str)
            result = {}
            for child in root:
                result[child.tag] = child.text
            return result
        except ET.ParseError:
            return {}
    
    def create_jsapi_pay(self, out_trade_no, total_fee, body, openid, trade_type="JSAPI"):
        """
        创建JSAPI支付（公众号/小程序支付）
        
        Args:
            out_trade_no: 商户订单号
            total_fee: 支付金额（分）
            body: 商品描述
            openid: 用户openid
            trade_type: 交易类型
            
        Returns:
            支付参数
        """
        params = {
            'appid': self.app_id,
            'mch_id': self.mch_id,
            'nonce_str': self._generate_nonce_str(),
            'body': body,
            'out_trade_no': out_trade_no,
            'total_fee': int(total_fee),
            'spbill_create_ip': '127.0.0.1',
            'notify_url': self.notify_url,
            'trade_type': trade_type,
            'openid': openid
        }
        
        params['sign'] = self._generate_sign(params)
        
        try:
            response = requests.post(
                self.unified_order_url,
                data=self._dict_to_xml(params),
                headers={'Content-Type': 'application/xml'}
            )
            
            result = self._xml_to_dict(response.text)
            
            if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
                # 生成JSAPI支付参数
                pay_params = {
                    'appId': self.app_id,
                    'timeStamp': str(int(time.time())),
                    'nonceStr': self._generate_nonce_str(),
                    'package': f"prepay_id={result.get('prepay_id')}",
                    'signType': 'MD5'
                }
                
                pay_params['paySign'] = self._generate_sign(pay_params)
                
                return {
                    'success': True,
                    'pay_params': pay_params,
                    'prepay_id': result.get('prepay_id'),
                    'out_trade_no': out_trade_no
                }
            else:
                return {
                    'success': False,
                    'error': result.get('return_msg', result.get('err_code_des', '创建支付失败'))
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'请求失败: {str(e)}'
            }
    
    def create_native_pay(self, out_trade_no, total_fee, body, product_id=""):
        """
        创建Native支付（扫码支付）
        
        Args:
            out_trade_no: 商户订单号
            total_fee: 支付金额（分）
            body: 商品描述
            product_id: 商品ID
            
        Returns:
            二维码内容
        """
        params = {
            'appid': self.app_id,
            'mch_id': self.mch_id,
            'nonce_str': self._generate_nonce_str(),
            'body': body,
            'out_trade_no': out_trade_no,
            'total_fee': int(total_fee),
            'spbill_create_ip': '127.0.0.1',
            'notify_url': self.notify_url,
            'trade_type': 'NATIVE',
            'product_id': product_id
        }
        
        params['sign'] = self._generate_sign(params)
        
        try:
            response = requests.post(
                self.unified_order_url,
                data=self._dict_to_xml(params),
                headers={'Content-Type': 'application/xml'}
            )
            
            result = self._xml_to_dict(response.text)
            
            if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
                return {
                    'success': True,
                    'code_url': result.get('code_url'),
                    'prepay_id': result.get('prepay_id'),
                    'out_trade_no': out_trade_no
                }
            else:
                return {
                    'success': False,
                    'error': result.get('return_msg', result.get('err_code_des', '创建支付失败'))
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'请求失败: {str(e)}'
            }
    
    def create_h5_pay(self, out_trade_no, total_fee, body, scene_info):
        """
        创建H5支付（手机浏览器支付）
        
        Args:
            out_trade_no: 商户订单号
            total_fee: 支付金额（分）
            body: 商品描述
            scene_info: 场景信息
            
        Returns:
            支付URL
        """
        params = {
            'appid': self.app_id,
            'mch_id': self.mch_id,
            'nonce_str': self._generate_nonce_str(),
            'body': body,
            'out_trade_no': out_trade_no,
            'total_fee': int(total_fee),
            'spbill_create_ip': '127.0.0.1',
            'notify_url': self.notify_url,
            'trade_type': 'MWEB',
            'scene_info': json.dumps(scene_info, ensure_ascii=False)
        }
        
        params['sign'] = self._generate_sign(params)
        
        try:
            response = requests.post(
                self.unified_order_url,
                data=self._dict_to_xml(params),
                headers={'Content-Type': 'application/xml'}
            )
            
            result = self._xml_to_dict(response.text)
            
            if result.get('return_code') == 'SUCCESS' and result.get('result_code') == 'SUCCESS':
                return {
                    'success': True,
                    'mweb_url': result.get('mweb_url'),
                    'prepay_id': result.get('prepay_id'),
                    'out_trade_no': out_trade_no
                }
            else:
                return {
                    'success': False,
                    'error': result.get('return_msg', result.get('err_code_des', '创建支付失败'))
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'请求失败: {str(e)}'
            }
    
    def query_order(self, out_trade_no=None, transaction_id=None):
        """
        查询订单状态
        
        Args:
            out_trade_no: 商户订单号
            transaction_id: 微信订单号
            
        Returns:
            订单信息
        """
        params = {
            'appid': self.app_id,
            'mch_id': self.mch_id,
            'nonce_str': self._generate_nonce_str(),
        }
        
        if out_trade_no:
            params['out_trade_no'] = out_trade_no
        if transaction_id:
            params['transaction_id'] = transaction_id
        
        params['sign'] = self._generate_sign(params)
        
        try:
            response = requests.post(
                self.order_query_url,
                data=self._dict_to_xml(params),
                headers={'Content-Type': 'application/xml'}
            )
            
            result = self._xml_to_dict(response.text)
            return result
            
        except Exception as e:
            return {'return_code': 'FAIL', 'return_msg': f'查询失败: {str(e)}'}
    
    def verify_notify(self, xml_data):
        """
        验证支付结果通知
        
        Args:
            xml_data: 微信支付POST的XML数据
            
        Returns:
            验证结果和订单信息
        """
        try:
            data = self._xml_to_dict(xml_data)
            
            if data.get('return_code') != 'SUCCESS':
                return False, data
            
            # 验证签名
            sign = data.pop('sign', None)
            if not sign:
                return False, data
            
            calculated_sign = self._generate_sign(data)
            
            if sign != calculated_sign:
                return False, data
            
            return True, data
            
        except Exception as e:
            return False, {'error': f'验证失败: {str(e)}'}

# 微信支付配置（从环境变量读取）
def get_wechat_client():
    """获取微信支付客户端实例"""
    app_id = os.getenv('WECHAT_APP_ID', 'wx1234567890abcdef')  # 测试AppID
    mch_id = os.getenv('WECHAT_MCH_ID', '1234567890')  # 测试商户号
    api_key = os.getenv('WECHAT_API_KEY', 'your_api_key_here')
    notify_url = os.getenv('WECHAT_NOTIFY_URL', 'http://localhost:5000/api/payment/wechat/notify')
    
    # 开发模式
    debug = os.getenv('FLASK_ENV') == 'development'
    
    if not api_key:
        # 使用测试密钥（仅用于开发）
        api_key = 'test_api_key_for_development_only'
    
    return WeChatPayClient(
        app_id=app_id,
        mch_id=mch_id,
        api_key=api_key,
        notify_url=notify_url,
        debug=debug
    )