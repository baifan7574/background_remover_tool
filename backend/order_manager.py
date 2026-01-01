"""
订单管理系统
处理支付订单的创建、查询、更新等操作
"""

import uuid
import json
from datetime import datetime, timedelta
from decimal import Decimal
from supabase import create_client

class OrderManager:
    """订单管理器"""
    
    def __init__(self, supabase_client):
        """
        初始化订单管理器
        
        Args:
            supabase_client: Supabase客户端实例
        """
        self.supabase = supabase_client
        
        # 会员计划配置
        self.membership_plans = {
            'basic': {
                'name': '基础版',
                'price': 1900,  # 19.00元（分为单位）
                'duration_days': 30,
                'features': ['高质量背景移除', '多格式支持', '优先处理']
            },
            'professional': {
                'name': '专业版',
                'price': 9900,  # 99.00元
                'duration_days': 30,
                'features': ['无限背景移除', '批量处理', 'API访问', '高级功能']
            },
            'flagship': {
                'name': '旗舰版',
                'price': 29900,  # 299.00元
                'duration_days': 30,
                'features': ['无限背景移除', '批量处理', 'API访问', '高级功能', '专属客服']
            }
        }
    
    def create_order(self, user_id, plan, payment_method, device_info=None):
        """
        创建支付订单
        
        Args:
            user_id: 用户ID (user_profiles.user_id字段)
            plan: 会员计划
            payment_method: 支付方式（alipay/wechat）
            device_info: 设备信息
            
        Returns:
            订单信息
        """
        try:
            # 验证会员计划
            if plan not in self.membership_plans:
                return {
                    'success': False,
                    'error': '无效的会员计划'
                }
            
            plan_info = self.membership_plans[plan]
            
            # 根据user_id查找用户的真实ID（user_profiles.id字段）
            user_response = self.supabase.table('user_profiles').select('id').eq('user_id', user_id).execute()
            
            if not user_response.data or len(user_response.data) == 0:
                return {
                    'success': False,
                    'error': f'用户 {user_id} 不存在'
                }
            
            # 使用数据库中的真实ID
            real_user_id = user_response.data[0]['id']
            
            # 生成订单号
            order_no = self._generate_order_no()
            
            # 创建订单数据 - 匹配数据库表结构
            order_data = {
                'order_no': order_no,
                'user_id': real_user_id,  # 使用真实的数据库ID
                'membership_type': plan,  # 使用正确的字段名
                'membership_duration': plan_info['duration_days'] // 30,  # 转换为月数
                'payment_method': payment_method,
                'amount': plan_info['price'],
                'original_price': plan_info['price'],  # 原价
                'status': 'pending',  # pending, paid, failed, refunded
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # 插入数据库
            response = self.supabase.table('payment_records').insert(order_data).execute()
            
            if response.data:
                return {
                    'success': True,
                    'order': response.data[0],
                    'plan_info': plan_info
                }
            else:
                return {
                    'success': False,
                    'error': '创建订单失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'创建订单异常: {str(e)}'
            }
    
    def get_order(self, order_no=None, order_id=None):
        """
        获取订单信息
        
        Args:
            order_no: 订单号
            order_id: 订单ID
            
        Returns:
            订单信息
        """
        try:
            if order_no:
                response = self.supabase.table('payment_records').select('*').eq('order_no', order_no).execute()
            elif order_id:
                response = self.supabase.table('payment_records').select('*').eq('id', order_id).execute()
            else:
                return {'success': False, 'error': '必须提供order_no或order_id'}
            
            if response.data and len(response.data) > 0:
                return {
                    'success': True,
                    'order': response.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': '订单不存在'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'获取订单异常: {str(e)}'
            }
    
    def update_order_status(self, order_no, status, transaction_id=None, payment_data=None):
        """
        更新订单状态
        
        Args:
            order_no: 订单号
            status: 新状态
            transaction_id: 第三方交易号
            payment_data: 支付数据
            
        Returns:
            更新结果
        """
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if transaction_id:
                update_data['transaction_id'] = transaction_id
            
            if payment_data:
                update_data['payment_data'] = json.dumps(payment_data, ensure_ascii=False)
            
            # 如果是支付成功，记录支付时间
            if status == 'paid':
                update_data['paid_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('payment_records').update(update_data).eq('order_no', order_no).execute()
            
            if response.data and len(response.data) > 0:
                return {
                    'success': True,
                    'order': response.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': '更新订单失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'更新订单异常: {str(e)}'
            }
    
    def activate_membership(self, order_no):
        """
        激活会员权益
        
        Args:
            order_no: 订单号
            
        Returns:
            激活结果
        """
        try:
            # 获取订单信息
            order_result = self.get_order(order_no)
            if not order_result['success']:
                return order_result
            
            order = order_result['order']
            real_user_id = order['user_id']  # 这是user_profiles表的id字段
            plan = order['membership_type']  # 修正字段名
            duration_days = order['membership_duration'] * 30  # 修正字段名并转换为天数
            
            # 计算会员到期时间
            start_time = datetime.now()
            end_time = start_time + timedelta(days=duration_days)
            
            # 更新用户会员信息 - 使用正确的字段名
            update_data = {
                'plan': plan,
                'membership_type': plan,  # 同时更新membership_type字段
                'membership_expires_at': end_time.isoformat(),  # 使用正确的字段名
                'updated_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('user_profiles').update(update_data).eq('id', real_user_id).execute()
            
            if response.data and len(response.data) > 0:
                # 获取用户的user_id用于日志记录
                user_profile = response.data[0]
                user_id_for_log = user_profile.get('user_id', real_user_id)
                
                # 记录会员激活日志
                log_data = {
                    'user_id': user_id_for_log,
                    'order_no': order_no,
                    'plan': plan,
                    'action': 'activate',
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'created_at': datetime.now().isoformat()
                }
                
                self.supabase.table('membership_logs').insert(log_data).execute()
                
                return {
                    'success': True,
                    'user': response.data[0],
                    'membership_end': end_time.isoformat()  # 保持API兼容性
                }
            else:
                return {
                    'success': False,
                    'error': '激活会员失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'激活会员异常: {str(e)}'
            }
    
    def get_user_orders(self, user_id, status=None, limit=20, offset=0):
        """
        获取用户订单列表
        
        Args:
            user_id: 用户ID
            status: 订单状态过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            订单列表
        """
        try:
            query = self.supabase.table('payment_records').select('*').eq('user_id', user_id)
            
            if status:
                query = query.eq('status', status)
            
            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            
            return {
                'success': True,
                'orders': response.data or []
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取订单列表异常: {str(e)}'
            }
    
    def get_order_statistics(self, user_id=None, start_date=None, end_date=None):
        """
        获取订单统计信息
        
        Args:
            user_id: 用户ID（可选）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息
        """
        try:
            query = self.supabase.table('payment_records').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            if start_date:
                query = query.gte('created_at', start_date)
            
            if end_date:
                query = query.lte('created_at', end_date)
            
            response = query.execute()
            orders = response.data or []
            
            # 统计计算
            total_orders = len(orders)
            paid_orders = [o for o in orders if o['status'] == 'paid']
            total_amount = sum(o['amount'] for o in paid_orders)
            
            # 按计划统计
            plan_stats = {}
            for order in paid_orders:
                plan = order['plan']
                if plan not in plan_stats:
                    plan_stats[plan] = {'count': 0, 'amount': 0}
                plan_stats[plan]['count'] += 1
                plan_stats[plan]['amount'] += order['amount']
            
            return {
                'success': True,
                'statistics': {
                    'total_orders': total_orders,
                    'paid_orders': len(paid_orders),
                    'total_amount': total_amount,
                    'conversion_rate': len(paid_orders) / total_orders if total_orders > 0 else 0,
                    'plan_statistics': plan_stats
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取统计信息异常: {str(e)}'
            }
    
    def _generate_order_no(self):
        """生成订单号"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = str(uuid.uuid4())[:8].upper()
        return f"ORDER{timestamp}{random_str}"
    
    def refund_order(self, order_no, refund_amount=None, reason=""):
        """
        订单退款
        
        Args:
            order_no: 订单号
            refund_amount: 退款金额（分）
            reason: 退款原因
            
        Returns:
            退款结果
        """
        try:
            # 获取订单信息
            order_result = self.get_order(order_no)
            if not order_result['success']:
                return order_result
            
            order = order_result['order']
            
            if order['status'] != 'paid':
                return {
                    'success': False,
                    'error': '只能退款已支付的订单'
                }
            
            # 默认全额退款
            if not refund_amount:
                refund_amount = order['amount']
            
            # 创建退款记录
            refund_data = {
                'refund_no': self._generate_order_no().replace('ORDER', 'REFUND'),
                'order_no': order_no,
                'user_id': order['user_id'],
                'refund_amount': refund_amount,
                'reason': reason,
                'status': 'processing',  # processing, success, failed
                'created_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('refund_records').insert(refund_data).execute()
            
            if response.data:
                # 更新订单状态
                self.update_order_status(order_no, 'refunded')
                
                return {
                    'success': True,
                    'refund': response.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': '创建退款记录失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'退款异常: {str(e)}'
            }

# 全局订单管理器实例
def get_order_manager(supabase_client):
    """获取订单管理器实例"""
    return OrderManager(supabase_client)