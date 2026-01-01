"""
PythonAnywhere 依赖安装脚本
针对跨境电商工具站的优化版本
"""

import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        print(f"📦 正在安装 {package}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {package} 安装成功")
            return True
        else:
            print(f"❌ {package} 安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {package} 安装异常: {e}")
        return False

def main():
    """主安装函数"""
    print("🚀 开始安装跨境电商工具站依赖包")
    print("=" * 50)
    
    # 核心依赖列表（按重要性排序）
    essential_packages = [
        "flask==2.3.3",           # Web框架
        "requests==2.31.0",       # HTTP请求
        "pillow==10.0.1",         # 图片处理
        "supabase==1.0.4",        # Supabase客户端
        "python-dotenv==1.0.0",   # 环境变量
    ]
    
    # 图片处理依赖
    image_packages = [
        "rembg==2.0.50",          # 背景移除
        "opencv-python==4.8.1.78", # 图像处理
        "numpy==1.24.3",          # 数值计算
    ]
    
    # 数据处理依赖
    data_packages = [
        "pandas==2.0.3",          # 数据处理
        "openpyxl==3.1.2",        # Excel支持
    ]
    
    # 可选依赖
    optional_packages = [
        "gunicorn==21.2.0",       # WSGI服务器
        "psutil==5.9.5",          # 系统监控
    ]
    
    # 分阶段安装
    stages = [
        ("核心依赖", essential_packages),
        ("图片处理依赖", image_packages),
        ("数据处理依赖", data_packages),
        ("可选依赖", optional_packages)
    ]
    
    total_installed = 0
    total_failed = 0
    
    for stage_name, packages in stages:
        print(f"\n🔧 安装 {stage_name}:")
        print("-" * 30)
        
        for package in packages:
            if install_package(package):
                total_installed += 1
            else:
                total_failed += 1
    
    # 安装总结
    print("\n" + "=" * 50)
    print("📊 安装总结:")
    print(f"✅ 成功安装: {total_installed} 个包")
    print(f"❌ 安装失败: {total_failed} 个包")
    
    if total_failed == 0:
        print("\n🎉 所有依赖安装成功！")
        print("现在可以运行 python pythonanywhere_compatibility_test.py 进行测试")
    else:
        print(f"\n⚠️ 有 {total_failed} 个包安装失败，请检查错误信息")
        print("可以尝试手动安装失败的包")

if __name__ == "__main__":
    main()