"""
独立测试版Flask应用 - 不依赖Supabase
用于测试基本的API结构和功能
"""

import os
import json
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import io
import base64

app = Flask(__name__, 
    static_folder='../static',
    template_folder='../templates')

# CORS配置 - 支持移动端访问
CORS(app, 
     resources={r"/api/*": {
         "origins": "*",  # 允许所有来源（包括移动端）
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True
     }},
     supports_credentials=True)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'test-secret-key'

# 模拟用户数据存储
users_db = {}
user_profiles_db = {}
tool_usage_db = {}

# 工具积分消耗配置
TOOL_CREDITS = {
    'background_remover': 2,
    'currency_converter': 1,
    'unit_converter': 1,
    'shipping_calculator': 1
}

def allowed_file(filename):
    """检查文件类型是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_from_token():
    """从请求头获取用户信息（模拟）"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    # 模拟token验证
    for user_id, user_data in users_db.items():
        if user_data.get('token') == token:
            return {'id': user_id, 'email': user_data['email']}
    return None

def check_user_credits(user_id, tool_name):
    """检查用户积分是否足够"""
    if user_id not in user_profiles_db:
        return False, 0, TOOL_CREDITS.get(tool_name, 1)
    
    credits = user_profiles_db[user_id].get('credits', 0)
    required_credits = TOOL_CREDITS.get(tool_name, 1)
    return credits >= required_credits, credits, required_credits

def deduct_user_credits(user_id, tool_name):
    """扣除用户积分"""
    if user_id not in user_profiles_db:
        return False, "用户不存在"
    
    required_credits = TOOL_CREDITS.get(tool_name, 1)
    current_credits = user_profiles_db[user_id].get('credits', 0)
    new_credits = current_credits - required_credits
    
    if new_credits < 0:
        return False, "积分不足"
    
    user_profiles_db[user_id]['credits'] = new_credits
    user_profiles_db[user_id]['updated_at'] = datetime.now().isoformat()
    
    return True, f"成功扣除{required_credits}积分，剩余{new_credits}积分"

def record_tool_usage(user_id, tool_name, input_data, output_data, credits_used):
    """记录工具使用情况"""
    if user_id not in tool_usage_db:
        tool_usage_db[user_id] = []
    
    usage_record = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'tool_name': tool_name,
        'credits_used': credits_used,
        'input_data': input_data,
        'output_data': output_data,
        'created_at': datetime.now().isoformat()
    }
    
    tool_usage_db[user_id].append(usage_record)
    return True

# ==================== API路由 ====================

@app.route('/')
def index():
    """主页"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>跨境工具API服务</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { background: #e8f5e8; padding: 20px; border-radius: 8px; }
            .api-list { margin-top: 20px; }
            .api-item { background: #f5f5f5; margin: 10px 0; padding: 10px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌍 跨境工具API服务</h1>
            <div class="status">
                <h2>✅ 服务状态</h2>
                <p>服务正在运行...</p>
                <p><a href="/health">健康检查</a></p>
            </div>
            <div class="api-list">
                <h3>📚 可用API</h3>
                <div class="api-item">
                    <strong>用户认证:</strong> POST /api/auth/register, /api/auth/login
                </div>
                <div class="api-item">
                    <strong>汇率转换:</strong> POST /api/tools/currency-converter
                </div>
                <div class="api-item">
                    <strong>单位转换:</strong> POST /api/tools/unit-converter
                </div>
                <div class="api-item">
                    <strong>运费计算:</strong> POST /api/tools/shipping-calculator
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'mock',
        'version': '2.1.0-test'
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        # 检查用户是否已存在
        for user_data in users_db.values():
            if user_data['email'] == email:
                return jsonify({'error': '用户已存在'}), 400
        
        # 创建用户
        user_id = str(uuid.uuid4())
        token = f"mock_token_{user_id[:8]}"
        
        users_db[user_id] = {
            'email': email,
            'password': password,  # 实际应用中应该加密
            'token': token
        }
        
        # 创建用户资料
        user_profiles_db[user_id] = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'plan': 'free',
            'credits': 10,  # 新用户赠送10积分
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'message': '注册成功',
            'user_id': user_id,
            'email': email
        })
            
    except Exception as e:
        return jsonify({'error': f'注册异常: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        # 验证用户
        user_id = None
        for uid, user_data in users_db.items():
            if user_data['email'] == email and user_data['password'] == password:
                user_id = uid
                break
        
        if not user_id:
            return jsonify({'error': '邮箱或密码错误'}), 401
        
        # 生成新token
        token = f"mock_token_{user_id[:8]}"
        users_db[user_id]['token'] = token
        
        profile = user_profiles_db[user_id]
        
        return jsonify({
            'message': '登录成功',
            'user': {
                'id': user_id,
                'email': profile['email'],
                'name': profile['name'],
                'plan': profile['plan'],
                'credits': profile['credits']
            },
            'token': token
        })
            
    except Exception as e:
        return jsonify({'error': f'登录异常: {str(e)}'}), 500

@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    """获取用户资料"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        if user_id not in user_profiles_db:
            return jsonify({'error': '用户资料不存在'}), 404
        
        profile = user_profiles_db[user_id]
        
        # 获取使用统计（如果存在）
        usage_stats = {}
        if user_id in tool_usage_db:
            usage_records = tool_usage_db[user_id]
            total_usage = len(usage_records)
            total_credits = sum(item.get('credits_used', 0) for item in usage_records)
            
            # 按工具类型统计
            tool_stats = {}
            for item in usage_records:
                tool_name = item.get('tool_name', 'unknown')
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {'count': 0, 'credits': 0}
                tool_stats[tool_name]['count'] += 1
                tool_stats[tool_name]['credits'] += item.get('credits_used', 0)
            
            usage_stats = {
                'total_usage': total_usage,
                'total_credits_used': total_credits,
                'tool_stats': tool_stats
            }
        
        return jsonify({
            'user': {
                'id': user_id,
                'email': profile['email'],
                'name': profile['name'],
                'plan': profile['plan'],
                'credits': profile['credits'],
                'created_at': profile['created_at'],
                'updated_at': profile['updated_at']
            },
            'usage_stats': usage_stats  # 添加使用统计，前端需要这个字段
        })
            
    except Exception as e:
        return jsonify({'error': f'获取资料异常: {str(e)}'}), 500

@app.route('/api/tools/currency-converter', methods=['POST'])
def currency_converter():
    """汇率转换工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查积分
        has_credits, current_credits, required_credits = check_user_credits(user_id, 'currency_converter')
        if not has_credits:
            return jsonify({'error': f'积分不足，需要{required_credits}积分，当前{current_credits}积分'}), 400
        
        data = request.get_json()
        amount = data.get('amount', 0)
        from_currency = data.get('from_currency', 'USD')
        to_currency = data.get('to_currency', 'CNY')
        
        # 模拟汇率转换
        exchange_rate = 7.2 if from_currency == 'USD' and to_currency == 'CNY' else 1.0
        result = amount * exchange_rate
        
        # 扣除积分
        success, message = deduct_user_credits(user_id, 'currency_converter')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user_id, 
            'currency_converter',
            {'amount': amount, 'from_currency': from_currency, 'to_currency': to_currency},
            {'result': result, 'exchange_rate': exchange_rate},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'result': round(result, 2),
            'exchange_rate': exchange_rate,
            'credits_used': required_credits,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': f'汇率转换异常: {str(e)}'}), 500

@app.route('/api/tools/unit-converter', methods=['POST'])
def unit_converter():
    """单位转换工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查积分
        has_credits, current_credits, required_credits = check_user_credits(user_id, 'unit_converter')
        if not has_credits:
            return jsonify({'error': f'积分不足，需要{required_credits}积分，当前{current_credits}积分'}), 400
        
        data = request.get_json()
        value = data.get('value', 0)
        from_unit = data.get('from_unit', 'kg')
        to_unit = data.get('to_unit', 'lb')
        
        # 模拟单位转换
        conversion_rate = 2.20462 if from_unit == 'kg' and to_unit == 'lb' else 1.0
        result = value * conversion_rate
        
        # 扣除积分
        success, message = deduct_user_credits(user_id, 'unit_converter')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user_id,
            'unit_converter',
            {'value': value, 'from_unit': from_unit, 'to_unit': to_unit},
            {'result': result, 'conversion_rate': conversion_rate},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'result': round(result, 4),
            'conversion_rate': conversion_rate,
            'credits_used': required_credits,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': f'单位转换异常: {str(e)}'}), 500

@app.route('/api/tools/shipping-calculator', methods=['POST'])
def shipping_calculator():
    """国际运费计算工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查积分
        has_credits, current_credits, required_credits = check_user_credits(user_id, 'shipping_calculator')
        if not has_credits:
            return jsonify({'error': f'积分不足，需要{required_credits}积分，当前{current_credits}积分'}), 400
        
        data = request.get_json()
        weight = data.get('weight', 0)  # kg
        from_country = data.get('from_country', 'CN')
        to_country = data.get('to_country', 'US')
        
        # 模拟运费计算
        base_rate = 50 if from_country == 'CN' and to_country == 'US' else 30
        shipping_cost = base_rate + (weight * 10)
        
        # 扣除积分
        success, message = deduct_user_credits(user_id, 'shipping_calculator')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user_id,
            'shipping_calculator',
            {'weight': weight, 'from_country': from_country, 'to_country': to_country},
            {'shipping_cost': shipping_cost, 'base_rate': base_rate},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'shipping_cost': round(shipping_cost, 2),
            'base_rate': base_rate,
            'credits_used': required_credits,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'error': f'运费计算异常: {str(e)}'}), 500

@app.route('/api/tools/usage-stats', methods=['GET'])
def usage_stats():
    """获取工具使用统计"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        if user_id not in tool_usage_db:
            return jsonify({
                'total_usage': 0,
                'total_credits_used': 0,
                'tool_breakdown': {}
            })
        
        usage_records = tool_usage_db[user_id]
        total_usage = len(usage_records)
        total_credits = sum(item.get('credits_used', 0) for item in usage_records)
        
        # 按工具类型统计
        tool_stats = {}
        for item in usage_records:
            tool_name = item.get('tool_name', 'unknown')
            if tool_name not in tool_stats:
                tool_stats[tool_name] = {'count': 0, 'credits': 0}
            tool_stats[tool_name]['count'] += 1
            tool_stats[tool_name]['credits'] += item.get('credits_used', 0)
        
        return jsonify({
            'total_usage': total_usage,
            'total_credits_used': total_credits,
            'tool_breakdown': tool_stats
        })
            
    except Exception as e:
        return jsonify({'error': f'获取统计异常: {str(e)}'}), 500

@app.route('/api/tools/remove-background', methods=['POST'])
def remove_background():
    """背景移除工具 - 简化版"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查积分
        has_credits, current_credits, required_credits = check_user_credits(user_id, 'background_remover')
        if not has_credits:
            return jsonify({'error': f'积分不足，需要{required_credits}积分，当前{current_credits}积分'}), 400
        
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 扣除积分
        success, message = deduct_user_credits(user_id, 'background_remover')
        if not success:
            return jsonify({'error': message}), 400
        
        # 模拟背景移除处理
        filename = secure_filename(file.filename)
        output_filename = f"processed_{uuid.uuid4().hex[:8]}_{filename}"
        
        # 记录使用
        record_tool_usage(
            user_id,
            'background_remover',
            {'filename': filename},
            {'output_filename': output_filename, 'processed': True},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'message': '背景移除完成（测试版）',
            'output_filename': output_filename,
            'credits_used': required_credits,
            'download_url': f'/api/download/{output_filename}'
        })
        
    except Exception as e:
        return jsonify({'error': f'背景移除异常: {str(e)}'}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载处理后的文件"""
    return jsonify({'message': f'下载文件 {filename}（测试版）'})

# ==================== 错误处理 ====================

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '文件太大，最大支持16MB'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'API端点不存在'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': '服务器内部错误'}), 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    print("🚀 启动独立测试版应用...")
    print("📊 数据库: 模拟内存数据库")
    print("🔧 背景移除功能：测试版")
    print("🌐 访问地址: http://localhost:5000")
    print("📈 健康检查: http://localhost:5000/health")
    print("🧪 测试命令: python test_supabase_simple.py")
    
    app.run(debug=True, host='0.0.0.0', port=5000)