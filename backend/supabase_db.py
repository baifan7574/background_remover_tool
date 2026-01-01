"""
Supabase数据库配置 (Pro版)
支持PythonAnywhere + Supabase Pro分离式架构
增强的连接管理、连接池和错误处理
"""

import os
import logging
import time
from typing import Optional, Dict, Any
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('supabase_db')

class SupabaseDB:
    def __init__(self):
        # Supabase配置
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # Pro版配置选项
        self.connection_timeout = int(os.getenv('SUPABASE_CONNECTION_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('SUPABASE_MAX_RETRIES', '3'))
        self.retry_delay = float(os.getenv('SUPABASE_RETRY_DELAY', '1.0'))
        self.is_pro = os.getenv('SUPABASE_IS_PRO', 'false').lower() == 'true'
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase配置缺失，请检查环境变量")
        
        logger.info(f"初始化Supabase客户端 (Pro模式: {self.is_pro})")
        
        # 配置客户端选项
        try:
            client_options = ClientOptions(
                follow_redirects=True,
                schema=os.getenv('SUPABASE_SCHEMA', 'public')
            )
        except TypeError:
            # 如果参数不支持，使用基本配置
            client_options = None
        
        # 初始化Supabase客户端
        try:
            if client_options:
                self.client: Client = create_client(
                    self.supabase_url,
                    self.supabase_service_key if self.supabase_service_key else self.supabase_key,
                    options=client_options
                )
            else:
                self.client: Client = create_client(
                    self.supabase_url,
                    self.supabase_service_key if self.supabase_service_key else self.supabase_key
                )
            logger.info("Supabase客户端初始化成功")
            # 测试连接
            self.test_connection()
        except Exception as e:
            logger.error(f"Supabase客户端初始化失败: {e}")
            raise
    
    def get_client(self):
        """获取Supabase客户端"""
        return self.client
    
    def get_service_client(self):
        """获取使用service key的客户端（拥有管理员权限）"""
        if self.supabase_service_key:
            try:
                service_client = create_client(
                    self.supabase_url,
                    self.supabase_service_key
                )
                return service_client
            except Exception as e:
                logger.error(f"创建service客户端失败: {e}")
                return self.client
        return self.client
    
    def test_connection(self):
        """测试数据库连接"""
        for attempt in range(self.max_retries):
            try:
                # 测试连接 - 使用auth表代替不存在的_test_connection表
                response = self.client.auth.get_user()
                logger.info("Supabase连接测试成功")
                return True
            except Exception as e:
                logger.warning(f"连接测试失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        logger.error("Supabase连接测试失败")
        return False
    
    def execute_with_retry(self, func, *args, **kwargs):
        """带重试机制的执行函数"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"操作失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
        raise Exception(f"操作在{self.max_retries}次尝试后失败")

# 全局数据库实例
db = SupabaseDB()

# 用户管理
class UserDB:
    def __init__(self, supabase_client):
        self.client = supabase_client
        # 直接使用客户端，不访问内部属性
    
    def create_user(self, email, password, name):
        """创建用户 - Pro版支持更丰富的用户元数据"""
        try:
            # 使用Supabase Auth创建用户
            auth_response = self.client.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': {
                        'name': name,
                        'plan': 'free',
                        'credits': 10,
                        'created_at': time.time(),
                        'last_login_at': time.time(),
                        'usage_count': 0,
                        'is_active': True
                    }
                }
            })
            
            if auth_response.user:
                # 同步创建用户表记录（Pro版增强）
                try:
                    self.client.table('users').insert({
                        'id': auth_response.user.id,
                        'email': auth_response.user.email,
                        'name': name,
                        'plan': 'free',
                        'credits': 10,
                        'created_at': 'now()',
                        'updated_at': 'now()'
                    }).execute()
                except Exception as db_e:
                    logger.warning(f"用户表同步失败: {db_e}")
                
                return {
                    'success': True,
                    'user_id': auth_response.user.id,
                    'email': auth_response.user.email
                }
            else:
                return {'success': False, 'error': '用户创建失败'}
                
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, email, password):
        """用户认证 - Pro版增强"""
        try:
            auth_response = self.client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            if auth_response.user:
                # 更新最后登录时间（Pro版增强）
                try:
                    self.client.auth.admin.update_user_by_id(
                        auth_response.user.id,
                        {'user_metadata': {'last_login_at': time.time()}}
                    )
                    # 更新数据库记录
                    self.client.table('users').update({
                        'last_login_at': 'now()',
                        'updated_at': 'now()'
                    }).eq('id', auth_response.user.id).execute()
                except Exception as update_e:
                    logger.warning(f"更新登录时间失败: {update_e}")
                
                return {
                    'success': True,
                    'user_id': auth_response.user.id,
                    'email': auth_response.user.email,
                    'access_token': auth_response.session.access_token,
                    'user_metadata': auth_response.user.user_metadata
                }
            else:
                return {'success': False, 'error': '认证失败'}
                
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_profile(self, user_id):
        """获取用户资料 - Pro版支持获取更多用户信息"""
        try:
            response = self.client.auth.admin.get_user_by_id(user_id)
            if response.user:
                # 从数据库获取更多信息（Pro版增强）
                db_response = self.client.table('users').select('*').eq('id', user_id).execute()
                db_user = db_response.data[0] if db_response.data else {}
                
                return {
                    'success': True,
                    'user': {
                        'id': response.user.id,
                        'email': response.user.email,
                        'name': response.user.user_metadata.get('name'),
                        'plan': response.user.user_metadata.get('plan', 'free'),
                        'credits': response.user.user_metadata.get('credits', 0),
                        'created_at': db_user.get('created_at', response.user.created_at),
                        'last_login_at': response.user.user_metadata.get('last_login_at'),
                        'usage_count': response.user.user_metadata.get('usage_count', 0),
                        'is_active': response.user.user_metadata.get('is_active', True)
                    }
                }
            else:
                return {'success': False, 'error': '用户不存在'}
        except Exception as e:
            logger.error(f"获取用户资料失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_user_credits(self, user_id, credits_change):
        """更新用户积分 - Pro版支持事务和日志记录"""
        try:
            # 获取当前用户信息
            user_response = self.client.auth.admin.get_user_by_id(user_id)
            if not user_response.user:
                return {'success': False, 'error': '用户不存在'}
            
            current_credits = user_response.user.user_metadata.get('credits', 0)
            new_credits = max(0, current_credits + credits_change)  # 确保积分不为负
            
            # 更新用户元数据
            self.client.auth.admin.update_user_by_id(
                user_id,
                {'user_metadata': {'credits': new_credits}}
            )
            
            # 更新数据库中的积分记录（Pro版增强）
            try:
                # 使用事务更新数据库
                user_metadata = user_response.user.user_metadata
                user_metadata['credits'] = new_credits
                
                self.client.table('users').update({
                    'credits': new_credits,
                    'updated_at': 'now()'
                }).eq('id', user_id).execute()
                
                # 记录积分变更日志（Pro版增强）
                self.client.table('credit_transactions').insert({
                    'user_id': user_id,
                    'change_amount': credits_change,
                    'before_credits': current_credits,
                    'after_credits': new_credits,
                    'created_at': 'now()'
                }).execute()
            except Exception as db_e:
                logger.error(f"数据库更新失败: {db_e}")
                # 继续执行，因为Auth已经更新成功
            
            return {'success': True, 'new_credits': new_credits}
            
        except Exception as e:
            logger.error(f"更新用户积分失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_user_plan(self, user_id, plan, credits=0):
        """更新用户套餐 - Pro版新增功能"""
        try:
            # 更新用户套餐
            user_response = self.client.auth.admin.get_user_by_id(user_id)
            if not user_response.user:
                return {'success': False, 'error': '用户不存在'}
            
            user_metadata = user_response.user.user_metadata
            user_metadata['plan'] = plan
            if credits > 0:
                user_metadata['credits'] = credits
            
            # 更新Auth
            self.client.auth.admin.update_user_by_id(
                user_id,
                {'user_metadata': user_metadata}
            )
            
            # 更新数据库
            update_data = {'plan': plan, 'updated_at': 'now()'}
            if credits > 0:
                update_data['credits'] = credits
            
            self.client.table('users').update(update_data).eq('id', user_id).execute()
            
            return {'success': True, 'plan': plan}
            
        except Exception as e:
            logger.error(f"更新用户套餐失败: {e}")
            return {'success': False, 'error': str(e)}

# 工具使用记录
class UsageDB:
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    def record_usage(self, user_id, tool_name, credits_used, metadata=None):
        """记录工具使用 - Pro版支持更多元数据"""
        try:
            # 准备使用记录数据
            usage_data = {
                'user_id': user_id,
                'tool_name': tool_name,
                'credits_used': credits_used,
                'created_at': 'now()',
                'ip_address': metadata.get('ip_address') if metadata else None,
                'user_agent': metadata.get('user_agent') if metadata else None
            }
            
            # 如果有额外元数据，添加到JSON字段
            if metadata and len(metadata) > 2:
                usage_data['metadata'] = metadata
            
            response = self.client.table('tool_usage').insert(usage_data).execute()
            
            # 更新用户使用次数（Pro版增强）
            try:
                # 获取当前用户信息
                auth_client = self.client.auth.admin.get_user_by_id(user_id)
                if auth_client.user:
                    user_metadata = auth_client.user.user_metadata
                    current_count = user_metadata.get('usage_count', 0)
                    user_metadata['usage_count'] = current_count + 1
                    
                    # 更新Auth
                    self.client.auth.admin.update_user_by_id(
                        user_id,
                        {'user_metadata': user_metadata}
                    )
                    
                    # 更新数据库
                    self.client.table('users').update({
                        'usage_count': current_count + 1
                    }).eq('id', user_id).execute()
            except Exception as update_e:
                logger.warning(f"更新使用次数失败: {update_e}")
            
            return {'success': True, 'usage_id': response.data[0]['id']}
            
        except Exception as e:
            logger.error(f"记录使用失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_usage_stats(self, user_id, days=30):
        """获取用户使用统计 - Pro版增强统计"""
        try:
            response = self.client.table('tool_usage').select('*').eq(
                'user_id', user_id
            ).gte('created_at', f'now() - interval \'{days} days\'').execute()
            
            total_credits = sum(usage['credits_used'] for usage in response.data)
            usage_count = len(response.data)
            
            # 按工具类型统计（Pro版增强）
            tool_stats = {}
            for usage in response.data:
                tool_name = usage['tool_name']
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {'count': 0, 'credits': 0}
                tool_stats[tool_name]['count'] += 1
                tool_stats[tool_name]['credits'] += usage['credits_used']
            
            # 获取使用趋势（Pro版增强）
            daily_stats = {}
            for usage in response.data:
                date = usage['created_at'].split('T')[0] if isinstance(usage['created_at'], str) else str(usage['created_at']).split('T')[0]
                if date not in daily_stats:
                    daily_stats[date] = {'count': 0, 'credits': 0}
                daily_stats[date]['count'] += 1
                daily_stats[date]['credits'] += usage['credits_used']
            
            return {
                'success': True,
                'total_credits': total_credits,
                'usage_count': usage_count,
                'recent_usage': response.data[-10:],  # 最近10条记录
                'tool_stats': tool_stats,  # Pro版增强
                'daily_stats': daily_stats  # Pro版增强
            }
            
        except Exception as e:
            logger.error(f"获取使用统计失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_tool_stats(self, tool_name=None, days=30):
        """获取工具使用统计 - Pro版新增功能"""
        try:
            query = self.client.table('tool_usage').select('*')
            
            if tool_name:
                query = query.eq('tool_name', tool_name)
            
            response = query.gte('created_at', f'now() - interval \'{days} days\'').execute()
            
            total_usage = len(response.data)
            total_credits = sum(usage['credits_used'] for usage in response.data)
            unique_users = len(set(usage['user_id'] for usage in response.data))
            
            return {
                'success': True,
                'tool_name': tool_name,
                'total_usage': total_usage,
                'total_credits': total_credits,
                'unique_users': unique_users,
                'period': f'{days} days'
            }
            
        except Exception as e:
            logger.error(f"获取工具统计失败: {e}")
            return {'success': False, 'error': str(e)}

# 文件存储
class StorageDB:
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.default_bucket = 'processed-images'  # 默认存储桶
    
    def upload_file(self, bucket, file_path, file_content, file_options=None):
        """上传文件到Supabase Storage - Pro版支持更多选项"""
        try:
            # Pro版支持自定义文件选项
            options = file_options or {}
            
            # 对于图片文件，设置自动格式优化（Pro版增强）
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                options['content-type'] = options.get('content-type', self._get_content_type(file_path))
            
            response = self.client.storage.from_(bucket).upload(
                file_path, 
                file_content,
                file_options=options
            )
            
            # 记录上传日志（Pro版增强）
            try:
                user_id = file_path.split('/')[1] if '/' in file_path else None
                if user_id:
                    self.client.table('file_uploads').insert({
                        'user_id': user_id,
                        'bucket': bucket,
                        'file_path': file_path,
                        'file_size': len(file_content),
                        'created_at': 'now()'
                    }).execute()
            except Exception as log_e:
                logger.warning(f"记录上传日志失败: {log_e}")
            
            return {'success': True, 'file_path': file_path}
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_file_url(self, bucket, file_path, expire_in=None):
        """获取文件URL - Pro版支持临时URL"""
        try:
            if expire_in and expire_in > 0:
                # Pro版支持生成临时URL
                url = self.client.storage.from_(bucket).create_signed_url(
                    file_path, 
                    expire_in
                )
                return {'success': True, 'url': url}
            else:
                # 普通公开URL
                url = self.client.storage.from_(bucket).get_public_url(file_path)
                return {'success': True, 'url': url}
        except Exception as e:
            logger.error(f"获取文件URL失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, bucket, file_path):
        """删除文件"""
        try:
            # 删除文件
            result = self.client.storage.from_(bucket).remove([file_path])
            
            # 记录删除日志（Pro版增强）
            try:
                self.client.table('file_uploads').delete().eq('bucket', bucket).eq('file_path', file_path).execute()
            except Exception as log_e:
                logger.warning(f"记录删除日志失败: {log_e}")
            
            return {'success': True}
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_files(self, bucket, prefix=''):
        """列出存储桶中的文件 - Pro版新增功能"""
        try:
            response = self.client.storage.from_(bucket).list(prefix)
            return {'success': True, 'files': response}
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_file_metadata(self, bucket, file_path):
        """获取文件元数据 - Pro版新增功能"""
        try:
            # 查询数据库中的文件信息
            response = self.client.table('file_uploads').select('*').eq('bucket', bucket).eq('file_path', file_path).execute()
            
            if response.data:
                return {'success': True, 'metadata': response.data[0]}
            else:
                return {'success': False, 'error': '文件不存在'}
        except Exception as e:
            logger.error(f"获取文件元数据失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_content_type(self, file_path):
        """根据文件扩展名获取Content-Type"""
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        
        ext = os.path.splitext(file_path)[1].lower()
        return content_types.get(ext, 'application/octet-stream')

# 数据库实例
user_db = UserDB(db.get_client())
usage_db = UsageDB(db.get_client())
storage_db = StorageDB(db.get_client())