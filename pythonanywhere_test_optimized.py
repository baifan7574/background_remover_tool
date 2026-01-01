#!/usr/bin/env python3
"""
PythonAnywhere 环境兼容性测试脚本 - 优化版本
专门针对免费版限制和依赖冲突优化
"""

import sys
import os
import platform
import subprocess
from pathlib import Path

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print('='*50)

def test_python_version():
    """测试Python版本"""
    print_section("Python版本测试")
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python版本符合要求 (>= 3.8)")
        return True
    else:
        print("❌ Python版本过低，需要 >= 3.8")
        return False

def test_system_info():
    """测试系统信息"""
    print_section("系统环境信息")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print(f"当前工作目录: {os.getcwd()}")

def test_core_packages_minimal():
    """测试核心包 - 最小化版本"""
    print_section("核心包测试（最小化版本）")
    
    # PythonAnywhere 免费版核心依赖
    essential_packages = {
        'flask': 'Web框架',
        'requests': 'HTTP请求库',
        'supabase': 'Supabase客户端',
        'python-dotenv': '环境变量管理'
    }
    
    # 图片处理依赖（兼容版本）
    image_packages = {
        'pillow': '基础图片处理',
        'numpy': '数值计算（兼容版本）'
    }
    
    results = {}
    
    print("🔧 测试核心依赖:")
    for package, description in essential_packages.items():
        try:
            if package == 'supabase':
                from supabase import create_client
                version = "已安装"
            else:
                module = __import__(package)
                version = getattr(module, '__version__', '未知版本')
            
            print(f"✅ {package} ({description}): {version}")
            results[package] = True
        except ImportError as e:
            print(f"❌ {package} ({description}): 未安装 - {e}")
            results[package] = False
    
    print("\n🔧 测试图片处理依赖:")
    for package, description in image_packages.items():
        try:
            module = __import__(package)
            version = getattr(module, '__version__', '未知版本')
            print(f"✅ {package} ({description}): {version}")
            results[package] = True
        except ImportError as e:
            print(f"❌ {package} ({description}): 未安装 - {e}")
            results[package] = False
    
    # 测试可选的高级功能
    print("\n🔧 测试可选功能:")
    optional_tests = {
        'rembg': '背景移除（可选）',
        'opencv-python': '高级图像处理（可选）'
    }
    
    for package, description in optional_tests.items():
        try:
            if package == 'opencv-python':
                import cv2
                version = cv2.__version__
                print(f"✅ {package} ({description}): {version}")
            else:
                import rembg
                print(f"✅ {package} ({description}): 已安装")
            results[package] = True
        except ImportError:
            print(f"⚠️ {package} ({description}): 未安装（可选）")
            results[package] = False
    
    return results

def test_file_operations():
    """测试文件操作权限"""
    print_section("文件操作权限测试")
    
    test_file = "test_write_permission.tmp"
    try:
        with open(test_file, 'w') as f:
            f.write("测试内容")
        os.remove(test_file)
        print("✅ 当前目录具有写权限")
        return True
    except Exception as e:
        print(f"❌ 当前目录无写权限: {e}")
        return False

def test_network_access():
    """测试网络访问"""
    print_section("网络访问测试")
    
    # 简化网络测试，只测试关键服务
    test_urls = [
        ('https://www.google.com', '基本网络连接'),
        ('https://pypi.org', 'PyPI包管理器')
    ]
    
    results = {}
    for url, description in test_urls:
        try:
            import requests
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: 可访问")
                results[url] = True
            else:
                print(f"⚠️ {description}: HTTP {response.status_code}")
                results[url] = False
        except Exception as e:
            print(f"❌ {description}: 无法访问 - {e}")
            results[url] = False
    
    return results

def test_basic_image_processing():
    """测试基础图片处理功能"""
    print_section("基础图片处理功能测试")
    
    try:
        from PIL import Image
        import numpy as np
        
        # 创建测试图片
        test_image = Image.new('RGB', (100, 100), color='red')
        test_array = np.array(test_image)
        
        print("✅ PIL图片处理: 正常")
        print("✅ NumPy数组操作: 正常")
        
        # 基础图片操作测试
        resized = test_image.resize((50, 50))
        print("✅ 图片缩放: 正常")
        
        return True
    except Exception as e:
        print(f"❌ 基础图片处理测试失败: {e}")
        return False

def test_supabase_connection():
    """测试 Supabase 连接配置"""
    print_section("Supabase 连接测试")
    
    # 检查环境变量
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url:
        print("⚠️ SUPABASE_URL 环境变量未设置")
        print("💡 请在 .env 文件中设置：SUPABASE_URL=your_supabase_url")
        return False
    
    if not supabase_key:
        print("⚠️ SUPABASE_KEY 环境变量未设置")
        print("💡 请在 .env 文件中设置：SUPABASE_KEY=your_supabase_key")
        return False
    
    try:
        from supabase import create_client
        client = create_client(supabase_url, supabase_key)
        print("✅ Supabase 客户端创建成功")
        print("✅ 环境变量配置正确")
        return True
    except Exception as e:
        print(f"❌ Supabase 连接测试失败: {e}")
        return False

def generate_pythonanywhere_report(test_results):
    """生成 PythonAnywhere 专用报告"""
    print_section("PythonAnywhere 部署建议")
    
    essential_passed = test_results.get('flask', False) and test_results.get('requests', False) and test_results.get('supabase', False)
    image_processing_passed = test_results.get('pillow', False) and test_results.get('numpy', False)
    
    print("📊 核心功能状态:")
    print(f"  Web框架 (Flask): {'✅' if test_results.get('flask', False) else '❌'}")
    print(f"  HTTP请求 (requests): {'✅' if test_results.get('requests', False) else '❌'}")
    print(f"  数据库 (Supabase): {'✅' if test_results.get('supabase', False) else '❌'}")
    print(f"  图片处理 (PIL): {'✅' if test_results.get('pillow', False) else '❌'}")
    
    print(f"\n🎯 部署就绪状态:")
    if essential_passed and image_processing_passed:
        print("🎉 环境已准备好部署到 PythonAnywhere！")
        print("\n📋 下一步操作:")
        print("1. 登录 PythonAnywhere 控制台")
        print("2. 上传项目代码文件")
        print("3. 在 PythonAnywhere 安装相同依赖")
        print("4. 配置环境变量")
        print("5. 启动 Web 应用")
    else:
        print("⚠️ 需要解决依赖问题后才能部署")
        
        if not test_results.get('flask', False):
            print("  - 安装 Flask: pip install flask")
        if not test_results.get('supabase', False):
            print("  - 安装 Supabase: pip install supabase")
        if not test_results.get('pillow', False):
            print("  - 安装 PIL: pip install pillow")

def main():
    """主函数"""
    print("🚀 PythonAnywhere 环境兼容性测试 - 优化版本")
    print(f"测试时间: {__import__('datetime').datetime.now()}")
    
    # 执行核心测试
    test_results = {}
    
    test_results['python_version'] = test_python_version()
    test_system_info()
    
    package_results = test_core_packages_minimal()
    test_results.update(package_results)
    
    test_results['file_operations'] = test_file_operations()
    
    network_results = test_network_access()
    test_results['network_access'] = all(network_results.values())
    
    test_results['image_processing'] = test_basic_image_processing()
    test_results['supabase_config'] = test_supabase_connection()
    
    # 生成部署建议
    generate_pythonanywhere_report(test_results)
    
    # 保存测试结果
    report_file = "pythonanywhere_test_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"PythonAnywhere 兼容性测试报告\n")
        f.write(f"测试时间: {__import__('datetime').datetime.now()}\n")
        f.write(f"Python版本: {sys.version}\n")
        f.write(f"测试结果: {test_results}\n")
    
    print(f"\n📄 详细测试报告已保存到: {report_file}")

if __name__ == "__main__":
    main()