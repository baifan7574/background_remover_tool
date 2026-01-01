"""
海外跨境小工具 - Supabase Pro版本
支持PythonAnywhere + Supabase Pro分离式架构
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
from rembg import remove
from PIL import Image
import io
from functools import wraps
import jwt
import logging
import time
import traceback
from typing import Optional, Dict, Any
import re

# 配置日志 (Pro版增强)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crossborder_tools_api')

from supabase_db import db, user_db, usage_db, storage_db

# 初始化应用
app = Flask(__name__, 
    static_folder='../frontend',
    template_folder='../frontend')
CORS(app)

# Pro版配置
IS_PRO_MODE = os.getenv('SUPABASE_IS_PRO', 'false').lower() == 'true'
logger.info(f"启动API服务 (Pro模式: {IS_PRO_MODE})")

# 配置
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['MAX_IMAGE_DIMENSION'] = 4096  # Pro版增强：最大图片尺寸限制

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 工具配置
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# 工具积分消耗配置 (Pro版可配置)
TOOL_CREDITS = {
    'background-remover': int(os.getenv('CREDIT_COST_BACKGROUND_REMOVE', '2')),
    'currency-converter': int(os.getenv('CREDIT_COST_CURRENCY', '1')),
    'shipping-calculator': int(os.getenv('CREDIT_COST_SHIPPING', '1')),
    'unit-converter': int(os.getenv('CREDIT_COST_UNIT', '1'))
}

# 全局错误处理 (Pro版新增)
@app.errorhandler(Exception)
async def handle_exception(e):
    logger.error(f"未处理的异常: {e}\n{traceback.format_exc()}")
    return jsonify({
        'success': False,
        'error': '服务器内部错误',
        'error_code': 'INTERNAL_ERROR'
    }), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def decode_auth_token(auth_header):
    """解码认证令牌 (Pro版增强)"""
    if not auth_header:
        return None
    
    try:
        auth_token = auth_header.split(" ")[1]
        # Pro版增强：使用Supabase Auth验证token
        try:
            result = db.execute_with_retry(
                lambda: db.client.auth.get_user(auth_token)
            )
            if result and result.user:
                return result.user.id
        except Exception as e:
            logger.warning(f"Supabase Auth验证失败: {e}")
        
        # 备用方案：简化处理
        return auth_token
    except Exception as e:
        logger.warning(f"Token解码失败: {e}")
        return None

def get_client_ip():
    """获取客户端IP地址 (Pro版新增)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def get_user_agent():
    """获取用户代理信息 (Pro版新增)"""
    return request.headers.get('User-Agent', '')

def log_request(route, user_id=None):
    """记录API请求 (Pro版新增)"""
    logger.info(f"API请求 - 路由: {route}, 用户ID: {user_id}, IP: {get_client_ip()}, UA: {get_user_agent()[:50]}...")

def create_usage_metadata():
    """创建使用元数据 (Pro版新增)"""
    return {
        'ip_address': get_client_ip(),
        'user_agent': get_user_agent(),
        'request_time': time.time(),
        'api_version': 'pro' if IS_PRO_MODE else 'standard'
    }

def require_auth(f):
    """认证装饰器 (Pro版增强)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        route = request.path
        auth_header = request.headers.get('Authorization')
        
        # 记录请求
        log_request(route)
        
        user_id = decode_auth_token(auth_header)
        
        if not user_id:
            logger.warning(f"认证失败 - 缺少或无效的token: {route}")
            return jsonify({ 
                'error': '需要认证',
                'error_code': 'AUTH_REQUIRED'
            }), 401
        
        # 验证用户是否存在 (Pro版增强：使用重试机制)
        user_profile = db.execute_with_retry(
            lambda: user_db.get_user_profile(user_id)
        )
        
        if not user_profile['success']:
            logger.warning(f"用户不存在: {user_id}")
            return jsonify({ 
                'error': '用户不存在',
                'error_code': 'USER_NOT_FOUND'
            }), 401
        
        # 将用户信息添加到请求上下文
        request.current_user = user_profile['user']
        request.user_id = user_id
        
        logger.info(f"用户认证成功: {user_id} - {route}")
        
        return f(*args, **kwargs)
    
    return decorated_function

def record_tool_usage(tool_name, credits_used, metadata=None):
    """记录工具使用情况 (Pro版增强)"""
    try:
        if hasattr(request, 'user_id'):
            user_id = request.user_id
            
            # Pro版增强：创建元数据
            if not metadata:
                metadata = create_usage_metadata()
            
            # Pro版增强：使用事务处理
            success = False
            retry_count = 3
            
            for attempt in range(retry_count):
                try:
                    # 开始事务
                    if db.start_transaction():
                        # 记录使用情况
                        usage_result = usage_db.record_usage(
                            user_id, 
                            tool_name, 
                            credits_used,
                            metadata=metadata
                        )
                        
                        if usage_result['success']:
                            # 扣除用户积分
                            credit_result = user_db.update_user_credits(user_id, -credits_used)
                            
                            if credit_result['success']:
                                # 提交事务
                                db.commit_transaction()
                                success = True
                                logger.info(f"工具使用记录成功: {user_id} - {tool_name} - {credits_used}")
                                break
                            else:
                                db.rollback_transaction()
                                logger.error(f"积分更新失败: {credit_result['error']}")
                        else:
                            db.rollback_transaction()
                            logger.error(f"使用记录失败: {usage_result['error']}")
                
                    if not success and attempt < retry_count - 1:
                        logger.warning(f"尝试 {attempt+1}/{retry_count} 失败，重试中...")
                        time.sleep(0.5)  # 退避延迟
                except Exception as e:
                    db.rollback_transaction()
                    logger.error(f"事务错误: {e}")
                    if attempt < retry_count - 1:
                        time.sleep(0.5)
            
            return success
    except Exception as e:
        logger.error(f"记录使用失败: {e}\n{traceback.format_exc()}")
        return False

# 主页路由
@app.route('/')
def index():
    log_request('/')
    return jsonify({
        'message': '海外跨境小工具API服务运行中 (Supabase Pro版)', 
        'version': '3.0.0',
        'mode': 'Pro' if IS_PRO_MODE else 'Standard',
        'architecture': 'PythonAnywhere + Supabase Pro',
        'features': ['高并发支持', '事务处理', '增强的错误处理', '详细日志', '使用统计分析'],
        'tools': [
            {'name': 'background-remover', 'description': '背景移除工具', 'credits': TOOL_CREDITS['background-remover']},
            {'name': 'currency-converter', 'description': '汇率转换工具', 'credits': TOOL_CREDITS['currency-converter']},
            {'name': 'shipping-calculator', 'description': '国际运费计算', 'credits': TOOL_CREDITS['shipping-calculator']},
            {'name': 'unit-converter', 'description': '尺寸单位转换', 'credits': TOOL_CREDITS['unit-converter']}
        ]
    })

# 用户注册
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            return jsonify({'error': '请填写完整信息'}), 400
        
        # 创建用户
        result = user_db.create_user(email, password, name)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '注册成功',
                'user_id': result['user_id'],
                'email': result['email']
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': f'注册失败: {str(e)}'}), 500

# 用户登录
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': '请填写邮箱和密码'}), 400
        
        # 用户认证
        result = user_db.authenticate_user(email, password)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user_id': result['user_id'],
                'email': result['email'],
                'access_token': result['access_token']
            })
        else:
            return jsonify({'error': result['error']}), 401
            
    except Exception as e:
        return jsonify({'error': f'登录失败: {str(e)}'}), 500

# 获取用户资料 (Pro版增强)
@app.route('/api/user/profile', methods=['GET'])
@app.route('/api/auth/profile', methods=['GET'])  # 添加前端调用的路由别名
@require_auth
def get_user_profile():
    """获取用户个人资料 (Pro版增强)"""
    route = request.path  # 使用实际请求的路径
    log_request(route, request.user_id)
    
    try:
        # Pro版增强：使用重试机制
        user_profile = db.execute_with_retry(
            lambda: user_db.get_user_profile(request.user_id)
        )
        
        if user_profile['success']:
            # Pro版增强：添加使用统计
            usage_stats_result = usage_db.get_user_usage_stats(request.user_id)
            
            # 兼容前端期望的格式 - 提取统计数据，移除success包装
            user_data = user_profile['user']
            usage_stats = usage_stats_result if usage_stats_result.get('success') else {}
            # 如果usage_stats有success字段，移除它（前端不需要）
            if isinstance(usage_stats, dict) and 'success' in usage_stats:
                usage_stats_clean = {k: v for k, v in usage_stats.items() if k != 'success'}
            else:
                usage_stats_clean = usage_stats
            
            return jsonify({
                'success': True,
                'user': user_data,
                'usage_stats': usage_stats_clean,
                'is_pro_user': IS_PRO_MODE
            })
        else:
            logger.warning(f"获取用户资料失败: {user_profile.get('error')}")
            return jsonify({
                'error': '获取用户资料失败',
                'error_code': 'PROFILE_NOT_FOUND'
            }), 404
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            'error': '服务器错误',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# 更新用户资料 (Pro版新增)
@app.route('/api/user/profile', methods=['POST'])
@require_auth
def update_user_profile():
    """更新用户个人资料 (Pro版增强)"""
    route = '/api/user/profile'
    log_request(route, request.user_id)
    
    try:
        data = request.json
        
        # Pro版增强：参数验证
        if not data or not isinstance(data, dict):
            return jsonify({
                'error': '无效的请求数据',
                'error_code': 'INVALID_REQUEST_DATA'
            }), 400
        
        # Pro版增强：使用事务和重试
        result = db.execute_with_retry(
            lambda: user_db.update_user_profile(request.user_id, data)
        )
        
        if result['success']:
            logger.info(f"用户资料更新成功: {request.user_id}")
            return jsonify({
                'success': True,
                'message': '个人资料更新成功',
                'user': result['user']
            })
        else:
            logger.warning(f"更新用户资料失败: {result.get('error')}")
            return jsonify({
                'error': result['error'],
                'error_code': 'UPDATE_FAILED'
            }), 400
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            'error': '服务器错误',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# 获取用户使用历史 (Pro版新增)
@app.route('/api/user/usage-history', methods=['GET'])
@require_auth
def get_usage_history():
    """获取用户使用历史 (Pro版新增)"""
    route = '/api/user/usage-history'
    log_request(route, request.user_id)
    
    try:
        # 获取分页参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        # Pro版增强：获取使用历史
        result = usage_db.get_user_usage_history(
            request.user_id,
            page=page,
            limit=limit
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'usage_history': result['history'],
                'total': result['total'],
                'page': page,
                'limit': limit,
                'total_pages': (result['total'] + limit - 1) // limit
            })
        else:
            return jsonify({
                'error': result['error'],
                'error_code': 'FETCH_FAILED'
            }), 500
    except Exception as e:
        logger.error(f"获取使用历史失败: {e}\n{traceback.format_exc()}")
        return jsonify({
            'error': '服务器错误',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# 背景移除工具 (Pro版增强)
@app.route('/api/tools/background-remover', methods=['POST'])
@require_auth
def remove_background():
    """背景移除工具 (Pro版增强)"""
    route = '/api/tools/background-remover'
    log_request(route, request.user_id)
    
    start_time = time.time()
    metadata = create_usage_metadata()
    
    try:
        # 检查积分
        credits_needed = TOOL_CREDITS['background-remover']
        if request.current_user['credits'] < credits_needed:
            logger.warning(f"积分不足: {request.user_id} - 所需: {credits_needed} - 当前: {request.current_user['credits']}")
            return jsonify({
                'error': '积分不足，请充值',
                'error_code': 'INSUFFICIENT_CREDITS',
                'required_credits': credits_needed,
                'current_credits': request.current_user['credits']
            }), 402
        
        # 检查文件
        if 'file' not in request.files:
            return jsonify({
                'error': '没有提供文件',
                'error_code': 'FILE_REQUIRED'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'error': '没有选择文件',
                'error_code': 'NO_FILE_SELECTED'
            }), 400
        
        if file and allowed_file(file.filename):
            # 获取可选参数 (Pro版增强)
            output_format = request.form.get('format', 'png')
            resize_width = request.form.get('width')
            resize_height = request.form.get('height')
            preserve_ratio = request.form.get('preserve_ratio', 'true').lower() == 'true'
            
            # 生成唯一文件名
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            unique_id = str(uuid.uuid4())
            input_filename = f'{unique_id}_{file.filename}'
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
            
            try:
                # 保存文件
                file.save(input_path)
                
                # Pro版增强：图片预处理和尺寸验证
                with Image.open(input_path) as img:
                    width, height = img.size
                    metadata['original_size'] = {'width': width, 'height': height}
                    
                    # 检查最大尺寸限制
                    if width > app.config['MAX_IMAGE_DIMENSION'] or height > app.config['MAX_IMAGE_DIMENSION']:
                        logger.warning(f"图片尺寸过大: {width}x{height} > {app.config['MAX_IMAGE_DIMENSION']}")
                        return jsonify({
                            'error': f'图片尺寸超过限制 ({app.config["MAX_IMAGE_DIMENSION"]}x{app.config["MAX_IMAGE_DIMENSION"]})',
                            'error_code': 'IMAGE_TOO_LARGE'
                        }), 400
                
                # 处理图片
                with open(input_path, 'rb') as input_file:
                    input_data = input_file.read()
                
                logger.info(f"开始处理背景移除: {request.user_id} - 图片尺寸: {width}x{height}")
                output_data = remove(input_data)
                
                # 添加白色背景并进行后处理
                output_image = Image.open(io.BytesIO(output_data))
                if output_image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', output_image.size, (255, 255, 255))
                    background.paste(output_image, mask=output_image.split()[-1])
                    output_image = background
                
                # Pro版增强：后期处理 (调整大小等)
                if resize_width or resize_height:
                    try:
                        new_width = int(resize_width) if resize_width else width
                        new_height = int(resize_height) if resize_height else height
                        
                        if preserve_ratio:
                            output_image.thumbnail((new_width, new_height), Image.LANCZOS)
                        else:
                            output_image = output_image.resize((new_width, new_height), Image.LANCZOS)
                        
                        metadata['resized'] = True
                        metadata['resized_size'] = {'width': output_image.width, 'height': output_image.height}
                    except Exception as e:
                        logger.error(f"调整图片尺寸失败: {e}")
                
                # 保存到内存 (Pro版优化：减少磁盘I/O)
                buffer = io.BytesIO()
                output_image.save(buffer, format=output_format.upper())
                output_data = buffer.getvalue()
                
                # 上传到Supabase Storage
                output_filename = f'{unique_id}_removed.{output_format}'
                storage_path = f"processed/{request.user_id}/{output_filename}"
                upload_result = storage_db.upload_file('processed-images', storage_path, output_data)
                
                if upload_result['success']:
                    # 记录使用情况
                    processing_time = time.time() - start_time
                    metadata['processing_time'] = round(processing_time, 2)
                    metadata['output_format'] = output_format
                    
                    record_tool_usage('background-remover', credits_needed, metadata)
                    
                    # 获取文件URL
                    file_url = storage_db.get_file_url('processed-images', storage_path)
                    
                    logger.info(f"背景移除成功: {request.user_id} - 处理时间: {processing_time:.2f}秒")
                    
                    return jsonify({
                        'success': True,
                        'message': '背景移除成功',
                        'credits_used': credits_needed,
                        'remaining_credits': request.current_user['credits'] - credits_needed,
                        'output_filename': output_filename,
                        'file_url': file_url.get('url', ''),
                        'storage_path': storage_path,
                        'processing_time': round(processing_time, 2),
                        'metadata': metadata
                    })
                else:
                    logger.error(f"文件上传失败: {upload_result.get('error')}")
                    return jsonify({
                        'error': '文件上传失败',
                        'error_code': 'UPLOAD_FAILED'
                    }), 500
                    
            except Exception as e:
                logger.error(f"背景移除处理失败: {e}\n{traceback.format_exc()}")
                return jsonify({
                    'error': '处理失败，请重试',
                    'error_code': 'PROCESSING_FAILED'
                }), 500
            finally:
                # 清理文件
                if os.path.exists(input_path):
                    os.remove(input_path)
        else:
            logger.warning(f"不支持的文件类型: {file.filename}")
            return jsonify({
                'error': '不支持的文件类型',
                'error_code': 'UNSUPPORTED_FILE_TYPE',
                'allowed_types': list(ALLOWED_EXTENSIONS)
            }), 400
            
    except Exception as e:
        logger.error(f"背景移除API异常: {e}\n{traceback.format_exc()}")
        return jsonify({
            'error': '服务器内部错误',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# 汇率转换工具
@app.route('/api/tools/currency-converter', methods=['POST'])
@require_auth
def currency_converter():
    try:
        credits_needed = TOOL_CREDITS['currency-converter']
        
        data = request.get_json()
        amount = float(data.get('amount', 0))
        from_currency = data.get('from_currency', 'CNY').upper()
        to_currency = data.get('to_currency', 'USD').upper()
        
        # 使用免费的汇率API (这里使用模拟数据，实际应用中应该使用真实的API)
        exchange_rates = {
            'CNY': {'USD': 0.14, 'EUR': 0.13, 'GBP': 0.11, 'JPY': 20.8},
            'USD': {'CNY': 7.2, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 149.5},
            'EUR': {'CNY': 7.8, 'USD': 1.09, 'GBP': 0.86, 'JPY': 162.8},
            'GBP': {'CNY': 9.1, 'USD': 1.27, 'EUR': 1.16, 'JPY': 189.2},
            'JPY': {'CNY': 0.048, 'USD': 0.0067, 'EUR': 0.0061, 'GBP': 0.0053}
        }
        
        if from_currency == to_currency:
            converted_amount = amount
        elif from_currency in exchange_rates and to_currency in exchange_rates[from_currency]:
            converted_amount = amount * exchange_rates[from_currency][to_currency]
        else:
            return jsonify({'error': '不支持的货币对'}), 400
        
        # 记录工具使用
        if record_tool_usage('currency-converter', credits_needed):
            return jsonify({
                'success': True,
                'amount': amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'converted_amount': round(converted_amount, 2),
                'rate': exchange_rates.get(from_currency, {}).get(to_currency, 1),
                'credits_used': credits_needed,
                'remaining_credits': request.current_user['credits'] - credits_needed
            })
        else:
            return jsonify({'error': '记录使用失败，请重试'}), 500
        
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500

# 国际运费计算工具
@app.route('/api/tools/shipping-calculator', methods=['POST'])
@require_auth
def shipping_calculator():
    try:
        credits_needed = TOOL_CREDITS['shipping-calculator']
        
        data = request.get_json()
        weight = float(data.get('weight', 0))  # 重量(kg)
        length = float(data.get('length', 0))  # 长度(cm)
        width = float(data.get('width', 0))    # 宽度(cm)
        height = float(data.get('height', 0))  # 高度(cm)
        destination = data.get('destination', 'US')  # 目的地国家代码
        shipping_type = data.get('shipping_type', 'standard')  # 运输类型
        
        # 计算体积重量 (kg)
        volume_weight = (length * width * height) / 5000
        
        # 取实际重量和体积重量的较大值
        chargeable_weight = max(weight, volume_weight)
        
        # 基础运费计算 (模拟数据)
        base_rates = {
            'US': {'standard': 80, 'express': 150, 'economy': 60},
            'UK': {'standard': 90, 'express': 170, 'economy': 70},
            'CA': {'standard': 75, 'express': 140, 'economy': 55},
            'AU': {'standard': 85, 'express': 160, 'economy': 65},
            'DE': {'standard': 70, 'express': 130, 'economy': 50}
        }
        
        base_rate = base_rates.get(destination, {}).get(shipping_type, 100)
        
        # 超重费用
        overweight_fee = max(0, chargeable_weight - 0.5) * 25
        
        # 总运费
        total_shipping = base_rate + overweight_fee
        
        # 记录工具使用
        if record_tool_usage('shipping-calculator', credits_needed):
            return jsonify({
                'success': True,
                'weight': weight,
                'volume_weight': round(volume_weight, 2),
                'chargeable_weight': round(chargeable_weight, 2),
                'destination': destination,
                'shipping_type': shipping_type,
                'base_rate': base_rate,
                'overweight_fee': round(overweight_fee, 2),
                'total_shipping': round(total_shipping, 2),
                'currency': 'CNY',
                'credits_used': credits_needed,
                'remaining_credits': request.current_user['credits'] - credits_needed
            })
        else:
            return jsonify({'error': '记录使用失败，请重试'}), 500
        
    except Exception as e:
        return jsonify({'error': f'计算失败: {str(e)}'}), 500

# 单位转换工具
@app.route('/api/tools/unit-converter', methods=['POST'])
@require_auth
def unit_converter():
    try:
        credits_needed = TOOL_CREDITS['unit-converter']
        
        data = request.get_json()
        value = float(data.get('value', 0))
        from_unit = data.get('from_unit', '')
        to_unit = data.get('to_unit', '')
        conversion_type = data.get('conversion_type', 'length')
        
        # 转换因子
        conversion_factors = {
            'length': {
                'cm': 1, 'mm': 10, 'm': 0.01, 'inch': 0.3937, 'ft': 0.0328
            },
            'weight': {
                'kg': 1, 'g': 1000, 'lb': 2.2046, 'oz': 35.274
            },
            'volume': {
                'l': 1, 'ml': 1000, 'gal': 0.2642, 'fl_oz': 33.814
            }
        }
        
        if conversion_type not in conversion_factors:
            return jsonify({'error': '不支持的转换类型'}), 400
        
        factors = conversion_factors[conversion_type]
        
        if from_unit not in factors or to_unit not in factors:
            return jsonify({'error': '不支持的单位'}), 400
        
        # 转换为基准单位，再转换为目标单位
        base_value = value / factors[from_unit]
        converted_value = base_value * factors[to_unit]
        
        # 记录工具使用
        if record_tool_usage('unit-converter', credits_needed):
            return jsonify({
                'success': True,
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'conversion_type': conversion_type,
                'converted_value': round(converted_value, 4),
                'credits_used': credits_needed,
                'remaining_credits': request.current_user['credits'] - credits_needed
            })
        else:
            return jsonify({'error': '记录使用失败，请重试'}), 500
        
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500

# 获取工具使用统计
@app.route('/api/tools/usage-stats')
@require_auth
def usage_stats():
    try:
        stats = usage_db.get_user_usage_stats(request.user_id)
        if stats['success']:
            return jsonify({
                'success': True,
                'stats': stats,
                'user_credits': request.current_user['credits']
            })
        else:
            return jsonify({'error': stats['error']}), 500
    except Exception as e:
        return jsonify({'error': f'获取统计失败: {str(e)}'}), 500

# 文件下载 (本地备用)
@app.route('/api/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

# 健康检查
# 提供静态HTML页面
@app.route('/terms.html')
def terms():
    """服务条款页面"""
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'terms.html')
        if os.path.exists(frontend_path):
            with open(frontend_path, 'r', encoding='utf-8') as f:
                return f.read()
        return "页面不存在", 404
    except Exception as e:
        return f"加载页面失败: {str(e)}", 500

@app.route('/privacy.html')
def privacy():
    """隐私政策页面"""
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'privacy.html')
        if os.path.exists(frontend_path):
            with open(frontend_path, 'r', encoding='utf-8') as f:
                return f.read()
        return "页面不存在", 404
    except Exception as e:
        return f"加载页面失败: {str(e)}", 500

@app.route('/cookie.html')
def cookie():
    """Cookie政策页面"""
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'cookie.html')
        if os.path.exists(frontend_path):
            with open(frontend_path, 'r', encoding='utf-8') as f:
                return f.read()
        return "页面不存在", 404
    except Exception as e:
        return f"加载页面失败: {str(e)}", 500

@app.route('/api/health')
def health_check():
    try:
        # 测试Supabase连接
        supabase_status = db.test_connection()
        
        return jsonify({
            'status': 'healthy',
            'supabase_connected': supabase_status,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

if __name__ == '__main__':
    print('🌍 海外跨境小工具服务启动中 (Supabase版)...')
    print('📱 访问地址: http://localhost:5000')
    print('📁 上传目录:', os.path.abspath(app.config['UPLOAD_FOLDER']))
    print('💾 输出目录:', os.path.abspath(app.config['OUTPUT_FOLDER']))
    print('🗄️  数据库: Supabase云数据库')
    print('☁️  存储: Supabase Storage')
    app.run(debug=True, host='0.0.0.0', port=5000)