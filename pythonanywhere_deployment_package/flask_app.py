"""
PythonAnywhere适配版Flask应用 - 不依赖Supabase
适配默认路径结构：/home/用户名/mysite/
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
    static_folder='static',
    template_folder='templates')
CORS(app)

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
    return render_template('index.html')

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'mock',
        'version': '2.1.0-pythonanywhere'
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

@app.route('/api/user/profile', methods=['GET'])
def get_user_profile():
    """获取用户资料"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        if user_id not in user_profiles_db:
            return jsonify({'error': '用户不存在'}), 404
        
        profile = user_profiles_db[user_id]
        
        # 获取使用统计
        usage_count = 0
        if user_id in tool_usage_db:
            usage_count = len(tool_usage_db[user_id])
        
        return jsonify({
            'user': {
                'id': user_id,
                'email': profile['email'],
                'name': profile['name'],
                'plan': profile['plan'],
                'credits': profile['credits'],
                'usage_count': usage_count,
                'created_at': profile['created_at']
            }
        })
            
    except Exception as e:
        return jsonify({'error': f'获取资料异常: {str(e)}'}), 500

@app.route('/api/tools/currency-converter', methods=['POST'])
def currency_converter():
    """汇率转换"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        can_use, current_credits, required_credits = check_user_credits(user_id, 'currency_converter')
        
        if not can_use:
            return jsonify({
                'error': '积分不足',
                'current_credits': current_credits,
                'required_credits': required_credits
            }), 400
        
        data = request.get_json()
        amount = data.get('amount')
        from_currency = data.get('from_currency')
        to_currency = data.get('to_currency')
        
        if not amount or not from_currency or not to_currency:
            return jsonify({'error': '参数不完整'}), 400
        
        # 模拟汇率转换（实际应用中应该调用真实汇率API）
        exchange_rates = {
            'USD': 1.0,
            'CNY': 7.2,
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.0
        }
        
        if from_currency not in exchange_rates or to_currency not in exchange_rates:
            return jsonify({'error': '不支持的货币'}), 400
        
        # 转换计算
        usd_amount = amount / exchange_rates[from_currency]
        result = usd_amount * exchange_rates[to_currency]
        
        # 扣除积分
        success, message = deduct_user_credits(user_id, 'currency_converter')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user_id, 'currency_converter',
            {'amount': amount, 'from': from_currency, 'to': to_currency},
            {'result': result},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'result': round(result, 2),
            'from_currency': from_currency,
            'to_currency': to_currency,
            'original_amount': amount,
            'credits_used': required_credits,
            'remaining_credits': user_profiles_db[user_id]['credits']
        })
        
    except Exception as e:
        return jsonify({'error': f'汇率转换异常: {str(e)}'}), 500

@app.route('/api/tools/unit-converter', methods=['POST'])
def unit_converter():
    """单位转换"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        can_use, current_credits, required_credits = check_user_credits(user_id, 'unit_converter')
        
        if not can_use:
            return jsonify({
                'error': '积分不足',
                'current_credits': current_credits,
                'required_credits': required_credits
            }), 400
        
        data = request.get_json()
        value = data.get('value')
        from_unit = data.get('from_unit')
        to_unit = data.get('to_unit')
        
        if not value or not from_unit or not to_unit:
            return jsonify({'error': '参数不完整'}), 400
        
        # 模拟单位转换
        conversion_factors = {
            'kg': 1.0,
            'g': 0.001,
            'lb': 0.453592,
            'oz': 0.0283495,
            'm': 1.0,
            'cm': 0.01,
            'inch': 0.0254,
            'ft': 0.3048
        }
        
        if from_unit not in conversion_factors or to_unit not in conversion_factors:
            return jsonify({'error': '不支持的单位'}), 400
        
        # 转换计算
        base_value = value * conversion_factors[from_unit]
        result = base_value / conversion_factors[to_unit]
        
        # 扣除积分
        success, message = deduct_user_credits(user_id, 'unit_converter')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user_id, 'unit_converter',
            {'value': value, 'from': from_unit, 'to': to_unit},
            {'result': result},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'result': round(result, 4),
            'from_unit': from_unit,
            'to_unit': to_unit,
            'original_value': value,
            'credits_used': required_credits,
            'remaining_credits': user_profiles_db[user_id]['credits']
        })
        
    except Exception as e:
        return jsonify({'error': f'单位转换异常: {str(e)}'}), 500

@app.route('/api/tools/shipping-calculator', methods=['POST'])
def shipping_calculator():
    """运费计算"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        can_use, current_credits, required_credits = check_user_credits(user_id, 'shipping_calculator')
        
        if not can_use:
            return jsonify({
                'error': '积分不足',
                'current_credits': current_credits,
                'required_credits': required_credits
            }), 400
        
        data = request.get_json()
        weight = data.get('weight')
        from_country = data.get('from_country')
        to_country = data.get('to_country')
        
        if not weight or not from_country or not to_country:
            return jsonify({'error': '参数不完整'}), 400
        
        # 模拟运费计算
        base_rates = {
            'US': {'CN': 50, 'GB': 35, 'DE': 40},
            'CN': {'US': 45, 'GB': 55, 'DE': 50},
            'GB': {'US': 30, 'CN': 50, 'DE': 15}
        }
        
        if from_country not in base_rates or to_country not in base_rates[from_country]:
            return jsonify({'error': '不支持的国家'}), 400
        
        base_rate = base_rates[from_country][to_country]
        shipping_cost = base_rate * (1 + weight / 10)  # 简单的重量加价
        
        # 扣除积分
        success, message = deduct_user_credits(user_id, 'shipping_calculator')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user_id, 'shipping_calculator',
            {'weight': weight, 'from': from_country, 'to': to_country},
            {'shipping_cost': shipping_cost},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'shipping_cost': round(shipping_cost, 2),
            'from_country': from_country,
            'to_country': to_country,
            'weight': weight,
            'credits_used': required_credits,
            'remaining_credits': user_profiles_db[user_id]['credits']
        })
        
    except Exception as e:
        return jsonify({'error': f'运费计算异常: {str(e)}'}), 500

@app.route('/api/tools/background-remover', methods=['POST'])
def background_remover():
    """背景移除（测试版）"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        can_use, current_credits, required_credits = check_user_credits(user_id, 'background_remover')
        
        if not can_use:
            return jsonify({
                'error': '积分不足',
                'current_credits': current_credits,
                'required_credits': required_credits
            }), 400
        
        if 'image' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 读取图片
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # 模拟背景移除（实际应用中应该调用remove.bg等API）
        # 这里只是简单地将图片转换为RGBA模式作为示例
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # 创建一个简单的透明背景效果（示例）
        width, height = image.size
        pixels = image.load()
        
        # 简单的边缘检测（示例效果）
        for x in range(width):
            for y in range(height):
                if x < 5 or x >= width-5 or y < 5 or y >= height-5:
                    r, g, b, a = pixels[x, y]
                    pixels[x, y] = (r, g, b, 128)  # 边缘半透明
        
        # 转换为base64返回
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # 扣除积分
        success, message = deduct_user_credits(user_id, 'background_remover')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user_id, 'background_remover',
            {'filename': file.filename, 'size': len(image_bytes)},
            {'result_size': len(buffer.getvalue())},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'message': '背景移除完成（测试版）',
            'image_data': f'data:image/png;base64,{image_base64}',
            'original_filename': file.filename,
            'credits_used': required_credits,
            'remaining_credits': user_profiles_db[user_id]['credits']
        })
        
    except Exception as e:
        return jsonify({'error': f'背景移除异常: {str(e)}'}), 500

@app.route('/api/user/usage-stats', methods=['GET'])
def get_usage_stats():
    """获取使用统计"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        
        if user_id not in tool_usage_db:
            return jsonify({
                'total_usage': 0,
                'tool_usage': {},
                'credits_used': 0
            })
        
        usage_records = tool_usage_db[user_id]
        total_usage = len(usage_records)
        tool_usage = {}
        total_credits = 0
        
        for record in usage_records:
            tool_name = record['tool_name']
            credits = record['credits_used']
            
            if tool_name not in tool_usage:
                tool_usage[tool_name] = {'count': 0, 'credits': 0}
            
            tool_usage[tool_name]['count'] += 1
            tool_usage[tool_name]['credits'] += credits
            total_credits += credits
        
        return jsonify({
            'total_usage': total_usage,
            'tool_usage': tool_usage,
            'total_credits_used': total_credits
        })
        
    except Exception as e:
        return jsonify({'error': f'获取统计异常: {str(e)}'}), 500

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': '文件太大'}), 413

# ==================== 启动应用 ====================

if __name__ == '__main__':
    print("🚀 启动PythonAnywhere适配版应用...")
    print("📊 数据库: 模拟内存数据库")
    print("🔧 背景移除功能：测试版")
    print("🌐 访问地址: http://baifan7574.pythonanywhere.com")
    print("📈 健康检查: http://baifan7574.pythonanywhere.com/health")
    app.run(debug=True, host='0.0.0.0', port=5000)