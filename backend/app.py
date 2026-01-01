from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import os
import uuid
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
from rembg import remove
from PIL import Image
import io

# 初始化应用
app = Flask(__name__)
CORS(app)

# 配置
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cross_border_tools.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tool_usage = db.relationship('ToolUsage', backref='user', lazy=True)

class ToolUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    tool_name = db.Column(db.String(50), nullable=False)
    usage_count = db.Column(db.Integer, default=1)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 工具配置
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def record_tool_usage(tool_name):
    """记录工具使用情况"""
    if current_user.is_authenticated:
        usage = ToolUsage.query.filter_by(user_id=current_user.id, tool_name=tool_name).first()
        if usage:
            usage.usage_count += 1
            usage.last_used = datetime.utcnow()
        else:
            usage = ToolUsage(user_id=current_user.id, tool_name=tool_name)
            db.session.add(usage)
        db.session.commit()

# 主页路由
@app.route('/')
def index():
    return jsonify({
        'message': '海外跨境小工具API服务运行中', 
        'version': '2.0.0',
        'tools': [
            {'name': 'background-remover', 'description': '背景移除工具'},
            {'name': 'currency-converter', 'description': '汇率转换工具'},
            {'name': 'shipping-calculator', 'description': '国际运费计算'},
            {'name': 'unit-converter', 'description': '尺寸单位转换'}
        ]
    })

# 背景移除工具
@app.route('/api/tools/background-remover', methods=['POST'])
def remove_background():
    try:
        record_tool_usage('background-remover')
        
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        input_filename = f'{unique_id}_{filename}'
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        file.save(input_path)
        
        # 处理图片
        with open(input_path, 'rb') as input_file:
            input_data = input_file.read()
        
        # 移除背景
        output_data = remove(input_data)
        
        # 添加白色背景
        output_image = Image.open(io.BytesIO(output_data))
        if output_image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', output_image.size, (255, 255, 255))
            background.paste(output_image, mask=output_image.split()[-1])
            output_image = background
        
        # 保存处理后的图片
        output_filename = f'{unique_id}_white_bg.png'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        output_image.save(output_path, 'PNG')
        
        # 清理临时文件
        os.remove(input_path)
        
        return jsonify({
            'success': True,
            'message': '背景移除成功',
            'output_filename': output_filename,
            'output_url': f'/api/download/{output_filename}'
        })
        
    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

# 汇率转换工具
@app.route('/api/tools/currency-converter', methods=['POST'])
def currency_converter():
    try:
        record_tool_usage('currency-converter')
        
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
        
        return jsonify({
            'success': True,
            'amount': amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'converted_amount': round(converted_amount, 2),
            'rate': exchange_rates.get(from_currency, {}).get(to_currency, 1)
        })
        
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500

# 国际运费计算工具
@app.route('/api/tools/shipping-calculator', methods=['POST'])
def shipping_calculator():
    try:
        record_tool_usage('shipping-calculator')
        
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
            'currency': 'CNY'
        })
        
    except Exception as e:
        return jsonify({'error': f'计算失败: {str(e)}'}), 500

# 单位转换工具
@app.route('/api/tools/unit-converter', methods=['POST'])
def unit_converter():
    try:
        record_tool_usage('unit-converter')
        
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
        
        return jsonify({
            'success': True,
            'value': value,
            'from_unit': from_unit,
            'to_unit': to_unit,
            'conversion_type': conversion_type,
            'converted_value': round(converted_value, 4)
        })
        
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500

# 文件下载
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

# 获取工具使用统计
@app.route('/api/tools/usage-stats')
@login_required
def usage_stats():
    try:
        stats = ToolUsage.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'stats': [
                {
                    'tool_name': stat.tool_name,
                    'usage_count': stat.usage_count,
                    'last_used': stat.last_used.isoformat()
                }
                for stat in stats
            ]
        })
    except Exception as e:
        return jsonify({'error': f'获取统计失败: {str(e)}'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print('🌍 海外跨境小工具服务启动中...')
    print('📱 访问地址: http://localhost:5000')
    print('📁 上传目录:', os.path.abspath(app.config['UPLOAD_FOLDER']))
    print('💾 输出目录:', os.path.abspath(app.config['OUTPUT_FOLDER']))
    print('🗄️  数据库:', os.path.abspath('cross_border_tools.db'))
    app.run(debug=True, host='0.0.0.0', port=5000)