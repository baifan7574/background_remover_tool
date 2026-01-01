"""
Supabase集成版Flask应用 - 完整版（集成rembg背景移除）
用于第3周图片处理模块开发
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
import rembg
from rembg import new_session, remove

# 导入支付API
from payment_api import payment_bp

# 加载环境变量
load_dotenv()

app = Flask(__name__, 
    static_folder='../frontend',
    template_folder='../frontend',
    static_url_path='/static')
CORS(app)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Supabase配置
app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
app.config['SUPABASE_KEY'] = os.getenv('SUPABASE_SERVICE_KEY')

if not app.config['SUPABASE_URL'] or not app.config['SUPABASE_KEY']:
    print("❌ 错误：请设置SUPABASE_URL和SUPABASE_SERVICE_KEY环境变量")
    exit(1)

supabase = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_KEY'])

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 工具积分消耗配置 - 根据会员等级调整
TOOL_CREDITS = {
    'background_remover': {'free': 3, 'basic': 2, 'pro': 1},
    'image_compressor': {'free': 2, 'basic': 1, 'pro': 1},
    'format_converter': {'free': 2, 'basic': 1, 'pro': 0},  # 专业版免费
    'image_cropper': {'free': 2, 'basic': 1, 'pro': 0}   # 专业版免费
}

# 会员等级配置 - 与会员策略文档保持一致
# 会员计划配置 - 仅包含每日次数限制
MEMBERSHIP_PLANS = {
    'free': {
        'name': '免费版',
        'daily_limit': 3,  # 免费版每天3次
        'price': 0,
        'features': ['基础背景移除', '标准质量输出']
    },
    'basic': {
        'name': '基础版',
        'daily_limit': 10,  # 基础版每天10次，与会员政策一致
        'price': 19,
        'features': ['高质量背景移除', '多格式支持', '优先处理']
    },
    'pro': {
        'name': '专业版',
        'daily_limit': 100,  # 专业版每天100次，与会员政策一致
        'price': 99,
        'features': ['无限背景移除', '批量处理', 'API访问', '高级功能']
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
        # 开发模式：处理临时token
        if token.startswith('dev-token-'):
            user_id = token.replace('dev-token-', '')
            # 开发模式特殊用户：直接返回模拟用户，不查询数据库
            if user_id == 'test-user-12345':
                class MockUser:
                    def __init__(self):
                        self.id = 'test-user-12345'
                        self.email = 'test@example.com'
                        self.user_metadata = {'name': '测试用户', 'plan': 'pro'}
                return MockUser()
            
            # 从数据库获取用户信息
            profile_response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            if profile_response.data and len(profile_response.data) > 0:
                user_data = profile_response.data[0]
                # 创建模拟用户对象
                class MockUser:
                    def __init__(self, user_data):
                        self.id = user_data.get('user_id')
                        self.email = user_data.get('email')
                        self.user_metadata = user_data
                
                return MockUser(user_data)
            return None
        else:
            # 生产环境：验证Supabase JWT
            user_data = supabase.auth.get_user(token)
            return user_data.user if user_data else None
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return None

def check_user_permissions(user_id, tool_name):
    """检查用户权限和使用限制 - 仅检查每日次数限制"""
    try:
        # 开发模式特殊用户：直接返回成功
        if user_id == 'test-user-12345':
            return True, "开发模式权限验证通过", {
                'plan': 'pro',
                'today_usage': 0,
                'daily_limit': 100,
                'remaining_daily': 100
            }
        
        # 获取用户资料
        profile_response = supabase.table('user_profiles').select('*').eq('user_id', user_id).single().execute()
        if not profile_response.data or len(profile_response.data) == 0:
            return False, "用户不存在", {}
        
        user_data = profile_response.data[0] if isinstance(profile_response.data, list) else profile_response.data
        user_plan = user_data.get('plan', 'free')
        
        # 获取今日使用次数
        today = datetime.now().strftime('%Y-%m-%d')
        usage_response = supabase.table('tool_usage').select('*').eq('user_id', user_id).gte('created_at', today).execute()
        
        today_usage = len(usage_response.data) if usage_response.data else 0
        daily_limit = MEMBERSHIP_PLANS[user_plan]['daily_limit']
        
        # 检查每日限制
        if daily_limit > 0 and today_usage >= daily_limit:
            return False, f"今日使用次数已达上限({daily_limit}次)", {
                'plan': user_plan,
                'today_usage': today_usage,
                'daily_limit': daily_limit,
                'remaining_daily': 0
            }
        
        return True, "权限验证通过", {
            'plan': user_plan,
            'today_usage': today_usage,
            'daily_limit': daily_limit,
            'remaining_daily': daily_limit - today_usage if daily_limit > 0 else -1
        }
        
    except Exception as e:
        print(f"权限检查失败: {e}")
        return False, f"权限检查异常: {str(e)}", {}

def get_user_plan_info(user_id):
    """获取用户会员信息 - 仅显示每日次数限制"""
    try:
        profile_response = supabase.table('user_profiles').select('*').eq('user_id', user_id).single().execute()
        if not profile_response.data or len(profile_response.data) == 0:
            return None
        
        user_data = profile_response.data[0] if isinstance(profile_response.data, list) else profile_response.data
        user_plan = user_data.get('plan', 'free')
        plan_info = MEMBERSHIP_PLANS[user_plan].copy()
        
        # 获取今日使用次数
        today = datetime.now().strftime('%Y-%m-%d')
        usage_response = supabase.table('tool_usage').select('*').eq('user_id', user_id).gte('created_at', today).execute()
        today_usage = len(usage_response.data) if usage_response.data else 0
        
        plan_info.update({
            'current_plan': user_plan,
            'today_usage': today_usage,
            'remaining_daily': plan_info['daily_limit'] - today_usage if plan_info['daily_limit'] > 0 else -1
        })
        
        return plan_info
        
    except Exception as e:
        print(f"获取会员信息失败: {e}")
        return None

# 新增API端点
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

# 注册支付蓝图
from payment_api import payment_bp
app.register_blueprint(payment_bp)

print("🚀 AI背景移除工具启动成功!")
print("📊 支付系统已集成: 支付宝、微信支付")
print("🔗 前端地址: http://localhost:8000")
print("🔧 后端API: http://localhost:5000")
print("💳 支付API: http://localhost:5000/api/payment")

@app.route('/api/auth/upgrade-plan', methods=['POST'])
def upgrade_plan():
    """升级会员计划 - 不再涉及积分"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        data = request.get_json()
        new_plan = data.get('plan')
        
        if new_plan not in ['basic', 'pro']:
            return jsonify({'error': '无效的会员计划'}), 400
        
        # 获取当前用户资料
        profile_response = supabase.table('user_profiles').select('*').eq('user_id', user.id).single().execute()
        if not profile_response.data or len(profile_response.data) == 0:
            return jsonify({'error': '用户不存在'}), 404
        
        user_data = profile_response.data[0] if isinstance(profile_response.data, list) else profile_response.data
        current_plan = user_data.get('plan', 'free')
        
        if current_plan == new_plan:
            return jsonify({'error': '您已经是该会员等级'}), 400
        
        # 更新会员计划 - 不再设置积分
        update_response = supabase.table('user_profiles').update({
            'plan': new_plan,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user.id).execute()
        
        if update_response.data:
            return jsonify({
                'message': f'成功升级到{MEMBERSHIP_PLANS[new_plan]["name"]}',
                'new_plan': new_plan,
                'daily_limit': MEMBERSHIP_PLANS[new_plan]['daily_limit']
            })
        else:
            return jsonify({'error': '升级失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'升级异常: {str(e)}'}), 500

# ==================== 图片处理API ====================

@app.route('/api/tools/crop-image', methods=['POST'])
def crop_image():
    """图片裁剪工具 - 支持预设尺寸和自定义裁剪"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user.id
        
        # 检查用户权限和每日限制
        has_permission, message, user_info = check_user_permissions(user_id, 'image_cropper')
        if not has_permission:
            return jsonify({'error': message}), 400
        
        # 获取请求数据
        data = request.get_json()
        image_data = data.get('image')
        crop_type = data.get('crop_type', 'custom')  # custom, preset, aspect_ratio
        crop_data = data.get('crop_data', {})
        
        if not image_data:
            return jsonify({'error': '没有提供图片数据'}), 400
        
        try:
            # 解码base64图片
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 记录处理开始时间
            start_time = datetime.now()
            
            # 预设尺寸配置
            preset_sizes = {
                'instagram_square': (1080, 1080),
                'instagram_story': (1080, 1920),
                'facebook_cover': (851, 315),
                'twitter_header': (1500, 500),
                'youtube_thumbnail': (1280, 720),
                'amazon_product': (1000, 1000),
                'product_detail': (800, 800),
                'banner_large': (1200, 300),
                'banner_small': (600, 150)
            }
            
            # 根据裁剪类型处理
            if crop_type == 'preset':
                preset_name = crop_data.get('preset', 'instagram_square')
                if preset_name not in preset_sizes:
                    return jsonify({'error': f'不支持的预设尺寸: {preset_name}'}), 400
                
                target_width, target_height = preset_sizes[preset_name]
                
                # 智能裁剪：保持宽高比，居中裁剪
                img_width, img_height = image.size
                aspect_ratio = target_width / target_height
                img_aspect = img_width / img_height
                
                if img_aspect > aspect_ratio:
                    # 图片更宽，裁剪宽度
                    new_width = int(img_height * aspect_ratio)
                    left = (img_width - new_width) // 2
                    crop_box = (left, 0, left + new_width, img_height)
                else:
                    # 图片更高，裁剪高度
                    new_height = int(img_width / aspect_ratio)
                    top = (img_height - new_height) // 2
                    crop_box = (0, top, img_width, top + new_height)
                
                cropped_image = image.crop(crop_box).resize((target_width, target_height), Image.Resampling.LANCZOS)
                
            elif crop_type == 'aspect_ratio':
                aspect_name = crop_data.get('aspect', '1:1')
                aspect_ratios = {
                    '1:1': 1.0,
                    '16:9': 16/9,
                    '4:3': 4/3,
                    '3:2': 3/2,
                    '2:1': 2.0,
                    '9:16': 9/16
                }
                
                if aspect_name not in aspect_ratios:
                    return jsonify({'error': f'不支持的宽高比: {aspect_name}'}), 400
                
                target_aspect = aspect_ratios[aspect_name]
                img_width, img_height = image.size
                img_aspect = img_width / img_height
                
                if img_aspect > target_aspect:
                    new_width = int(img_height * target_aspect)
                    left = (img_width - new_width) // 2
                    crop_box = (left, 0, left + new_width, img_height)
                else:
                    new_height = int(img_width / target_aspect)
                    top = (img_height - new_height) // 2
                    crop_box = (0, top, img_width, top + new_height)
                
                cropped_image = image.crop(crop_box)
                
            elif crop_type == 'custom':
                # 自定义裁剪
                x = crop_data.get('x', 0)
                y = crop_data.get('y', 0)
                width = crop_data.get('width', image.width)
                height = crop_data.get('height', image.height)
                
                # 验证裁剪参数
                if x < 0 or y < 0 or width <= 0 or height <= 0:
                    return jsonify({'error': '裁剪参数无效'}), 400
                
                if x + width > image.width or y + height > image.height:
                    return jsonify({'error': '裁剪区域超出图片范围'}), 400
                
                crop_box = (x, y, x + width, y + height)
                cropped_image = image.crop(crop_box)
                
            else:
                return jsonify({'error': f'不支持的裁剪类型: {crop_type}'}), 400
            
            # 转换为base64返回
            buffer = io.BytesIO()
            cropped_image.save(buffer, format='PNG', optimize=True)
            cropped_image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录工具使用
            record_tool_usage(
                user_id=user_id,
                tool_name='image_cropper',
                input_data={
                    'original_size': f"{image.width}x{image.height}",
                    'crop_type': crop_type,
                    'crop_data': crop_data
                },
                output_data={
                    'cropped_size': f"{cropped_image.width}x{cropped_image.height}",
                    'processing_time': processing_time
                },
                credits_used=0
            )
            
            return jsonify({
                'success': True,
                'message': '图片裁剪完成',
                'cropped_image': cropped_image_base64,
                'user_info': user_info,
                'crop_info': {
                    'original_size': f"{image.width}x{image.height}",
                    'cropped_size': f"{cropped_image.width}x{cropped_image.height}",
                    'crop_type': crop_type,
                    'processing_time': round(processing_time, 2)
                }
            })
            
        except MemoryError:
            return jsonify({'error': '图片过大导致内存不足，请尝试更小的图片'}), 400
        except IOError as img_error:
            return jsonify({'error': f'图片格式不支持或文件损坏: {str(img_error)}'}), 400
        except Exception as img_error:
            print(f"图片裁剪错误: {img_error}")
            return jsonify({'error': f'图片裁剪失败: {str(img_error)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'图片裁剪异常: {str(e)}'}), 500

@app.route('/api/tools/convert-format', methods=['POST'])
def convert_format():
    """格式转换工具 - 支持JPG/PNG/WebP等主流格式互转"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user.id
        
        # 检查用户权限和每日限制
        has_permission, message, user_info = check_user_permissions(user_id, 'format_converter')
        if not has_permission:
            return jsonify({'error': message}), 400
        
        # 获取请求数据
        data = request.get_json()
        image_data = data.get('image')
        target_format = data.get('format', 'PNG').upper()
        quality = data.get('quality', 95)  # 对于支持质量的格式
        
        if not image_data:
            return jsonify({'error': '没有提供图片数据'}), 400
        
        # 支持的格式
        supported_formats = ['JPEG', 'PNG', 'WEBP', 'BMP', 'GIF']
        if target_format not in supported_formats:
            return jsonify({'error': f'不支持的格式，支持的格式: {", ".join(supported_formats)}'}), 400
        
        try:
            # 解码base64图片
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 记录处理开始时间
            start_time = datetime.now()
            
            # 处理透明度（对于不支持透明度的格式）
            if target_format in ['JPEG', 'BMP'] and image.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif target_format == 'GIF' and image.mode not in ['P', 'L']:
                # GIF转换为调色板模式以减小文件大小
                image = image.convert('P', palette=Image.ADAPTIVE, colors=256)
            
            # 转换格式
            buffer = io.BytesIO()
            save_kwargs = {'format': target_format, 'optimize': True}
            
            # 设置质量参数（对于支持的格式）
            if target_format in ['JPEG', 'WEBP']:
                save_kwargs['quality'] = quality
            
            # GIF特殊处理
            if target_format == 'GIF':
                save_kwargs['save_all'] = True
                save_kwargs['duration'] = 100  # 默认帧持续时间
                save_kwargs['loop'] = 0
            
            image.save(buffer, **save_kwargs)
            converted_bytes = buffer.getvalue()
            
            # 转换为base64返回
            converted_image_base64 = base64.b64encode(converted_bytes).decode()
            
            # 计算处理时间和文件信息
            original_size = len(image_bytes)
            converted_size = len(converted_bytes)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录工具使用
            record_tool_usage(
                user_id=user_id,
                tool_name='format_converter',
                input_data={
                    'original_format': image.format,
                    'original_size': original_size,
                    'target_format': target_format,
                    'quality': quality
                },
                output_data={
                    'converted_size': converted_size,
                    'processing_time': processing_time,
                    'final_format': target_format
                },
                credits_used=0
            )
            
            return jsonify({
                'success': True,
                'message': f'格式转换完成: {image.format} → {target_format}',
                'converted_image': converted_image_base64,
                'user_info': user_info,
                'conversion_info': {
                    'original_format': image.format,
                    'target_format': target_format,
                    'original_size': f"{original_size / 1024:.2f} KB",
                    'converted_size': f"{converted_size / 1024:.2f} KB",
                    'size_change': f"{((converted_size - original_size) / original_size * 100):+.2f}%",
                    'processing_time': round(processing_time, 2),
                    'quality': quality if target_format in ['JPEG', 'WEBP'] else 'N/A'
                }
            })
            
        except MemoryError:
            return jsonify({'error': '图片过大导致内存不足，请尝试更小的图片'}), 400
        except IOError as img_error:
            return jsonify({'error': f'图片格式不支持或文件损坏: {str(img_error)}'}), 400
        except Exception as img_error:
            print(f"格式转换错误: {img_error}")
            return jsonify({'error': f'格式转换失败: {str(img_error)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'格式转换异常: {str(e)}'}), 500

@app.route('/api/tools/compress-image', methods=['POST'])
def compress_image():
    """图片压缩工具 - 支持质量调节和文件大小优化"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user.id
        
        # 检查用户权限和每日限制
        has_permission, message, user_info = check_user_permissions(user_id, 'image_compressor')
        if not has_permission:
            return jsonify({'error': message}), 400
        
        # 获取请求数据
        data = request.get_json()
        image_data = data.get('image')
        quality = data.get('quality', 85)  # 默认质量85
        format_type = data.get('format', 'JPEG')  # 默认输出JPEG
        max_size = data.get('max_size', None)  # 可选的最大文件大小(KB)
        
        if not image_data:
            return jsonify({'error': '没有提供图片数据'}), 400
        
        # 验证质量参数
        if not (1 <= quality <= 100):
            return jsonify({'error': '质量参数必须在1-100之间'}), 400
        
        try:
            # 解码base64图片
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 记录处理开始时间
            start_time = datetime.now()
            
            # 转换为RGB模式（如果需要）
            if format_type == 'JPEG' and image.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # 压缩图片
            buffer = io.BytesIO()
            save_kwargs = {'format': format_type, 'optimize': True}
            
            if format_type in ['JPEG', 'WEBP']:
                save_kwargs['quality'] = quality
            
            image.save(buffer, **save_kwargs)
            compressed_bytes = buffer.getvalue()
            
            # 如果指定了最大文件大小，进行自适应压缩
            if max_size and len(compressed_bytes) > max_size * 1024:
                # 二分法找到合适的质量参数
                min_quality, max_quality = 1, quality
                best_bytes = compressed_bytes
                
                while min_quality <= max_quality:
                    mid_quality = (min_quality + max_quality) // 2
                    buffer = io.BytesIO()
                    save_kwargs['quality'] = mid_quality
                    image.save(buffer, **save_kwargs)
                    test_bytes = buffer.getvalue()
                    
                    if len(test_bytes) <= max_size * 1024:
                        best_bytes = test_bytes
                        min_quality = mid_quality + 1
                    else:
                        max_quality = mid_quality - 1
                
                compressed_bytes = best_bytes
                final_quality = save_kwargs['quality']
            else:
                final_quality = quality
            
            # 转换为base64返回
            compressed_image_base64 = base64.b64encode(compressed_bytes).decode()
            
            # 计算压缩率和处理时间
            original_size = len(image_bytes)
            compressed_size = len(compressed_bytes)
            compression_ratio = round((1 - compressed_size / original_size) * 100, 2)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录工具使用
            record_tool_usage(
                user_id=user_id,
                tool_name='image_compressor',
                input_data={
                    'original_size': original_size,
                    'quality': quality,
                    'format': format_type,
                    'max_size': max_size
                },
                output_data={
                    'compressed_size': compressed_size,
                    'compression_ratio': compression_ratio,
                    'final_quality': final_quality,
                    'processing_time': processing_time
                },
                credits_used=0
            )
            
            return jsonify({
                'success': True,
                'message': '图片压缩完成',
                'compressed_image': compressed_image_base64,
                'user_info': user_info,
                'compression_info': {
                    'original_size': f"{original_size / 1024:.2f} KB",
                    'compressed_size': f"{compressed_size / 1024:.2f} KB",
                    'compression_ratio': f"{compression_ratio}%",
                    'final_quality': final_quality,
                    'processing_time': round(processing_time, 2),
                    'format': format_type
                }
            })
            
        except MemoryError:
            return jsonify({'error': '图片过大导致内存不足，请尝试更小的图片'}), 400
        except IOError as img_error:
            return jsonify({'error': f'图片格式不支持或文件损坏: {str(img_error)}'}), 400
        except Exception as img_error:
            print(f"图片压缩错误: {img_error}")
            return jsonify({'error': f'图片压缩失败: {str(img_error)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'图片压缩异常: {str(e)}'}), 500

# 导入优化版背景移除模块
from optimized_background_remover import optimized_remove_background, get_cache_info

@app.route('/api/tools/background-remover', methods=['POST'])
def remove_background():
    """背景移除工具 - 优化版，支持多种模型和错误处理"""
    try:
        # 获取用户信息（可选）
        user = get_user_from_token()
        user_id = user.id if user else None
        
        # 检查用户权限和每日限制 - 如果用户已登录则检查，否则跳过
        if user:
            has_permission, message, user_info = check_user_permissions(user_id, 'background_remover')
            if not has_permission:
                return jsonify({'error': message}), 400
        else:
            # 未登录用户使用默认配置
            user_info = {'plan': 'free', 'today_usage': 0, 'daily_limit': 3, 'remaining_daily': 3}
        
        # 获取请求数据
        data = request.get_json()
        image_data = data.get('image')
        model_type = data.get('model', 'u2net')  # 支持多种模型选择
        alpha_matting = data.get('alpha_matting', False)
        
        if not image_data:
            return jsonify({'error': '没有提供图片数据'}), 400
        
        # 进度回调函数
        progress_data = {'progress': 0, 'status': '准备中...'}
        
        def progress_callback(progress, status):
            progress_data['progress'] = progress
            progress_data['status'] = status
            print(f"📊 处理进度: {progress}% - {status}")
        
        try:
            # 使用优化版背景移除
            result = optimized_remove_background(
                image_data=image_data,
                model_name=model_type,
                alpha_matting=alpha_matting,
                progress_callback=progress_callback,
                max_size=1024  # 限制输入尺寸以提高速度
            )
            
            if not result['success']:
                return jsonify({'error': result['error']}), 400
            
            # 记录工具使用
            record_tool_usage(
                user_id=user_id,
                tool_name='background_remover',
                input_data={
                    'model': model_type,
                    'alpha_matting': alpha_matting,
                    'optimization': 'enabled'
                },
                output_data=result['performance_info'],
                credits_used=0
            )
            
            return jsonify({
                'success': True,
                'message': '背景移除完成',
                'processed_image': result['processed_image'],
                'user_info': user_info,
                'performance_info': result['performance_info'],
                'cache_info': get_cache_info()
            })
            
        except Exception as img_error:
            print(f"图片处理错误: {img_error}")
            return jsonify({'error': f'图片处理失败: {str(img_error)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'背景移除异常: {str(e)}'}), 500

@app.route('/api/tools/mobile-optimize', methods=['POST'])
def mobile_optimize():
    """移动端图片优化 - 自动调整尺寸和压缩"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user.id
        
        # 检查用户权限和每日限制
        has_permission, message, user_info = check_user_permissions(user_id, 'mobile_optimizer')
        if not has_permission:
            return jsonify({'error': message}), 400
        
        # 获取请求数据
        data = request.get_json()
        image_data = data.get('image')
        target_device = data.get('target_device', 'mobile')  # mobile, tablet, desktop
        quality_level = data.get('quality_level', 'balanced')  # high, balanced, fast
        
        if not image_data:
            return jsonify({'error': '没有提供图片数据'}), 400
        
        try:
            # 解码base64图片
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 记录处理开始时间
            start_time = datetime.now()
            
            # 设备优化配置
            device_configs = {
                'mobile': {
                    'max_width': 1080,
                    'max_height': 1920,
                    'target_quality': 85,
                    'max_file_size': 500 * 1024  # 500KB
                },
                'tablet': {
                    'max_width': 2048,
                    'max_height': 2048,
                    'target_quality': 90,
                    'max_file_size': 1024 * 1024  # 1MB
                },
                'desktop': {
                    'max_width': 1920,
                    'max_height': 1080,
                    'target_quality': 95,
                    'max_file_size': 2048 * 1024  # 2MB
                }
            }
            
            config = device_configs.get(target_device, device_configs['mobile'])
            
            # 质量级别调整
            quality_multipliers = {
                'high': 1.1,
                'balanced': 1.0,
                'fast': 0.9
            }
            
            target_quality = int(config['target_quality'] * quality_multipliers.get(quality_level, 1.0))
            target_quality = min(100, max(60, target_quality))
            
            # 获取图片信息
            original_width, original_height = image.size
            original_format = image.format or 'JPEG'
            
            # 计算目标尺寸
            max_width = config['max_width']
            max_height = config['max_height']
            
            # 保持宽高比缩放
            if original_width > max_width or original_height > max_height:
                aspect_ratio = original_width / original_height
                
                if original_width > original_height:
                    # 横向图片
                    new_width = min(original_width, max_width)
                    new_height = int(new_width / aspect_ratio)
                    
                    if new_height > max_height:
                        new_height = max_height
                        new_width = int(new_height * aspect_ratio)
                else:
                    # 纵向图片
                    new_height = min(original_height, max_height)
                    new_width = int(new_height * aspect_ratio)
                    
                    if new_width > max_width:
                        new_width = max_width
                        new_height = int(new_width / aspect_ratio)
                
                optimized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                optimized_image = image.copy()
                new_width, new_height = original_width, original_height
            
            # 转换为RGB模式（用于JPEG）
            if optimized_image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', optimized_image.size, (255, 255, 255))
                if optimized_image.mode == 'P':
                    optimized_image = optimized_image.convert('RGBA')
                background.paste(optimized_image, mask=optimized_image.split()[-1] if optimized_image.mode == 'RGBA' else None)
                optimized_image = background
            
            # 自适应压缩
            buffer = io.BytesIO()
            
            # 初始压缩
            optimized_image.save(buffer, format='JPEG', quality=target_quality, optimize=True)
            file_size = buffer.tell()
            
            # 如果文件仍然过大，进一步压缩
            if file_size > config['max_file_size']:
                buffer.seek(0)
                buffer.truncate()
                
                # 二分法找到最佳质量
                min_quality = 60
                max_quality = target_quality
                best_quality = target_quality
                
                while min_quality <= max_quality:
                    test_quality = (min_quality + max_quality) // 2
                    
                    test_buffer = io.BytesIO()
                    optimized_image.save(test_buffer, format='JPEG', quality=test_quality, optimize=True)
                    test_size = test_buffer.tell()
                    
                    if test_size <= config['max_file_size']:
                        best_quality = test_quality
                        min_quality = test_quality + 1
                    else:
                        max_quality = test_quality - 1
                
                # 使用最佳质量保存
                optimized_image.save(buffer, format='JPEG', quality=best_quality, optimize=True)
                file_size = buffer.tell()
            
            optimized_image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # 计算优化效果
            original_size = len(image_bytes)
            compression_ratio = (original_size - file_size) / original_size * 100 if original_size > 0 else 0
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录工具使用
            record_tool_usage(
                user_id=user_id,
                tool_name='mobile_optimizer',
                input_data={
                    'original_size': f"{original_width}x{original_height}",
                    'target_device': target_device,
                    'quality_level': quality_level,
                    'original_file_size': original_size
                },
                output_data={
                    'optimized_size': f"{new_width}x{new_height}",
                    'optimized_file_size': file_size,
                    'compression_ratio': compression_ratio,
                    'processing_time': processing_time
                },
                credits_used=0
            )
            
            return jsonify({
                'success': True,
                'message': '移动端优化完成',
                'optimized_image': optimized_image_base64,
                'user_info': user_info,
                'optimization_info': {
                    'original_size': f"{original_width}x{original_height}",
                    'optimized_size': f"{new_width}x{new_height}",
                    'original_file_size': f"{original_size/1024:.1f}KB",
                    'optimized_file_size': f"{file_size/1024:.1f}KB",
                    'compression_ratio': f"{compression_ratio:.1f}%",
                    'target_device': target_device,
                    'quality_level': quality_level,
                    'processing_time': round(processing_time, 2)
                }
            })
            
        except MemoryError:
            return jsonify({'error': '图片过大导致内存不足，请尝试更小的图片'}), 400
        except IOError as img_error:
            return jsonify({'error': f'图片格式不支持或文件损坏: {str(img_error)}'}), 400
        except Exception as img_error:
            print(f"移动端优化错误: {img_error}")
            return jsonify({'error': f'移动端优化失败: {str(img_error)}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'移动端优化异常: {str(e)}'}), 500

@app.route('/api/tools/batch-process', methods=['POST'])
def batch_process():
    """批量图片处理 - 支持多图片同时处理"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user.id
        
        # 获取请求数据
        data = request.get_json()
        images = data.get('images', [])  # 图片数组
        operation = data.get('operation')  # background_remove, compress, convert, crop, mobile_optimize
        batch_settings = data.get('settings', {})  # 批量处理设置
        
        if not images or len(images) == 0:
            return jsonify({'error': '没有提供图片数据'}), 400
        
        if not operation:
            return jsonify({'error': '没有指定处理操作'}), 400
        
        # 检查批量处理权限
        has_permission, message, user_info = check_user_permissions(user_id, f'batch_{operation}')
        if not has_permission:
            return jsonify({'error': message}), 400
        
        # 限制批量处理数量
        max_batch_size = 10  # 最大批量处理数量
        if len(images) > max_batch_size:
            return jsonify({'error': f'批量处理最多支持{max_batch_size}张图片'}), 400
        
        # 记录处理开始时间
        start_time = datetime.now()
        
        results = []
        successful_count = 0
        failed_count = 0
        
        # 处理每张图片
        for i, image_data in enumerate(images):
            try:
                result = process_single_image(
                    image_data=image_data,
                    operation=operation,
                    settings=batch_settings,
                    user_id=user_id,
                    index=i
                )
                
                if result['success']:
                    successful_count += 1
                else:
                    failed_count += 1
                
                results.append(result)
                
            except Exception as e:
                failed_count += 1
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })
        
        # 计算总处理时间
        total_processing_time = (datetime.now() - start_time).total_seconds()
        
        # 记录批量处理使用
        record_tool_usage(
            user_id=user_id,
            tool_name=f'batch_{operation}',
            input_data={
                'batch_size': len(images),
                'operation': operation,
                'settings': batch_settings
            },
            output_data={
                'successful_count': successful_count,
                'failed_count': failed_count,
                'total_processing_time': total_processing_time
            },
            credits_used=0
        )
        
        return jsonify({
            'success': True,
            'message': f'批量处理完成：成功{successful_count}张，失败{failed_count}张',
            'results': results,
            'batch_summary': {
                'total_images': len(images),
                'successful_count': successful_count,
                'failed_count': failed_count,
                'total_processing_time': round(total_processing_time, 2),
                'operation': operation
            },
            'user_info': user_info
        })
        
    except Exception as e:
        return jsonify({'error': f'批量处理异常: {str(e)}'}), 500

def process_single_image(image_data, operation, settings, user_id, index):
    """处理单张图片的内部函数"""
    try:
        # 解码base64图片
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        original_width, original_height = image.size
        original_size = len(image_bytes)
        
        processed_image = None
        processing_info = {}
        
        # 根据操作类型处理图片
        if operation == 'background_remove':
            # 背景移除
            model_name = settings.get('model', 'u2net')
            alpha_matting = settings.get('alpha_matting', False)
            
            processed_image = remove_background(image, model_name, alpha_matting)
            processing_info = {
                'model_used': model_name,
                'alpha_matting': alpha_matting
            }
            
        elif operation == 'compress':
            # 图片压缩
            quality = settings.get('quality', 80)
            max_size = settings.get('max_size', 1024 * 1024)
            
            processed_image = compress_image_internal(image, quality, max_size)
            processing_info = {
                'quality': quality,
                'max_size': max_size
            }
            
        elif operation == 'convert':
            # 格式转换
            target_format = settings.get('format', 'JPEG')
            quality = settings.get('quality', 90)
            
            processed_image = convert_format_internal(image, target_format, quality)
            processing_info = {
                'target_format': target_format,
                'quality': quality
            }
            
        elif operation == 'crop':
            # 图片裁剪
            crop_type = settings.get('crop_type', 'custom')
            crop_data = settings.get('crop_data', {})
            
            processed_image = crop_image_internal(image, crop_type, crop_data)
            processing_info = {
                'crop_type': crop_type,
                'crop_data': crop_data
            }
            
        elif operation == 'mobile_optimize':
            # 移动端优化
            target_device = settings.get('target_device', 'mobile')
            quality_level = settings.get('quality_level', 'balanced')
            
            processed_image = mobile_optimize_internal(image, target_device, quality_level)
            processing_info = {
                'target_device': target_device,
                'quality_level': quality_level
            }
            
        else:
            return {
                'index': index,
                'success': False,
                'error': f'不支持的操作: {operation}'
            }
        
        # 转换为base64
        buffer = io.BytesIO()
        if processed_image.mode in ('RGBA', 'LA'):
            processed_image.save(buffer, format='PNG', optimize=True)
        else:
            processed_image.save(buffer, format='JPEG', quality=90, optimize=True)
        
        processed_image_base64 = base64.b64encode(buffer.getvalue()).decode()
        processed_size = buffer.tell()
        
        return {
            'index': index,
            'success': True,
            'processed_image': processed_image_base64,
            'image_info': {
                'original_size': f"{original_width}x{original_height}",
                'processed_size': f"{processed_image.width}x{processed_image.height}",
                'original_file_size': f"{original_size/1024:.1f}KB",
                'processed_file_size': f"{processed_size/1024:.1f}KB",
                'compression_ratio': f"{(original_size - processed_size) / original_size * 100:.1f}%" if original_size > 0 else "0%"
            },
            'processing_info': processing_info
        }
        
    except Exception as e:
        return {
            'index': index,
            'success': False,
            'error': str(e)
        }

# 辅助函数实现
def remove_background(image, model_name, alpha_matting):
    """背景移除内部实现"""
    from rembg import new_session, remove
    
    session = new_session(model_name)
    return remove(image, session=session, alpha_matting=alpha_matting)

def compress_image_internal(image, quality, max_size):
    """图片压缩内部实现"""
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=quality, optimize=True)
    
    if buffer.tell() > max_size:
        # 二分法调整质量
        min_q, max_q = 60, quality
        best_q = quality
        
        while min_q <= max_q:
            test_q = (min_q + max_q) // 2
            test_buffer = io.BytesIO()
            image.save(test_buffer, format='JPEG', quality=test_q, optimize=True)
            
            if test_buffer.tell() <= max_size:
                best_q = test_q
                min_q = test_q + 1
            else:
                max_q = test_q - 1
        
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=best_q, optimize=True)
    
    return Image.open(buffer)

def convert_format_internal(image, target_format, quality):
    """格式转换内部实现"""
    if target_format.upper() in ['JPEG', 'JPG'] and image.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    
    return image

def crop_image_internal(image, crop_type, crop_data):
    """图片裁剪内部实现"""
    if crop_type == 'preset':
        preset_sizes = {
            'instagram_square': (1080, 1080),
            'instagram_story': (1080, 1920),
            'facebook_cover': (851, 315),
            'twitter_header': (1500, 500),
            'youtube_thumbnail': (1280, 720)
        }
        
        preset_name = crop_data.get('preset', 'instagram_square')
        target_width, target_height = preset_sizes.get(preset_name, (1080, 1080))
        
        # 智能裁剪
        aspect_ratio = target_width / target_height
        img_aspect = image.width / image.height
        
        if img_aspect > aspect_ratio:
            new_width = int(image.height * aspect_ratio)
            left = (image.width - new_width) // 2
            crop_box = (left, 0, left + new_width, image.height)
        else:
            new_height = int(image.width / aspect_ratio)
            top = (image.height - new_height) // 2
            crop_box = (0, top, image.width, top + new_height)
        
        return image.crop(crop_box).resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    elif crop_type == 'custom':
        x = crop_data.get('x', 0)
        y = crop_data.get('y', 0)
        width = crop_data.get('width', image.width)
        height = crop_data.get('height', image.height)
        
        crop_box = (x, y, x + width, y + height)
        return image.crop(crop_box)
    
    return image

def mobile_optimize_internal(image, target_device, quality_level):
    """移动端优化内部实现"""
    device_configs = {
        'mobile': {'max_width': 1080, 'max_height': 1920, 'quality': 85},
        'tablet': {'max_width': 2048, 'max_height': 2048, 'quality': 90},
        'desktop': {'max_width': 1920, 'max_height': 1080, 'quality': 95}
    }
    
    config = device_configs.get(target_device, device_configs['mobile'])
    quality_multipliers = {'high': 1.1, 'balanced': 1.0, 'fast': 0.9}
    
    target_quality = int(config['quality'] * quality_multipliers.get(quality_level, 1.0))
    target_quality = min(100, max(60, target_quality))
    
    # 缩放
    if image.width > config['max_width'] or image.height > config['max_height']:
        aspect_ratio = image.width / image.height
        
        if image.width > image.height:
            new_width = min(image.width, config['max_width'])
            new_height = int(new_width / aspect_ratio)
            
            if new_height > config['max_height']:
                new_height = config['max_height']
                new_width = int(new_height * aspect_ratio)
        else:
            new_height = min(image.height, config['max_height'])
            new_width = int(new_height / aspect_ratio)
            
            if new_width > config['max_width']:
                new_width = config['max_width']
                new_height = int(new_width / aspect_ratio)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 转换模式
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    
    return image

@app.route('/api/auth/check-permission/<tool_name>', methods=['GET'])
def check_permission(tool_name):
    """检查用户对特定工具的使用权限"""
    try:
        # 从Authorization header获取用户信息（可选）
        user = get_user_from_token()
        
        if user:
            # 已登录用户，检查权限
            user_id = user.id
            has_permission, message, user_info = check_user_permissions(user_id, tool_name)
        else:
            # 未登录用户，给予默认权限
            has_permission = True
            message = "未登录用户可以使用免费功能"
            user_info = {
                'plan': 'free', 
                'today_usage': 0, 
                'daily_limit': 3, 
                'remaining_daily': 3
            }
        
        return jsonify({
            'has_permission': has_permission,
            'message': message,
            'user_info': user_info,
            'tool_name': tool_name
        })
        
    except Exception as e:
        return jsonify({'error': f'权限检查异常: {str(e)}'}), 500

@app.route('/api/tools/image-processor', methods=['POST'])
def image_processor():
    """通用图片处理API - 保持向后兼容"""
    try:
        # 重定向到背景移除API
        return background_remover()
    except Exception as e:
        return jsonify({'error': f'处理异常: {str(e)}'}), 500

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

def check_user_credits(user_id, tool_name):
    """检查用户积分是否足够"""
    try:
        # 获取用户积分
        response = supabase.table('user_profiles').select('credits').eq('user_id', user_id).single()
        if response.data:
            credits = response.data.get('credits', 0)
            user_plan = response.data.get('plan', 'free')
            tool_credits = TOOL_CREDITS.get(tool_name, {})
            required_credits = tool_credits.get(user_plan, 1)
            return credits >= required_credits, credits, required_credits
        return False, 0, TOOL_CREDITS.get(tool_name, 1)
    except Exception as e:
        print(f"检查用户积分失败: {e}")
        return False, 0, 0

def deduct_credits(user_id, credits_to_deduct):
    """扣除用户积分 - 简化版"""
    try:
        # 获取用户当前积分
        profile_response = supabase.table('user_profiles').select('credits').eq('user_id', user_id).single()
        if not profile_response.data:
            return False, "用户不存在"
        
        current_credits = profile_response.data.get('credits', 0)
        new_credits = current_credits - credits_to_deduct
        
        if new_credits < 0:
            return False, "积分不足"
        
        # 更新积分
        update_response = supabase.table('user_profiles').update({
            'credits': new_credits,
            'updated_at': datetime.now().isoformat()
        }).eq('user_id', user_id)
        
        if update_response.data:
            return True, f"成功扣除{credits_to_deduct}积分，剩余{new_credits}积分"
        else:
            return False, "积分扣除失败"
            
    except Exception as e:
        print(f"扣除积分失败: {e}")
        return False, f"积分扣除异常: {str(e)}"

def record_tool_usage(user_id, tool_name, input_data, output_data, credits_used=0):
    """记录工具使用情况 - 不再涉及积分"""
    try:
        usage_data = {
            'user_id': user_id,
            'tool_type': 'remove-background',
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('tool_usage').insert(usage_data).execute()
        return response.data is not None
        
    except Exception as e:
        print(f"记录工具使用失败: {e}")
        return False

# ==================== API路由 ====================

@app.route('/')
def index():
    """主页 - 返回前端应用"""
    try:
        # 直接返回前端应用的index.html
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'index.html')
        if os.path.exists(frontend_path):
            with open(frontend_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return "前端应用文件不存在", 404
    except Exception as e:
        return f"加载前端应用失败: {str(e)}", 500

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

@app.route('/health')
def health_check():
    """健康检查"""
    try:
        # 简化健康检查 - 不依赖数据库连接
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'features': {
                'background_removal': 'enabled',
                'image_compression': 'enabled', 
                'format_conversion': 'enabled',
                'image_cropping': 'enabled',
                'batch_processing': 'enabled'
            },
            'version': '2.1.0-enhanced',
            'rembg_status': 'loaded'
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
                'daily_limit': MEMBERSHIP_PLANS['free']['daily_limit'],
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
            # 获取使用统计
            usage_stats = get_user_usage_stats(user_data.get('user_id'))
            
            return jsonify({
                'message': '登录成功（开发模式）',
                'user': {
                    'id': user_data.get('user_id'),
                    'email': user_data.get('email'),
                    'name': user_data.get('name', ''),
                    'plan': user_data.get('plan', 'free'),
                    'daily_limit': MEMBERSHIP_PLANS[user_data.get('plan', 'free')]['daily_limit']
                },
                'token': 'dev-token-' + user_data.get('user_id'),  # 临时token
                'usage_stats': usage_stats,
                'note': '开发模式：已绕过密码验证'
            })
        else:
            return jsonify({'error': '用户不存在'}), 401
            
    except Exception as e:
        return jsonify({'error': f'登录异常: {str(e)}'}), 500

def get_user_usage_stats(user_id):
    """获取用户使用统计 - 仅基于每日次数限制"""
    try:
        # 获取今日使用统计
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        response = supabase.table('tool_usage').select('*').eq('user_id', user_id).gte('created_at', today_start).execute()
        
        # 获取用户资料
        profile_response = supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
        
        if not profile_response.data or len(profile_response.data) == 0:
            return {}
        
        user_data = profile_response.data[0]
        user_plan = user_data.get('plan', 'free')
        daily_limit = MEMBERSHIP_PLANS[user_plan]['daily_limit']
        
        # 统计今日总使用次数（所有工具共享每日限制）
        today_usage_count = 0
        if response.data:
            today_usage_count = len(response.data)
        
        # 计算剩余可用次数
        remaining_daily = max(0, daily_limit - today_usage_count) if daily_limit > 0 else -1
        
        return {
            'today_usage': today_usage_count,
            'daily_limit': daily_limit,
            'remaining_daily': remaining_daily
        }
        
    except Exception as e:
        print(f"获取使用统计失败: {e}")
        return {}

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
            user_data = profile_response.data[0]
            
            # 获取使用统计
            usage_stats = get_user_usage_stats(user.id)
            
            return jsonify({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user_data.get('name', ''),
                    'plan': user_data.get('plan', 'free'),
                    'daily_limit': MEMBERSHIP_PLANS[user_data.get('plan', 'free')]['daily_limit'],
                    'created_at': user_data.get('created_at'),
                    'updated_at': user_data.get('updated_at')
                },
                'usage_stats': usage_stats
            })
        else:
            return jsonify({'error': '用户资料不存在'}), 404
            
    except Exception as e:
        return jsonify({'error': f'获取资料异常: {str(e)}'}), 500

@app.route('/debug')
def debug_page():
    """调试页面"""
    return app.send_static_file('debug_simple.html')

@app.route('/api/tools/usage-stats', methods=['GET'])
def usage_stats():
    """获取工具使用统计 - 仅基于每日次数限制"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        # 获取今日使用统计
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        response = supabase.table('tool_usage').select('*').eq('user_id', user.id).gte('created_at', today_start).execute()
        
        if response.data:
            total_usage = len(response.data)
            
            # 按工具类型统计
            tool_stats = {}
            for item in response.data:
                tool_name = item.get('tool_type', 'unknown')
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {'count': 0}
                tool_stats[tool_name]['count'] += 1
            
            return jsonify({
                'total_usage': total_usage,
                'tool_breakdown': tool_stats
            })
        else:
            return jsonify({
                'total_usage': 0,
                'tool_breakdown': {}
            })
            
    except Exception as e:
        return jsonify({'error': f'获取统计异常: {str(e)}'}), 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    print("🔍 注册的路由:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods - {'OPTIONS', 'HEAD'})}]")
    
    print("\n🚀 启动Supabase集成版应用（简化版）...")
    print(f"📊 Supabase URL: {app.config['SUPABASE_URL']}")
    print("🔧 背景移除功能：完整版（集成rembg AI模型）")
    print("🌐 访问地址: http://localhost:5000")
    print("📈 健康检查: http://localhost:5000/health")
    
    app.run(host='0.0.0.0', port=5000, debug=True)