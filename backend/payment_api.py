"""
支付API接口
整合支付宝、微信支付和订单管理功能
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json
import traceback

from alipay_client import get_alipay_client
from wechat_pay_client import get_wechat_client
from order_manager import get_order_manager
from supabase import create_client

# 创建支付蓝图
payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

def get_supabase_client():
    """获取Supabase客户端"""
    return create_client(
        current_app.config['SUPABASE_URL'],
        current_app.config['SUPABASE_KEY']
    )

@payment_bp.route('/create-order', methods=['POST'])
def create_payment_order():
    """创建支付订单"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        plan = data.get('plan')
        payment_method = data.get('payment_method')
        device_info = data.get('device_info', {})
        
        # 验证参数
        if not all([user_id, plan, payment_method]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        if payment_method not in ['alipay', 'wechat']:
            return jsonify({
                'success': False,
                'error': '不支持的支付方式'
            }), 400
        
        # 创建订单
        supabase = get_supabase_client()
        order_manager = get_order_manager(supabase)
        result = order_manager.create_order(user_id, plan, payment_method, device_info)
        
        if not result['success']:
            return jsonify(result), 400
        
        order = result['order']
        plan_info = result['plan_info']
        
        # 根据支付方式创建支付
        if payment_method == 'alipay':
            alipay_client = get_alipay_client()
            payment_result = alipay_client.create_order(
                order_no=order['order_no'],
                subject=f"AI背景移除工具 - {plan_info['name']}",
                total_amount=plan_info['price'] / 100,  # 转换为元
                notify_url=f"{request.host_url}api/payment/alipay/notify",
                return_url=f"{request.host_url}payment/success?order_no={order['order_no']}"
            )
        else:  # wechat
            wechat_client = get_wechat_client()
            payment_result = wechat_client.create_order(
                order_no=order['order_no'],
                description=f"AI背景移除工具 - {plan_info['name']}",
                amount=plan_info['price'],
                notify_url=f"{request.host_url}api/payment/wechat/notify"
            )
        
        if payment_result['success']:
            return jsonify({
                'success': True,
                'order': order,
                'payment_info': payment_result['payment_info']
            })
        else:
            return jsonify(payment_result), 400
            
    except Exception as e:
        current_app.logger.error(f"创建支付订单异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': '创建订单失败'
        }), 500

@payment_bp.route('/alipay/notify', methods=['POST'])
def alipay_notify():
    """支付宝异步通知"""
    try:
        data = request.form.to_dict()
        
        # 验证签名
        alipay_client = get_alipay_client()
        if not alipay_client.verify_notify(data):
            return 'failure'
        
        # 处理订单
        order_no = data.get('out_trade_no')
        trade_status = data.get('trade_status')
        trade_no = data.get('trade_no')
        
        if trade_status == 'TRADE_SUCCESS' or trade_status == 'TRADE_FINISHED':
            supabase = get_supabase_client()
            order_manager = get_order_manager(supabase)
            
            # 更新订单状态
            update_result = order_manager.update_order_status(
                order_no=order_no,
                status='paid',
                transaction_id=trade_no,
                payment_data=data
            )
            
            if update_result['success']:
                # 激活会员
                activate_result = order_manager.activate_membership(order_no)
                if activate_result['success']:
                    current_app.logger.info(f"订单 {order_no} 支付成功，会员已激活")
                else:
                    current_app.logger.error(f"激活会员失败: {activate_result['error']}")
            else:
                current_app.logger.error(f"更新订单状态失败: {update_result['error']}")
        
        return 'success'
        
    except Exception as e:
        current_app.logger.error(f"支付宝通知处理异常: {str(e)}")
        return 'failure'

@payment_bp.route('/wechat/notify', methods=['POST'])
def wechat_notify():
    """微信支付异步通知"""
    try:
        data = request.get_data(as_text=True)
        
        # 验证签名
        wechat_client = get_wechat_pay_client()
        notify_data = wechat_client.parse_notify(data)
        
        if not notify_data:
            return jsonify({'code': 'FAIL', 'message': '签名验证失败'})
        
        # 处理订单
        if notify_data.get('trade_state') == 'SUCCESS':
            order_no = notify_data.get('out_trade_no')
            transaction_id = notify_data.get('transaction_id')
            
            supabase = get_supabase_client()
            order_manager = get_order_manager(supabase)
            
            # 更新订单状态
            update_result = order_manager.update_order_status(
                order_no=order_no,
                status='paid',
                transaction_id=transaction_id,
                payment_data=notify_data
            )
            
            if update_result['success']:
                # 激活会员
                activate_result = order_manager.activate_membership(order_no)
                if activate_result['success']:
                    current_app.logger.info(f"微信支付订单 {order_no} 支付成功，会员已激活")
                else:
                    current_app.logger.error(f"激活会员失败: {activate_result['error']}")
            else:
                current_app.logger.error(f"更新订单状态失败: {update_result['error']}")
        
        return jsonify({'code': 'SUCCESS', 'message': '处理成功'})
        
    except Exception as e:
        current_app.logger.error(f"微信支付通知处理异常: {str(e)}")
        return jsonify({'code': 'FAIL', 'message': '处理失败'})

@payment_bp.route('/query-order/<order_no>', methods=['GET'])
def query_order(order_no):
    """查询订单状态"""
    try:
        supabase = get_supabase_client()
        order_manager = get_order_manager(supabase)
        result = order_manager.get_order(order_no)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        current_app.logger.error(f"查询订单异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': '查询订单失败'
        }), 500

@payment_bp.route('/user-orders/<user_id>', methods=['GET'])
def get_user_orders(user_id):
    """获取用户订单列表"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        supabase = get_supabase_client()
        order_manager = get_order_manager(supabase)
        result = order_manager.get_user_orders(user_id, status, limit, offset)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取用户订单异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取订单列表失败'
        }), 500

@payment_bp.route('/plans', methods=['GET'])
def get_membership_plans():
    """获取会员计划信息"""
    try:
        supabase = get_supabase_client()
        order_manager = get_order_manager(supabase)
        
        plans = {}
        for plan_id, plan_info in order_manager.membership_plans.items():
            plans[plan_id] = {
                'name': plan_info['name'],
                'price': plan_info['price'],
                'price_yuan': plan_info['price'] / 100,
                'duration_days': plan_info['duration_days'],
                'features': plan_info['features']
            }
        
        return jsonify({
            'success': True,
            'plans': plans
        })
        
    except Exception as e:
        current_app.logger.error(f"获取会员计划异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取会员计划失败'
        }), 500

@payment_bp.route('/statistics', methods=['GET'])
def get_payment_statistics():
    """获取支付统计信息"""
    try:
        user_id = request.args.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        supabase = get_supabase_client()
        order_manager = get_order_manager(supabase)
        result = order_manager.get_order_statistics(user_id, start_date, end_date)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取支付统计异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取统计信息失败'
        }), 500

@payment_bp.route('/refund', methods=['POST'])
def refund_order():
    """申请退款"""
    try:
        data = request.get_json()
        order_no = data.get('order_no')
        refund_amount = data.get('refund_amount')
        reason = data.get('reason', '')
        
        if not order_no:
            return jsonify({
                'success': False,
                'error': '缺少订单号'
            }), 400
        
        supabase = get_supabase_client()
        order_manager = get_order_manager(supabase)
        result = order_manager.refund_order(order_no, refund_amount, reason)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"申请退款异常: {str(e)}")
        return jsonify({
            'success': False,
            'error': '申请退款失败'
        }), 500

@payment_bp.route('/health', methods=['GET'])
def payment_health():
    """支付服务健康检查"""
    try:
        # 检查各个支付客户端状态
        alipay_client = get_alipay_client()
        wechat_client = get_wechat_pay_client()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'services': {
                'alipay': 'available',
                'wechat': 'available',
                'order_manager': 'available'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"支付健康检查异常: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# 错误处理
@payment_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@payment_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500