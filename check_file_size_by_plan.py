# 检查文件大小限制的辅助函数（用于后端）

def get_max_file_size_by_plan(plan):
    """根据会员类型获取文件大小限制（字节）"""
    plan_limits = {
        'free': 5 * 1024 * 1024,          # 5MB
        'basic': 10 * 1024 * 1024,        # 10MB
        'professional': 50 * 1024 * 1024,  # 50MB
        'flagship': 100 * 1024 * 1024,    # 100MB
        'enterprise': 500 * 1024 * 1024   # 500MB
    }
    return plan_limits.get(plan, 5 * 1024 * 1024)  # 默认5MB

def check_file_size_by_user(user, file_size):
    """检查文件大小是否超过用户会员类型限制
    
    Args:
        user: 用户信息字典，包含 'plan' 字段
        file_size: 文件大小（字节）
    
    Returns:
        (is_valid, error_message)
        is_valid: True表示文件大小符合限制，False表示超过限制
        error_message: 如果超过限制，返回错误信息
    """
    plan = user.get('plan') or user.get('membership_type') or 'free'
    max_size = get_max_file_size_by_plan(plan)
    
    if file_size > max_size:
        plan_names = {
            'free': '免费版',
            'basic': '基础版',
            'professional': '专业版',
            'flagship': '旗舰版',
            'enterprise': '企业版'
        }
        plan_limits_mb = {
            'free': '5MB',
            'basic': '10MB',
            'professional': '50MB',
            'flagship': '100MB',
            'enterprise': '500MB'
        }
        plan_name = plan_names.get(plan, '免费版')
        plan_limit = plan_limits_mb.get(plan, '5MB')
        file_size_mb = (file_size / (1024 * 1024)).toFixed(2)
        
        error_msg = f'图片文件过大！当前文件大小：{file_size_mb} MB，您的会员类型（{plan_name}）限制：{plan_limit}。请使用较小的图片，或升级会员以获得更大的文件大小限制。'
        return False, error_msg
    
    return True, None

