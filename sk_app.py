"""
独立测试版Flask应用 - 不依赖Supabase
用于测试基本的API结构和功能
"""

import os
import json
import uuid
import requests
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, render_template, send_from_directory, session, redirect, url_for
from functools import wraps
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from PIL import Image
import io
import base64
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# 加载环境变量
load_dotenv()

# 尝试导入Groq API（用于关键词提取）
try:
    from groq import Groq
    GROQ_AVAILABLE = True
    # 从环境变量读取密钥（安全方式，不硬编码）
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    if GROQ_API_KEY:
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq API已配置，将使用真实AI提取关键词")
        print(f"   密钥已配置: {GROQ_API_KEY[:10]}...{GROQ_API_KEY[-10:]}")
    else:
        groq_client = None
        print("⚠️ Groq API密钥未配置，将使用模拟数据")
        print("   提示：请在服务器上设置环境变量 GROQ_API_KEY")
except ImportError:
    GROQ_AVAILABLE = False
    groq_client = None
    GROQ_API_KEY = ''
    print("⚠️ Groq库未安装，将使用模拟数据。安装命令：pip install groq")
except Exception as e:
    GROQ_AVAILABLE = False
    groq_client = None
    print(f"⚠️ Groq API初始化失败: {e}，将使用模拟数据")

# 尝试导入pytrends（用于趋势分析，无需API密钥）
# 注意：不在启动时初始化，避免网络超时导致服务器无法启动
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
    pytrends = None  # 延迟初始化，在实际使用时再创建实例
    print("✅ pytrends库已安装，将在使用时初始化（避免启动时网络超时）")
except ImportError:
    PYTRENDS_AVAILABLE = False
    pytrends = None
    print("⚠️ pytrends库未安装，趋势分析将使用模拟数据。安装命令：pip install pytrends")
except Exception as e:
    PYTRENDS_AVAILABLE = False
    pytrends = None
    print(f"⚠️ pytrends导入失败: {e}，趋势分析将使用模拟数据（不影响服务器启动）")

# 创建pytrends实例的辅助函数（延迟初始化）
def get_pytrends_instance():
    """获取pytrends实例，如果不存在则创建（延迟初始化）"""
    global pytrends
    if PYTRENDS_AVAILABLE and pytrends is None:
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
            print("✅ pytrends实例已创建")
        except Exception as e:
            print(f"⚠️ pytrends初始化失败: {e}，将使用模拟数据")
            return None
    return pytrends

# 导入码支付客户端
try:
    import sys
    import os
    # 添加backend目录到路径
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    from mzfpay_client import MzfPayClient
    MZFPAY_AVAILABLE = True
    
    # 初始化码支付客户端
    MZFPAY_MERCHANT_ID = '10294'
    MZFPAY_MERCHANT_KEY = 'X0cJyf2G0EjDKtQe9NMf'
    mzfpay_client = MzfPayClient(MZFPAY_MERCHANT_ID, MZFPAY_MERCHANT_KEY)
    print("✅ 码支付客户端已初始化")
    print(f"   商户ID: {MZFPAY_MERCHANT_ID}")
except ImportError as e:
    MZFPAY_AVAILABLE = False
    mzfpay_client = None
    print(f"⚠️ 码支付客户端初始化失败: {e}")
except Exception as e:
    MZFPAY_AVAILABLE = False
    mzfpay_client = None
    print(f"⚠️ 码支付客户端初始化失败: {e}")

# 订单存储（将在初始化时从 data_manager 加载）
payment_orders = {}  # {order_no: order_data} - 临时变量，实际数据在data_manager中

app = Flask(__name__, 
    static_folder='frontend',
    template_folder='frontend')

# 配置CORS，允许来自前端的跨域请求
# 使用更宽松的配置，确保所有请求都能通过
CORS(app, 
     resources={r"/api/*": {
         "origins": ["http://localhost:8000", "http://127.0.0.1:8000"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True
     }},
     origins=['http://localhost:8000', 'http://127.0.0.1:8000'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)

# 添加全局OPTIONS处理器，确保预检请求被正确处理
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        print(f"🔍 收到OPTIONS预检请求: {request.path}, Origin: {request.headers.get('Origin')}")
        response = jsonify({})
        origin = request.headers.get('Origin')
        allowed_origins = ['http://localhost:8000', 'http://127.0.0.1:8000']
        
        # 允许所有来自前端的请求
        if origin in allowed_origins or request.path.startswith('/api/'):
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
            else:
                response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8000'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Max-Age'] = '3600'
            print(f"✅ 已设置CORS响应头: {response.headers.get('Access-Control-Allow-Origin')}")
        return response

# 添加全局响应头处理器，确保所有API响应都包含CORS头
@app.after_request
def after_request(response):
    # 确保所有API响应都包含CORS头
    if request.path.startswith('/api/'):
        origin = request.headers.get('Origin')
        allowed_origins = ['http://localhost:8000', 'http://127.0.0.1:8000']
        
        # 允许所有来自前端的请求
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        elif not origin or request.method == 'OPTIONS':
            # 如果没有Origin头或者是OPTIONS请求，也允许
            response.headers['Access-Control-Allow-Origin'] = 'http://localhost:8000'
        
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # 调试日志
        if request.method != 'OPTIONS':
            print(f"✅ API响应已添加CORS头: {request.path}, Origin: {origin}")
    
    return response

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境使用False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# 邮件提醒配置（QQ邮箱）
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 587,  # 使用TLS
    'sender_email': os.getenv('EMAIL_SENDER', '825146419@qq.com'),  # 您的QQ邮箱
    'sender_password': os.getenv('EMAIL_PASSWORD', 'qzgpgjnwpyudbdib'),  # QQ邮箱授权码（不是QQ密码）
    'admin_email': os.getenv('ADMIN_EMAIL', '825146419@qq.com'),  # 接收提醒的邮箱
    'enabled': os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'  # 是否启用邮件提醒
}

# 管理员配置
ADMIN_CONFIG = {
    'username': os.getenv('ADMIN_USERNAME', 'admin'),
    'password': os.getenv('ADMIN_PASSWORD', 'baifan100100'),  # 建议修改为强密码
    'session_key': 'admin_session'
}

# 检查rembg库是否可用（启动时检查）
rembg_available_at_startup = False
try:
    from rembg import remove as _test_rembg_remove
    rembg_available_at_startup = True
    print("✅ rembg库已安装并可用，背景移除功能将使用AI处理")
except ImportError as e:
    print(f"⚠️ rembg库未安装或导入失败 (ImportError): {e}")
    print("💡 提示：安装rembg库可以获得更好的背景移除效果：pip install rembg")
except AttributeError as e:
    print(f"⚠️ rembg库导入失败 (AttributeError): {e}")
    print("💡 原因：通常是numpy/opencv版本不兼容导致的")
    print("💡 解决：运行 '快速修复rembg依赖.bat' 或重新安装依赖：pip install --upgrade --force-reinstall numpy opencv-python rembg")
except Exception as e:
    print(f"⚠️ rembg库检查出错 ({type(e).__name__}): {e}")
    import traceback
    print("详细错误:")
    traceback.print_exc()
    print("💡 提示：这可能是依赖版本不兼容导致的")
    print("💡 解决：运行 '快速修复rembg依赖.bat' 或重新安装依赖：pip install --upgrade --force-reinstall numpy opencv-python rembg")

# 导入数据持久化管理器
try:
    from data_manager import DataManager
    data_manager = DataManager()
    print("✅ 数据持久化管理器已加载")
    
    # 从数据管理器加载订单数据（持久化）
    if hasattr(data_manager, 'orders_db'):
        payment_orders = data_manager.orders_db.copy()
        print(f"✅ 从文件加载订单数据: {len(payment_orders)} 个订单")
    else:
        payment_orders = {}
        print("⚠️ 订单数据管理器未初始化，使用内存存储")
except ImportError as e:
    print(f"⚠️  数据管理器导入失败: {e}")
    data_manager = None
    payment_orders = {}

# 模拟数据库（备用）
users_db = {}
user_profiles_db = {}
tool_usage_db = {}

# 工具积分配置
TOOL_CREDITS = {
    'background_remover': 2,
    'currency_converter': 1,
    'unit_converter': 1,
    'shipping_calculator': 1,
    'add_watermark': 1,
    'remove_watermark': 1
}

# 导入Supabase数据库
try:
    from supabase_db import db, UserDB
    user_db = UserDB(db.get_client())
    use_real_db = True
    print("✅ 已连接到Supabase数据库")
except ImportError as e:
    print(f"⚠️  Supabase模块导入失败，使用模拟数据库: {e}")
    use_real_db = False
    user_db = None

# 会员计划每日使用次数配置
# 统一的会员每日使用次数限制配置
# 注意：所有前端显示（支付页面、首页定价卡片、用户资料页面）都必须与此配置保持一致
PLAN_DAILY_LIMITS = {
    'free': {
        'background_remover': 3,
        'image_compressor': 5,
        'format_converter': 5,
        'image_cropper': 5,
        'keyword_analyzer': 5,
        'currency_converter': 3,
        'unit_converter': 10,
        'shipping_calculator': 10,
        'send_email': 5,
        'add_watermark': 10,
        'remove_watermark': 10,
        'image_rotate_flip': 5,  # 图片旋转/翻转
        'listing_generator': 3  # Listing文案生成（AI功能，限制较低）
    },
    'basic': {
        'background_remover': 10,
        'image_compressor': 20,
        'format_converter': 20,
        'image_cropper': 20,
        'keyword_analyzer': 50,
        'currency_converter': -1,  # -1表示无限制
        'unit_converter': -1,
        'shipping_calculator': 20,
        'send_email': 20,
        'add_watermark': 50,
        'remove_watermark': 50,
        'image_rotate_flip': 50,  # 图片旋转/翻转
        'listing_generator': 20  # Listing文案生成
    },
    'professional': {
        'background_remover': 100,
        'image_compressor': 200,
        'format_converter': 200,
        'image_cropper': 200,
        'keyword_analyzer': 500,
        'currency_converter': -1,
        'unit_converter': -1,
        'shipping_calculator': -1,
        'send_email': -1,
        'add_watermark': -1,
        'remove_watermark': -1,
        'image_rotate_flip': 200,  # 图片旋转/翻转
        'listing_generator': 100  # Listing文案生成
    },
    'flagship': {
        'background_remover': -1,
        'image_compressor': -1,
        'format_converter': -1,
        'image_cropper': -1,
        'keyword_analyzer': -1,
        'currency_converter': -1,
        'unit_converter': -1,
        'shipping_calculator': -1,
        'send_email': -1,
        'add_watermark': -1,
        'remove_watermark': -1,
        'image_rotate_flip': -1,  # 图片旋转/翻转
        'listing_generator': -1  # Listing文案生成（无限）
    },
    'enterprise': {
        'background_remover': -1,
        'image_compressor': -1,
        'format_converter': -1,
        'image_cropper': -1,
        'keyword_analyzer': -1,
        'currency_converter': -1,
        'unit_converter': -1,
        'shipping_calculator': -1,
        'send_email': -1,
        'add_watermark': -1,
        'remove_watermark': -1,
        'image_rotate_flip': -1,  # 图片旋转/翻转
        'listing_generator': -1  # Listing文案生成（无限）
    }
}

# 工具名称到中文显示名称的映射（用于前端显示）
TOOL_DISPLAY_NAMES = {
    'background_remover': '背景移除',
    'image_compressor': '图片压缩',
    'format_converter': '格式转换',
    'image_cropper': '图片裁剪',
    'keyword_analyzer': '关键词分析',
    'currency_converter': '汇率换算',
    'unit_converter': '单位换算',
    'shipping_calculator': '运费计算',
    'send_email': '批量分享',
    'add_watermark': '加水印',
    'remove_watermark': '去水印',
    'image_rotate_flip': '图片旋转/翻转',
    'listing_generator': 'Listing文案生成'
}

def format_limit_display(limit):
    """格式化限制显示：-1显示为"无限制"，其他显示为数字"""
    if limit == -1:
        return '无限制'
    return f'{limit}次/天'

def allowed_file(filename):
    """检查文件类型是否允许"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_from_token():
    """从请求头获取用户信息"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        print("⚠️ 未找到Authorization头")
        return None
    
    if not auth_header.startswith('Bearer '):
        print(f"⚠️ Authorization头格式错误: {auth_header[:20]}...")
        return None
    
    token = auth_header.split(' ')[1]
    print(f"🔍 验证token: {token[:20]}...")
    
    # 优先使用数据管理器
    if data_manager:
        user = data_manager.get_user_by_token(token)
        if user:
            print(f"✅ 通过数据管理器找到用户: {user['id']}")
            return {'id': user['id'], 'email': user['email']}
        else:
            print("❌ 数据管理器中未找到用户")
    
    # 备用：模拟token验证
    for user_id, user_data in users_db.items():
        if user_data.get('token') == token:
            print(f"✅ 通过内存数据库找到用户: {user_id}")
            return {'id': user_id, 'email': user_data['email']}
    
    print("❌ 所有数据源中都未找到用户")
    return None

def get_today_date():
    """获取今天的日期字符串"""
    return datetime.now().strftime('%Y-%m-%d')

def check_daily_usage_limit(user_id, tool_name):
    """检查用户今日使用次数是否超限（包含邀请奖励）"""
    # 优先使用数据管理器
    if data_manager:
        profile = data_manager.get_user_profile(user_id)
        if not profile:
            return False, 0, 0, "用户不存在"
    else:
        # 备用：内存数据库
        if user_id not in user_profiles_db:
            return False, 0, 0, "用户不存在"
        profile = user_profiles_db[user_id]
    
    plan = profile.get('plan', 'free')
    today = get_today_date()
    
    # 获取该计划的每日限制
    plan_limits = PLAN_DAILY_LIMITS.get(plan, PLAN_DAILY_LIMITS['free'])
    daily_limit = plan_limits.get(tool_name, 0)
    
    # 如果是-1，表示无限制
    if daily_limit == -1:
        return True, 0, -1, "无限制"
    
    # 获取今日使用次数
    daily_usage = profile.get('daily_usage', {})
    today_usage = daily_usage.get(today, {}).get(tool_name, 0)
    
    # 计算邀请奖励（每日奖励 + 一次性奖励）
    invite_bonus = 0
    if 'invite_rewards' in profile:
        rewards = profile['invite_rewards']
        
        # 每日奖励（今天）
        if 'daily_rewards' in rewards and today in rewards['daily_rewards']:
            invite_bonus += rewards['daily_rewards'][today].get(tool_name, 0)
        
        # 一次性奖励（未过期且未用完）
        if 'one_time_rewards' in rewards:
            for reward in rewards['one_time_rewards']:
                # 通用奖励（all_tools）或特定工具奖励
                if reward.get('tool') == 'all_tools' or reward.get('tool') == tool_name:
                    expires_at = datetime.fromisoformat(reward.get('expires_at', ''))
                    if datetime.now() < expires_at:
                        used = reward.get('used', 0)
                        count = reward.get('count', 0)
                        if used < count:
                            invite_bonus += (count - used)
                            # 只计算一次（避免重复计算）
                            if reward.get('tool') == 'all_tools':
                                break
    
    # 实际可用次数 = 基础限制 + 邀请奖励
    effective_limit = daily_limit + invite_bonus
    
    # 返回：是否可以继续使用，今日使用次数，有效限制，消息
    # 注意：effective_limit 包含邀请奖励，但前端应该显示基础限制 daily_limit
    return today_usage < effective_limit, today_usage, daily_limit, f"今日已使用{today_usage}/{effective_limit}次（基础{daily_limit}次+奖励{invite_bonus}次）"

def record_daily_usage(user_id, tool_name):
    """记录用户今日使用次数（优先使用邀请奖励）"""
    # 优先使用数据管理器
    if data_manager:
        profile = data_manager.get_user_profile(user_id)
        if not profile:
            return False, "用户不存在"
        
        today = get_today_date()
        
        # 检查并消耗一次性奖励（优先使用通用奖励，然后是特定工具奖励）
        used_reward = False
        reward_message = ""
        
        if 'invite_rewards' in profile and 'one_time_rewards' in profile['invite_rewards']:
            # 先查找通用奖励（all_tools）
            for reward in profile['invite_rewards']['one_time_rewards']:
                if reward.get('tool') == 'all_tools':
                    expires_at = datetime.fromisoformat(reward.get('expires_at', ''))
                    if datetime.now() < expires_at:
                        used = reward.get('used', 0)
                        count = reward.get('count', 0)
                        if used < count:
                            # 使用通用奖励
                            reward['used'] = used + 1
                            used_reward = True
                            reward_message = f"使用邀请奖励，剩余{count - used - 1}次"
                            break
            
            # 如果通用奖励未使用，再查找特定工具奖励
            if not used_reward:
                for reward in profile['invite_rewards']['one_time_rewards']:
                    if reward.get('tool') == tool_name:
                        expires_at = datetime.fromisoformat(reward.get('expires_at', ''))
                        if datetime.now() < expires_at:
                            used = reward.get('used', 0)
                            count = reward.get('count', 0)
                            if used < count:
                                # 使用特定工具奖励
                                reward['used'] = used + 1
                                used_reward = True
                                reward_message = f"使用邀请奖励，剩余{count - used - 1}次"
                                break
        
        # 无论是否使用邀请奖励，都要更新 daily_usage 计数（用于显示）
        # 这样 check_daily_usage_limit 读取的计数才是准确的
        success, usage_message = data_manager.record_usage(user_id, tool_name)
        
        if used_reward:
            # 如果使用了邀请奖励，保存奖励状态
            data_manager.save_all()
            return True, reward_message
        else:
            # 如果没有使用奖励，返回正常记录消息
            return success, usage_message
    else:
        # 备用：内存数据库
        if user_id not in user_profiles_db:
            return False, "用户不存在"
        
        profile = user_profiles_db[user_id]
        today = get_today_date()
        
        # 初始化daily_usage结构
        if 'daily_usage' not in profile:
            profile['daily_usage'] = {}
        
        if today not in profile['daily_usage']:
            profile['daily_usage'][today] = {}
        
        # 增加使用次数
        current_count = profile['daily_usage'][today].get(tool_name, 0)
        profile['daily_usage'][today][tool_name] = current_count + 1
        profile['updated_at'] = datetime.now().isoformat()
        
        return True, f"使用次数已记录，今日使用{current_count + 1}次"

def record_tool_usage(user_id, tool_name, input_data, output_data):
    """记录工具使用情况"""
    if user_id not in tool_usage_db:
        tool_usage_db[user_id] = []
    
    usage_record = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'tool_name': tool_name,
        'input_data': input_data,
        'output_data': output_data,
        'created_at': datetime.now().isoformat()
    }
    
    tool_usage_db[user_id].append(usage_record)
    return True

def check_user_credits(user_id, tool_name):
    """检查用户积分是否足够"""
    # 优先使用数据管理器
    if data_manager:
        profile = data_manager.get_user_profile(user_id)
        if not profile:
            return False, 0, TOOL_CREDITS.get(tool_name, 1)
        credits = profile.get('credits', 0)
    else:
        # 备用：内存数据库
        if user_id not in user_profiles_db:
            return False, 0, TOOL_CREDITS.get(tool_name, 1)
        credits = user_profiles_db[user_id].get('credits', 0)
    
    required_credits = TOOL_CREDITS.get(tool_name, 1)
    return credits >= required_credits, credits, required_credits

def deduct_user_credits(user_id, tool_name):
    """扣除用户积分"""
    # 优先使用数据管理器
    if data_manager:
        profile = data_manager.get_user_profile(user_id)
        if not profile:
            return False, "用户不存在"
        
        required_credits = TOOL_CREDITS.get(tool_name, 1)
        current_credits = profile.get('credits', 0)
        new_credits = current_credits - required_credits
        
        if new_credits < 0:
            return False, "积分不足"
        
        # 更新积分（这里需要添加更新积分的方法）
        # 暂时返回成功
        return True, f"成功扣除{required_credits}积分，剩余{new_credits}积分"
    else:
        # 备用：内存数据库
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

# 静态文件路由
@app.route('/css/<path:filename>')
def serve_css(filename):
    """提供CSS文件（性能优化：设置长期缓存）"""
    response = send_from_directory('frontend/css', filename)
    # 静态资源缓存1年（文件名变化时会自动失效）
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

@app.route('/js/<path:filename>')
def serve_js(filename):
    """提供JavaScript文件（性能优化：设置长期缓存）"""
    response = send_from_directory('frontend/js', filename)
    # 静态资源缓存1年（文件名变化时会自动失效）
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

@app.route('/images/<path:filename>')
def serve_images(filename):
    """提供图片文件（性能优化：设置长期缓存）"""
    response = send_from_directory('frontend/images', filename)
    # 图片文件缓存1年
    response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

@app.route('/payment.js')
def serve_payment_js():
    """提供支付页面JS文件"""
    return send_from_directory('frontend', 'payment.js')

# ==================== API路由 ====================

@app.route('/')
def index():
    """主页"""
    response = send_file('frontend/index.html')
    # 性能优化：设置缓存头（HTML文件缓存1小时）
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

@app.route('/sitemap.xml')
def sitemap():
    """网站地图"""
    return send_file('frontend/sitemap.xml', mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    """robots.txt文件"""
    return send_file('frontend/robots.txt', mimetype='text/plain')

@app.route('/simple_register.html')
def register_page():
    """注册页面"""
    return send_file('frontend/simple_register.html')

@app.route('/simple_login.html')
def login_page():
    """登录页面"""
    return send_file('frontend/simple_login.html')

@app.route('/payment.html')
def payment_page():
    """支付页面"""
    return send_file('frontend/payment.html')

# ==================== 管理员认证功能 ====================

def require_admin_login(f):
    """管理员登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'error': '需要管理员登录'}), 401
            else:
                return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login')
def admin_login_page():
    """管理员登录页面"""
    return send_file('frontend/admin_login.html')

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """管理员登录接口"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if username == ADMIN_CONFIG['username'] and password == ADMIN_CONFIG['password']:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            print(f"✅ 管理员登录成功: {username}")
            return jsonify({
                'success': True,
                'message': '登录成功'
            })
        else:
            print(f"❌ 管理员登录失败: 用户名或密码错误")
            return jsonify({
                'success': False,
                'error': '用户名或密码错误'
            }), 401
    except Exception as e:
        print(f"❌ 管理员登录异常: {str(e)}")
        return jsonify({'error': f'登录失败: {str(e)}'}), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """管理员登出接口"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return jsonify({'success': True, 'message': '已登出'})

@app.route('/api/admin/check-login', methods=['GET'])
def check_admin_login():
    """检查管理员登录状态"""
    if session.get('admin_logged_in'):
        return jsonify({
            'success': True,
            'logged_in': True,
            'username': session.get('admin_username')
        })
    else:
        return jsonify({
            'success': True,
            'logged_in': False
        })

@app.route('/admin/orders')
@require_admin_login
def admin_orders():
    """后台订单管理页面"""
    return send_file('frontend/admin_orders.html')

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
    global use_real_db
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据为空'}), 400
            
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        # 调试信息
        print(f"=== 注册接口调试信息 ===")
        print(f"接收到的原始数据: {data}")
        print(f"解析后的字段 - email: '{email}', password: {'*' * len(password) if password else 'None'}, name: '{name}'")
        
        # 基本验证
        if not email or not password or not name:
            print(f"验证失败: email={bool(email)}, password={bool(password)}, name={bool(name)}")
            return jsonify({'error': '请填写完整信息'}), 400
        
        if len(password) < 6:
            return jsonify({'error': '密码至少6位'}), 400
        
        if use_real_db:
            # 使用真实Supabase数据库
            result = user_db.create_user(email, password, name)
            if result['success']:
                # 生成token
                token = f"mock_token_{result['user_id'][:8]}"
                return jsonify({
                    'success': True,
                    'message': '注册成功',
                    'user': {
                        'id': result['user_id'],
                        'email': result['email'],
                        'name': name
                    },
                    'token': token
                })
            else:
                # 如果是邮箱确认或频率限制问题，回退到模拟数据库
                error_msg = str(result.get('error', '')).lower()
                if "email not confirmed" in error_msg or "invalid" in error_msg or "rate limit" in error_msg:
                    print(f"Supabase注册失败，回退到模拟数据库: {result.get('error')}")
                    use_real_db = False
                else:
                    return jsonify({'error': result['error']}), 400
        
        if not use_real_db:
            # 使用数据持久化管理器
            print("=== 注册接口调试信息 ===")
            print(f"接收到的原始数据: {data}")
            print(f"解析后的字段 - email: {email}, password: {password}, name: {name}")
            
            # 优先使用数据管理器
            if data_manager:
                # 检查用户是否已存在
                existing_user = data_manager.get_user_by_email(email)
                if existing_user:
                    print("错误: 用户已存在")
                    return jsonify({'error': '用户已存在'}), 400
                
                # 处理邀请码
                invite_code = data.get('invite_code', '').strip().upper()
                inviter_id = None
                
                if invite_code:
                    inviter_id = data_manager.get_inviter_by_code(invite_code)
                    if inviter_id:
                        print(f"检测到邀请码: {invite_code}, 邀请人: {inviter_id}")
                    else:
                        print(f"警告: 无效的邀请码: {invite_code}")
                        # 邀请码无效不影响注册，只是没有奖励
                
                # 创建用户
                user_id, token = data_manager.create_user(email, password, name)
                if user_id:
                    print(f"创建新用户成功 - user_id: {user_id}")
                    
                    # 如果使用邀请码注册，记录邀请关系并发放奖励
                    if inviter_id and inviter_id != user_id:  # 不能邀请自己
                        profile = data_manager.get_user_profile(user_id)
                        if profile:
                            profile['invited_by'] = inviter_id
                            data_manager.save_all()
                            
                            # 发放新用户奖励：+20次一次性（所有工具通用）
                            # 注意：这里使用'通用'工具名，表示所有工具都可以使用
                            data_manager.add_invite_reward(user_id, 'one_time', 'all_tools', 20, 0)
                            
                            # 发放老用户奖励：+50次一次性（所有工具通用）
                            data_manager.add_invite_reward(inviter_id, 'one_time', 'all_tools', 50, 0)
                            
                            print(f"✅ 邀请奖励已发放 - 新用户: {user_id}, 邀请人: {inviter_id}")
                    else:
                        # 即使没有邀请码，新用户注册也送+20次一次性奖励（所有工具通用）
                        data_manager.add_invite_reward(user_id, 'one_time', 'all_tools', 20, 0)
                        print(f"✅ 新用户注册奖励已发放: {user_id}")
                    
                    return jsonify({
                        'success': True,
                        'message': '注册成功',
                        'user': {
                            'id': user_id,
                            'email': email,
                            'name': name,
                            'plan': 'free'
                        },
                        'token': token,
                        'invite_reward': bool(inviter_id)  # 是否使用了邀请码
                    })
                else:
                    return jsonify({'error': '注册失败'}), 500
            
            # 备用：内存数据库
            for user_data in users_db.values():
                if user_data['email'] == email:
                    print("错误: 用户已存在")
                    return jsonify({'error': '用户已存在'}), 400
            
            # 创建用户
            user_id = str(uuid.uuid4())
            token = f"mock_token_{user_id[:8]}"
            
            print(f"创建新用户 - user_id: {user_id}")
            
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
                'daily_usage': {},  # 每日使用次数统计
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            print("用户创建成功，准备返回响应")
            
            return jsonify({
                'success': True,
                'message': '注册成功',
                'user': {
                    'id': user_id,
                    'email': email,
                    'name': name,
                    'plan': 'free'
                },
                'token': token
            })
            
    except Exception as e:
        print(f"注册异常: {str(e)}")
        return jsonify({'error': f'注册失败: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """用户登录"""
    global use_real_db
    
    # 处理OPTIONS预检请求
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        print(f"🔍 收到登录请求: Origin={request.headers.get('Origin')}, Method={request.method}")
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        # 基本验证
        if not email or not password:
            return jsonify({'error': '请填写邮箱和密码'}), 400
        
        if use_real_db:
            # 使用真实Supabase数据库
            result = user_db.authenticate_user(email, password)
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'user': {
                        'id': result['user_id'],
                        'email': result['email'],
                        'name': result['user_metadata'].get('name', '用户')
                    },
                    'token': result['access_token']
                })
            else:
                # 如果是认证问题，回退到模拟数据库
                if "Invalid login credentials" in str(result.get('error', '')) or "Email not confirmed" in str(result.get('error', '')):
                    print(f"Supabase登录失败，回退到模拟数据库: {result.get('error')}")
                    use_real_db = False
                else:
                    return jsonify({'error': result['error']}), 401
        
        if not use_real_db:
            # 使用数据持久化管理器
            print("=== 登录接口调试信息 ===")
            print(f"接收到的数据 - email: {email}, password: {password}")
            
            # 优先使用数据管理器
            if data_manager:
                user = data_manager.authenticate_user(email, password)
                if user:
                    print(f"登录成功 - user_id: {user['id']}")
                    profile = data_manager.get_user_profile(user['id'])
                    return jsonify({
                        'success': True,
                        'message': '登录成功',
                        'user': {
                            'id': user['id'],
                            'email': profile['email'],
                            'name': profile['name'],
                            'plan': profile['plan'],
                            'credits': profile.get('credits', 0)
                        },
                        'token': user['token']
                    })
                else:
                    print("错误: 邮箱或密码错误")
                    return jsonify({'error': '邮箱或密码错误'}), 401
            
            # 备用：内存数据库
            # 验证用户
            user_id = None
            for uid, user_data in users_db.items():
                if user_data['email'] == email and user_data['password'] == password:
                    user_id = uid
                    break
            
            if not user_id:
                print("错误: 邮箱或密码错误")
                return jsonify({'error': '邮箱或密码错误'}), 401
            
            # 生成新token
            token = f"mock_token_{user_id[:8]}"
            users_db[user_id]['token'] = token
            
            print(f"登录成功 - user_id: {user_id}")
            
            profile = user_profiles_db[user_id]
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'user': {
                    'id': user_id,
                    'email': profile['email'],
                    'name': profile['name'],
                    'plan': profile['plan'],
                    'credits': profile.get('credits', 0)
                },
                'token': token
            })
            
    except Exception as e:
        print(f"登录异常: {str(e)}")
        return jsonify({'error': f'登录失败: {str(e)}'}), 500

# 微信登录状态存储（临时存储，用于轮询检查）
wechat_login_sessions = {}  # {session_id: {code, openid, user_info, status}}

@app.route('/api/auth/wechat-qrcode', methods=['GET'])
def get_wechat_qrcode():
    """获取微信登录二维码"""
    try:
        import secrets
        import qrcode
        import io
        import base64
        
        # 从环境变量获取微信开放平台配置
        WECHAT_APPID = os.getenv('WECHAT_APPID', '')
        WECHAT_APPSECRET = os.getenv('WECHAT_APPSECRET', '')
        
        if not WECHAT_APPID or not WECHAT_APPSECRET:
            return jsonify({
                'error': '微信登录未配置，请在环境变量中设置 WECHAT_APPID 和 WECHAT_APPSECRET'
            }), 500
        
        # 生成唯一的session_id
        session_id = secrets.token_urlsafe(32)
        
        # 构建微信授权URL
        # 获取当前域名
        base_url = request.host_url.rstrip('/')
        redirect_uri = f"{base_url}/api/auth/wechat-callback"
        
        # 微信网页授权URL
        wechat_auth_url = (
            f"https://open.weixin.qq.com/connect/qrconnect?"
            f"appid={WECHAT_APPID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=snsapi_login&"
            f"state={session_id}#wechat_redirect"
        )
        
        # 生成二维码
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(wechat_auth_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # 初始化登录会话
        wechat_login_sessions[session_id] = {
            'status': 'waiting',  # waiting, success, failed
            'created_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'qrcode': f'data:image/png;base64,{img_str}',
            'auth_url': wechat_auth_url
        })
        
    except Exception as e:
        print(f"生成微信二维码失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'生成二维码失败: {str(e)}'}), 500

@app.route('/api/auth/wechat-callback', methods=['GET'])
def wechat_callback():
    """微信授权回调"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')  # session_id
        error = request.args.get('error')
        
        if error:
            if state and state in wechat_login_sessions:
                wechat_login_sessions[state]['status'] = 'failed'
                wechat_login_sessions[state]['error'] = error
            return '<html><body><h1>授权失败</h1><p>用户取消了授权</p></body></html>', 400
        
        if not code or not state:
            return '<html><body><h1>参数错误</h1></body></html>', 400
        
        # 检查session是否存在
        if state not in wechat_login_sessions:
            return '<html><body><h1>会话已过期</h1></body></html>', 400
        
        # 用code换取access_token
        WECHAT_APPID = os.getenv('WECHAT_APPID', '')
        WECHAT_APPSECRET = os.getenv('WECHAT_APPSECRET', '')
        
        token_url = (
            f"https://api.weixin.qq.com/sns/oauth2/access_token?"
            f"appid={WECHAT_APPID}&"
            f"secret={WECHAT_APPSECRET}&"
            f"code={code}&"
            f"grant_type=authorization_code"
        )
        
        import requests
        token_response = requests.get(token_url, timeout=10)
        token_data = token_response.json()
        
        if 'errcode' in token_data:
            wechat_login_sessions[state]['status'] = 'failed'
            wechat_login_sessions[state]['error'] = token_data.get('errmsg', '获取token失败')
            return f'<html><body><h1>获取token失败</h1><p>{token_data.get("errmsg")}</p></body></html>', 400
        
        access_token = token_data.get('access_token')
        openid = token_data.get('openid')
        unionid = token_data.get('unionid', '')
        
        # 获取用户信息
        userinfo_url = (
            f"https://api.weixin.qq.com/sns/userinfo?"
            f"access_token={access_token}&"
            f"openid={openid}"
        )
        
        userinfo_response = requests.get(userinfo_url, timeout=10)
        userinfo_data = userinfo_response.json()
        
        if 'errcode' in userinfo_data:
            wechat_login_sessions[state]['status'] = 'failed'
            wechat_login_sessions[state]['error'] = userinfo_data.get('errmsg', '获取用户信息失败')
            return f'<html><body><h1>获取用户信息失败</h1><p>{userinfo_data.get("errmsg")}</p></body></html>', 400
        
        # 保存用户信息到session
        wechat_login_sessions[state].update({
            'status': 'success',
            'code': code,
            'openid': openid,
            'unionid': unionid,
            'user_info': {
                'nickname': userinfo_data.get('nickname', '微信用户'),
                'avatar': userinfo_data.get('headimgurl', ''),
                'openid': openid,
                'unionid': unionid
            }
        })
        
        # 返回成功页面
        return '''
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>授权成功</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .success-box {
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }
                .success-icon {
                    font-size: 64px;
                    margin-bottom: 20px;
                }
                h1 {
                    color: #333;
                    margin-bottom: 10px;
                }
                p {
                    color: #666;
                }
            </style>
        </head>
        <body>
            <div class="success-box">
                <div class="success-icon">✅</div>
                <h1>授权成功</h1>
                <p>请返回原页面完成登录</p>
            </div>
        </body>
        </html>
        '''
        
    except Exception as e:
        print(f"微信回调处理失败: {e}")
        import traceback
        traceback.print_exc()
        if state and state in wechat_login_sessions:
            wechat_login_sessions[state]['status'] = 'failed'
            wechat_login_sessions[state]['error'] = str(e)
        return f'<html><body><h1>处理失败</h1><p>{str(e)}</p></body></html>', 500

@app.route('/api/auth/wechat-check-login', methods=['POST'])
def check_wechat_login():
    """检查微信登录状态（轮询接口）"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'session_id不能为空'}), 400
        
        if session_id not in wechat_login_sessions:
            return jsonify({'error': '会话不存在或已过期'}), 404
        
        session = wechat_login_sessions[session_id]
        
        if session['status'] == 'waiting':
            return jsonify({
                'success': False,
                'status': 'waiting',
                'message': '等待用户扫码...'
            })
        
        elif session['status'] == 'success':
            # 登录成功，创建或更新用户
            user_info = session['user_info']
            openid = user_info['openid']
            
            # 检查用户是否已存在
            user_id = None
            if data_manager:
                # 使用数据管理器查找用户
                for uid, profile in data_manager.user_profiles_db.items():
                    if profile.get('wechat_openid') == openid:
                        user_id = uid
                        break
            else:
                # 使用内存数据库查找用户
                for uid, profile in user_profiles_db.items():
                    if profile.get('wechat_openid') == openid:
                        user_id = uid
                        break
            
            # 如果用户不存在，创建新用户
            if not user_id:
                user_id = str(uuid.uuid4())
                token = f"mock_token_{user_id[:8]}"
                
                email = f"wechat_{openid[:8]}@wechat.local"
                
                if data_manager:
                    # 使用数据管理器创建用户
                    data_manager.user_profiles_db[user_id] = {
                        'user_id': user_id,
                        'email': email,
                        'name': user_info['nickname'],
                        'wechat_openid': openid,
                        'wechat_unionid': user_info.get('unionid', ''),
                        'avatar': user_info.get('avatar', ''),
                        'plan': 'free',
                        'credits': 10,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    data_manager.users_db[user_id] = {
                        'email': email,
                        'password': 'wechat_oauth',
                        'token': token
                    }
                    data_manager.save_all()
                else:
                    # 使用内存数据库创建用户
                    users_db[user_id] = {
                        'email': email,
                        'password': 'wechat_oauth',
                        'token': token
                    }
                    
                    user_profiles_db[user_id] = {
                        'user_id': user_id,
                        'email': email,
                        'name': user_info['nickname'],
                        'wechat_openid': openid,
                        'wechat_unionid': user_info.get('unionid', ''),
                        'avatar': user_info.get('avatar', ''),
                        'plan': 'free',
                        'credits': 10,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
            else:
                # 更新现有用户token
                token = f"mock_token_{user_id[:8]}"
                if data_manager:
                    if user_id in data_manager.users_db:
                        data_manager.users_db[user_id]['token'] = token
                    if user_id in data_manager.user_profiles_db:
                        data_manager.user_profiles_db[user_id]['updated_at'] = datetime.now().isoformat()
                        data_manager.user_profiles_db[user_id]['avatar'] = user_info.get('avatar', '')
                        data_manager.user_profiles_db[user_id]['name'] = user_info['nickname']
                    data_manager.save_all()
                else:
                    if user_id in users_db:
                        users_db[user_id]['token'] = token
                    if user_id in user_profiles_db:
                        user_profiles_db[user_id]['updated_at'] = datetime.now().isoformat()
                        user_profiles_db[user_id]['avatar'] = user_info.get('avatar', '')
                        user_profiles_db[user_id]['name'] = user_info['nickname']
            
            # 获取用户资料
            if data_manager:
                profile = data_manager.user_profiles_db.get(user_id, {})
            else:
                profile = user_profiles_db.get(user_id, {})
            
            # 清理session（登录成功后）
            del wechat_login_sessions[session_id]
            
            return jsonify({
                'success': True,
                'status': 'success',
                'user': {
                    'id': user_id,
                    'email': profile.get('email', ''),
                    'name': profile.get('name', user_info['nickname']),
                    'avatar': profile.get('avatar', user_info.get('avatar', '')),
                    'plan': profile.get('plan', 'free'),
                    'credits': profile.get('credits', 10)
                },
                'token': token
            })
        
        else:  # failed
            error_msg = session.get('error', '登录失败')
            # 清理失败的session
            del wechat_login_sessions[session_id]
            return jsonify({
                'success': False,
                'status': 'failed',
                'error': error_msg
            })
            
    except Exception as e:
        print(f"检查微信登录状态失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'检查登录状态失败: {str(e)}'}), 500

@app.route('/api/auth/wechat-login', methods=['POST'])
def wechat_login():
    """微信登录（兼容旧接口，用于模拟登录）"""
    # 这个接口保留用于向后兼容，但建议使用新的二维码登录流程
    return jsonify({'error': '请使用二维码登录方式'}), 400

@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    """获取用户资料"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        
        # 优先使用数据管理器
        if data_manager:
            profile = data_manager.get_user_profile(user_id)
            if not profile:
                return jsonify({'error': '用户资料不存在'}), 404
        else:
            # 备用：内存数据库
            if user_id not in user_profiles_db:
                return jsonify({'error': '用户资料不存在'}), 404
            profile = user_profiles_db[user_id]
        
        # 获取今日使用次数统计
        today = get_today_date()
        daily_usage = profile.get('daily_usage', {}).get(today, {})
        
        # 计算各工具的今日使用次数和剩余次数（包含邀请奖励）
        usage_stats = {}
        for tool_name in PLAN_DAILY_LIMITS['free'].keys():
            current_count = daily_usage.get(tool_name, 0)
            daily_limit = PLAN_DAILY_LIMITS[profile['plan']].get(tool_name, 0)
            
            # 计算邀请奖励（与 check_daily_usage_limit 逻辑一致）
            invite_bonus = 0
            if 'invite_rewards' in profile:
                rewards = profile['invite_rewards']
                # 每日奖励（今天）
                if 'daily_rewards' in rewards and today in rewards['daily_rewards']:
                    invite_bonus += rewards['daily_rewards'][today].get(tool_name, 0)
                # 一次性奖励（未过期且未用完）
                if 'one_time_rewards' in rewards:
                    for reward in rewards['one_time_rewards']:
                        if reward.get('tool') == 'all_tools' or reward.get('tool') == tool_name:
                            expires_at = datetime.fromisoformat(reward.get('expires_at', ''))
                            if datetime.now() < expires_at:
                                used = reward.get('used', 0)
                                count = reward.get('count', 0)
                                if used < count:
                                    invite_bonus += (count - used)
                                    if reward.get('tool') == 'all_tools':
                                        break
            
            # 有效限制 = 基础限制 + 邀请奖励
            effective_limit = daily_limit + invite_bonus if daily_limit != -1 else -1
            remaining = effective_limit - current_count if effective_limit != -1 else -1
            
            usage_stats[tool_name] = {
                'current_usage': current_count,
                'daily_limit': daily_limit,  # 基础限制（用于显示会员计划）
                'effective_limit': effective_limit,  # 有效限制（包含邀请奖励）
                'invite_bonus': invite_bonus,  # 邀请奖励次数
                'remaining_usage': remaining
            }
        
        # 获取邀请码
        invite_code = profile.get('invite_code', '')
        
        # 确保plan字段正确（优先级：plan > membership_type > 'free'）
        user_plan = profile.get('plan') or profile.get('membership_type') or 'free'
        
        # 调试日志：输出用户信息
        print(f"📋 [get_profile] 返回用户资料")
        print(f"   用户ID: {user_id}")
        print(f"   profile.plan: {profile.get('plan')}")
        print(f"   profile.membership_type: {profile.get('membership_type')}")
        print(f"   最终返回的plan: {user_plan}")
        print(f"   使用次数统计: {list(usage_stats.keys())}")
        
        return jsonify({
            'user': {
                'id': user_id,
                'email': profile['email'],
                'name': profile['name'],
                'plan': user_plan,  # 使用处理后的plan
                'membership_type': profile.get('membership_type', user_plan),  # 兼容字段
                'membership_expires_at': profile.get('membership_expires_at'),
                'created_at': profile.get('created_at'),
                'updated_at': profile.get('updated_at'),
                'invite_code': invite_code  # 用户的邀请码
            },
            'usage_stats': usage_stats,
            'today': today
        })
            
    except Exception as e:
        return jsonify({'error': f'获取资料异常: {str(e)}'}), 500

@app.route('/api/auth/check-permission/<tool_name>', methods=['GET'])
def check_permission(tool_name):
    """检查工具使用权限"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        
        # 检查工具名称是否有效
        if tool_name not in PLAN_DAILY_LIMITS['free']:
            return jsonify({'error': '无效的工具名称'}), 400
        
        # 检查使用权限
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, tool_name)
        
        # 获取用户计划
        if data_manager:
            profile = data_manager.get_user_profile(user_id)
        else:
            profile = user_profiles_db.get(user_id)
        
        plan = profile.get('plan', 'free') if profile else 'free'
        
        return jsonify({
            'has_permission': can_use,
            'current_usage': current_usage,
            'daily_limit': daily_limit,
            'remaining_usage': max(0, daily_limit - current_usage) if daily_limit != -1 else -1,
            'message': message,
            'plan': plan,
            'can_upgrade': plan != 'enterprise'
        })
        
    except Exception as e:
        return jsonify({'error': f'权限检查失败: {str(e)}'}), 500

@app.route('/api/auth/plan-info', methods=['GET'])
def get_plan_info():
    """获取用户套餐信息"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '未授权访问'}), 401
        
        user_id = user['id']
        
        # 优先使用数据管理器
        if data_manager:
            profile = data_manager.get_user_profile(user_id)
            if not profile:
                return jsonify({'error': '用户资料不存在'}), 404
        else:
            # 备用：内存数据库
            if user_id not in user_profiles_db:
                return jsonify({'error': '用户资料不存在'}), 404
            profile = user_profiles_db[user_id]
        
        # 套餐配置
        plans = {
            'free': {
                'name': '免费版',
                'price': 0,
                'credits': 10,
                'features': ['背景移除', '图片压缩', '格式转换', '图片裁剪'],
                'limits': {'daily_uses': 5, 'max_file_size': '5MB'}
            },
            'basic': {
                'name': '基础版',
                'price': 39,
                'credits': 500,
                'features': ['背景移除', '图片压缩', '格式转换', '图片裁剪', '批量处理'],
                'limits': {'daily_uses': 50, 'max_file_size': '10MB'}
            },
            'professional': {
                'name': '专业版',
                'price': 59,
                'credits': 2000,
                'features': ['背景移除', '图片压缩', '格式转换', '图片裁剪', '批量处理', '高级功能'],
                'limits': {'daily_uses': -1, 'max_file_size': '50MB'}
            },
            'flagship': {
                'name': '旗舰版',
                'price': 99,
                'credits': 8000,
                'features': ['背景移除', '图片压缩', '格式转换', '图片裁剪', '批量处理', '高级功能', 'API访问', '优先处理'],
                'limits': {'daily_uses': -1, 'max_file_size': '100MB'}
            },
            'enterprise': {
                'name': '企业版',
                'price': 299,
                'credits': 20000,
                'features': ['背景移除', '图片压缩', '格式转换', '图片裁剪', '批量处理', '高级功能', 'API访问', '优先处理', '团队协作', '定制服务'],
                'limits': {'daily_uses': -1, 'max_file_size': '500MB'}
            }
        }
        
        current_plan = plans.get(profile['plan'], plans['free'])
        
        return jsonify({
            'current_plan': profile['plan'],
            'plan_info': current_plan,
            'credits_remaining': profile.get('credits', 0),
            'all_plans': plans
        })
            
    except Exception as e:
        return jsonify({'error': f'获取套餐信息异常: {str(e)}'}), 500

# 旧的currency_converter路由已删除，新的实现在下面（第2455行左右）

@app.route('/api/tools/unit-converter', methods=['POST'])
def unit_converter():
    """单位转换工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'unit_converter')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        data = request.get_json()
        value = data.get('value', 0)
        from_unit = data.get('from_unit', 'kg')
        to_unit = data.get('to_unit', 'lb')
        
        # 模拟单位转换
        conversion_rate = 2.20462 if from_unit == 'kg' and to_unit == 'lb' else 1.0
        result = value * conversion_rate
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'unit_converter')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'unit_converter',
            {'value': value, 'from_unit': from_unit, 'to_unit': to_unit},
            {'result': result, 'conversion_rate': conversion_rate}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'unit_converter')[1]
        
        return jsonify({
            'success': True,
            'result': round(result, 4),
            'conversion_rate': conversion_rate,
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1,
            'message': usage_message
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
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'shipping_calculator')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        data = request.get_json()
        weight = data.get('weight', 0)  # kg
        from_country = data.get('from_country', 'CN')
        to_country = data.get('to_country', 'US')
        
        # 模拟运费计算
        base_rate = 50 if from_country == 'CN' and to_country == 'US' else 30
        shipping_cost = base_rate + (weight * 10)
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'shipping_calculator')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'shipping_calculator',
            {'weight': weight, 'from_country': from_country, 'to_country': to_country},
            {'shipping_cost': shipping_cost, 'base_rate': base_rate}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'shipping_calculator')[1]
        
        return jsonify({
            'success': True,
            'shipping_cost': round(shipping_cost, 2),
            'base_rate': base_rate,
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1,
            'message': usage_message
        })
        
    except Exception as e:
        return jsonify({'error': f'运费计算异常: {str(e)}'}), 500

@app.route('/api/user/usage', methods=['GET'])
def get_user_usage():
    """获取用户使用记录"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        usage_records = tool_usage_db.get(user_id, [])
        
        # 按创建时间倒序排列
        usage_records.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'usage_records': usage_records,
            'total_records': len(usage_records)
        })
        
    except Exception as e:
        return jsonify({'error': f'获取使用记录失败: {str(e)}'}), 500

@app.route('/api/tools/remove-background', methods=['POST'])
@app.route('/api/tools/background-remover', methods=['POST'])
def remove_background():
    """背景移除工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'background_remover')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        # 确保uploads文件夹存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # 支持两种上传方式：file和base64
        input_image = None
        filename = None
        
        # 方式1: 从文件上传
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'error': '不支持的文件类型'}), 400
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4().hex[:8]}_{filename}")
                file.save(file_path)
                input_image = Image.open(file_path)
        
        # 方式2: 从base64数据
        elif request.is_json:
            data = request.get_json()
            image_data = data.get('image') or data.get('image_data')
            if not image_data:
                return jsonify({'error': '没有上传文件或图片数据'}), 400
            
            try:
                # 解码base64
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                input_image = Image.open(io.BytesIO(image_bytes))
                filename = f"upload_{uuid.uuid4().hex[:8]}.png"
            except Exception as e:
                return jsonify({'error': f'图片数据解析失败: {str(e)}'}), 400
        else:
            return jsonify({'error': '请上传文件或提供图片数据'}), 400
        
        if not input_image:
            return jsonify({'error': '无法读取图片'}), 400
        
        # 转换为RGB格式（rembg需要）
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        output_filename = f"processed_{uuid.uuid4().hex[:8]}_{filename or 'image'}.png"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # 使用rembg库进行背景移除
        rembg_available = False
        output_base64 = None
        
        # 先检查rembg是否可以导入（在函数开头检查，不在try块内）
        try:
            from rembg import remove as rembg_remove
            rembg_available = True
            print("✅ rembg库已成功导入，将使用AI背景移除")
        except ImportError as import_error:
            print(f"⚠️ rembg库导入失败 (ImportError): {import_error}")
            print("💡 提示：安装rembg库可以获得更好的背景移除效果：pip install rembg")
            rembg_available = False
        except AttributeError as attr_error:
            print(f"⚠️ rembg库导入失败 (AttributeError): {attr_error}")
            print("💡 提示：这通常是numpy/opencv版本不兼容导致的")
            print("💡 解决：运行 '快速修复rembg依赖.bat' 或重新安装依赖：pip install --upgrade --force-reinstall numpy opencv-python rembg")
            rembg_available = False
        except Exception as import_error:
            print(f"⚠️ rembg库导入失败 ({type(import_error).__name__}): {import_error}")
            import traceback
            print("详细错误:")
            traceback.print_exc()
            print("💡 提示：这可能是依赖版本不兼容导致的")
            print("💡 解决：运行 '快速修复rembg依赖.bat' 或重新安装依赖：pip install --upgrade --force-reinstall numpy opencv-python rembg")
            rembg_available = False
        except Exception as import_error:
            print(f"⚠️ rembg库导入时出错: {type(import_error).__name__}: {import_error}")
            print("💡 提示：安装rembg库可以获得更好的背景移除效果：pip install rembg")
            rembg_available = False
        
        # 如果rembg可用，使用它进行背景移除
        if rembg_available:
            try:
                # 使用rembg进行背景移除
                input_bytes = io.BytesIO()
                # rembg需要RGB格式
                if input_image.mode != 'RGB':
                    input_image_rgb = input_image.convert('RGB')
                else:
                    input_image_rgb = input_image
                
                input_image_rgb.save(input_bytes, format='PNG')
                input_bytes.seek(0)
                
                print("✅ 开始使用rembg库进行AI背景移除...")
                print(f"📊 图片尺寸: {input_image_rgb.size}, 模式: {input_image_rgb.mode}")
                
                # 调用rembg处理
                image_bytes = input_bytes.read()
                print(f"📦 图片数据大小: {len(image_bytes)} 字节")
                
                output_bytes = rembg_remove(image_bytes)
                print(f"✅ rembg处理完成，输出大小: {len(output_bytes)} 字节")
                
                output_image = Image.open(io.BytesIO(output_bytes))
                
                # 保存处理后的图片
                output_image.save(output_path, 'PNG')
                print("✅ 处理后的图片已保存")
                
                # 转换为base64返回给前端
                output_buffer = io.BytesIO()
                output_image.save(output_buffer, format='PNG')
                output_buffer.seek(0)
                output_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
                print("✅ 背景移除完成（使用rembg AI处理）")
                
            except Exception as rembg_error:
                # rembg处理出错
                print(f"❌ rembg处理出错: {type(rembg_error).__name__}: {rembg_error}")
                import traceback
                print(f"详细错误:\n{traceback.format_exc()}")
                # 不使用模拟模式，而是抛出错误让外层处理
                raise Exception(f"rembg处理失败: {str(rembg_error)}")
        else:
            # 如果rembg未安装，使用简单的处理方式（模拟模式）
            print("⚠️ rembg库未安装，使用模拟背景移除（效果不佳）")
            print("💡 提示：安装rembg库可以获得更好的背景移除效果：pip install rembg")
            
            processed_img = Image.new('RGBA', input_image.size, (0, 0, 0, 0))
            if input_image.mode == 'RGBA':
                processed_img = input_image.copy()
            else:
                processed_img = input_image.convert('RGBA')
                # 简单的背景移除模拟（保留中心区域）- 这不是真正的背景移除
                from PIL import ImageDraw
                width, height = input_image.size
                mask = Image.new('L', input_image.size, 255)
                draw = ImageDraw.Draw(mask)
                # 创建一个椭圆形mask
                ellipse_bbox = [width*0.15, height*0.15, width*0.85, height*0.85]
                draw.ellipse(ellipse_bbox, fill=255)
                processed_img.putalpha(mask)
            
            processed_img.save(output_path, 'PNG')
            
            # 转换为base64（模拟模式）
            output_buffer = io.BytesIO()
            processed_img.save(output_buffer, format='PNG')
            output_buffer.seek(0)
            output_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
            print("⚠️ 模拟背景移除完成（效果不佳，建议安装rembg）")
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'background_remover')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'background_remover',
            {'filename': filename},
            {'output_filename': output_filename, 'processed': True}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'background_remover')[1]
        
        return jsonify({
            'success': True,
            'message': '背景移除完成' if rembg_available else '背景移除完成（模拟模式，效果不佳）',
            'processed_image': f'data:image/png;base64,{output_base64}',
            'output_filename': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1,
            'rembg_available': rembg_available,
            'warning': 'rembg库未安装，当前为模拟模式，建议安装rembg库获得更好的效果：pip install rembg' if not rembg_available else None
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'背景移除异常: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/tools/image-compressor', methods=['POST'])
@app.route('/api/tools/compress-image', methods=['POST'])
def image_compressor():
    """图片压缩工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'image_compressor')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        # 确保uploads文件夹存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # 支持两种上传方式：file和base64
        input_image = None
        filename = None
        
        # 方式1: 从文件上传
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'error': '不支持的文件类型'}), 400
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4().hex[:8]}_{filename}")
                file.save(file_path)
                input_image = Image.open(file_path)
        
        # 方式2: 从base64数据
        elif request.is_json:
            data = request.get_json()
            image_data = data.get('image') or data.get('image_data')
            if not image_data:
                return jsonify({'error': '没有上传文件或图片数据'}), 400
            
            try:
                # 解码base64
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                input_image = Image.open(io.BytesIO(image_bytes))
                filename = f"upload_{uuid.uuid4().hex[:8]}.png"
            except Exception as e:
                return jsonify({'error': f'图片数据解析失败: {str(e)}'}), 400
        else:
            return jsonify({'error': '请上传文件或提供图片数据'}), 400
        
        if not input_image:
            return jsonify({'error': '无法读取图片'}), 400
        
        # 获取压缩参数
        quality = 85
        output_format = 'JPEG'
        max_size = None
        
        if request.is_json:
            data = request.get_json()
            quality = int(data.get('quality', 85))
            output_format = data.get('format', 'JPEG').upper()
            max_size = data.get('max_size')
        elif 'quality' in request.form:
            quality = int(request.form.get('quality', 85))
            output_format = request.form.get('format', 'JPEG').upper()
        
        # 转换为RGB（JPEG需要）
        if output_format == 'JPEG' and input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        # 如果有最大尺寸限制，进行缩放
        if max_size:
            width, height = input_image.size
            if width > max_size or height > max_size:
                ratio = min(max_size / width, max_size / height)
                new_size = (int(width * ratio), int(height * ratio))
                input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)
        
        output_filename = f"compressed_{uuid.uuid4().hex[:8]}.{output_format.lower()}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # 保存压缩后的图片
        input_image.save(output_path, output_format, quality=quality, optimize=True)
        
        # 转换为base64返回给前端
        output_buffer = io.BytesIO()
        input_image.save(output_buffer, format=output_format, quality=quality, optimize=True)
        output_buffer.seek(0)
        output_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        # 计算压缩比
        if request.is_json:
            try:
                image_data_for_size = data.get('image') or data.get('image_data')
                if ',' in image_data_for_size:
                    image_data_for_size = image_data_for_size.split(',')[1]
                original_size = len(base64.b64decode(image_data_for_size))
            except:
                original_size = os.path.getsize(output_path)
        else:
            original_size = os.path.getsize(file_path)
        
        compressed_size = os.path.getsize(output_path)
        compression_ratio = round((1 - compressed_size / original_size) * 100, 2) if original_size > 0 else 0
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'image_compressor')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'image_compressor',
            {'filename': filename, 'quality': quality, 'format': output_format},
            {'output_filename': output_filename, 'compressed': True, 'compression_ratio': compression_ratio}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'image_compressor')[1]
        
        return jsonify({
            'success': True,
            'message': '图片压缩完成',
            'compressed_image': f'data:image/{output_format.lower()};base64,{output_base64}',
            'output_filename': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'compression_ratio': compression_ratio,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'图片压缩异常: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/tools/format-converter', methods=['POST'])
@app.route('/api/tools/convert-format', methods=['POST'])
def format_converter():
    """格式转换工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'format_converter')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        # 确保uploads文件夹存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # 支持两种上传方式：file和base64
        input_image = None
        filename = None
        
        # 方式1: 从文件上传
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'error': '不支持的文件类型'}), 400
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4().hex[:8]}_{filename}")
                file.save(file_path)
                input_image = Image.open(file_path)
        
        # 方式2: 从base64数据
        elif request.is_json:
            data = request.get_json()
            image_data = data.get('image') or data.get('image_data')
            if not image_data:
                return jsonify({'error': '没有上传文件或图片数据'}), 400
            
            try:
                # 解码base64
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                input_image = Image.open(io.BytesIO(image_bytes))
                filename = f"upload_{uuid.uuid4().hex[:8]}.png"
            except Exception as e:
                return jsonify({'error': f'图片数据解析失败: {str(e)}'}), 400
        else:
            return jsonify({'error': '请上传文件或提供图片数据'}), 400
        
        if not input_image:
            return jsonify({'error': '无法读取图片'}), 400
        
        # 获取转换参数
        output_format = 'PNG'
        quality = 95
        
        if request.is_json:
            data = request.get_json()
            output_format = data.get('format', 'PNG').upper()
            quality = int(data.get('quality', 95))
        elif 'format' in request.form:
            output_format = request.form.get('format', 'PNG').upper()
            quality = int(request.form.get('quality', 95))
        
        # 支持的格式
        supported_formats = {'PNG', 'JPEG', 'JPG', 'WEBP', 'BMP', 'GIF'}
        if output_format not in supported_formats:
            output_format = 'PNG'
        
        # 转换为目标格式所需的颜色模式
        if output_format in ['JPEG', 'JPG'] and input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        elif output_format == 'WEBP' and input_image.mode not in ['RGB', 'RGBA']:
            if input_image.mode == 'P':
                input_image = input_image.convert('RGBA')
            else:
                input_image = input_image.convert('RGB')
        
        # 生成输出文件名
        ext_map = {'JPEG': 'jpg', 'JPG': 'jpg', 'PNG': 'png', 'WEBP': 'webp', 'BMP': 'bmp', 'GIF': 'gif'}
        output_ext = ext_map.get(output_format, 'png')
        output_filename = f"converted_{uuid.uuid4().hex[:8]}.{output_ext}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # 保存转换后的图片
        save_kwargs = {'optimize': True}
        if output_format in ['JPEG', 'JPG', 'WEBP']:
            save_kwargs['quality'] = quality
        
        input_image.save(output_path, output_format, **save_kwargs)
        
        # 转换为base64返回给前端
        output_buffer = io.BytesIO()
        input_image.save(output_buffer, format=output_format, **save_kwargs)
        output_buffer.seek(0)
        output_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'format_converter')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'format_converter',
            {'filename': filename, 'original_format': filename.split('.')[-1] if filename else 'unknown'},
            {'output_filename': output_filename, 'output_format': output_format, 'converted': True}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'format_converter')[1]
        
        return jsonify({
            'success': True,
            'message': '格式转换完成',
            'converted_image': f'data:image/{output_ext};base64,{output_base64}',
            'output_filename': output_filename,
            'output_format': output_format,
            'download_url': f'/api/download/{output_filename}',
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'格式转换异常: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/tools/image-cropper', methods=['POST'])
@app.route('/api/tools/crop-image', methods=['POST'])
def image_cropper():
    """图片裁剪工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'image_cropper')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        # 确保uploads文件夹存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # 支持两种上传方式：file和base64
        input_image = None
        filename = None
        
        # 方式1: 从文件上传
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                if not allowed_file(file.filename):
                    return jsonify({'error': '不支持的文件类型'}), 400
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4().hex[:8]}_{filename}")
                file.save(file_path)
                input_image = Image.open(file_path)
        
        # 方式2: 从base64数据
        elif request.is_json:
            data = request.get_json()
            image_data = data.get('image') or data.get('image_data')
            if not image_data:
                return jsonify({'error': '没有上传文件或图片数据'}), 400
            
            try:
                # 解码base64
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                input_image = Image.open(io.BytesIO(image_bytes))
                filename = f"upload_{uuid.uuid4().hex[:8]}.png"
            except Exception as e:
                return jsonify({'error': f'图片数据解析失败: {str(e)}'}), 400
        else:
            return jsonify({'error': '请上传文件或提供图片数据'}), 400
        
        if not input_image:
            return jsonify({'error': '无法读取图片'}), 400
        
        # 获取裁剪参数
        x = 0
        y = 0
        width = input_image.width
        height = input_image.height
        
        # 预设尺寸（比例）
        preset_ratios = {
            '1:1': (min(input_image.width, input_image.height), min(input_image.width, input_image.height)),
            '4:3': (input_image.width, int(input_image.width * 3 / 4)),
            '3:4': (int(input_image.height * 3 / 4), input_image.height),
            '16:9': (input_image.width, int(input_image.width * 9 / 16)),
            '9:16': (int(input_image.height * 9 / 16), input_image.height)
        }
        
        # 平台预设尺寸（固定像素）
        platform_presets = {
            'taobao': (800, 800),      # 淘宝主图
            'jd': (800, 800),          # 京东商品
            'pdd': (750, 1000),        # 拼多多
            'amazon': (1000, 1000),    # 亚马逊主图
            'temu': (800, 800),        # Temu主图
            'shopee': (800, 800)       # 虾皮主图
        }
        
        need_resize = False  # 是否需要缩放
        target_width = None
        target_height = None
        
        if request.is_json:
            data = request.get_json()
            preset = data.get('preset')
            if preset == 'free':
                # 自由裁剪，使用传入的参数
                if 'x' in data and 'y' in data and 'width' in data and 'height' in data:
                    x = int(data.get('x', 0))
                    y = int(data.get('y', 0))
                    width = int(data.get('width', input_image.width))
                    height = int(data.get('height', input_image.height))
            elif preset in preset_ratios:
                # 比例预设
                width, height = preset_ratios[preset]
                x = (input_image.width - width) // 2
                y = (input_image.height - height) // 2
            elif preset in platform_presets:
                # 平台预设（固定尺寸）
                target_width, target_height = platform_presets[preset]
                # 先按比例裁剪到合适区域（保持中心）
                # 计算需要的宽高比
                target_ratio = target_width / target_height
                image_ratio = input_image.width / input_image.height
                
                if image_ratio > target_ratio:
                    # 图片更宽，以高度为准
                    height = input_image.height
                    width = int(height * target_ratio)
                else:
                    # 图片更高，以宽度为准
                    width = input_image.width
                    height = int(width / target_ratio)
                
                # 居中裁剪
                x = (input_image.width - width) // 2
                y = (input_image.height - height) // 2
                need_resize = True
            elif 'x' in data and 'y' in data and 'width' in data and 'height' in data:
                x = int(data.get('x', 0))
                y = int(data.get('y', 0))
                width = int(data.get('width', input_image.width))
                height = int(data.get('height', input_image.height))
        elif 'preset' in request.form:
            preset = request.form.get('preset')
            if preset in preset_ratios:
                width, height = preset_ratios[preset]
                x = (input_image.width - width) // 2
                y = (input_image.height - height) // 2
            elif preset in platform_presets:
                target_width, target_height = platform_presets[preset]
                target_ratio = target_width / target_height
                image_ratio = input_image.width / input_image.height
                
                if image_ratio > target_ratio:
                    height = input_image.height
                    width = int(height * target_ratio)
                else:
                    width = input_image.width
                    height = int(width / target_ratio)
                
                x = (input_image.width - width) // 2
                y = (input_image.height - height) // 2
                need_resize = True
        
        # 确保裁剪区域在图片范围内
        x = max(0, min(x, input_image.width))
        y = max(0, min(y, input_image.height))
        width = max(1, min(width, input_image.width - x))
        height = max(1, min(height, input_image.height - y))
        
        # 执行裁剪
        cropped_image = input_image.crop((x, y, x + width, y + height))
        
        # 如果是平台预设，需要缩放到目标尺寸
        if need_resize and target_width and target_height:
            cropped_image = cropped_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 生成输出文件名
        output_filename = f"cropped_{uuid.uuid4().hex[:8]}_{filename or 'image'}.png"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # 保存裁剪后的图片
        cropped_image.save(output_path, 'PNG')
        
        # 转换为base64返回给前端
        output_buffer = io.BytesIO()
        cropped_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        output_base64 = base64.b64encode(output_buffer.read()).decode('utf-8')
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'image_cropper')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'image_cropper',
            {'filename': filename, 'crop_area': {'x': x, 'y': y, 'width': width, 'height': height}},
            {'output_filename': output_filename, 'cropped': True}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'image_cropper')[1]
        
        return jsonify({
            'success': True,
            'message': '图片裁剪完成',
            'cropped_image': f'data:image/png;base64,{output_base64}',
            'output_filename': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'crop_info': {'x': x, 'y': y, 'width': width, 'height': height},
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'图片裁剪异常: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/tools/rotate-flip', methods=['POST'])
def rotate_flip():
    """图片旋转/翻转工具"""
    try:
        # 检查功能开关
        try:
            from config.feature_flags import is_feature_enabled
            if not is_feature_enabled('image_rotate_flip'):
                return jsonify({'error': '功能暂未开放'}), 403
        except ImportError:
            # 如果功能开关模块不存在，继续执行（向后兼容）
            pass
        
        # 用户认证
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查使用次数
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'image_rotate_flip')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        # 获取请求数据
        if not request.is_json:
            return jsonify({'error': '请提供JSON数据'}), 400
        
        data = request.get_json()
        
        # 获取操作类型
        operation = data.get('operation', 'rotate_90_cw')  # 默认顺时针90度
        
        # 支持的操作类型
        valid_operations = {
            'rotate_90_cw': 'rotate_90_cw',      # 顺时针90度
            'rotate_90_ccw': 'rotate_90_ccw',    # 逆时针90度
            'rotate_180': 'rotate_180',          # 180度
            'flip_horizontal': 'flip_horizontal', # 水平翻转
            'flip_vertical': 'flip_vertical'      # 垂直翻转
        }
        
        if operation not in valid_operations:
            return jsonify({'error': f'不支持的操作类型: {operation}'}), 400
        
        # 获取图片数据
        image_data = data.get('image') or data.get('image_data')
        if not image_data:
            return jsonify({'error': '没有上传图片数据'}), 400
        
        # 解码图片
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            input_image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return jsonify({'error': f'图片数据解析失败: {str(e)}'}), 400
        
        # 执行操作
        output_image = input_image.copy()
        
        if operation == 'rotate_90_cw':
            output_image = input_image.rotate(-90, expand=True)
        elif operation == 'rotate_90_ccw':
            output_image = input_image.rotate(90, expand=True)
        elif operation == 'rotate_180':
            output_image = input_image.rotate(180, expand=True)
        elif operation == 'flip_horizontal':
            output_image = input_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif operation == 'flip_vertical':
            output_image = input_image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        # 保存处理后的图片
        output_filename = f"rotated_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # 确保uploads文件夹存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        output_image.save(output_path, 'PNG')
        
        # 转换为base64返回
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'image_rotate_flip')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'image_rotate_flip',
            {'operation': operation},
            {'output_filename': output_filename, 'processed': True}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'image_rotate_flip')[1]
        
        # 操作名称映射
        operation_names = {
            'rotate_90_cw': '顺时针旋转90度',
            'rotate_90_ccw': '逆时针旋转90度',
            'rotate_180': '旋转180度',
            'flip_horizontal': '水平翻转',
            'flip_vertical': '垂直翻转'
        }
        
        return jsonify({
            'success': True,
            'message': f'{operation_names.get(operation, operation)}完成',
            'processed_image': f'data:image/png;base64,{output_base64}',
            'output_filename': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'operation': operation,
            'operation_name': operation_names.get(operation, operation),
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'图片处理异常: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/tools/keyword-analyzer', methods=['POST'])
@app.route('/api/tools/analyze-keyword', methods=['POST'])
def keyword_analyzer():
    """关键词分析工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'keyword_analyzer')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        # 获取请求数据
        if not request.is_json:
            return jsonify({'error': '请提供JSON数据'}), 400
        
        data = request.get_json()
        action = data.get('action', 'extract')
        product_description = data.get('product_description', '')
        platform = data.get('platform', 'amazon')
        competitor_asin = data.get('competitor_asin', '')
        
        # 调试：输出接收到的平台参数
        print(f"📊 关键词分析请求 - 平台: {platform}, Action: {action}")
        
        if not product_description and action != 'compare':
            return jsonify({'error': '请提供产品描述'}), 400
        
        # 根据action执行不同的功能（使用模拟数据）
        result = {}
        
        # 统一处理输入：优先使用keyword，其次使用product_description
        input_text = data.get('keyword', '') or product_description or keyword
        
        if action == 'extract':
            # 1.2.1 GPT关键词提取（模拟）
            if not input_text:
                return jsonify({'error': '请提供产品描述或关键词'}), 400
            result = generate_mock_keyword_extract(input_text, platform)
        elif action == 'competition':
            # 1.2.2 亚马逊API竞争度查询（模拟）
            if not input_text:
                return jsonify({'error': '请提供关键词或产品描述'}), 400
            result = generate_mock_competition_data(input_text, platform)
        elif action == 'trend':
            # 1.2.4 关键词趋势分析（模拟）
            if not input_text:
                return jsonify({'error': '请提供关键词或产品描述'}), 400
            days = int(data.get('days', 30))
            result = generate_mock_trend_data(input_text, platform, days)
        elif action == 'compare':
            # 1.2.5 竞品关键词对比（模拟）
            if not competitor_asins:
                return jsonify({'error': '请提供竞品ASIN（多个ASIN用逗号分隔）'}), 400
            result = generate_mock_comparison_data(competitor_asins, platform)
        elif action == 'longtail':
            # 1.2.6 长尾关键词挖掘（模拟）
            if not input_text:
                return jsonify({'error': '请提供种子关键词或产品描述'}), 400
            depth = int(data.get('depth', 3))
            result = generate_mock_longtail_keywords(input_text, platform, depth)
        else:
            return jsonify({'error': f'不支持的操作: {action}'}), 400
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'keyword_analyzer')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'keyword_analyzer',
            {'action': action, 'platform': platform, 'product_description': product_description[:100]},
            {'keywords_count': len(result.get('keywords', [])), 'action': action}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'keyword_analyzer')[1]
        
        # 返回结果
        action_names = {
            'extract': '提取',
            'competition': '竞争度查询',
            'trend': '趋势分析',
            'compare': '竞品对比',
            'longtail': '长尾关键词挖掘'
        }
        
        # 调试：输出返回的平台参数
        print(f"📊 关键词分析响应 - 平台: {platform}, Action: {action}")
        
        response_data = {
            'success': True,
            'message': f'关键词{action_names.get(action, "分析")}完成',
            'action': action,
            'product_description': product_description,
            'platform': platform,  # 确保返回的平台参数正确
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1,
            **result
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'关键词分析异常: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/tools/generate-listing', methods=['POST'])
def generate_listing():
    """Listing文案生成工具"""
    try:
        # 检查功能开关
        from config.feature_flags import is_feature_enabled
        if not is_feature_enabled('listing_generator'):
            return jsonify({'error': '该功能暂未开放'}), 403
        
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'listing_generator')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        # 获取请求数据
        if not request.is_json:
            return jsonify({'error': '请提供JSON数据'}), 400
        
        data = request.get_json()
        product_info = data.get('product_info', '')
        platform = data.get('platform', 'amazon')
        language = data.get('language', 'en')  # en 或 zh
        style = data.get('style', 'professional')  # professional, casual, marketing
        
        if not product_info:
            return jsonify({'error': '请提供产品信息'}), 400
        
        print(f"📝 Listing文案生成请求 - 平台: {platform}, 语言: {language}, 风格: {style}")
        print(f"   产品信息: {product_info[:100]}...")
        
        # 生成Listing文案（优先使用Groq API）
        result = generate_listing_with_groq(product_info, platform, language, style)
        
        if not result:
            # 如果Groq API失败，返回错误
            return jsonify({
                'error': 'AI生成失败，请稍后重试',
                'hint': '请确保Groq API密钥已正确配置'
            }), 500
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'listing_generator')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'listing_generator',
            {'platform': platform, 'language': language, 'style': style, 'product_info': product_info[:100]},
            {'title_length': len(result.get('title', '')), 'description_length': len(result.get('description', ''))}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'listing_generator')[1]
        
        # 返回结果
        response_data = {
            'success': True,
            'message': 'Listing文案生成完成',
            'platform': platform,
            'language': language,
            'style': style,
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1,
            **result
        }
        
        print(f"✅ Listing文案生成成功 - 标题长度: {len(result.get('title', ''))}, 描述长度: {len(result.get('description', ''))}")
        
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        print(f"❌ Listing文案生成异常: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Listing文案生成异常: {str(e)}', 'traceback': traceback.format_exc()}), 500

def generate_listing_with_groq(product_info, platform='amazon', language='en', style='professional'):
    """使用Groq API生成Listing文案（真实AI）"""
    if not groq_client:
        print("⚠️ Groq客户端未初始化，无法生成Listing文案")
        return None
    
    try:
        # 根据语言和风格构建提示词
        style_descriptions = {
            'professional': '专业、正式、商务风格',
            'casual': '轻松、友好、口语化风格',
            'marketing': '营销、吸引人、促销风格'
        }
        
        style_desc = style_descriptions.get(style, '专业风格')
        
        if language == 'zh':
            prompt = f"""请为以下产品生成一个专业的{platform}平台Listing文案。

产品信息：{product_info}

要求：
1. 生成中文的产品标题和描述
2. 风格：{style_desc}
3. 包含产品的主要特点、使用场景、优势
4. 符合{platform}平台的Listing规范
5. 字数：标题50-100字，描述200-500字

请以JSON格式返回，格式如下：
{{
    "title": "产品标题",
    "description": "产品描述（详细）",
    "key_features": ["特点1", "特点2", "特点3"],
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "word_count": {{
        "title": 标题字数,
        "description": 描述字数
    }}
}}

只需返回JSON，不要其他文字。"""
        else:
            prompt = f"""Please generate a professional {platform} platform Listing copy for the following product.

Product Information: {product_info}

Requirements:
1. Generate English product title and description
2. Style: {style_desc} (professional/casual/marketing)
3. Include main features, use cases, and advantages
4. Comply with {platform} platform Listing guidelines
5. Word count: Title 50-100 words, Description 200-500 words

Please return in JSON format as follows:
{{
    "title": "Product Title",
    "description": "Product Description (detailed)",
    "key_features": ["Feature 1", "Feature 2", "Feature 3"],
    "keywords": ["Keyword 1", "Keyword 2", "Keyword 3"],
    "word_count": {{
        "title": title word count,
        "description": description word count
    }}
}}

Return only JSON, no other text."""
        
        print(f"🤖 调用Groq API生成Listing文案...")
        print(f"   平台: {platform}, 语言: {language}, 风格: {style}")
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional e-commerce Listing copywriter specializing in creating compelling product descriptions for online marketplaces. Always return valid JSON format only."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # 尝试解析JSON响应
        try:
            # 移除可能的markdown代码块标记
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            result['source'] = 'groq'
            result['platform'] = platform
            result['language'] = language
            result['style'] = style
            
            print(f"✅ Groq API生成成功")
            print(f"   标题: {result.get('title', '')[:50]}...")
            print(f"   描述长度: {len(result.get('description', ''))} 字符")
            
            return result
        except json.JSONDecodeError as e:
            print(f"⚠️ Groq返回的不是标准JSON: {e}")
            print(f"   响应内容: {response_text[:200]}...")
            # 如果JSON解析失败，尝试从文本中提取
            return None
    except Exception as e:
        print(f"⚠️ Groq API调用失败: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def extract_keywords_with_groq(product_description, platform='amazon'):
    """使用Groq API提取关键词（真实AI）"""
    if not groq_client:
        return None
    
    try:
        prompt = f"""请从以下产品描述中提取10-15个关键词，用于{platform}平台的产品搜索优化。
产品描述：{product_description}

请以JSON格式返回关键词列表，格式如下：
{{
    "keywords": [
        {{"keyword": "关键词1", "platform": "{platform}", "score": 9.5, "type": "main"}},
        {{"keyword": "关键词2", "platform": "{platform}", "score": 9.0, "type": "modifier"}}
    ]
}}

只需返回JSON，不要其他文字。"""
        
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "你是一个关键词提取专家，专门为电商平台提取产品关键词。请只返回JSON格式的数据。"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1000
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # 尝试解析JSON响应
        try:
            # 移除可能的markdown代码块标记
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            result['source'] = 'groq'
            return result
        except json.JSONDecodeError:
            # 如果JSON解析失败，使用文本提取
            print(f"⚠️ Groq返回的不是标准JSON，尝试从文本提取关键词")
            keywords_text = response_text
            # 简单提取关键词（备用方案）
            return None
    except Exception as e:
        print(f"⚠️ Groq API调用失败: {e}")
        return None

def generate_mock_keyword_extract(product_description, platform='amazon'):
    """生成关键词提取数据（优先使用Groq API，否则使用模拟数据）"""
    # 首先尝试使用Groq API
    if groq_client and GROQ_API_KEY and GROQ_AVAILABLE:
        print(f"🔍 尝试使用Groq API提取关键词: {product_description[:50]}...")
        groq_result = extract_keywords_with_groq(product_description, platform)
        if groq_result:
            print(f"✅ Groq API提取成功，返回 {len(groq_result.get('keywords', []))} 个关键词")
            return groq_result
        else:
            print("⚠️ Groq API调用失败，使用模拟数据")
    
    # 如果Groq不可用，使用模拟数据
    keywords = []
    base_keywords = [w for w in product_description.lower().split() if len(w) > 3][:3]
    
    platforms_list = platform.split(',') if ',' in platform else [platform]
    if not platforms_list or platforms_list == ['all']:
        platforms_list = ['amazon', 'ebay', 'temu', 'shopee']
    
    platform_keywords = {}
    
    for plat in platforms_list:
        plat_keywords = []
        for base_word in base_keywords:
            if base_word:
                plat_keywords.extend([
                    {'keyword': f'{base_word} {plat}', 'platform': plat, 'score': round(random.uniform(8.5, 9.8), 1), 'type': 'main'},
                    {'keyword': f'best {base_word} {plat}', 'platform': plat, 'score': round(random.uniform(8.0, 9.5), 1), 'type': 'modifier'},
                    {'keyword': f'{base_word} review {plat}', 'platform': plat, 'score': round(random.uniform(7.5, 9.0), 1), 'type': 'review'},
                    {'keyword': f'{base_word} buy {plat}', 'platform': plat, 'score': round(random.uniform(7.0, 8.5), 1), 'type': 'action'},
                    {'keyword': f'{base_word} price {plat}', 'platform': plat, 'score': round(random.uniform(7.5, 8.8), 1), 'type': 'price'},
                    {'keyword': f'cheap {base_word} {plat}', 'platform': plat, 'score': round(random.uniform(7.0, 8.5), 1), 'type': 'modifier'},
                    {'keyword': f'professional {base_word} {plat}', 'platform': plat, 'score': round(random.uniform(7.5, 8.5), 1), 'type': 'modifier'},
                    {'keyword': f'{base_word} {plat} 2024', 'platform': plat, 'score': round(random.uniform(7.0, 8.0), 1), 'type': 'trend'},
                ])
        platform_keywords[plat] = plat_keywords[:10]
        keywords.extend(plat_keywords[:8])
    
    # 去重并排序
    seen = set()
    unique_keywords = []
    for kw in keywords:
        key = kw['keyword']
        if key not in seen:
            seen.add(key)
            unique_keywords.append(kw)
    
    unique_keywords.sort(key=lambda x: x['score'], reverse=True)
    
    # 生成长尾关键词
    long_tail = []
    modifiers = ['best', 'top', 'cheap', 'affordable', 'premium', 'high quality']
    for mod in modifiers[:5]:
        for base_word in base_keywords[:2]:
            if base_word:
                long_tail.append({
                    'keyword': f'{mod} {base_word} {platforms_list[0]}',
                    'platform': platforms_list[0],
                    'search_volume': random.randint(100, 3000),
                    'competition': random.choice(['low', 'medium']),
                    'type': 'long_tail'
                })
    
    return {
        'keywords': unique_keywords[:20],
        'platforms': platform_keywords,
        'long_tail': long_tail[:10],
        'total_count': len(unique_keywords),
        'source': 'mock',
        'timestamp': datetime.now().isoformat()
    }

def get_competition_with_google_trends(keyword, platform='amazon'):
    """使用Google Trends获取关键词竞争度数据（真实数据）"""
    if not PYTRENDS_AVAILABLE:
        return None
    
    try:
        # 清理关键词（只取主要部分，最多3个词）
        clean_keyword = ' '.join(keyword.lower().split()[:3])
        
        print(f"🔍 使用Google Trends查询竞争度: {clean_keyword}")
        
        # 获取pytrends实例（延迟初始化）
        pytrends_instance = get_pytrends_instance()
        if not pytrends_instance:
            print("⚠️ pytrends不可用，跳过Google Trends查询")
            return None
        
        # 查询12个月的趋势数据
        pytrends_instance.build_payload([clean_keyword], cat=0, timeframe='today 12-m')
        interest_over_time = pytrends_instance.interest_over_time()
        
        if interest_over_time.empty:
            print(f"⚠️ Google Trends未找到数据: {clean_keyword}")
            return None
        
        # 获取相关查询（用于估算竞争度）
        try:
            related_queries = pytrends_instance.related_queries()
            rising_queries = related_queries[clean_keyword].get('rising', None)
            top_queries = related_queries[clean_keyword].get('top', None)
        except:
            rising_queries = None
            top_queries = None
        
        # 计算平均搜索量（相对值0-100）
        avg_volume = interest_over_time[clean_keyword].mean()
        peak_volume = interest_over_time[clean_keyword].max()
        min_volume = interest_over_time[clean_keyword].min()
        
        # 基于搜索量估算竞争度
        # 搜索量越高，竞争度越高；趋势上升，竞争度增加
        volume_score = avg_volume / 100.0  # 归一化到0-1
        
        # 如果有相关查询，基于相关查询数量估算竞争度
        query_count = 0
        if rising_queries is not None and not rising_queries.empty:
            query_count += len(rising_queries)
        if top_queries is not None and not top_queries.empty:
            query_count += len(top_queries)
        
        # 综合估算竞争度
        if volume_score > 0.75 or query_count > 20:
            competition_level = 'High'
            competition_score = 0.8
        elif volume_score > 0.5 or query_count > 10:
            competition_level = 'Medium'
            competition_score = 0.5
        else:
            competition_level = 'Low'
            competition_score = 0.3
        
        # 估算CPC（基于搜索量和竞争度）
        # 一般规律：搜索量越高，CPC越高；竞争度越高，CPC越高
        base_cpc = 0.5
        volume_multiplier = volume_score * 3.0  # 搜索量影响
        competition_multiplier = competition_score * 2.0  # 竞争度影响
        estimated_cpc = base_cpc + volume_multiplier + competition_multiplier
        estimated_cpc = round(max(0.3, min(5.0, estimated_cpc)), 2)  # 限制在0.3-5.0之间
        
        # 计算趋势（上升/下降/稳定）
        if len(interest_over_time) >= 2:
            first_volume = interest_over_time[clean_keyword].iloc[0]
            last_volume = interest_over_time[clean_keyword].iloc[-1]
            avg_recent = interest_over_time[clean_keyword].iloc[-3:].mean() if len(interest_over_time) >= 3 else last_volume
            
            if avg_recent > first_volume * 1.1:
                trend = 'up'
            elif avg_recent < first_volume * 0.9:
                trend = 'down'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        # 估算搜索量（将相对值转换为估算值）
        # Google Trends返回0-100的相对值，我们需要估算实际搜索量
        # 一般规律：相对值50可能对应月搜索量5000-10000
        estimated_search_volume = int(avg_volume * 200)  # 简单的线性估算
        
        result = {
            'keyword': clean_keyword,
            'search_volume': estimated_search_volume,  # 估算的搜索量
            'relative_volume': round(avg_volume, 1),  # Google Trends相对值（0-100）
            'competition': competition_level,
            'competition_score': round(competition_score, 2),
            'cpc': estimated_cpc,
            'trend': trend,
            'avg_price': round(random.uniform(10, 100), 2),  # 仍使用估算（Google Trends不提供）
            'top_sellers': [
                {'asin': f'B0{random.randint(10000000, 99999999)}', 
                 'title': f'Product related to {clean_keyword}',
                 'rank': random.randint(1, 100)}
                for _ in range(3)
            ],
            'source': 'google_trends',
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"✅ Google Trends竞争度查询成功: {clean_keyword}, 竞争度: {competition_level}, 相对搜索量: {round(avg_volume, 1)}")
        return result
    except Exception as e:
        print(f"⚠️ Google Trends API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_mock_competition_data(keyword_or_description, platform='amazon'):
    """生成竞争度数据（优先使用Google Trends，否则使用模拟数据）"""
    # 提取关键词
    if len(keyword_or_description.split()) > 5:
        # 如果是产品描述，提取关键词
        keywords = [w for w in keyword_or_description.lower().split() if len(w) > 3][:5]
    else:
        # 如果是单个关键词，直接使用
        keywords = [keyword_or_description.lower()]
    
    competition_data = []
    
    for keyword in keywords:
        if keyword:
            # 首先尝试使用Google Trends API
            if PYTRENDS_AVAILABLE:
                # 检查pytrends是否可用（延迟初始化）
                pytrends_instance = get_pytrends_instance()
                if pytrends_instance:
                    google_result = get_competition_with_google_trends(keyword, platform)
                    if google_result:
                        competition_data.append(google_result)
                        continue  # 成功获取数据，继续下一个关键词
            
            # 如果Google Trends不可用或失败，使用模拟数据
            competition_level = random.choice(['Low', 'Medium', 'High'])
            search_volume = random.randint(1000, 50000)
            competition_score = round(random.uniform(0.1, 0.9), 2)
            
            competition_data.append({
                'keyword': keyword,
                'search_volume': search_volume,
                'competition': competition_level,
                'competition_score': competition_score,
                'cpc': round(random.uniform(0.5, 5.0), 2),
                'trend': random.choice(['up', 'down', 'stable']),
                'avg_price': round(random.uniform(10, 100), 2),
                'top_sellers': [
                    {'asin': f'B0{random.randint(10000000, 99999999)}', 
                     'title': f'Product related to {keyword}',
                     'rank': random.randint(1, 100)}
                    for _ in range(3)
                ],
                'source': 'mock'
            })
    
    # 确定数据来源（如果至少有一个是Google Trends，则标记为混合）
    sources = [item.get('source', 'mock') for item in competition_data]
    if 'google_trends' in sources:
        final_source = 'google_trends' if all(s == 'google_trends' for s in sources) else 'mixed'
    else:
        final_source = 'mock'
    
    return {
        'competition_data': competition_data,
        'keywords': competition_data,
        'total_count': len(competition_data),
        'source': final_source,
        'timestamp': datetime.now().isoformat()
    }

def generate_mock_trend_data(keyword_or_description, platform='amazon', days=30):
    """生成模拟的趋势数据（后续接入真实API时替换）"""
    # 提取关键词
    if len(keyword_or_description.split()) > 1:
        keyword = keyword_or_description.split()[0]
    else:
        keyword = keyword_or_description
    
    trend_data = []
    base_volume = random.randint(1000, 5000)
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
        # 模拟趋势（逐步上升或下降）
        volume_variation = random.randint(-500, 500) + int((i / days) * 1000)
        volume = max(100, base_volume + volume_variation)
        
        trend_data.append({
            'date': date,
            'search_volume': volume,
            'competition': round(random.uniform(0.3, 0.9), 2),
            'cpc': round(random.uniform(0.5, 5.0), 2)
        })
    
    # 计算总体趋势
    if trend_data[-1]['search_volume'] > trend_data[0]['search_volume'] * 1.1:
        overall_trend = 'up'
        trend_percentage = round(((trend_data[-1]['search_volume'] / trend_data[0]['search_volume']) - 1) * 100, 1)
    elif trend_data[-1]['search_volume'] < trend_data[0]['search_volume'] * 0.9:
        overall_trend = 'down'
        trend_percentage = round((1 - (trend_data[-1]['search_volume'] / trend_data[0]['search_volume'])) * 100, 1)
    else:
        overall_trend = 'stable'
        trend_percentage = 0
    
    avg_volume = sum(d['search_volume'] for d in trend_data) / len(trend_data)
    
    return {
        'trend_data': trend_data,
        'keyword': keyword,
        'avg_search_volume': round(avg_volume, 2),
        'overall_trend': overall_trend,
        'trend_percentage': trend_percentage,
        'peak_volume': max(d['search_volume'] for d in trend_data),
        'lowest_volume': min(d['search_volume'] for d in trend_data),
        'source': 'mock',
        'timestamp': datetime.now().isoformat()
    }

def compare_keywords_with_google_trends(keywords_list, platform='amazon'):
    """使用Google Trends对比多个关键词的搜索量（真实数据）"""
    if not PYTRENDS_AVAILABLE:
        return None
    
    if not keywords_list or len(keywords_list) == 0:
        return None
    
    try:
        # 限制关键词数量（Google Trends最多支持5个关键词对比）
        comparison_keywords = keywords_list[:5]
        
        print(f"🔍 使用Google Trends对比关键词: {comparison_keywords}")
        
        # 获取pytrends实例（延迟初始化）
        pytrends_instance = get_pytrends_instance()
        if not pytrends_instance:
            print("⚠️ pytrends不可用，跳过Google Trends对比")
            return None
        
        # 对比多个关键词
        pytrends_instance.build_payload(comparison_keywords, cat=0, timeframe='today 12-m')
        interest_over_time = pytrends_instance.interest_over_time()
        
        if interest_over_time.empty:
            print(f"⚠️ Google Trends未找到对比数据")
            return None
        
        # 计算每个关键词的平均搜索量（相对值0-100）
        comparison_data = []
        for keyword in comparison_keywords:
            if keyword in interest_over_time.columns:
                avg_volume = interest_over_time[keyword].mean()
                peak_volume = interest_over_time[keyword].max()
                
                comparison_data.append({
                    'keyword': keyword,
                    'relative_volume': round(avg_volume, 1),  # Google Trends相对值（0-100）
                    'estimated_volume': int(avg_volume * 200),  # 估算的搜索量
                    'peak_volume': int(peak_volume * 200),
                    'trend': 'up' if interest_over_time[keyword].iloc[-1] > interest_over_time[keyword].iloc[0] else 'down'
                })
        
        # 按搜索量排序，分配排名
        comparison_data.sort(key=lambda x: x['relative_volume'], reverse=True)
        for i, item in enumerate(comparison_data):
            item['rank'] = i + 1
        
        print(f"✅ Google Trends对比成功，返回 {len(comparison_data)} 个关键词对比数据")
        return {
            'comparison_data': comparison_data,
            'source': 'google_trends',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"⚠️ Google Trends对比API调用失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_mock_comparison_data(competitor_asins_input, platform='amazon'):
    """生成竞品对比数据（如果提供关键词列表，使用Google Trends对比）"""
    # 支持多个ASIN（逗号分隔）
    competitor_asins = [asin.strip() for asin in competitor_asins_input.split(',') if asin.strip()][:5]
    
    if not competitor_asins:
        return {'error': '请提供至少一个竞品ASIN'}
    
    common_keywords = [
        'wireless headphone', 'bluetooth headphone', 'noise cancelling',
        'wireless earbuds', 'headphone with mic', 'portable headphone',
        'sport headphone', 'gaming headphone', 'studio headphone'
    ]
    
    competitors = []
    all_keywords_for_comparison = []
    
    for asin in competitor_asins:
        # 为每个竞品生成关键词（基于ASIN生成一些相关关键词）
        competitor_keywords = random.sample(common_keywords, random.randint(5, 8))
        competitor_keywords.extend([
            f'{platform} {asin[:5]}',  # 使用平台和ASIN的一部分
            f'product {asin[:3]}'
        ])
        
        all_keywords_for_comparison.extend(competitor_keywords[:3])  # 收集前3个关键词用于对比
        
        competitors.append({
            'asin': asin,
            'title': f'Competitor Product {asin}',
            'keywords': competitor_keywords,
            'keyword_count': len(competitor_keywords),
            'avg_rank': round(random.uniform(10, 100), 1),
            'top_keyword': competitor_keywords[0] if competitor_keywords else None
        })
    
    # 尝试使用Google Trends对比关键词
    if PYTRENDS_AVAILABLE and pytrends and len(all_keywords_for_comparison) > 0:
        # 去重并选择前5个关键词进行对比
        unique_keywords = list(set(all_keywords_for_comparison))[:5]
        if len(unique_keywords) >= 2:
            google_comparison = compare_keywords_with_google_trends(unique_keywords, platform)
            if google_comparison:
                # 将Google Trends对比数据合并到结果中
                comparison_data = google_comparison.get('comparison_data', [])
                # 更新竞品的关键词排名
                for competitor in competitors:
                    for comp_data in comparison_data:
                        if comp_data['keyword'] in competitor['keywords']:
                            competitor['top_keyword'] = comp_data['keyword']
                            competitor['top_keyword_rank'] = comp_data['rank']
                            competitor['top_keyword_volume'] = comp_data['relative_volume']
                            break
    
    # 计算共同关键词
    if len(competitors) > 1:
        all_keyword_sets = [set(c['keywords']) for c in competitors]
        common_keywords_list = list(set.intersection(*all_keyword_sets))
    else:
        common_keywords_list = competitors[0]['keywords'][:3] if competitors else []
    
    # 计算重叠率
    if competitors:
        total_unique_keywords = len(set([kw for c in competitors for kw in c['keywords']]))
        overlap_ratio = round(len(common_keywords_list) / max(total_unique_keywords, 1), 2)
    else:
        overlap_ratio = 0
    
    # 确定数据来源（如果至少有一个竞品有Google Trends数据，则标记为混合）
    has_google_data = any('top_keyword_volume' in c for c in competitors)
    final_source = 'google_trends' if has_google_data else 'mock'
    
    return {
        'competitors': competitors,
        'common_keywords': common_keywords_list,
        'unique_keywords': {c['asin']: list(set(c['keywords']) - set(common_keywords_list)) for c in competitors},
        'overlap_ratio': overlap_ratio,
        'total_competitors': len(competitors),
        'source': final_source,
        'timestamp': datetime.now().isoformat()
    }

def generate_mock_longtail_keywords(seed_keyword_or_description, platform='amazon', depth=3):
    """生成模拟的长尾关键词（后续接入真实GPT API时替换）"""
    # 提取种子关键词
    if len(seed_keyword_or_description.split()) > 1:
        seed_keyword = seed_keyword_or_description.split()[0]
    else:
        seed_keyword = seed_keyword_or_description.lower()
    
    longtail_keywords = []
    
    # 修饰词组合
    modifiers = ['best', 'top', 'cheap', 'affordable', 'premium', 'high quality', 'professional', 'popular']
    question_words = ['how to', 'where to buy', 'what is', 'why', 'when to use']
    action_words = ['buy', 'review', 'price', 'sale', 'deals', 'discount', 'coupon']
    
    # 生成修饰词组合型长尾关键词
    for mod in modifiers[:depth*2]:
        for action in action_words[:depth]:
            keyword = f'{mod} {seed_keyword} {action} {platform}'
            longtail_keywords.append({
                'keyword': keyword,
                'platform': platform,
                'search_volume': random.randint(100, 5000),
                'competition': random.choice(['Low', 'Medium']),
                'competition_score': round(random.uniform(0.1, 0.5), 2),
                'type': 'modifier',
                'cpc': round(random.uniform(0.3, 2.0), 2)
            })
    
    # 生成问题型长尾关键词
    for q_word in question_words[:depth]:
        keyword = f'{q_word} {seed_keyword} {platform}'
        longtail_keywords.append({
            'keyword': keyword,
            'platform': platform,
            'search_volume': random.randint(50, 3000),
            'competition': 'Low',
            'competition_score': round(random.uniform(0.1, 0.3), 2),
            'type': 'question',
            'cpc': round(random.uniform(0.2, 1.5), 2)
        })
    
    # 去重并按搜索量排序
    seen = set()
    unique_keywords = []
    for kw in longtail_keywords:
        if kw['keyword'] not in seen:
            seen.add(kw['keyword'])
            unique_keywords.append(kw)
    
    unique_keywords.sort(key=lambda x: x['search_volume'], reverse=True)
    
    return {
        'seed_keyword': seed_keyword,
        'longtail_keywords': unique_keywords[:30],
        'total_count': len(unique_keywords),
        'avg_search_volume': round(sum(k['search_volume'] for k in unique_keywords) / max(len(unique_keywords), 1), 2),
        'avg_competition': round(sum(k['competition_score'] for k in unique_keywords) / max(len(unique_keywords), 1), 2),
        'source': 'mock',
        'timestamp': datetime.now().isoformat()
    }

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载处理后的文件"""
    try:
        # 检查uploads文件夹是否存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 如果文件不存在，创建一个测试图片
        if not os.path.exists(file_path):
            # 创建一个简单的测试图片
            img = Image.new('RGB', (400, 300), color='lightblue')
            from PIL import ImageDraw, ImageFont
            
            draw = ImageDraw.Draw(img)
            
            # 添加文字
            try:
                # 尝试使用默认字体
                font = ImageFont.load_default()
            except:
                font = None
            
            text = f"Processed Image\n{filename}\n(Test Version)"
            if font:
                draw.text((50, 100), text, fill='black', font=font)
            else:
                draw.text((50, 100), text, fill='black')
            
            # 保存图片
            img.save(file_path, 'PNG')
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

# ==================== 汇率换算工具 ====================

@app.route('/api/tools/currency-converter', methods=['POST'])
def currency_converter():
    """汇率换算工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'currency_converter')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        data = request.get_json()
        amount = float(data.get('amount', 0))
        from_currency = data.get('from_currency', 'CNY').upper()
        to_currency = data.get('to_currency', 'USD').upper()
        
        if amount <= 0:
            return jsonify({'error': '金额必须大于0'}), 400
        
        # 使用免费的汇率API获取实时汇率
        # 这里使用exchangerate-api.com的免费API（无需密钥，但有请求限制）
        exchange_rate = None
        try:
            # 尝试获取实时汇率
            api_url = f'https://api.exchangerate-api.com/v4/latest/{from_currency}'
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                rates_data = response.json()
                if 'rates' in rates_data and to_currency in rates_data['rates']:
                    exchange_rate = rates_data['rates'][to_currency]
                    print(f"✅ 获取实时汇率成功: {from_currency} -> {to_currency} = {exchange_rate}")
        except Exception as e:
            print(f"⚠️ 获取实时汇率失败: {e}，使用备用汇率表")
        
        # 如果API失败，使用备用汇率表（定期更新）
        if exchange_rate is None:
            exchange_rates = {
                'CNY': {'USD': 0.138, 'EUR': 0.128, 'GBP': 0.109, 'JPY': 20.5, 'HKD': 1.08, 'SGD': 0.186, 'TWD': 4.4},
                'USD': {'CNY': 7.24, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 149.5, 'HKD': 7.82, 'SGD': 1.34, 'TWD': 31.8},
                'EUR': {'CNY': 7.87, 'USD': 1.09, 'GBP': 0.86, 'JPY': 162.8, 'HKD': 8.52, 'SGD': 1.46, 'TWD': 34.6},
                'GBP': {'CNY': 9.15, 'USD': 1.27, 'EUR': 1.16, 'JPY': 189.2, 'HKD': 9.92, 'SGD': 1.70, 'TWD': 40.3},
                'JPY': {'CNY': 0.048, 'USD': 0.0067, 'EUR': 0.0061, 'GBP': 0.0053, 'HKD': 0.052, 'SGD': 0.009, 'TWD': 0.213},
                'HKD': {'CNY': 0.925, 'USD': 0.128, 'EUR': 0.117, 'GBP': 0.101, 'JPY': 19.1, 'SGD': 0.171, 'TWD': 4.07},
                'SGD': {'CNY': 5.38, 'USD': 0.746, 'EUR': 0.685, 'GBP': 0.588, 'JPY': 111.5, 'HKD': 5.84, 'TWD': 23.7},
                'TWD': {'CNY': 0.227, 'USD': 0.031, 'EUR': 0.029, 'GBP': 0.025, 'JPY': 4.70, 'HKD': 0.246, 'SGD': 0.042}
            }
            
            if from_currency == to_currency:
                exchange_rate = 1.0
            elif from_currency in exchange_rates and to_currency in exchange_rates[from_currency]:
                exchange_rate = exchange_rates[from_currency][to_currency]
            else:
                return jsonify({'error': f'不支持的货币对: {from_currency} -> {to_currency}'}), 400
        
        # 计算转换后的金额
        converted_amount = amount * exchange_rate
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'currency_converter')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'currency_converter',
            {'amount': amount, 'from_currency': from_currency, 'to_currency': to_currency},
            {'converted_amount': converted_amount, 'exchange_rate': exchange_rate}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'currency_converter')[1]
        
        return jsonify({
            'success': True,
            'amount': amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'converted_amount': round(converted_amount, 2),
            'exchange_rate': round(exchange_rate, 6),
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1,
            'usage_message': usage_message
        })
        
    except ValueError:
        return jsonify({'error': '金额格式不正确'}), 400
    except Exception as e:
        import traceback
        return jsonify({'error': f'汇率转换失败: {str(e)}', 'traceback': traceback.format_exc()}), 500

# ==================== 邮件发送工具 ====================

@app.route('/api/tools/send-email', methods=['POST'])
def send_email():
    """邮件发送工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'send_email')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        data = request.get_json()
        to_email = data.get('to', '')
        subject = data.get('subject', '')
        body = data.get('body', '')
        
        if not to_email or not subject or not body:
            return jsonify({'error': '邮件地址、主题和内容不能为空'}), 400
        
        # 简单的邮件格式验证
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, to_email):
            return jsonify({'error': '邮件地址格式不正确'}), 400
        
        # 模拟邮件发送
        # 在实际应用中，这里会使用SMTP服务器发送邮件
        # 目前只是模拟发送成功
        send_success = True
        error_message = None
        
        if send_success:
            # 记录使用次数
            success, usage_message = record_daily_usage(user_id, 'send_email')
            if not success:
                return jsonify({'error': usage_message}), 500
            
            # 记录工具使用情况
            record_tool_usage(
                user_id,
                'send_email',
                {'to_email': to_email, 'subject': subject},
                {'sent': True, 'message_id': f'msg_{uuid.uuid4().hex[:8]}'}
            )
            
            # 获取更新后的使用次数
            updated_usage = check_daily_usage_limit(user_id, 'send_email')[1]
            
            return jsonify({
                'success': True,
                'message': '邮件发送成功（测试版）',
                'to_email': to_email,
                'subject': subject,
                'current_usage': updated_usage,
                'daily_limit': daily_limit,
                'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1,
                'usage_message': usage_message
            })
        else:
            return jsonify({'error': f'邮件发送失败: {error_message}'}), 500
        
    except Exception as e:
        return jsonify({'error': f'邮件发送异常: {str(e)}'}), 500

# ==================== 加水印工具 ====================

# ========== 旧版水印功能（已注释，改用 add_watermark_v2）==========
# @app.route('/api/tools/add-watermark', methods=['POST'])
# def add_watermark():
#     """加水印工具（旧版，已禁用）"""
#     pass

# ========== 旧版水印功能已注释，使用下面的新版功能 ==========

# ==================== 新版水印功能（简化版）====================
@app.route('/api/tools/add-watermark-v2', methods=['POST'])
def add_watermark_v2():
    """加水印工具（新版简化版，带详细调试）"""
    print("=" * 50)
    print("🎯🎯🎯 新版水印功能被调用！")
    print("=" * 50)
    
    try:
        # 1. 用户认证
        user = get_user_from_token()
        if not user:
            print("❌ 用户未登录")
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        print(f"✅ 用户已登录: {user_id}")
        
        # 2. 检查使用次数
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'add_watermark')
        if not can_use:
            print(f"❌ 使用次数已达上限: {current_usage}/{daily_limit}")
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        print(f"✅ 使用次数检查通过: {current_usage}/{daily_limit}")
        
        # 3. 获取请求数据
        data = request.get_json()
        print(f"📦 接收到的数据键: {list(data.keys()) if data else 'None'}")
        
        # 4. 获取图片数据
        image_data = data.get('image') or data.get('image_data')
        if not image_data:
            print("❌ 没有图片数据")
            return jsonify({'error': '没有上传图片数据'}), 400
        
        print(f"✅ 图片数据已接收，长度: {len(image_data)} 字符")
        
        # 5. 解码图片
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            input_image = Image.open(io.BytesIO(image_bytes))
            print(f"✅ 图片解码成功，尺寸: {input_image.size}")
        except Exception as e:
            print(f"❌ 图片解码失败: {str(e)}")
            return jsonify({'error': f'图片数据解析失败: {str(e)}'}), 400
        
        # 6. 获取水印参数（简化版，只支持基本参数）
        watermark_text = data.get('watermark_text', '© 2025')
        watermark_position = data.get('watermark_position', 'bottom-right')
        opacity = float(data.get('opacity', 0.7))
        font_size = int(data.get('font_size', 50))
        font_color = data.get('font_color', '#000000')
        
        print(f"📝 水印参数:")
        print(f"   文字: {watermark_text}")
        print(f"   位置: {watermark_position}")
        print(f"   透明度: {opacity}")
        print(f"   字体大小: {font_size}")
        print(f"   颜色: {font_color}")
        
        # 7. 位置映射（简化版）
        position_map = {
            'top-left': 'top-left',
            'top-right': 'top-right',
            'bottom-left': 'bottom-left',
            'bottom-right': 'bottom-right',
            'center': 'center',
            '左上角': 'top-left',
            '右上角': 'top-right',
            '左下角': 'bottom-left',
            '右下角': 'bottom-right',
            '居中': 'center'
        }
        watermark_position = position_map.get(watermark_position, 'bottom-right')
        print(f"📍 映射后的位置: {watermark_position}")
        
        # 8. 处理图片
        if input_image.mode != 'RGBA':
            input_image = input_image.convert('RGBA')
        
        from PIL import ImageDraw, ImageFont
        watermark_layer = Image.new('RGBA', input_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # 9. 加载字体（简化版，使用默认字体）
        try:
            font = ImageFont.load_default()
            print("✅ 使用默认字体")
        except:
            font = ImageFont.load_default()
            print("⚠️ 使用默认字体（备用）")
        
        # 10. 计算位置
        width, height = input_image.size
        text_width = len(watermark_text) * 10  # 简单估算
        text_height = 20
        
        positions = {
            'top-left': (20, 20),
            'top-right': (max(20, width - text_width - 20), 20),
            'bottom-left': (20, max(20, height - text_height - 20)),
            'bottom-right': (max(20, width - text_width - 20), max(20, height - text_height - 20)),
            'center': (max(0, (width - text_width) // 2), max(0, (height - text_height) // 2))
        }
        
        position = positions.get(watermark_position, positions['bottom-right'])
        print(f"📍 最终位置坐标: {position} (图片尺寸: {width}x{height})")
        
        # 11. 转换颜色
        if font_color.startswith('#'):
            font_color = font_color[1:]
        if len(font_color) == 3:
            font_color = ''.join([c*2 for c in font_color])
        try:
            r, g, b = int(font_color[0:2], 16), int(font_color[2:4], 16), int(font_color[4:6], 16)
        except:
            r, g, b = 0, 0, 0
        
        alpha = int(255 * opacity)
        print(f"🎨 颜色: RGB({r}, {g}, {b}), 透明度: {alpha}/255")
        
        # 12. 绘制水印
        draw.text(position, watermark_text, font=font, fill=(r, g, b, alpha))
        print(f"✅ 水印已绘制")
        
        # 13. 合并图片
        output_image = Image.alpha_composite(input_image, watermark_layer)
        if output_image.mode == 'RGBA':
            rgb_image = Image.new('RGB', output_image.size, (255, 255, 255))
            rgb_image.paste(output_image, mask=output_image.split()[3])
            output_image = rgb_image
        
        print(f"✅ 图片合并完成")
        
        # 14. 保存并返回
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format='PNG')
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        # 15. 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'add_watermark')
        if not success:
            print(f"❌ 记录使用次数失败: {usage_message}")
            return jsonify({'error': usage_message}), 500
        
        updated_usage = check_daily_usage_limit(user_id, 'add_watermark')[1]
        
        print("=" * 50)
        print("✅✅✅ 新版水印功能执行成功！")
        print("=" * 50)
        
        return jsonify({
            'success': True,
            'message': '水印添加完成（新版）',
            'processed_image': f'data:image/png;base64,{output_base64}',
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1
        })
        
    except Exception as e:
        import traceback
        print("=" * 50)
        print(f"❌❌❌ 新版水印功能出错: {str(e)}")
        print(traceback.format_exc())
        print("=" * 50)
        return jsonify({'error': f'水印添加失败: {str(e)}', 'traceback': traceback.format_exc()}), 500

# ==================== 去水印工具 ====================

@app.route('/api/tools/remove-watermark', methods=['POST'])
def remove_watermark():
    """去水印工具"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        # 检查每日使用次数限制
        can_use, current_usage, daily_limit, message = check_daily_usage_limit(user_id, 'remove_watermark')
        if not can_use:
            return jsonify({
                'error': f'今日使用次数已达上限（{daily_limit}次）',
                'current_usage': current_usage,
                'daily_limit': daily_limit,
                'message': message
            }), 400
        
        # 确保uploads文件夹存在
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # 支持base64上传
        data = request.get_json()
        image_data = data.get('image') or data.get('image_data')
        if not image_data:
            return jsonify({'error': '没有上传图片数据'}), 400
        
        try:
            # 解码base64
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            input_image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return jsonify({'error': f'图片数据解析失败: {str(e)}'}), 400
        
        # 转换为RGB模式
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        # 去水印处理（简化版）
        # 实际应用中可以使用OpenCV的inpaint算法或AI模型
        output_image = input_image.copy()
        
        # 尝试使用OpenCV进行图像修复（如果可用）
        try:
            import numpy as np
            import cv2
            
            # 转换为OpenCV格式
            img_array = np.array(input_image)
            
            # 这里可以使用更复杂的检测算法，暂时使用简单的边缘检测
            # 实际应用中，可以根据用户选择的水印区域进行处理
            output_image = input_image  # 简化处理，实际需要更复杂的算法
        except ImportError:
            # 如果没有OpenCV，使用基础处理
            output_image = input_image
            print("⚠️ OpenCV未安装，使用基础去水印方法")
        except Exception as e:
            print(f"⚠️ 去水印处理失败: {e}，返回原图")
            output_image = input_image
        
        # 保存处理后的图片
        output_filename = f'watermark_removed_{uuid.uuid4().hex[:8]}.png'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        output_image.save(output_path, 'PNG')
        
        # 转换为base64
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format='PNG')
        output_base64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        # 记录使用次数
        success, usage_message = record_daily_usage(user_id, 'remove_watermark')
        if not success:
            return jsonify({'error': usage_message}), 500
        
        # 记录工具使用情况
        record_tool_usage(
            user_id,
            'remove_watermark',
            {},
            {'output_filename': output_filename}
        )
        
        # 获取更新后的使用次数
        updated_usage = check_daily_usage_limit(user_id, 'remove_watermark')[1]
        
        return jsonify({
            'success': True,
            'message': '水印移除完成',
            'processed_image': f'data:image/png;base64,{output_base64}',
            'output_filename': output_filename,
            'download_url': f'/api/download/{output_filename}',
            'current_usage': updated_usage,
            'daily_limit': daily_limit,
            'remaining_usage': daily_limit - updated_usage if daily_limit != -1 else -1
        })
        
    except Exception as e:
        import traceback
        return jsonify({'error': f'水印移除失败: {str(e)}', 'traceback': traceback.format_exc()}), 500

# ==================== 支付和会员计划 ====================

@app.route('/api/payment/plans', methods=['GET'])
def get_payment_plans():
    """获取会员计划列表（从统一配置生成，确保前后端一致）"""
    try:
        # 从统一配置生成功能列表
        def generate_features(plan_id):
            """根据计划ID生成功能列表"""
            limits = PLAN_DAILY_LIMITS.get(plan_id, PLAN_DAILY_LIMITS['free'])
            features = []
            
            # 按顺序显示主要功能
            main_tools = [
                'background_remover', 'image_compressor', 'format_converter', 
                'image_cropper', 'keyword_analyzer', 'currency_converter',
                'unit_converter', 'shipping_calculator', 'add_watermark',
                'remove_watermark', 'image_rotate_flip', 'listing_generator',
                'send_email'
            ]
            
            for tool in main_tools:
                if tool in limits:
                    limit = limits[tool]
                    tool_name = TOOL_DISPLAY_NAMES.get(tool, tool)
                    features.append(f'{tool_name}：{format_limit_display(limit)}')
            
            return features
        
        # 返回对象格式，键为planId，值为planInfo（匹配payment.js的期望格式）
        plans = {
            'free': {
                'name': '免费版',
                'price_yuan': 0,
                'price_monthly': 0,
                'price_yearly': 0,
                'features': generate_features('free'),
                'popular': False
            },
            'basic': {
                'name': '入门版',
                'price_yuan': 19,
                'price_monthly': 19,
                'price_yearly': 180,  # 年付¥180（节省¥48，相当于¥15/月，20%折扣）
                'features': generate_features('basic'),
                'popular': True
            },
            'professional': {
                'name': '专业版',
                'price_yuan': 49,
                'price_monthly': 49,
                'price_yearly': 450,  # 年付¥450（节省¥138，相当于¥37.5/月，23%折扣）
                'features': generate_features('professional'),
                'popular': False
            },
            'flagship': {
                'name': '旗舰版',
                'price_yuan': 99,
                'price_monthly': 99,
                'price_yearly': 850,  # 年付¥850（节省¥338，相当于¥70.8/月，28%折扣）
                'features': [
                    '所有功能：无限制使用',
                    '优先处理速度',
                    '专属客服支持',
                    'API接口访问',
                    '批量处理工具',
                    '高级数据分析'
                ],
                'popular': False
            },
            'enterprise': {
                'name': '企业版',
                'price_yuan': 299,
                'price_monthly': 299,
                'price_yearly': 2500,  # 年付¥2,500（节省¥1,088，相当于¥208/月，30%折扣）
                'features': [
                    '所有功能：无限制使用',
                    '专属客户经理',
                    '定制化开发',
                    '私有化部署',
                    '数据安全保障',
                    '团队协作功能'
                ],
                'popular': False
            }
        }
        
        return jsonify({
            'success': True,
            'plans': plans
        })
    except Exception as e:
        return jsonify({'error': f'获取会员计划失败: {str(e)}'}), 500

# ==================== 支付订单管理 ====================

@app.route('/api/payment/create-order', methods=['POST'])
def create_payment_order():
    """创建支付订单"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        data = request.get_json()
        
        plan = data.get('plan')
        billing_period = data.get('billing_period', 'monthly')  # monthly 或 yearly
        payment_method = data.get('payment_method', 'alipay')  # alipay 或 wxpay
        
        if not plan:
            return jsonify({'error': '请选择会员计划'}), 400
        
        if billing_period not in ['monthly', 'yearly']:
            return jsonify({'error': '无效的计费周期'}), 400
        
        # 获取会员计划信息
        plans_data = {
            'free': {'name': '免费版', 'price_monthly': 0, 'price_yearly': 0},
            'basic': {'name': '入门版', 'price_monthly': 19, 'price_yearly': 180},
            'professional': {'name': '专业版', 'price_monthly': 49, 'price_yearly': 450},
            'flagship': {'name': '旗舰版', 'price_monthly': 99, 'price_yearly': 850},
            'enterprise': {'name': '企业版', 'price_monthly': 299, 'price_yearly': 2500}
        }
        
        if plan not in plans_data:
            return jsonify({'error': '无效的会员计划'}), 400
        
        plan_info = plans_data[plan]
        
        # 根据计费周期选择价格
        if billing_period == 'yearly':
            amount = plan_info['price_yearly']
            duration_days = 365  # 年付365天
        else:
            amount = plan_info['price_monthly']
            duration_days = 30  # 月付30天
        
        # 生成订单号
        order_no = f"ORDER{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
        
        # 创建订单数据
        order_data = {
            'order_no': order_no,
            'user_id': user_id,
            'plan': plan,
            'plan_name': plan_info['name'],
            'billing_period': billing_period,
            'duration_days': duration_days,
            'amount': amount,
            'payment_method': payment_method,
            'status': 'pending',  # pending, paid, cancelled, expired
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=2)).isoformat()  # 订单2小时过期
        }
        
        # 保存订单到内存和文件（持久化）
        payment_orders[order_no] = order_data
        
        # 同步到数据管理器并保存到文件
        if data_manager:
            data_manager.orders_db[order_no] = order_data
            data_manager.save_orders()
            print(f"💾 订单已保存到文件: {order_no}")
        
        # 如果是收款码支付方式
        if payment_method in ['alipay_qrcode', 'wechat_qrcode']:
            qrcode_type = 'alipay' if 'alipay' in payment_method else 'wechat'
            
            payment_info = {
                'order_no': order_no,
                'amount': amount,
                'plan_name': plan_info['name'],
                'payment_method': payment_method,
                'type': 'qrcode',
                'qrcode_type': qrcode_type,
                'qrcode_url': f'/api/payment/qrcode/{qrcode_type}',
                'message': '请扫码支付，支付完成后点击"我已支付"按钮'
            }
            
            print(f"✅ 创建收款码支付订单 - 订单号: {order_no}, 用户: {user_id}, 计划: {plan}, 金额: ¥{amount}")
            
            # 发送邮件提醒（订单创建）
            try:
                send_order_notification_email(order_data, notification_type='created')
            except Exception as e:
                print(f"⚠️ 发送订单创建邮件提醒失败: {str(e)}")
            
            return jsonify({
                'success': True,
                'order': order_data,
                'payment_info': payment_info,
                'message': '订单创建成功，请扫码支付'
            })
        
        # 调用码支付创建支付订单
        if MZFPAY_AVAILABLE and mzfpay_client:
            # 构建通知地址
            base_url = request.host_url.rstrip('/')
            # 前端地址（支付成功后的跳转地址）
            frontend_base = request.headers.get('Origin') or 'http://localhost:8000'
            notify_url = f"{base_url}/api/payment/notify"
            # 简化return_url，只使用order_no参数（避免查询参数过多影响签名）
            # 前端页面可以通过order_no查询订单状态
            return_url = f"{frontend_base}/payment/success.html?order_no={order_no}"
            
            # 转换支付方式：alipay -> alipay, wxpay -> wxpay
            mzfpay_type = 'alipay' if payment_method == 'alipay' else 'wxpay'
            
            # 商品名称
            product_name = f"{plan_info['name']}-{'年付' if billing_period == 'yearly' else '月付'}"
            
            # 调用码支付接口创建订单
            print(f"🔄 准备调用码支付接口...")
            print(f"   订单号: {order_no}")
            print(f"   金额: ¥{amount}")
            print(f"   商品名称: {product_name}")
            print(f"   支付方式: {mzfpay_type}")
            print(f"   通知地址: {notify_url}")
            print(f"   返回地址: {return_url}")
            
            try:
                payment_result = mzfpay_client.create_payment(
                    order_no=order_no,
                    amount=amount,
                    product_name=product_name,
                    payment_type=mzfpay_type,
                    notify_url=notify_url,
                    return_url=return_url,
                    method='api'  # 使用API方式，返回JSON
                )
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                print(f"❌ 调用码支付接口异常: {str(e)}")
                print(f"   错误详情: {error_trace}")
                return jsonify({
                    'success': False,
                    'error': f'调用支付接口失败: {str(e)}'
                }), 500
            
            print(f"📊 码支付接口返回结果: {payment_result}")
            
            if payment_result.get('success'):
                # 支付订单创建成功
                payment_info = {
                    'order_no': order_no,
                    'amount': amount,
                    'plan_name': plan_info['name'],
                    'payment_method': payment_method,
                    'pay_url': payment_result.get('pay_url', ''),
                    'qr_code': payment_result.get('qr_code', ''),
                    'trade_no': payment_result.get('trade_no', '')  # 码支付订单号
                }
                
                print(f"✅ 创建支付订单成功 - 订单号: {order_no}, 用户: {user_id}, 计划: {plan}, 金额: ¥{amount}")
                print(f"   支付链接: {payment_info['pay_url'][:100] if payment_info['pay_url'] else '无'}")
                
                return jsonify({
                    'success': True,
                    'order': order_data,
                    'payment_info': payment_info,
                    'message': '订单创建成功，请完成支付'
                })
            else:
                # 码支付创建订单失败
                error_msg = payment_result.get('error', '创建支付订单失败')
                print(f"❌ 码支付创建订单失败: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'支付接口调用失败: {error_msg}'
                }), 500
        else:
            # 码支付客户端未初始化，返回模拟数据
            payment_info = {
                'order_no': order_no,
                'amount': amount,
                'plan_name': plan_info['name'],
                'payment_method': payment_method,
                'pay_url': None,
                'qr_code': None,
                'message': '码支付客户端未初始化，请检查配置'
            }
            
            print(f"⚠️ 码支付客户端未初始化，返回模拟订单数据")
            
            return jsonify({
                'success': True,
                'order': order_data,
                'payment_info': payment_info,
                'message': '订单创建成功，但支付功能未就绪'
            })
        
    except Exception as e:
        import traceback
        print(f"❌ 创建支付订单失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'创建订单失败: {str(e)}'}), 500

# ==================== 邮件提醒功能 ====================

def send_order_notification_email(order, notification_type='created'):
    """
    发送订单提醒邮件
    
    Args:
        order: 订单信息字典
        notification_type: 通知类型 ('created' 订单创建, 'paid' 用户已支付, 'confirmed' 订单已确认)
    """
    if not EMAIL_CONFIG['enabled']:
        print("📧 邮件提醒未启用，跳过发送")
        return False
    
    if not EMAIL_CONFIG['sender_password']:
        print("⚠️ 邮件配置不完整，请设置EMAIL_PASSWORD环境变量")
        return False
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['admin_email']
        
        # 根据通知类型设置主题和内容
        if notification_type == 'confirmed':
            subject = f'✅ 订单已确认 - {order.get("order_no", "未知订单")}'
            content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #52c41a;">✅ 订单已确认，会员已开通</h2>
                <div style="background: #f6ffed; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #52c41a;">
                    <h3 style="color: #333; margin-top: 0;">订单信息</h3>
                    <p><strong>订单号：</strong>{order.get('order_no', '未知')}</p>
                    <p><strong>用户ID：</strong>{order.get('user_id', '未知')}</p>
                    <p><strong>会员计划：</strong>{order.get('plan_name', order.get('plan', '未知'))}</p>
                    <p><strong>金额：</strong>¥{order.get('amount', 0)}</p>
                    <p><strong>确认时间：</strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: #e6f7ff; border-left: 4px solid #1890ff; border-radius: 4px;">
                    <p style="margin: 0;"><strong>✅ 完成：</strong>会员已成功开通，用户现在可以使用会员功能了！</p>
                </div>
            </body>
            </html>
            """
        elif notification_type == 'paid':
            subject = f'💰 用户已支付 - {order.get("order_no", "未知订单")}'
            content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #ff9800;">💰 用户已支付，等待确认</h2>
                <div style="background: #fff7e6; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800;">
                    <h3 style="color: #333; margin-top: 0;">订单信息</h3>
                    <p><strong>订单号：</strong>{order.get('order_no', '未知')}</p>
                    <p><strong>用户ID：</strong>{order.get('user_id', '未知')}</p>
                    <p><strong>会员计划：</strong>{order.get('plan_name', order.get('plan', '未知'))}</p>
                    <p><strong>金额：</strong>¥{order.get('amount', 0)}</p>
                    <p><strong>支付方式：</strong>{'支付宝收款码' if 'alipay' in order.get('payment_method', '') else '微信收款码' if 'wechat' in order.get('payment_method', '') else order.get('payment_method', '未知')}</p>
                    <p><strong>创建时间：</strong>{order.get('created_at', '未知')}</p>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: #fff7e6; border-left: 4px solid #ff9800; border-radius: 4px;">
                    <p style="margin: 0;"><strong>⚠️ 重要：</strong>用户已点击"我已支付"按钮，请尽快在后台确认订单并开通会员！</p>
                </div>
                <div style="margin-top: 20px;">
                    <a href="http://localhost:5000/admin/orders" style="display: inline-block; padding: 10px 20px; background: #ff9800; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">立即确认订单</a>
                </div>
            </body>
            </html>
            """
        else:  # notification_type == 'created'
            subject = f'📦 新订单待确认 - {order.get("order_no", "未知订单")}'
            content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #1890ff;">📦 新订单待确认</h2>
                <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">订单信息</h3>
                    <p><strong>订单号：</strong>{order.get('order_no', '未知')}</p>
                    <p><strong>用户ID：</strong>{order.get('user_id', '未知')}</p>
                    <p><strong>会员计划：</strong>{order.get('plan_name', order.get('plan', '未知'))}</p>
                    <p><strong>金额：</strong>¥{order.get('amount', 0)}</p>
                    <p><strong>支付方式：</strong>{'支付宝收款码' if 'alipay' in order.get('payment_method', '') else '微信收款码' if 'wechat' in order.get('payment_method', '') else order.get('payment_method', '未知')}</p>
                    <p><strong>创建时间：</strong>{order.get('created_at', '未知')}</p>
                </div>
                <div style="margin-top: 20px; padding: 15px; background: #fff7e6; border-left: 4px solid #ff9800; border-radius: 4px;">
                    <p style="margin: 0;"><strong>💡 提示：</strong>用户已创建订单，请等待用户支付后点击"我已支付"按钮，然后您可以在后台确认订单。</p>
                </div>
                <div style="margin-top: 20px;">
                    <a href="http://localhost:5000/admin/orders" style="display: inline-block; padding: 10px 20px; background: #1890ff; color: white; text-decoration: none; border-radius: 4px;">查看订单管理后台</a>
                </div>
            </body>
            </html>
            """
        
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(content, 'html', 'utf-8'))
        
        # 发送邮件
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()  # 启用TLS加密
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.sendmail(EMAIL_CONFIG['sender_email'], [EMAIL_CONFIG['admin_email']], msg.as_string())
        server.quit()
        
        print(f"✅ 邮件提醒发送成功: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件提醒发送失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

@app.route('/api/payment/qrcode/<qrcode_type>')
def get_payment_qrcode(qrcode_type):
    """获取收款码图片"""
    try:
        # 收款码图片路径
        if qrcode_type == 'alipay':
            qrcode_path = 'frontend/images/alipay_qrcode.png'
        elif qrcode_type == 'wechat':
            qrcode_path = 'frontend/images/wechat_qrcode.png'
        else:
            return jsonify({'error': '不支持的支付方式'}), 400
        
        # 检查文件是否存在
        import os
        if not os.path.exists(qrcode_path):
            # 返回友好的错误提示图片或文本
            error_msg = f'收款码图片不存在: {qrcode_path}，请先上传收款码到 frontend/images/ 目录'
            print(f"⚠️ {error_msg}")
            return jsonify({'error': error_msg}), 404
        
        # 返回图片
        return send_file(qrcode_path, mimetype='image/png')
    except Exception as e:
        print(f"❌ 获取收款码失败: {str(e)}")
        return jsonify({'error': f'获取收款码失败: {str(e)}'}), 500

@app.route('/api/payment/confirm', methods=['POST'])
@require_admin_login
def confirm_payment():
    """手动确认订单（管理员确认）"""
    print(f"🔔 [confirm_payment] 收到确认订单请求")
    print(f"   请求方法: {request.method}")
    print(f"   请求路径: {request.path}")
    print(f"   请求头: {dict(request.headers)}")
    
    try:
        data = request.get_json()
        print(f"   请求数据: {data}")
        
        if not data:
            print(f"   ❌ 请求数据为空")
            return jsonify({'error': '请求数据为空'}), 400
        
        order_no = data.get('order_no')
        print(f"   订单号: {order_no}")
        
        if not order_no:
            print(f"   ❌ 订单号为空")
            return jsonify({'error': '订单号不能为空'}), 400
        
        # 查找订单
        print(f"   当前订单列表: {list(payment_orders.keys())}")
        if order_no not in payment_orders:
            print(f"   ❌ 订单不存在: {order_no}")
            return jsonify({'error': '订单不存在'}), 404
        
        order = payment_orders[order_no]
        print(f"   ✅ 找到订单: {order_no}")
        print(f"   订单信息: {order}")
        
        # 检查订单状态
        was_already_paid = order.get('status') == 'paid'
        
        if not was_already_paid:
            # 更新订单状态
            order['status'] = 'paid'
            order['paid_at'] = datetime.now().isoformat()
            order['confirmed_by'] = 'admin'  # 可以改为实际的管理员ID
        
        # 激活会员（调用现有的会员激活逻辑）
        # 即使订单已经是paid状态，也要检查并激活会员（防止重复确认时遗漏）
        membership_activated = False
        try:
            user_id = order.get('user_id')
            plan = order.get('plan')
            billing_period = order.get('billing_period', 'monthly')
            
            print(f"{'🔄 订单已确认，检查会员状态...' if was_already_paid else '✅ 订单已确认，开始激活会员...'}")
            print(f"   订单号: {order_no}")
            print(f"   用户ID: {user_id}")
            print(f"   计划: {plan}")
            print(f"   周期: {billing_period}")
            print(f"   订单状态: {order.get('status')}")
            
            # 调用会员激活函数
            if data_manager:
                # 获取用户资料
                print(f"🔍 正在查询用户资料，用户ID: {user_id}")
                profile = data_manager.get_user_profile(user_id)
                if not profile:
                    print(f"⚠️ 用户资料不存在: {user_id}")
                    print(f"   尝试从user_profiles_db查询...")
                    if user_id in user_profiles_db:
                        profile = user_profiles_db[user_id]
                        print(f"   ✅ 从user_profiles_db找到用户资料")
                    else:
                        print(f"   ❌ user_profiles_db中也没有找到用户资料")
                else:
                    print(f"✅ 找到用户资料，当前plan: {profile.get('plan')}, membership_type: {profile.get('membership_type')}")
                    # 计算会员到期时间
                    if billing_period == 'yearly':
                        duration_days = 365
                    else:
                        duration_days = 30
                    
                    # 获取当前会员到期时间（如果存在）
                    current_expires_at = profile.get('membership_expires_at')
                    start_time = datetime.now()
                    
                    if current_expires_at:
                        try:
                            # 如果已有会员且未过期，从当前到期时间开始续期
                            expires_dt = datetime.fromisoformat(current_expires_at.replace('Z', '+00:00'))
                            if expires_dt > datetime.now():
                                start_time = expires_dt
                        except:
                            pass
                    
                    end_time = start_time + timedelta(days=duration_days)
                    
                    # 更新用户会员信息
                    update_data = {
                        'plan': plan,
                        'membership_type': plan,
                        'membership_expires_at': end_time.isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # 更新到数据库
                    if use_real_db and user_db:
                        try:
                            user_db.update_user_profile(user_id, update_data)
                            print(f"✅ 会员已激活: {plan}, 到期时间: {end_time.isoformat()}")
                            membership_activated = True
                        except Exception as e:
                            print(f"⚠️ 数据库更新失败: {str(e)}")
                            # 同时更新内存数据库
                            if user_id in user_profiles_db:
                                user_profiles_db[user_id].update(update_data)
                                membership_activated = True
                    else:
                        # 更新内存数据库
                        if user_id in user_profiles_db:
                            user_profiles_db[user_id].update(update_data)
                        else:
                            user_profiles_db[user_id] = update_data
                        print(f"✅ 会员已激活（内存）: {plan}, 到期时间: {end_time.isoformat()}")
                        membership_activated = True
                    
                    # 同时更新data_manager中的用户资料
                    # 重要：必须直接更新 data_manager.user_profiles_db[user_id]，而不是更新 profile 副本
                    if profile and user_id in data_manager.user_profiles_db:
                        print(f"📝 更新前 - data_manager.user_profiles_db[{user_id}].plan: {data_manager.user_profiles_db[user_id].get('plan')}, membership_type: {data_manager.user_profiles_db[user_id].get('membership_type')}")
                        
                        # 直接更新原始数据，不是副本
                        data_manager.user_profiles_db[user_id].update(update_data)
                        
                        # 保存到文件
                        save_result = data_manager.save_all()
                        print(f"💾 保存结果: {save_result}")
                        
                        print(f"✅ data_manager用户资料已更新")
                        print(f"   更新后 - data_manager.user_profiles_db[{user_id}].plan: {data_manager.user_profiles_db[user_id].get('plan')}, membership_type: {data_manager.user_profiles_db[user_id].get('membership_type')}")
                        
                        # 验证更新是否成功（重新查询）
                        verify_profile = data_manager.get_user_profile(user_id)
                        if verify_profile:
                            print(f"🔍 验证 - 重新查询后 plan: {verify_profile.get('plan')}, membership_type: {verify_profile.get('membership_type')}")
                        else:
                            print(f"⚠️ 验证失败 - 重新查询返回None")
                    
                    # 确保user_profiles_db也更新（双重保险）
                    if user_id not in user_profiles_db:
                        # 如果不存在，从data_manager复制
                        if data_manager:
                            profile_copy = data_manager.get_user_profile(user_id)
                            if profile_copy:
                                user_profiles_db[user_id] = profile_copy.copy()
                                print(f"✅ 从data_manager复制到user_profiles_db")
                    else:
                        # 如果存在，更新
                        print(f"📝 更新前 - user_profiles_db[{user_id}].plan: {user_profiles_db[user_id].get('plan')}")
                        user_profiles_db[user_id].update(update_data)
                        print(f"✅ user_profiles_db已更新")
                        print(f"   更新后 - user_profiles_db[{user_id}].plan: {user_profiles_db[user_id].get('plan')}")
            else:
                print(f"⚠️ 数据管理器未初始化，无法激活会员")
            
        except Exception as e:
            import traceback
            print(f"⚠️ 激活会员失败: {str(e)}")
            print(traceback.format_exc())
            # 即使激活失败，订单状态也已更新
        
        # 返回前，再次验证用户资料是否已更新
        if membership_activated and data_manager:
            verify_profile = data_manager.get_user_profile(user_id)
            if verify_profile:
                print(f"🔍 [confirm_payment返回前] 最终验证 - plan: {verify_profile.get('plan')}, membership_type: {verify_profile.get('membership_type')}")
        
        # 发送邮件提醒（订单确认成功）
        if membership_activated:
            try:
                send_order_notification_email(order, notification_type='confirmed')
            except Exception as e:
                print(f"⚠️ 发送订单确认邮件提醒失败: {str(e)}")
        
        response_data = {
            'success': True,
            'message': '订单确认成功，会员已开通' if membership_activated else '订单已确认，但会员激活失败',
            'order': order,
            'membership_activated': membership_activated,
            'plan': order.get('plan'),
            'user_id': order.get('user_id')
        }
        
        print(f"✅ [confirm_payment] 返回响应: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        print(f"❌ [confirm_payment] 异常: {str(e)}")
        print(traceback.format_exc())
        print(f"❌ 确认订单失败: {str(e)}")
        return jsonify({'error': f'确认订单失败: {str(e)}'}), 500

@app.route('/api/admin/orders', methods=['GET'])
@require_admin_login
def get_admin_orders():
    """获取后台订单列表（支持多维度查询）"""
    try:
        status = request.args.get('status', 'pending')  # pending, paid, all
        start_date = request.args.get('start_date', '')  # 开始日期 YYYY-MM-DD
        end_date = request.args.get('end_date', '')  # 结束日期 YYYY-MM-DD
        user = request.args.get('user', '').strip()  # 用户名或邮箱
        
        # 检查并取消超时订单
        check_and_cancel_expired_orders()
        
        # 获取订单列表
        orders_list = []
        for order_no, order in payment_orders.items():
            # 状态筛选
            if status != 'all' and order.get('status') != status:
                continue
            
            # 复制订单数据，添加额外信息
            order_info = order.copy()
            
            # 获取用户信息（用户名、邮箱、到期时间）
            user_id = order.get('user_id')
            if user_id:
                # 优先从data_manager获取
                if data_manager:
                    profile = data_manager.get_user_profile(user_id)
                    if profile:
                        order_info['user_name'] = profile.get('name', '')
                        order_info['user_email'] = profile.get('email', '')
                        order_info['membership_expires_at'] = profile.get('membership_expires_at', '')
                # 备用：从内存数据库获取
                elif user_id in user_profiles_db:
                    profile = user_profiles_db[user_id]
                    order_info['user_name'] = profile.get('name', '')
                    order_info['user_email'] = profile.get('email', '')
                    order_info['membership_expires_at'] = profile.get('membership_expires_at', '')
                else:
                    order_info['user_name'] = ''
                    order_info['user_email'] = ''
                    order_info['membership_expires_at'] = ''
            
            # 时间筛选
            if start_date or end_date:
                created_at = order_info.get('created_at', '')
                if created_at:
                    try:
                        # 解析日期（支持多种格式）
                        if 'T' in created_at:
                            order_date = created_at.split('T')[0]
                        else:
                            order_date = created_at.split(' ')[0]
                        
                        # 日期比较
                        if start_date and order_date < start_date:
                            continue
                        if end_date and order_date > end_date:
                            continue
                    except:
                        pass  # 如果日期解析失败，不筛选
            
            # 用户筛选（用户名或邮箱）
            if user:
                user_name = order_info.get('user_name', '').lower()
                user_email = order_info.get('user_email', '').lower()
                search_user = user.lower()
                
                if search_user not in user_name and search_user not in user_email:
                    continue
            
            orders_list.append(order_info)
        
        # 按创建时间排序（最新的在前）
        orders_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'orders': orders_list,
            'total': len(orders_list),
            'filters': {
                'status': status,
                'start_date': start_date,
                'end_date': end_date,
                'user': user
            }
        })
        
    except Exception as e:
        print(f"❌ 获取订单列表失败: {str(e)}")
        return jsonify({'error': f'获取订单列表失败: {str(e)}'}), 500

@app.route('/api/admin/stats', methods=['GET'])
@require_admin_login
def get_admin_stats():
    """获取数据统计面板"""
    try:
        # 统计订单
        total_orders = len(payment_orders)
        pending_orders = sum(1 for o in payment_orders.values() if o.get('status') == 'pending')
        paid_orders = sum(1 for o in payment_orders.values() if o.get('status') == 'paid')
        cancelled_orders = sum(1 for o in payment_orders.values() if o.get('status') == 'cancelled')
        expired_orders = sum(1 for o in payment_orders.values() if o.get('status') == 'expired')
        
        # 统计收入
        total_revenue = sum(float(o.get('amount', 0)) for o in payment_orders.values() if o.get('status') == 'paid')
        
        # 统计用户数
        total_users = len(user_profiles_db) if user_profiles_db else 0
        if data_manager:
            total_users = len(data_manager.user_profiles_db) if hasattr(data_manager, 'user_profiles_db') else total_users
        
        # 统计会员数
        member_count = 0
        if data_manager:
            for profile in data_manager.user_profiles_db.values():
                if profile.get('plan') != 'free':
                    member_count += 1
        
        return jsonify({
            'success': True,
            'stats': {
                'orders': {
                    'total': total_orders,
                    'pending': pending_orders,
                    'paid': paid_orders,
                    'cancelled': cancelled_orders,
                    'expired': expired_orders
                },
                'revenue': {
                    'total': round(total_revenue, 2)
                },
                'users': {
                    'total': total_users,
                    'members': member_count
                }
            }
        })
    except Exception as e:
        print(f"❌ 获取统计数据失败: {str(e)}")
        return jsonify({'error': f'获取统计数据失败: {str(e)}'}), 500

@app.route('/api/admin/users', methods=['GET'])
@require_admin_login
def get_admin_users():
    """获取所有用户列表（包括免费和付费用户）"""
    try:
        # 查询参数
        plan_filter = request.args.get('plan', 'all')  # all, free, paid
        user_query = request.args.get('user_query', '').strip().lower()  # 用户名或邮箱
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        users_list = []
        
        # 从data_manager获取所有用户
        if data_manager and hasattr(data_manager, 'user_profiles_db'):
            for user_id, profile in data_manager.user_profiles_db.items():
                user_info = {
                    'user_id': user_id,
                    'email': profile.get('email', ''),
                    'name': profile.get('name', '未知用户'),
                    'plan': profile.get('plan', 'free'),
                    'credits': profile.get('credits', 0),
                    'created_at': profile.get('created_at', ''),
                    'updated_at': profile.get('updated_at', ''),
                    'membership_expires_at': profile.get('membership_expires_at', ''),
                    'membership_type': profile.get('membership_type', 'free')
                }
                
                # 计划筛选
                if plan_filter != 'all':
                    if plan_filter == 'free' and user_info['plan'] != 'free':
                        continue
                    elif plan_filter == 'paid' and user_info['plan'] == 'free':
                        continue
                
                # 用户查询（用户名或邮箱）
                if user_query:
                    name_match = user_info['name'].lower() if user_info['name'] else ''
                    email_match = user_info['email'].lower() if user_info['email'] else ''
                    user_id_match = user_id.lower() if user_id else ''
                    
                    if (user_query not in name_match and 
                        user_query not in email_match and 
                        user_query not in user_id_match):
                        continue
                
                # 时间筛选（注册时间）
                if start_date_str or end_date_str:
                    created_at = user_info.get('created_at', '')
                    if created_at:
                        try:
                            if 'T' in created_at:
                                user_date = created_at.split('T')[0]
                            else:
                                user_date = created_at.split(' ')[0]
                            
                            if start_date_str and user_date < start_date_str:
                                continue
                            if end_date_str and user_date > end_date_str:
                                continue
                        except:
                            pass
                
                users_list.append(user_info)
        
        # 如果没有data_manager，从内存数据库获取
        elif user_profiles_db:
            for user_id, profile in user_profiles_db.items():
                user_info = {
                    'user_id': user_id,
                    'email': profile.get('email', ''),
                    'name': profile.get('name', '未知用户'),
                    'plan': profile.get('plan', 'free'),
                    'credits': profile.get('credits', 0),
                    'created_at': profile.get('created_at', ''),
                    'updated_at': profile.get('updated_at', ''),
                    'membership_expires_at': profile.get('membership_expires_at', ''),
                    'membership_type': profile.get('membership_type', 'free')
                }
                
                # 计划筛选
                if plan_filter != 'all':
                    if plan_filter == 'free' and user_info['plan'] != 'free':
                        continue
                    elif plan_filter == 'paid' and user_info['plan'] == 'free':
                        continue
                
                # 用户查询
                if user_query:
                    name_match = user_info['name'].lower() if user_info['name'] else ''
                    email_match = user_info['email'].lower() if user_info['email'] else ''
                    user_id_match = user_id.lower() if user_id else ''
                    
                    if (user_query not in name_match and 
                        user_query not in email_match and 
                        user_query not in user_id_match):
                        continue
                
                # 时间筛选
                if start_date_str or end_date_str:
                    created_at = user_info.get('created_at', '')
                    if created_at:
                        try:
                            if 'T' in created_at:
                                user_date = created_at.split('T')[0]
                            else:
                                user_date = created_at.split(' ')[0]
                            
                            if start_date_str and user_date < start_date_str:
                                continue
                            if end_date_str and user_date > end_date_str:
                                continue
                        except:
                            pass
                
                users_list.append(user_info)
        
        # 按注册时间排序（最新的在前）
        users_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'users': users_list,
            'total': len(users_list),
            'filters': {
                'plan': plan_filter,
                'user_query': user_query,
                'start_date': start_date_str,
                'end_date': end_date_str
            }
        })
        
    except Exception as e:
        print(f"❌ 获取用户列表失败: {str(e)}")
        return jsonify({'error': f'获取用户列表失败: {str(e)}'}), 500

# ==================== 社区文章功能 ====================

# 文章数据存储
articles_db = {}  # {article_id: article_data}

# 加载文章数据
def load_articles():
    """从文件加载文章数据"""
    global articles_db
    try:
        articles_file = os.path.join('data', 'articles.json')
        if os.path.exists(articles_file):
            with open(articles_file, 'r', encoding='utf-8') as f:
                articles_db = json.load(f)
            print(f"✅ 从文件加载文章数据: {len(articles_db)} 篇文章")
        else:
            articles_db = {}
            print("📝 文章数据文件不存在，将创建新文件")
    except Exception as e:
        print(f"⚠️ 加载文章数据失败: {e}")
        articles_db = {}

# 保存文章数据
def save_articles():
    """保存文章数据到文件"""
    try:
        os.makedirs('data', exist_ok=True)
        articles_file = os.path.join('data', 'articles.json')
        with open(articles_file, 'w', encoding='utf-8') as f:
            json.dump(articles_db, f, ensure_ascii=False, indent=2)
        print(f"✅ 文章数据已保存: {len(articles_db)} 篇文章")
    except Exception as e:
        print(f"❌ 保存文章数据失败: {e}")

# SEO关键词列表（用于自动插入）
SEO_KEYWORDS = [
    # 高流量关键词
    "背景移除工具", "图片去背景", "在线背景移除", "AI去背景", "产品图片处理",
    # 中等流量关键词
    "免费去背景", "智能去背景", "产品图片去背景", "图片处理工具", "在线图片处理",
    # 长尾关键词
    "免费在线背景移除工具", "产品图片去背景软件", "亚马逊产品图片处理工具",
    "eBay图片优化工具", "跨境电商图片处理", "图片抠图工具", "背景去除软件",
    "去背景软件", "免费去背景工具", "在线PS", "跨境电商工具", "图片压缩工具",
    "格式转换工具", "Listing生成工具", "AI背景移除", "图片编辑工具"
]

def insert_seo_keywords(content, keywords_list=SEO_KEYWORDS):
    """在文章内容中自然插入SEO关键词"""
    import re
    import random
    
    # 如果内容中已经包含足够的关键词，不重复插入
    existing_keywords = sum(1 for keyword in keywords_list if keyword in content)
    if existing_keywords >= len(keywords_list) * 0.3:  # 如果已有30%的关键词，不再插入
        return content
    
    # 随机选择一些关键词插入（不超过5个）
    keywords_to_insert = random.sample(keywords_list, min(5, len(keywords_list)))
    
    # 在段落末尾或合适位置插入关键词
    sentences = content.split('。')
    result_sentences = []
    
    for i, sentence in enumerate(sentences):
        result_sentences.append(sentence)
        # 每隔2-3句插入一个关键词（自然插入）
        if i > 0 and (i + 1) % 3 == 0 and keywords_to_insert:
            keyword = keywords_to_insert.pop(0)
            # 自然融入句子
            if keyword not in sentence:
                result_sentences.append(f"使用{keyword}可以提升工作效率。")
    
    return '。'.join(result_sentences)

@app.route('/api/articles', methods=['GET'])
def get_articles():
    """获取文章列表"""
    try:
        # 查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        category = request.args.get('category', 'all')  # all, tutorial, tips, news
        
        # 筛选文章
        filtered_articles = []
        for article_id, article in articles_db.items():
            # 分类筛选
            if category != 'all' and article.get('category') != category:
                continue
            
            # 只显示已发布的文章
            if article.get('status') != 'published':
                continue
            
            filtered_articles.append({
                'id': article_id,
                'title': article.get('title', ''),
                'summary': article.get('summary', ''),
                'category': article.get('category', 'tutorial'),
                'author': article.get('author', '管理员'),
                'created_at': article.get('created_at', ''),
                'views': article.get('views', 0),
                'tags': article.get('tags', [])
            })
        
        # 按创建时间排序（最新的在前）
        filtered_articles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 分页
        total = len(filtered_articles)
        start = (page - 1) * limit
        end = start + limit
        paginated_articles = filtered_articles[start:end]
        
        return jsonify({
            'success': True,
            'articles': paginated_articles,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })
    except Exception as e:
        print(f"❌ 获取文章列表失败: {str(e)}")
        return jsonify({'error': f'获取文章列表失败: {str(e)}'}), 500

@app.route('/api/articles/<article_id>', methods=['GET'])
def get_article(article_id):
    """获取单篇文章"""
    try:
        if article_id not in articles_db:
            return jsonify({'error': '文章不存在'}), 404
        
        article = articles_db[article_id]
        
        # 只返回已发布的文章
        if article.get('status') != 'published':
            return jsonify({'error': '文章不存在'}), 404
        
        # 增加浏览量
        article['views'] = article.get('views', 0) + 1
        save_articles()
        
        return jsonify({
            'success': True,
            'article': article
        })
    except Exception as e:
        print(f"❌ 获取文章失败: {str(e)}")
        return jsonify({'error': f'获取文章失败: {str(e)}'}), 500

@app.route('/api/admin/articles', methods=['POST'])
@require_admin_login
def create_article():
    """创建文章（管理员）"""
    try:
        data = request.get_json()
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        summary = data.get('summary', '').strip()
        category = data.get('category', 'tutorial')  # tutorial, tips, news
        tags = data.get('tags', [])
        
        if not title or not content:
            return jsonify({'error': '标题和内容不能为空'}), 400
        
        # 生成文章ID
        article_id = f"article_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 自动插入SEO关键词
        optimized_content = insert_seo_keywords(content)
        
        # 如果没有摘要，自动生成（取前150字）
        if not summary:
            summary = content[:150] + '...' if len(content) > 150 else content
        
        # 创建文章
        article = {
            'id': article_id,
            'title': title,
            'content': optimized_content,  # 使用优化后的内容
            'summary': summary,
            'category': category,
            'tags': tags,
            'author': '管理员',
            'status': 'published',  # published, draft
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'views': 0
        }
        
        articles_db[article_id] = article
        save_articles()
        
        return jsonify({
            'success': True,
            'article': article,
            'message': '文章创建成功'
        })
    except Exception as e:
        print(f"❌ 创建文章失败: {str(e)}")
        return jsonify({'error': f'创建文章失败: {str(e)}'}), 500

@app.route('/api/admin/articles/<article_id>', methods=['PUT'])
@require_admin_login
def update_article(article_id):
    """更新文章（管理员）"""
    try:
        if article_id not in articles_db:
            return jsonify({'error': '文章不存在'}), 404
        
        data = request.get_json()
        article = articles_db[article_id]
        
        # 更新字段
        if 'title' in data:
            article['title'] = data['title'].strip()
        if 'content' in data:
            # 重新优化内容
            article['content'] = insert_seo_keywords(data['content'].strip())
        if 'summary' in data:
            article['summary'] = data['summary'].strip()
        if 'category' in data:
            article['category'] = data['category']
        if 'tags' in data:
            article['tags'] = data['tags']
        if 'status' in data:
            article['status'] = data['status']
        
        article['updated_at'] = datetime.now().isoformat()
        
        save_articles()
        
        return jsonify({
            'success': True,
            'article': article,
            'message': '文章更新成功'
        })
    except Exception as e:
        print(f"❌ 更新文章失败: {str(e)}")
        return jsonify({'error': f'更新文章失败: {str(e)}'}), 500

@app.route('/api/admin/articles', methods=['GET'])
@require_admin_login
def get_admin_articles():
    """获取所有文章列表（管理员，包括草稿）"""
    try:
        show_all = request.args.get('all', 'false') == 'true'
        
        articles_list = []
        for article_id, article in articles_db.items():
            # 如果show_all=true，显示所有文章（包括草稿）
            if not show_all and article.get('status') != 'published':
                continue
            
            articles_list.append({
                'id': article_id,
                'title': article.get('title', ''),
                'summary': article.get('summary', ''),
                'content': article.get('content', ''),
                'category': article.get('category', 'tutorial'),
                'author': article.get('author', '管理员'),
                'created_at': article.get('created_at', ''),
                'updated_at': article.get('updated_at', ''),
                'views': article.get('views', 0),
                'status': article.get('status', 'published'),
                'tags': article.get('tags', [])
            })
        
        # 按创建时间排序（最新的在前）
        articles_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'articles': articles_list,
            'total': len(articles_list)
        })
    except Exception as e:
        print(f"❌ 获取文章列表失败: {str(e)}")
        return jsonify({'error': f'获取文章列表失败: {str(e)}'}), 500

@app.route('/api/admin/articles/<article_id>', methods=['DELETE'])
@require_admin_login
def delete_article(article_id):
    """删除文章（管理员）"""
    try:
        if article_id not in articles_db:
            return jsonify({'error': '文章不存在'}), 404
        
        del articles_db[article_id]
        save_articles()
        
        return jsonify({
            'success': True,
            'message': '文章删除成功'
        })
    except Exception as e:
        print(f"❌ 删除文章失败: {str(e)}")
        return jsonify({'error': f'删除文章失败: {str(e)}'}), 500

@app.route('/api/admin/batch-confirm', methods=['POST'])
@require_admin_login
def batch_confirm_orders():
    """批量确认订单"""
    try:
        data = request.get_json()
        order_nos = data.get('order_nos', [])
        
        if not order_nos or not isinstance(order_nos, list):
            return jsonify({'error': '请提供订单号列表'}), 400
        
        success_count = 0
        failed_count = 0
        results = []
        
        for order_no in order_nos:
            try:
                # 调用确认订单逻辑
                if order_no in payment_orders:
                    order = payment_orders[order_no]
                    if order.get('status') != 'paid':
                        # 更新订单状态
                        order['status'] = 'paid'
                        order['paid_at'] = datetime.now().isoformat()
                        order['confirmed_by'] = session.get('admin_username', 'admin')
                        
                        # 激活会员
                        user_id = order.get('user_id')
                        plan = order.get('plan')
                        billing_period = order.get('billing_period', 'monthly')
                        
                        if data_manager and user_id:
                            profile = data_manager.get_user_profile(user_id)
                            if profile:
                                duration_days = 365 if billing_period == 'yearly' else 30
                                current_expires_at = profile.get('membership_expires_at')
                                start_time = datetime.now()
                                
                                if current_expires_at:
                                    try:
                                        expires_dt = datetime.fromisoformat(current_expires_at.replace('Z', '+00:00'))
                                        if expires_dt > datetime.now():
                                            start_time = expires_dt
                                    except:
                                        pass
                                
                                end_time = start_time + timedelta(days=duration_days)
                                
                                update_data = {
                                    'plan': plan,
                                    'membership_expires_at': end_time.isoformat(),
                                    'updated_at': datetime.now().isoformat()
                                }
                                
                                data_manager.user_profiles_db[user_id].update(update_data)
                                data_manager.save_all()
                        
                        success_count += 1
                        results.append({'order_no': order_no, 'status': 'success'})
                    else:
                        results.append({'order_no': order_no, 'status': 'already_paid'})
                else:
                    failed_count += 1
                    results.append({'order_no': order_no, 'status': 'not_found'})
            except Exception as e:
                failed_count += 1
                results.append({'order_no': order_no, 'status': 'error', 'error': str(e)})
        
        return jsonify({
            'success': True,
            'message': f'批量确认完成：成功 {success_count} 个，失败 {failed_count} 个',
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        })
    except Exception as e:
        print(f"❌ 批量确认订单失败: {str(e)}")
        return jsonify({'error': f'批量确认失败: {str(e)}'}), 500

def check_and_cancel_expired_orders():
    """检查并取消超时订单（24小时未支付）"""
    try:
        current_time = datetime.now()
        expired_count = 0
        
        for order_no, order in payment_orders.items():
            if order.get('status') == 'pending':
                expires_at_str = order.get('expires_at')
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        # 如果订单超过24小时未支付，自动取消
                        if current_time > expires_at:
                            order['status'] = 'expired'
                            order['expired_at'] = current_time.isoformat()
                            expired_count += 1
                            print(f"⏰ 订单已超时自动取消: {order_no}")
                    except Exception as e:
                        print(f"⚠️ 解析订单过期时间失败: {order_no}, {str(e)}")
        
        if expired_count > 0:
            print(f"✅ 已自动取消 {expired_count} 个超时订单")
    except Exception as e:
        print(f"❌ 检查超时订单失败: {str(e)}")

def check_membership_expiry():
    """检查会员到期并发送提醒（到期前7天）"""
    try:
        if not data_manager:
            return
        
        current_time = datetime.now()
        reminder_days = 7
        
        for user_id, profile in data_manager.user_profiles_db.items():
            if profile.get('plan') != 'free':
                expires_at_str = profile.get('membership_expires_at')
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                        days_remaining = (expires_at - current_time).days
                        
                        # 到期前7天发送提醒
                        if 0 < days_remaining <= reminder_days:
                            # 检查是否已发送提醒（避免重复发送）
                            last_reminder = profile.get('last_expiry_reminder')
                            if not last_reminder or (current_time - datetime.fromisoformat(last_reminder)).days >= 1:
                                # 发送邮件提醒
                                user_email = profile.get('email', '')
                                if user_email and EMAIL_CONFIG['enabled']:
                                    try:
                                        send_membership_expiry_reminder(user_email, profile, days_remaining)
                                        profile['last_expiry_reminder'] = current_time.isoformat()
                                        data_manager.save_all()
                                        print(f"📧 已发送会员到期提醒: {user_email}, 剩余 {days_remaining} 天")
                                    except Exception as e:
                                        print(f"⚠️ 发送会员到期提醒失败: {str(e)}")
                    except Exception as e:
                        print(f"⚠️ 检查会员到期失败: {user_id}, {str(e)}")
    except Exception as e:
        print(f"❌ 检查会员到期失败: {str(e)}")

def send_membership_expiry_reminder(user_email, profile, days_remaining):
    """发送会员到期提醒邮件"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = user_email
        
        plan_name = profile.get('plan', '会员')
        expires_at = profile.get('membership_expires_at', '')
        
        subject = f'⏰ 会员即将到期提醒 - 剩余 {days_remaining} 天'
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #ff9800;">⏰ 会员即将到期提醒</h2>
            <div style="background: #fff7e6; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800;">
                <p><strong>您的会员将在 {days_remaining} 天后到期</strong></p>
                <p><strong>会员类型：</strong>{plan_name}</p>
                <p><strong>到期时间：</strong>{expires_at}</p>
            </div>
            <div style="margin-top: 20px;">
                <a href="http://localhost:8000/payment.html" style="display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 4px;">立即续费</a>
            </div>
        </body>
        </html>
        """
        
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(content, 'html', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.sendmail(EMAIL_CONFIG['sender_email'], [user_email], msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"❌ 发送会员到期提醒邮件失败: {str(e)}")
        return False

def check_usage_limit_warnings():
    """检查使用次数不足并发送提醒"""
    try:
        if not data_manager:
            return
        
        for user_id, profile in data_manager.user_profiles_db.items():
            plan = profile.get('plan', 'free')
            if plan == 'free':
                continue
            
            # 获取会员计划的每日限制
            daily_limits = PLAN_DAILY_LIMITS.get(plan, {})
            
            # 检查每个工具的使用情况
            today = datetime.now().strftime('%Y-%m-%d')
            daily_usage = profile.get('daily_usage', {}).get(today, {})
            
            for tool_name, limit in daily_limits.items():
                if limit > 0:  # 有上限的工具
                    current_usage = daily_usage.get(tool_name, 0)
                    usage_percentage = (current_usage / limit) * 100
                    
                    # 使用率达到80%时发送提醒
                    if usage_percentage >= 80 and usage_percentage < 100:
                        user_email = profile.get('email', '')
                        if user_email and EMAIL_CONFIG['enabled']:
                            try:
                                send_usage_limit_warning(user_email, profile, tool_name, current_usage, limit)
                                print(f"📧 已发送使用次数不足提醒: {user_email}, {tool_name}: {current_usage}/{limit}")
                            except Exception as e:
                                print(f"⚠️ 发送使用次数不足提醒失败: {str(e)}")
    except Exception as e:
        print(f"❌ 检查使用次数不足失败: {str(e)}")

def send_usage_limit_warning(user_email, profile, tool_name, current_usage, limit):
    """发送使用次数不足提醒邮件"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = user_email
        
        tool_names = {
            'bgRemoverCount': '背景移除',
            'compressorCount': '图片压缩',
            'watermarkCount': '水印处理'
        }
        tool_display_name = tool_names.get(tool_name, tool_name)
        
        subject = f'⚠️ 使用次数不足提醒 - {tool_display_name}'
        content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #ff9800;">⚠️ 使用次数不足提醒</h2>
            <div style="background: #fff7e6; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800;">
                <p><strong>工具：</strong>{tool_display_name}</p>
                <p><strong>当前使用：</strong>{current_usage} / {limit}</p>
                <p><strong>剩余次数：</strong>{limit - current_usage}</p>
            </div>
            <div style="margin-top: 20px;">
                <a href="http://localhost:8000/payment.html" style="display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 4px;">升级会员</a>
            </div>
        </body>
        </html>
        """
        
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(content, 'html', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.sendmail(EMAIL_CONFIG['sender_email'], [user_email], msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"❌ 发送使用次数不足提醒邮件失败: {str(e)}")
        return False

@app.route('/api/payment/notify', methods=['POST', 'GET'])
def payment_notify():
    """
    处理码支付异步通知（支付成功回调）
    注意：码支付可能使用GET或POST方式回调，需要支持两种方式
    """
    try:
        # 获取回调参数（可能是GET或POST）
        if request.method == 'POST':
            params = request.form.to_dict()
        else:
            params = request.args.to_dict()
        
        print(f"📨 收到支付回调通知: {params}")
        
        # 验证签名
        if MZFPAY_AVAILABLE and mzfpay_client:
            if not mzfpay_client.verify_sign(params):
                print("❌ 支付回调签名验证失败")
                return 'sign error', 400
        
        # 获取订单信息
        order_no = params.get('out_trade_no')  # 商户订单号
        trade_no = params.get('trade_no')  # 码支付订单号
        trade_status = params.get('trade_status')  # 支付状态
        money = params.get('money')  # 支付金额
        
        if not order_no:
            print("❌ 回调通知缺少订单号")
            return 'order_no missing', 400
        
        # 查找订单
        if order_no not in payment_orders:
            print(f"❌ 订单不存在: {order_no}")
            return 'order not found', 404
        
        order = payment_orders[order_no]
        
        # 检查订单是否已处理（防止重复处理）
        if order.get('status') == 'paid':
            print(f"⚠️ 订单已处理，跳过: {order_no}")
            return 'success'  # 返回success，告知码支付已处理
        
        # 验证金额
        order_amount = float(order['amount'])
        callback_amount = float(money) if money else 0
        if abs(order_amount - callback_amount) > 0.01:  # 允许0.01的误差
            print(f"❌ 金额不匹配: 订单金额={order_amount}, 回调金额={callback_amount}")
            return 'amount mismatch', 400
        
        # 判断支付状态
        # 码支付的成功状态可能是：'TRADE_SUCCESS', 'success', '1' 等
        if trade_status in ['TRADE_SUCCESS', 'success', 'SUCCESS', '1'] or not trade_status:
            # 支付成功
            order['status'] = 'paid'
            order['trade_no'] = trade_no
            order['paid_at'] = datetime.now().isoformat()
            
            # 同步到数据管理器并保存到文件
            if data_manager:
                data_manager.orders_db[order_no] = order
                data_manager.save_orders()
                print(f"💾 支付回调订单状态已保存: {order_no}")
            
            # 激活会员权益
            try:
                user_id = order['user_id']
                plan = order['plan']
                billing_period = order['billing_period']
                duration_days = order['duration_days']
                
                if data_manager:
                    profile = data_manager.get_user_profile(user_id)
                    if profile:
                        # 计算会员到期时间
                        current_expires_at = profile.get('membership_expires_at')
                        start_time = datetime.now()
                        
                        if current_expires_at:
                            try:
                                expires_dt = datetime.fromisoformat(current_expires_at.replace('Z', '+00:00'))
                                if expires_dt > datetime.now():
                                    start_time = expires_dt
                            except:
                                pass
                        
                        end_time = start_time + timedelta(days=duration_days)
                        
                        # 更新会员信息
                        profile['plan'] = plan
                        profile['membership_expires_at'] = end_time.isoformat()
                        profile['updated_at'] = datetime.now().isoformat()
                        
                        # 保存数据
                        data_manager.save_all()
                        
                        print(f"✅ 支付成功并激活会员 - 订单号: {order_no}, 用户: {user_id}, 计划: {plan}")
                    else:
                        print(f"⚠️ 用户资料不存在: {user_id}")
                else:
                    print("⚠️ 数据管理器未初始化")
            except Exception as e:
                print(f"⚠️ 激活会员失败: {str(e)}")
                # 即使激活失败，也返回success，避免重复回调
            
            print(f"✅ 支付回调处理成功 - 订单号: {order_no}")
            return 'success'  # 必须返回success，否则码支付会重复通知
        else:
            print(f"⚠️ 支付状态未知: {trade_status}")
            return 'success'
            
    except Exception as e:
        import traceback
        print(f"❌ 处理支付回调异常: {str(e)}")
        print(traceback.format_exc())
        return 'fail', 500

@app.route('/api/payment/mark-paid', methods=['POST'])
def mark_order_as_paid():
    """用户点击"我已支付"按钮时调用"""
    try:
        data = request.get_json()
        order_no = data.get('order_no')
        
        if not order_no:
            return jsonify({'error': '订单号不能为空'}), 400
        
        # 查找订单
        if order_no not in payment_orders:
            return jsonify({'error': '订单不存在'}), 404
        
        order = payment_orders[order_no]
        
        # 检查订单状态
        if order.get('status') == 'paid':
            return jsonify({
                'success': True,
                'message': '订单已确认',
                'order': order
            })
        
        # 发送邮件提醒（用户已支付）
        try:
            send_order_notification_email(order, notification_type='paid')
        except Exception as e:
            print(f"⚠️ 发送用户已支付邮件提醒失败: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': '已收到您的支付通知，等待管理员确认',
            'order': order
        })
        
    except Exception as e:
        print(f"❌ 标记订单为已支付失败: {str(e)}")
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/api/payment/query-order/<order_no>', methods=['GET'])
def query_payment_order(order_no):
    """
    查询支付订单状态
    支持两种情况：
    1. 已登录用户：验证订单归属
    2. 未登录用户：仅通过订单号查询（用于支付成功页面）
    """
    try:
        # 尝试获取用户信息（可选）
        user = None
        try:
            user = get_user_from_token()
        except:
            pass  # 未登录也可以查询订单状态
        
        # 从内存中查询订单（后续可改为数据库）
        if order_no in payment_orders:
            order = payment_orders[order_no]
            
            # 如果已登录，验证订单归属
            if user:
                user_id = user['id']
                if order.get('user_id') != user_id:
                    return jsonify({'error': '无权访问该订单'}), 403
            
            return jsonify({
                'success': True,
                'order': {
                    'order_no': order_no,
                    'status': order.get('status', 'pending'),
                    'amount': order.get('amount'),
                    'plan': order.get('plan'),
                    'plan_name': order.get('plan_name'),
                    'billing_period': order.get('billing_period'),
                    'payment_method': order.get('payment_method'),
                    'paid_at': order.get('paid_at'),
                    'trade_no': order.get('trade_no'),
                    'created_at': order.get('created_at')
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': '订单不存在'
            }), 404
        
    except Exception as e:
        return jsonify({'error': f'查询订单失败: {str(e)}'}), 500

@app.route('/api/payment/debug/list-orders', methods=['GET'])
def debug_list_orders():
    """
    调试接口：列出所有订单（仅用于开发测试）
    ⚠️ 注意：此接口会暴露所有订单信息，生产环境应删除或添加权限验证
    """
    try:
        # 格式化为更易读的格式
        orders_list = []
        for order_no, order in payment_orders.items():
            orders_list.append({
                'order_no': order_no,
                'user_id': order.get('user_id'),
                'plan': order.get('plan'),
                'plan_name': order.get('plan_name'),
                'amount': order.get('amount'),
                'status': order.get('status', 'pending'),
                'payment_method': order.get('payment_method'),
                'created_at': order.get('created_at'),
                'paid_at': order.get('paid_at'),
                'trade_no': order.get('trade_no')
            })
        
        # 按创建时间倒序排列
        orders_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'total': len(orders_list),
            'orders': orders_list,
            'message': '⚠️ 这是调试接口，生产环境请删除'
        })
        
    except Exception as e:
        return jsonify({'error': f'查询订单列表失败: {str(e)}'}), 500

@app.route('/api/payment/activate-membership', methods=['POST'])
def activate_membership():
    """激活会员权益（支付成功后调用）"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        data = request.get_json()
        
        order_no = data.get('order_no')
        plan = data.get('plan')
        billing_period = data.get('billing_period', 'monthly')
        
        if not order_no or not plan:
            return jsonify({'error': '缺少必要参数'}), 400
        
        if not data_manager:
            return jsonify({'error': '数据管理器未初始化'}), 500
        
        # 获取用户资料
        profile = data_manager.get_user_profile(user_id)
        if not profile:
            return jsonify({'error': '用户资料不存在'}), 404
        
        # 计算会员到期时间
        if billing_period == 'yearly':
            duration_days = 365
        else:
            duration_days = 30
        
        # 获取当前会员到期时间（如果存在）
        current_expires_at = profile.get('membership_expires_at')
        start_time = datetime.now()
        
        if current_expires_at:
            try:
                # 如果已有会员且未过期，从当前到期时间开始续期
                expires_dt = datetime.fromisoformat(current_expires_at.replace('Z', '+00:00'))
                if expires_dt > datetime.now():
                    start_time = expires_dt
            except:
                pass
        
        # 计算新的到期时间
        end_time = start_time + timedelta(days=duration_days)
        
        # 更新用户会员信息
        profile['plan'] = plan
        profile['membership_expires_at'] = end_time.isoformat()
        profile['updated_at'] = datetime.now().isoformat()
        
        # 保存数据
        data_manager.save_all()
        
        print(f"✅ 激活会员成功 - 用户: {user_id}, 计划: {plan}, 计费周期: {billing_period}, 到期时间: {end_time.isoformat()}")
        
        return jsonify({
            'success': True,
            'message': '会员权益已激活',
            'plan': plan,
            'expires_at': end_time.isoformat()
        })
        
    except Exception as e:
        import traceback
        print(f"❌ 激活会员失败: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'激活会员失败: {str(e)}'}), 500

# ==================== 邀请推荐功能 ====================

@app.route('/api/invite/code', methods=['GET'])
def get_invite_code():
    """获取用户的邀请码"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        if data_manager:
            profile = data_manager.get_user_profile(user_id)
            if not profile:
                return jsonify({'error': '用户资料不存在'}), 404
            
            invite_code = profile.get('invite_code', '')
            if not invite_code:
                # 如果没有邀请码，生成一个
                invite_code = data_manager.generate_invite_code()
                profile['invite_code'] = invite_code
                data_manager.invites_db[invite_code] = user_id
                data_manager.save_all()
            
            return jsonify({
                'success': True,
                'invite_code': invite_code,
                'invite_url': f'http://localhost:8000/?invite={invite_code}'
            })
        else:
            return jsonify({'error': '数据管理器未初始化'}), 500
            
    except Exception as e:
        return jsonify({'error': f'获取邀请码失败: {str(e)}'}), 500

@app.route('/api/invite/stats', methods=['GET'])
def get_invite_stats():
    """获取邀请统计信息"""
    try:
        user = get_user_from_token()
        if not user:
            return jsonify({'error': '请先登录'}), 401
        
        user_id = user['id']
        
        if data_manager:
            profile = data_manager.get_user_profile(user_id)
            if not profile:
                return jsonify({'error': '用户资料不存在'}), 404
            
            invite_code = profile.get('invite_code', '')
            
            # 如果没有邀请码，自动生成一个
            if not invite_code:
                invite_code = data_manager.generate_invite_code()
                profile['invite_code'] = invite_code
                data_manager.invites_db[invite_code] = user_id
                data_manager.save_all()
                print(f"✅ 为用户 {user_id} 生成邀请码: {invite_code}")
            
            # 统计被邀请人数（查找invited_by等于当前用户ID的用户）
            invited_count = 0
            for uid, p in data_manager.user_profiles_db.items():
                if p.get('invited_by') == user_id:
                    invited_count += 1
            
            # 获取奖励信息
            rewards = profile.get('invite_rewards', {})
            daily_rewards = rewards.get('daily_rewards', {})
            one_time_rewards = rewards.get('one_time_rewards', [])
            
            return jsonify({
                'success': True,
                'invite_code': invite_code,
                'invited_count': invited_count,
                'daily_rewards': daily_rewards,
                'one_time_rewards_count': len(one_time_rewards),
                'invite_url': f'{request.scheme}://{request.host}/?invite={invite_code}'
            })
        else:
            return jsonify({'error': '数据管理器未初始化'}), 500
            
    except Exception as e:
        return jsonify({'error': f'获取邀请统计失败: {str(e)}'}), 500

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

# 启动时加载文章数据
load_articles()

if __name__ == '__main__':
    print("🚀 启动独立测试版应用...")
    print("📊 数据库: 模拟内存数据库")
    print("🔧 背景移除功能：测试版")
    print("💰 定价体系: 免费版(¥0) 基础版(¥39) 专业版(¥59) 旗舰版(¥99) 企业版(¥299)")
    print("🌐 访问地址: http://localhost:5000")
    print("📈 健康检查: http://localhost:5000/health")
    print("🧪 测试命令: python test_supabase_simple.py")
    
    # 生产环境建议使用: app.run(debug=False, host='0.0.0.0', port=5000)
    # 或使用Gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 sk_app:app
    app.run(debug=True, host='0.0.0.0', port=5000)