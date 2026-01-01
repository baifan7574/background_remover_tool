#!/usr/bin/env python3
"""
PythonAnywhere 最小依赖安装脚本
专门针对免费版限制优化，避免依赖冲突
"""

import subprocess
import sys

def install_package_minimal(package, description=""):
    """安装包的最小版本"""
    try:
        print(f"📦 正在安装 {package} {description}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {package} 安装成功")
            return True
        else:
            print(f"❌ {package} 安装失败")
            print(f"   错误信息: {result.stderr[:200]}...")
            return False
    except Exception as e:
        print(f"❌ {package} 安装异常: {e}")
        return False

def main():
    """主安装函数"""
    print("🚀 PythonAnywhere 最小依赖安装")
    print("=" * 50)
    print("💡 专为免费版优化，避免依赖冲突")
    
    # PythonAnywhere 免费版必需依赖
    minimal_packages = [
        ("flask==2.3.3", "Web框架"),
        ("requests==2.31.0", "HTTP请求"),
        ("supabase==1.0.4", "数据库客户端"),
        ("python-dotenv==1.0.0", "环境变量"),
        ("pillow==10.0.1", "基础图片处理"),
        ("numpy==1.24.3", "数值计算（兼容版本）"),
    ]
    
    # 可选依赖（如果安装失败不影响核心功能）
    optional_packages = [
        ("pandas==2.0.3", "数据处理"),
        ("gunicorn==21.2.0", "WSGI服务器"),
    ]
    
    total_installed = 0
    total_failed = 0
    
    print("\n🔧 安装核心依赖:")
    print("-" * 30)
    
    for package, description in minimal_packages:
        if install_package_minimal(package, f"({description})"):
            total_installed += 1
        else:
            total_failed += 1
    
    print(f"\n🔧 安装可选依赖:")
    print("-" * 30)
    
    for package, description in optional_packages:
        if install_package_minimal(package, f"({description})"):
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
        print("🚀 现在可以部署到 PythonAnywhere 了！")
    else:
        print(f"\n⚠️ 有 {total_failed} 个包安装失败")
        print("💡 核心功能应该仍然可用，可以尝试部署")
    
    print("\n📋 下一步:")
    print("1. 运行: python pythonanywhere_test_optimized.py")
    print("2. 登录 PythonAnywhere 控制台")
    print("3. 在 PythonAnywhere 中安装相同的包")
    print("4. 上传项目代码")

if __name__ == "__main__":
    main()