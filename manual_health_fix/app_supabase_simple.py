"""
Supabase集成版Flask应用 - 简化版（不依赖rembg）
用于测试基本的Supabase集成功能
"""

import os
import json
import uuid
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from supabase import create_client
from PIL import Image
import io
import base64

# 加载环境变量
load_dotenv()

app = Flask(__name__, 
    static_folder='../static',
    template_folder='../templates')
CORS(app)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Supabase配置
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    print("❌ 错误：请设置SUPABASE_URL和SUPABASE_KEY环境变量")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    """从请求头获取用户信息"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        # 这里简化处理，实际应该验证JWT token
        # 在生产环境中，需要正确验证Supabase的JWT token
        user_data = supabase.auth.get_user(token)
        return user_data.user if user_data else None
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return None

def check_user_credits(user_id, tool_name):
    """检查用户积分是否足够"""
    try:
        # 获取用户积分
        response = supabase.table('user_profiles').select('credits').eq('user_id', user_id).single()
        if response.data:
            credits = response.data.get('credits', 0)
            required_credits = TOOL_CREDITS.get(tool_name, 1)
            return credits >= required_credits, credits, required_credits
        return False, 0, TOOL_CREDITS.get(tool_name, 1)
    except Exception as e:
        print(f"检查用户积分失败: {e}")
        return False, 0, 0

def deduct_user_credits(user_id, tool_name):
    """扣除用户积分"""
    try:
        required_credits = TOOL_CREDITS.get(tool_name, 1)
        
        # 获取当前积分
        response = supabase.table('user_profiles').select('credits').eq('user_id', user_id).single()
        if not response.data:
            return False, "用户不存在"
        
        current_credits = response.data.get('credits', 0)
        new_credits = current_credits - required_credits
        
        if new_credits < 0:
            return False, "积分不足"
        
        # 更新积分
        update_response = supabase.table('user_profiles').update({
            'credits': new_credits,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id)
        
        if update_response.data:
            return True, f"成功扣除{required_credits}积分，剩余{new_credits}积分"
        else:
            return False, "积分扣除失败"
            
    except Exception as e:
        print(f"扣除积分失败: {e}")
        return False, f"积分扣除异常: {str(e)}"

def record_tool_usage(user_id, tool_name, input_data, output_data, credits_used):
    """记录工具使用情况"""
    try:
        usage_data = {
            'user_id': user_id,
            'tool_name': tool_name,
            'credits_used': credits_used,
            'input_data': input_data,
            'output_data': output_data,
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('tool_usage').insert(usage_data)
        return response.data is not None
        
    except Exception as e:
        print(f"记录工具使用失败: {e}")
        return False

# ==================== API路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """健康检查"""
    try:
        # 测试Supabase连接
        supabase.table('system_config').select('config_key').limit(1).execute()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'supabase': 'connected',
            'version': '2.1.0-simplified'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册 - 绕过邮件验证（临时解决方案）"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name', '')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        # 生成用户ID（绕过Supabase Auth）
        user_id = str(uuid.uuid4())
        
        # 直接创建用户资料（不使用Supabase Auth）
        profile_data = {
            'user_id': user_id,
            'email': email,
            'password_hash': 'dev_mode_no_hash',  # 开发模式密码占位符
            'name': name,
            'plan': 'free',
            'credits': 10,  # 新用户赠送10积分
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 插入用户资料
        profile_response = supabase.table('user_profiles').insert(profile_data).execute()
        
        if profile_response.data:
            return jsonify({
                'message': '注册成功（开发模式）',
                'user_id': user_id,
                'email': email,
                'name': name,
                'plan': 'free',
                'credits': 10,
                'note': '开发模式：已绕过邮件验证'
            })
        else:
            return jsonify({'error': '注册失败：无法创建用户资料'}), 400
            
    except Exception as e:
        return jsonify({'error': f'注册异常: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录 - 开发模式（简化验证）"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': '邮箱和密码不能为空'}), 400
        
        # 开发模式：直接查询用户资料（不验证密码）
        profile_response = supabase.table('user_profiles').select('*').eq('email', email).execute()
        
        if profile_response.data and len(profile_response.data) > 0:
            user_data = profile_response.data[0]
            return jsonify({
                'message': '登录成功（开发模式）',
                'user': {
                    'id': user_data.get('user_id'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name', ''),
                    'plan': user_data.get('plan', 'free'),
                    'credits': user_data.get('credits', 0)
                },
                'token': 'dev-token-' + user_data.get('user_id'),  # 临时token
                'note': '开发模式：已绕过密码验证'
            })
        else:
            return jsonify({'error': '用户不存在'}), 401
            
    except Exception as e:
        return jsonify({'error': f'登录异常: {str(e)}'}), 500

@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    """获取用户资料"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        # 获取用户详细资料
        profile_response = supabase.table('user_profiles').select('*').eq('user_id', user.id).single()
        
        if profile_response.data:
            return jsonify({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': profile_response.data.get('name', ''),
                    'plan': profile_response.data.get('plan', 'free'),
                    'credits': profile_response.data.get('credits', 0),
                    'created_at': profile_response.data.get('created_at'),
                    'updated_at': profile_response.data.get('updated_at')
                }
            })
        else:
            return jsonify({'error': '用户资料不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'获取资料异常: {str(e)}'}), 500

@app.route('/api/tools/currency-converter', methods=['POST'])
def currency_converter():
    """汇率转换工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        # 检查积分
        has_credits, current_credits, required_credits = check_user_credits(user.id, 'currency_converter')
        if not has_credits:
            return jsonify({'error': f'积分不足，需要{required_credits}积分，当前{current_credits}积分'}), 400
        
        data = request.get_json()
        amount = data.get('amount', 0)
        from_currency = data.get('from_currency', 'USD')
        to_currency = data.get('to_currency', 'CNY')
        
        # 模拟汇率转换（实际应该调用真实汇率API）
        exchange_rate = 7.2 if from_currency == 'USD' and to_currency == 'CNY' else 1.0
        result = amount * exchange_rate
        
        # 扣除积分
        success, message = deduct_user_credits(user.id, 'currency_converter')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user.id, 
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
        
        # 检查积分
        has_credits, current_credits, required_credits = check_user_credits(user.id, 'unit_converter')
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
        success, message = deduct_user_credits(user.id, 'unit_converter')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user.id,
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
        
        # 检查积分
        has_credits, current_credits, required_credits = check_user_credits(user.id, 'shipping_calculator')
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
        success, message = deduct_user_credits(user.id, 'shipping_calculator')
        if not success:
            return jsonify({'error': message}), 400
        
        # 记录使用
        record_tool_usage(
            user.id,
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
        
        # 获取使用统计
        response = supabase.table('tool_usage').select('*').eq('user_id', user.id).execute()
        
        if response.data:
            total_usage = len(response.data)
            total_credits = sum(item.get('credits_used', 0) for item in response.data)
            
            # 按工具类型统计
            tool_stats = {}
            for item in response.data:
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
        else:
            return jsonify({
                'total_usage': 0,
                'total_credits_used': 0,
                'tool_breakdown': {}
            })
            
    except Exception as e:
        return jsonify({'error': f'获取统计异常: {str(e)}'}), 500

@app.route('/api/tools/remove-background', methods=['POST'])
def remove_background():
    """背景移除工具 - 简化版（仅返回模拟结果）"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        # 检查积分
        has_credits, current_credits, required_credits = check_user_credits(user.id, 'background_remover')
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
        success, message = deduct_user_credits(user.id, 'background_remover')
        if not success:
            return jsonify({'error': message}), 400
        
        # 模拟背景移除处理
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f"input_{filename}")
        output_filename = f"processed_{uuid.uuid4().hex[:8]}_{filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        file.save(input_path)
        
        # 简单的图片处理（添加白色背景作为示例）
        try:
            with Image.open(input_path) as img:
                # 转换为RGBA模式
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 创建白色背景
                white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                white_bg.paste(img, (0, 0), img)
                
                # 保存处理后的图片
                white_bg.save(output_path, 'PNG')
                
        except Exception as img_error:
            return jsonify({'error': f'图片处理失败: {str(img_error)}'}), 500
        
        finally:
            # 清理临时文件
            if os.path.exists(input_path):
                os.remove(input_path)
        
        # 记录使用
        record_tool_usage(
            user.id,
            'background_remover',
            {'filename': filename, 'file_size': os.path.getsize(output_path)},
            {'output_filename': output_filename, 'processed': True},
            required_credits
        )
        
        return jsonify({
            'success': True,
            'message': '背景移除完成（简化版处理）',
            'output_filename': output_filename,
            'credits_used': required_credits,
            'download_url': f'/api/download/{output_filename}'
        })
        
    except Exception as e:
        return jsonify({'error': f'背景移除异常: {str(e)}'}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载处理后的文件"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

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
    print("🚀 启动Supabase集成版应用（简化版）...")
    print(f"📊 Supabase URL: {supabase_url}")
    print("🔧 背景移除功能：简化版（不依赖rembg）")
    print("🌐 访问地址: http://localhost:5000")
    print("📈 健康检查: http://localhost:5000/health")
    
    app.run(debug=True, host='0.0.0.0', port=5000)