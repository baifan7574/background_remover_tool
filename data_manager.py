#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据持久化管理器
解决数据丢失问题
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import uuid

class DataManager:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.users_file = self.data_dir / 'users.json'
        self.profiles_file = self.data_dir / 'profiles.json'
        self.usage_file = self.data_dir / 'usage.json'
        self.invites_file = self.data_dir / 'invites.json'  # 邀请关系数据
        self.orders_file = self.data_dir / 'orders.json'  # 订单数据
        
        # 初始化数据
        self.users_db = self.load_data(self.users_file, {})
        self.user_profiles_db = self.load_data(self.profiles_file, {})
        self.tool_usage_db = self.load_data(self.usage_file, {})
        self.invites_db = self.load_data(self.invites_file, {})  # 邀请关系：{invite_code: inviter_user_id, ...}
        self.orders_db = self.load_data(self.orders_file, {})  # 订单数据：{order_no: order_data, ...}
        
        print(f"✅ 数据持久化管理器初始化成功")
        print(f"📁 数据目录: {self.data_dir.absolute()}")
        print(f"👥 用户数量: {len(self.users_db)}")
        print(f"📊 资料数量: {len(self.user_profiles_db)}")
    
    def load_data(self, file_path, default_data):
        """加载数据文件"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ 成功加载 {file_path.name}: {len(data)} 条记录")
                return data
            else:
                print(f"📝 创建新文件 {file_path.name}")
                return default_data
        except Exception as e:
            print(f"❌ 加载 {file_path.name} 失败: {e}")
            return default_data
    
    def save_data(self, file_path, data):
        """保存数据到文件"""
        try:
            # 创建备份
            if file_path.exists():
                backup_path = file_path.with_suffix('.json.bak')
                try:
                    import shutil
                    shutil.copy2(str(file_path), str(backup_path))
                except Exception as backup_error:
                    print(f"⚠️ 备份 {file_path.name} 失败: {backup_error}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 成功保存 {file_path.name}: {len(data)} 条记录")
            return True
        except Exception as e:
            print(f"❌ 保存 {file_path.name} 失败: {e}")
            return False
    
    def save_users(self):
        """保存用户数据"""
        return self.save_data(self.users_file, self.users_db)
    
    def save_profiles(self):
        """保存用户资料数据"""
        return self.save_data(self.profiles_file, self.user_profiles_db)
    
    def save_usage(self):
        """保存使用记录数据"""
        return self.save_data(self.usage_file, self.tool_usage_db)
    
    def save_invites(self):
        """保存邀请关系数据"""
        return self.save_data(self.invites_file, self.invites_db)
    
    def save_orders(self):
        """保存订单数据"""
        return self.save_data(self.orders_file, self.orders_db)
    
    def save_all(self):
        """保存所有数据"""
        results = {
            'users': self.save_users(),
            'profiles': self.save_profiles(),
            'usage': self.save_usage(),
            'invites': self.save_invites(),
            'orders': self.save_orders()
        }
        success_count = sum(results.values())
        print(f"💾 数据保存完成: {success_count}/5 个文件成功")
        return success_count == 5
    
    def save_order(self, order_data):
        """保存单个订单"""
        if not hasattr(self, 'orders_db'):
            self.orders_db = {}
        
        order_no = order_data.get('order_no')
        if order_no:
            self.orders_db[order_no] = order_data
            result = self.save_orders()
            # 同步更新 payment_orders (如果在 sk_app 中引用了)
            return result
        return False
    
    def create_user(self, email, password, name, plan='free'):
        """创建用户"""
        user_id = str(uuid.uuid4())
        token = f"mock_token_{user_id[:8]}"
        
        # 确保邮箱转小写存储
        email_lower = email.lower().strip() if email else ''
        
        # 创建用户
        self.users_db[user_id] = {
            'email': email_lower,
            'password': password,
            'token': token,
            'created_at': datetime.now().isoformat()
        }
        
        # 生成邀请码（8位随机字符串）
        invite_code = self.generate_invite_code()
        
        # 创建用户资料
        self.user_profiles_db[user_id] = {
            'user_id': user_id,
            'email': email_lower,
            'name': name,
            'plan': plan,
            'daily_usage': {},
            'usage_stats': self.get_default_usage_stats(plan),
            'invite_code': invite_code,  # 用户的邀请码
            'invited_by': None,  # 邀请人ID（如果使用邀请码注册）
            'invite_rewards': {  # 邀请奖励记录
                'daily_rewards': {},  # {date: {tool: count}} 每日奖励
                'one_time_rewards': []  # [{date, tool, count, expires_at}] 一次性奖励
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 注册邀请码到邀请关系表
        self.invites_db[invite_code] = user_id
        
        # 保存数据
        self.save_all()
        
        return user_id, token
    
    def generate_invite_code(self):
        """生成唯一的邀请码（8位大写字母+数字）"""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if code not in self.invites_db:
                return code
    
    def get_inviter_by_code(self, invite_code):
        """通过邀请码获取邀请人ID"""
        return self.invites_db.get(invite_code.upper())
    
    def add_invite_reward(self, user_id, reward_type, tool_name, count, days=0):
        """添加邀请奖励
        reward_type: 'daily' 每日奖励（持续N天）或 'one_time' 一次性奖励
        """
        if user_id not in self.user_profiles_db:
            return False, "用户不存在"
        
        profile = self.user_profiles_db[user_id]
        if 'invite_rewards' not in profile:
            profile['invite_rewards'] = {
                'daily_rewards': {},
                'one_time_rewards': []
            }
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        if reward_type == 'daily':
            # 每日奖励：记录未来N天的奖励
            for i in range(days):
                reward_date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                if reward_date not in profile['invite_rewards']['daily_rewards']:
                    profile['invite_rewards']['daily_rewards'][reward_date] = {}
                if tool_name not in profile['invite_rewards']['daily_rewards'][reward_date]:
                    profile['invite_rewards']['daily_rewards'][reward_date][tool_name] = 0
                profile['invite_rewards']['daily_rewards'][reward_date][tool_name] += count
        elif reward_type == 'one_time':
            # 一次性奖励：30天内有效
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
            profile['invite_rewards']['one_time_rewards'].append({
                'date': today,
                'tool': tool_name,
                'count': count,
                'expires_at': expires_at,
                'used': 0
            })
        
        profile['updated_at'] = datetime.now().isoformat()
        self.save_all()
        return True, "奖励已添加"
    
    def get_default_usage_stats(self, plan='free'):
        """获取默认使用统计"""
        # 注意：此配置必须与 sk_app.py 中的 PLAN_DAILY_LIMITS 保持一致
        # 直接定义套餐限制，避免循环导入
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
        
        stats = {}
        plan_limits = PLAN_DAILY_LIMITS.get(plan, PLAN_DAILY_LIMITS['free'])
        
        for tool_name, daily_limit in plan_limits.items():
            stats[tool_name] = {
                'current_usage': 0,
                'daily_limit': daily_limit,
                'remaining_usage': daily_limit if daily_limit != -1 else -1
            }
        
        return stats
    
    def get_user_by_token(self, token):
        """通过token获取用户"""
        # 先在内存中查找
        found_user = self._find_user_by_token_in_memory(token)
        if found_user:
            return found_user
            
        # 如果没找到，尝试重新加载数据（处理多进程不同步问题）
        print(f"🔄 内存中未找到用户Token，尝试重新加载用户数据...")
        self.users_db = self.load_data(self.users_file, {})
        
        # 再次查找
        return self._find_user_by_token_in_memory(token)
    
    def _find_user_by_token_in_memory(self, token):
        """仅在内存中查找用户Token"""
        for user_id, user_data in self.users_db.items():
            if user_data.get('token') == token:
                return {
                    'id': user_id,
                    'email': user_data['email'],
                    'password': user_data['password'],
                    'token': token
                }
        return None
    
    def get_user_by_email(self, email):
        """通过邮箱获取用户"""
        # 确保邮箱转小写进行比较
        email_lower = email.lower().strip() if email else ''
        for user_id, user_data in self.users_db.items():
            stored_email = user_data.get('email', '').lower().strip()
            if stored_email == email_lower:
                return {
                    'id': user_id,
                    'email': user_data['email'],
                    'password': user_data['password'],
                    'token': user_data['token']
                }
        return None
    
    def authenticate_user(self, email, password):
        """用户认证"""
        # 确保邮箱转小写
        email_lower = email.lower().strip() if email else ''
        user = self.get_user_by_email(email_lower)
        
        if user:
            # 比较密码（确保密码一致）
            if user.get('password') == password:
                # 生成新token
                new_token = f"mock_token_{user['id'][:8]}"
                self.users_db[user['id']]['token'] = new_token
                self.save_users()
                user['token'] = new_token
                return user
            else:
                print(f"密码验证失败 - 存储的密码长度: {len(user.get('password', ''))}, 输入的密码长度: {len(password)}")
        else:
            print(f"用户未找到 - 邮箱: {email_lower}")
        
        return None
    
    def get_user_profile(self, user_id):
        """获取用户资料"""
        # 如果内存中没有，尝试重新加载
        if user_id not in self.user_profiles_db:
            print(f"🔄 内存中未找到用户资料 {user_id}，尝试重新加载...")
            self.user_profiles_db = self.load_data(self.profiles_file, {})

        if user_id in self.user_profiles_db:
            profile = self.user_profiles_db[user_id].copy()
            
            # 更新使用统计
            today = datetime.now().strftime('%Y-%m-%d')
            daily_usage = profile.get('daily_usage', {})
            today_usage = daily_usage.get(today, {})
            
            # 获取当前计划的所有工具配置
            plan = profile.get('plan', 'free')
            default_stats = self.get_default_usage_stats(plan)
            
            # 补充缺失的工具到 usage_stats（兼容老会员）
            if 'usage_stats' not in profile:
                profile['usage_stats'] = {}
                
            for tool_name, tool_stats in default_stats.items():
                if tool_name not in profile['usage_stats']:
                    # 新工具，添加到 usage_stats
                    profile['usage_stats'][tool_name] = {
                        'current_usage': 0,
                        'daily_limit': tool_stats['daily_limit'],
                        'remaining_usage': tool_stats['remaining_usage']
                    }
                else:
                    # 已存在的工具，更新限制（如果配置有变化）
                    profile['usage_stats'][tool_name]['daily_limit'] = tool_stats['daily_limit']
            
            # 更新所有工具的使用次数和剩余次数
            for tool_name in profile['usage_stats']:
                current_usage = today_usage.get(tool_name, 0)
                daily_limit = profile['usage_stats'][tool_name]['daily_limit']
                remaining = daily_limit - current_usage if daily_limit != -1 else -1
                
                profile['usage_stats'][tool_name]['current_usage'] = current_usage
                profile['usage_stats'][tool_name]['remaining_usage'] = remaining
            
            # 保存更新后的资料（包含新工具）
            self.save_all()
            
            return profile
        return None
    
    def record_usage(self, user_id, tool_name):
        """记录工具使用"""
        if user_id not in self.user_profiles_db:
            return False, "用户不存在"
        
        profile = self.user_profiles_db[user_id]
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 初始化daily_usage
        if 'daily_usage' not in profile:
            profile['daily_usage'] = {}
        
        if today not in profile['daily_usage']:
            profile['daily_usage'][today] = {}
        
        # 增加使用次数
        current_count = profile['daily_usage'][today].get(tool_name, 0)
        profile['daily_usage'][today][tool_name] = current_count + 1
        profile['updated_at'] = datetime.now().isoformat()
        
        # 保存数据
        self.save_all()
        
        return True, f"使用次数已记录，今日使用{current_count + 1}次"
    
    def get_all_users(self):
        """获取所有用户信息（调试用）"""
        users_info = []
        for user_id, user_data in self.users_db.items():
            profile = self.user_profiles_db.get(user_id, {})
            users_info.append({
                'user_id': user_id,
                'email': user_data.get('email', '未知'),
                'name': profile.get('name', '未知'),
                'plan': profile.get('plan', '未知'),
                'token': user_data.get('token', '未知'),
                'created_at': user_data.get('created_at', '未知')
            })
        return users_info

# 全局数据管理器实例
data_manager = None

def get_data_manager():
    """获取数据管理器实例"""
    global data_manager
    if data_manager is None:
        data_manager = DataManager()
    return data_manager

if __name__ == '__main__':
    # 测试数据管理器
    dm = DataManager()
    
    print("\n=== 测试创建用户 ===")
    result = dm.create_user(
        user_id='test-123',
        email='test@example.com',
        password='123456',
        name='测试用户'
    )
    print(f"创建结果: {result}")
    
    print("\n=== 所有用户信息 ===")
    users = dm.get_all_users()
    for user in users:
        print(f"用户: {user}")
    
    print("\n=== 测试token验证 ===")
    token = result['token']
    user = dm.get_user_by_token(token)
    print(f"Token验证结果: {user}")
    
    print("\n=== 测试使用记录 ===")
    success, message = dm.record_usage('test-123', 'background_remover')
    print(f"使用记录: {success}, {message}")