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
    static_folder='../frontend',
    template_folder='../frontend')
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

# 工具积分消耗配置 - 根据会员等级调整
TOOL_CREDITS = {
    'background_remover': {'free': 3, 'basic': 2, 'pro': 1},
    'image_compressor': {'free': 2, 'basic': 1, 'pro': 1},
    'format_converter': {'free': 2, 'basic': 1, 'pro': 0},  # 专业版免费
    'image_cropper': {'free': 2, 'basic': 1, 'pro': 0}   # 专业版免费
}

# 会员等级配置
MEMBERSHIP_PLANS = {
    'free': {
        'name': '免费版',
        'daily_limit': 3,
        'monthly_credits': 10,
        'features': ['基础背景移除', '图片压缩', '格式转换', '图片裁剪']
    },
    'basic': {
        'name': '基础版',
        'daily_limit': 20,
        'monthly_credits': 100,
        'features': ['所有免费功能', '更高质量处理', '优先处理队列']
    },
    'pro': {
        'name': '专业版',
        'daily_limit': -1,  # 无限制
        'monthly_credits': 500,
        'features': ['所有基础版功能', '无限制使用', 'API访问', '批量处理']
    }
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
        # 开发模式：如果是dev-token，直接提取用户ID
        if token.startswith('dev-token-'):
            user_id = token.replace('dev-token-', '')
            # 创建一个简单的用户对象
            class SimpleUser:
                def __init__(self, user_id):
                    self.id = user_id
                    self.email = None
            
            return SimpleUser(user_id)
        
        # 生产模式：验证JWT token（暂时禁用）
        # user_data = supabase.auth.get_user(token)
        # return user_data.user if user_data else None
        return None
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return None

def check_user_permissions(user_id, tool_name):
    """检查用户权限和使用限制"""
    try:
        # 获取用户资料
        profile_response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        if not profile_response.data or len(profile_response.data) == 0:
            return False, "用户不存在", {}
        
        profile_data = profile_response.data[0]
        user_plan = profile_data.get('plan', 'free')
        user_credits = profile_data.get('credits', 0)
        
        # 获取今日使用次数
        today = datetime.now().strftime('%Y-%m-%d')
        usage_response = supabase.table('tool_usage').select('*').eq('user_id', user_id).gte('created_at', today).execute()
        
        today_usage = len(usage_response.data) if usage_response.data else 0
        daily_limit = MEMBERSHIP_PLANS[user_plan]['daily_limit']
        
        # 检查每日限制
        if daily_limit > 0 and today_usage >= daily_limit:
            return False, f"今日使用次数已达上限({daily_limit}次)", {
                'plan': user_plan,
                'credits': user_credits,
                'today_usage': today_usage,
                'daily_limit': daily_limit
            }
        
        # 获取工具所需积分
        tool_credits = TOOL_CREDITS.get(tool_name, {})
        required_credits = tool_credits.get(user_plan, 1)
        
        # 检查积分
        if user_credits < required_credits:
            return False, f"积分不足，需要{required_credits}积分，当前{user_credits}积分", {
                'plan': user_plan,
                'credits': user_credits,
                'required_credits': required_credits,
                'today_usage': today_usage,
                'daily_limit': daily_limit
            }
        
        return True, "权限验证通过", {
            'plan': user_plan,
            'credits': user_credits,
            'required_credits': required_credits,
            'today_usage': today_usage,
            'daily_limit': daily_limit
        }
        
    except Exception as e:
        print(f"权限检查失败: {e}")
        return False, f"权限检查异常: {str(e)}", {}

def get_user_plan_info(user_id):
    """获取用户会员信息"""
    try:
        profile_response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        if not profile_response.data or len(profile_response.data) == 0:
            return None
        
        profile_data = profile_response.data[0]  # 获取第一条记录
        user_plan = profile_data.get('plan', 'free')
        plan_info = MEMBERSHIP_PLANS[user_plan].copy()
        
        # 获取今日使用次数
        today = datetime.now().strftime('%Y-%m-%d')
        usage_response = supabase.table('tool_usage').select('*').eq('user_id', user_id).gte('created_at', today).execute()
        today_usage = len(usage_response.data) if usage_response.data else 0
        
        plan_info.update({
            'current_plan': user_plan,
            'credits': profile_data.get('credits', 0),
            'today_usage': today_usage,
            'remaining_daily': plan_info['daily_limit'] - today_usage if plan_info['daily_limit'] > 0 else -1
        })
        
        return plan_info
        
    except Exception as e:
        print(f"获取会员信息失败: {e}")
        return None

def check_user_credits(user_id, tool_name):
    """检查用户积分是否足够"""
    try:
        # 获取用户积分
        response = supabase.table('user_profiles').select('credits').eq('user_id', user_id).execute()
        if response.data and len(response.data) > 0:
            profile_data = response.data[0]
            credits = profile_data.get('credits', 0)
            user_plan = profile_data.get('plan', 'free')
            tool_credits = TOOL_CREDITS.get(tool_name, {})
            required_credits = tool_credits.get(user_plan, 1)
            return credits >= required_credits, credits, required_credits
        return False, 0, TOOL_CREDITS.get(tool_name, 1)
    except Exception as e:
        print(f"检查用户积分失败: {e}")
        return False, 0, 0

def deduct_user_credits(user_id, tool_name):
    """扣除用户积分"""
    try:
        # 获取用户计划和所需积分
        profile_response = supabase.table('user_profiles').select('plan, credits').eq('user_id', user_id).execute()
        if not profile_response.data or len(profile_response.data) == 0:
            return False, "用户不存在"
        
        profile_data = profile_response.data[0]
        user_plan = profile_data.get('plan', 'free')
        tool_credits = TOOL_CREDITS.get(tool_name, {})
        required_credits = tool_credits.get(user_plan, 1)
        
        current_credits = profile_data.get('credits', 0)
        new_credits = current_credits - required_credits
        
        if new_credits < 0:
            return False, "积分不足"
        
        # 更新积分
        update_response = supabase.table('user_profiles').update({
            'credits': new_credits,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id).execute()
        
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
            'version': '2.1.0-enhanced'
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
        profile_response = supabase.table('user_profiles').select('*').eq('user_id', user.id).execute()
        
        if profile_response.data and len(profile_response.data) > 0:
            profile_data = profile_response.data[0]
            return jsonify({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': profile_data.get('name', ''),
                    'plan': profile_data.get('plan', 'free'),
                    'credits': profile_data.get('credits', 0),
                    'created_at': profile_data.get('created_at'),
                    'updated_at': profile_data.get('updated_at')
                }
            })
        else:
            return jsonify({'error': '用户资料不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'获取资料异常: {str(e)}'}), 500

@app.route('/api/auth/wechat-login', methods=['POST'])
def wechat_login():
    """微信登录/注册"""
    try:
        data = request.get_json()
        openid = data.get('openid')
        nickname = data.get('nickname', '微信用户')
        avatar = data.get('avatar', '')
        unionid = data.get('unionid', '')
        
        if not openid:
            return jsonify({'error': '微信授权信息无效'}), 400
        
        # 检查用户是否已存在
        existing_user = supabase.table('user_profiles').select('*').eq('wechat_openid', openid).execute()
        
        if existing_user.data and len(existing_user.data) > 0:
            # 用户已存在，直接登录
            user = existing_user.data[0]
            
            # 更新最后登录时间
            supabase.table('user_profiles').update({
                'last_login': datetime.now().isoformat()
            }).eq('user_id', user['user_id']).execute()
            
            # 生成JWT token
            token = generate_token(user['user_id'])
            
            return jsonify({
                'message': '微信登录成功',
                'token': token,
                'user': {
                    'id': user['user_id'],
                    'email': user.get('email', ''),
                    'first_name': user.get('first_name', nickname),
                    'last_name': user.get('last_name', ''),
                    'plan': user.get('plan', 'free'),
                    'credits': user.get('credits', 10),
                    'wechat_nickname': user.get('wechat_nickname', nickname),
                    'avatar': user.get('avatar', avatar)
                },
                'is_new_user': False
            })
            
        else:
            # 新用户，自动注册
            user_id = str(uuid.uuid4())
            
            # 创建新用户
            new_user = {
                'user_id': user_id,
                'email': f'wechat_{user_id[:8]}@placeholder.com',  # 临时邮箱
                'first_name': nickname,
                'last_name': '',
                'wechat_openid': openid,
                'wechat_unionid': unionid,
                'wechat_nickname': nickname,
                'avatar': avatar,
                'plan': 'free',
                'credits': 10,  # 新用户赠送10积分
                'created_at': datetime.now().isoformat(),
                'last_login': datetime.now().isoformat(),
                'is_verified': True,  # 微信用户默认已验证
                'registration_method': 'wechat'
            }
            
            # 插入新用户
            insert_response = supabase.table('user_profiles').insert(new_user).execute()
            
            if insert_response.data and len(insert_response.data) > 0:
                # 生成JWT token
                token = generate_token(user_id)
                
                return jsonify({
                    'message': '微信注册成功',
                    'token': token,
                    'user': {
                        'id': user_id,
                        'email': new_user['email'],
                        'first_name': nickname,
                        'last_name': '',
                        'plan': 'free',
                        'credits': 10,
                        'wechat_nickname': nickname,
                        'avatar': avatar
                    },
                    'is_new_user': True
                })
            else:
                return jsonify({'error': '微信注册失败'}), 500
                
    except Exception as e:
        return jsonify({'error': f'微信登录异常: {str(e)}'}), 500

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

@app.route('/api/auth/plan-info', methods=['GET'])
def get_plan_info():
    """获取用户会员信息"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        plan_info = get_user_plan_info(user.id)
        if plan_info:
            return jsonify({'plan_info': plan_info})
        else:
            return jsonify({'error': '获取会员信息失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'获取会员信息异常: {str(e)}'}), 500

@app.route('/api/auth/upgrade-plan', methods=['POST'])
def upgrade_plan():
    """升级会员计划"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        data = request.get_json()
        new_plan = data.get('plan')
        
        if new_plan not in ['basic', 'pro']:
            return jsonify({'error': '无效的会员计划'}), 400
        
        # 更新用户计划
        update_response = supabase.table('user_profiles').update({
            'plan': new_plan,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user.id).execute()
        
        if update_response.data and len(update_response.data) > 0:
            return jsonify({
                'message': f'成功升级到{MEMBERSHIP_PLANS[new_plan]["name"]}',
                'new_plan': new_plan
            })
        else:
            return jsonify({'error': '升级失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'升级异常: {str(e)}'}), 500

@app.route('/api/tools/image-processor', methods=['POST'])
def image_processor():
    """通用图像处理接口"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        tool_name = request.form.get('tool_name', 'background_remover')
        
        # 检查用户权限
        has_permission, message, permission_info = check_user_permissions(user.id, tool_name)
        if not has_permission:
            return jsonify({'error': message}), 400
        
        # 处理图像
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 简化的图像处理（仅作示例）
            image = Image.open(filepath)
            
            # 根据工具类型进行不同处理
            if tool_name == 'background_remover':
                # 简化版：只是转换为RGBA格式
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                processed_image = image
            elif tool_name == 'image_compressor':
                # 简化版：降低质量
                img_io = io.BytesIO()
                image.save(img_io, format='JPEG', quality=70)
                processed_image = Image.open(img_io)
            else:
                processed_image = image
            
            # 保存处理后的图像
            processed_filename = f"processed_{filename}"
            processed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
            processed_image.save(processed_filepath)
            
            # 扣除积分
            deduct_success, deduct_message = deduct_user_credits(user.id, tool_name)
            if not deduct_success:
                return jsonify({'error': deduct_message}), 400
            
            # 记录使用情况
            record_tool_usage(
                user.id, 
                tool_name, 
                filename, 
                processed_filename, 
                permission_info['required_credits']
            )
            
            return jsonify({
                'message': '处理成功',
                'processed_file': processed_filename,
                'credits_used': permission_info['required_credits'],
                'remaining_credits': permission_info['credits'] - permission_info['required_credits']
            })
            
        finally:
            # 清理临时文件
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        return jsonify({'error': f'处理异常: {str(e)}'}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载处理后的文件"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'下载异常: {str(e)}'}), 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    # 打印所有路由
    print("🔍 注册的路由:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
    
    print("🚀 启动Supabase集成版应用（简化版）...")
    print(f"📊 Supabase URL: {supabase_url}")
    print("🔧 背景移除功能：简化版（不依赖rembg）")
    print("🌐 访问地址: http://localhost:5000")
    print("📈 健康检查: http://localhost:5000/health")
    
    app.run(debug=True, host='0.0.0.0', port=5000)