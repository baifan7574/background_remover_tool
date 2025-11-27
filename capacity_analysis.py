"""
Supabase免费版容量分析
计算项目资源需求
"""

# 用户数据量估算
def calculate_user_data():
    # 单用户数据量
    user_profile = 1  # KB
    usage_records = 50  # 条记录，每条0.5KB
    
    per_user = user_profile + (usage_records * 0.5)
    print(f"单用户数据量: {per_user} KB")
    
    # 1000用户数据量
    thousand_users = per_user * 1000
    print(f"1000用户数据量: {thousand_users} KB = {thousand_users/1024:.2f} MB")
    
    # 10000用户数据量
    ten_thousand_users = per_user * 10000
    print(f"10000用户数据量: {ten_thousand_users} KB = {ten_thousand_users/1024:.2f} MB")
    
    return per_user, thousand_users, ten_thousand_users

# 图片存储量估算
def calculate_image_storage():
    # 处理后图片大小
    avg_image_size = 500  # KB (压缩后)
    
    # 不同用户量的存储需求
    user_scenarios = [100, 500, 1000, 2000]
    
    for users in user_scenarios:
        # 假设每个用户平均处理10张图片
        total_images = users * 10
        total_storage = total_images * avg_image_size
        
        print(f"{users}用户 × 10张图片 = {total_images}张图片")
        print(f"存储需求: {total_storage} KB = {total_storage/1024:.2f} MB")
        print("---")
    
    return avg_image_size

# 带宽使用量估算
def calculate_bandwidth():
    # API调用数据量
    api_call_size = 2  # KB 每次调用
    
    # 不同活跃用户的带宽需求
    active_users = [100, 500, 1000, 2000]
    calls_per_user_per_day = 20
    
    print("=== 带宽使用量估算 ===")
    for users in active_users:
        daily_calls = users * calls_per_user_per_day
        daily_bandwidth = daily_calls * api_call_size
        monthly_bandwidth = daily_bandwidth * 30
        
        print(f"{users}活跃用户:")
        print(f"  每日API调用: {daily_calls}次")
        print(f"  每日带宽: {daily_bandwidth} KB = {daily_bandwidth/1024:.2f} MB")
        print(f"  每月带宽: {monthly_bandwidth} KB = {monthly_bandwidth/1024:.2f} MB")
        print("---")

# Supabase限制对比
def supabase_limits_comparison():
    print("=== Supabase免费版限制对比 ===")
    
    limits = {
        "数据库存储": "500MB",
        "文件存储": "1GB", 
        "月活用户": "50,000",
        "带宽": "5GB/月",
        "并发连接": "2个"
    }
    
    for resource, limit in limits.items():
        print(f"{resource}: {limit}")
    
    print("\n=== 项目需求对比 ===")
    print("数据库存储: 1000用户约5MB ✅ 远低于500MB")
    print("文件存储: 2000用户约1GB ✅ 接近上限")
    print("月活用户: 目标1000用户 ✅ 远低于50,000")
    print("带宽: 2000用户约2.4GB/月 ✅ 低于5GB")
    print("并发连接: 2个可能不足 ⚠️ 需要优化")

if __name__ == "__main__":
    print("=== Supabase免费版容量分析 ===\n")
    
    # 计算用户数据
    per_user, thousand_users, ten_thousand_users = calculate_user_data()
    print()
    
    # 计算图片存储
    avg_image_size = calculate_image_storage()
    print()
    
    # 计算带宽
    calculate_bandwidth()
    print()
    
    # 限制对比
    supabase_limits_comparison()