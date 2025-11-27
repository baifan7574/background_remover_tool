# 支付配置文件
# 请根据实际情况修改以下配置

# 支付宝配置
ALIPAY_CONFIG = {
    'app_id': 'your_alipay_app_id',  # 支付宝应用ID
    'app_private_key': '''-----BEGIN RSA PRIVATE KEY-----
your_app_private_key_content
-----END RSA PRIVATE KEY-----''',  # 应用私钥
    'alipay_public_key': '''-----BEGIN PUBLIC KEY-----
your_alipay_public_key_content
-----END PUBLIC KEY-----''',  # 支付宝公钥
    'gateway_url': 'https://openapi.alipay.com/gateway.do',  # 支付宝网关
    'notify_url': 'http://localhost:5000/api/payment/alipay/notify',  # 异步通知地址
    'return_url': 'http://localhost:8000/payment/success.html',  # 同步返回地址
    'sign_type': 'RSA2',  # 签名算法
    'charset': 'utf-8',  # 字符编码
    'version': '1.0'  # API版本
}

# 微信支付配置
WECHAT_PAY_CONFIG = {
    'app_id': 'your_wechat_app_id',  # 微信应用ID
    'mch_id': 'your_merchant_id',  # 商户号
    'api_key': 'your_wechat_api_key',  # API密钥
    'apiclient_cert': '''-----BEGIN CERTIFICATE-----
your_apiclient_cert_content
-----END CERTIFICATE-----''',  # API证书
    'apiclient_key': '''-----BEGIN PRIVATE KEY-----
your_apiclient_key_content
-----END PRIVATE KEY-----''',  # API私钥
    'gateway_url': 'https://api.mch.weixin.qq.com',  # 微信支付网关
    'notify_url': 'http://localhost:5000/api/payment/wechat/notify',  # 异步通知地址
    'trade_type': 'NATIVE'  # 交易类型
}

# 系统配置
SYSTEM_CONFIG = {
    'debug': True,  # 调试模式
    'log_level': 'INFO',  # 日志级别
    'order_timeout': 3600,  # 订单超时时间（秒）
    'refund_timeout': 86400  # 退款超时时间（秒）
}