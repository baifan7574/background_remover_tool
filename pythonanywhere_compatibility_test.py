#!/usr/bin/env python3
"""
PythonAnywhere 环境兼容性测试脚本
测试跨境电商工具站所需的技术栈和依赖
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
    print(f"处理器: {platform.processor()}")
    print(f"当前工作目录: {os.getcwd()}")

def test_core_packages():
    """测试核心包"""
    print_section("核心包测试")
    
    required_packages = {
        'flask': 'Web框架',
        'requests': 'HTTP请求库',
        'pillow': '图片处理',
        'supabase': 'Supabase客户端',
        'rembg': '背景移除',
        'opencv-python': '图像处理',
        'numpy': '数值计算',
        'pandas': '数据处理'
    }
    
    results = {}
    for package, description in required_packages.items():
        try:
            if package == 'opencv-python':
                import cv2
                version = cv2.__version__
            elif package == 'pillow':
                from PIL import Image
                version = Image.__version__
            elif package == 'supabase':
                from supabase import create_client, Client
                version = "已安装"
            else:
                module = __import__(package.replace('-', '_'))
                version = getattr(module, '__version__', '未知版本')
            
            print(f"✅ {package} ({description}): {version}")
            results[package] = True
        except ImportError as e:
            print(f"❌ {package} ({description}): 未安装 - {e}")
            results[package] = False
    
    return results

def test_file_operations():
    """测试文件操作权限"""
    print_section("文件操作权限测试")
    
    # 测试当前目录写权限
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
    
    test_urls = [
        ('https://api.supabase.io', 'Supabase API'),
        ('https://pypi.org', 'PyPI包管理器'),
        ('https://www.google.com', 'Google')
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

def test_memory_and_storage():
    """测试内存和存储空间"""
    print_section("资源限制测试")
    
    try:
        import psutil
        # 内存信息
        memory = psutil.virtual_memory()
        print(f"总内存: {memory.total / (1024**3):.2f} GB")
        print(f"可用内存: {memory.available / (1024**3):.2f} GB")
        print(f"内存使用率: {memory.percent:.1f}%")
        
        # 磁盘空间
        disk = psutil.disk_usage('/')
        print(f"磁盘总空间: {disk.total / (1024**3):.2f} GB")
        print(f"磁盘可用空间: {disk.free / (1024**3):.2f} GB")
        print(f"磁盘使用率: {disk.percent:.1f}%")
        
        return True
    except ImportError:
        print("⚠️ psutil未安装，无法获取详细资源信息")
        return False
    except Exception as e:
        print(f"❌ 获取资源信息失败: {e}")
        return False

def test_image_processing():
    """测试图片处理功能"""
    print_section("图片处理功能测试")
    
    try:
        from PIL import Image
        import numpy as np
        
        # 创建测试图片
        test_image = Image.new('RGB', (100, 100), color='red')
        test_array = np.array(test_image)
        
        print("✅ PIL图片处理: 正常")
        print("✅ NumPy数组操作: 正常")
        
        # 测试rembg
        try:
            import rembg
            print("✅ rembg背景移除: 已安装")
        except ImportError:
            print("❌ rembg背景移除: 未安装")
        
        # 测试OpenCV
        try:
            import cv2
            gray = cv2.cvtColor(test_array, cv2.COLOR_RGB2GRAY)
            print("✅ OpenCV图像处理: 正常")
        except ImportError:
            print("❌ OpenCV图像处理: 未安装")
        
        return True
    except Exception as e:
        print(f"❌ 图片处理测试失败: {e}")
        return False

def generate_report(test_results):
    """生成测试报告"""
    print_section("测试报告总结")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    print(f"总测试项: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！PythonAnywhere环境完全兼容")
    elif passed_tests >= total_tests * 0.8:
        print("\n✅ 大部分测试通过，环境基本兼容")
    else:
        print("\n⚠️ 多项测试失败，需要环境调整")

def main():
    """主函数"""
    print("🚀 PythonAnywhere 环境兼容性测试开始")
    print(f"测试时间: {__import__('datetime').datetime.now()}")
    
    # 执行所有测试
    test_results = {}
    
    test_results['python_version'] = test_python_version()
    test_system_info()
    
    package_results = test_core_packages()
    test_results['core_packages'] = all(package_results.values())
    
    test_results['file_operations'] = test_file_operations()
    
    network_results = test_network_access()
    test_results['network_access'] = all(network_results.values())
    
    test_results['memory_storage'] = test_memory_and_storage()
    test_results['image_processing'] = test_image_processing()
    
    # 生成报告
    generate_report({
        'python_version': test_results['python_version'],
        'core_packages': test_results['core_packages'],
        'file_operations': test_results['file_operations'],
        'network_access': test_results['network_access'],
        'memory_storage': test_results['memory_storage'],
        'image_processing': test_results['image_processing']
    })
    
    # 保存测试结果到文件
    report_file = "pythonanywhere_compatibility_test.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"PythonAnywhere 兼容性测试报告\n")
        f.write(f"测试时间: {__import__('datetime').datetime.now()}\n")
        f.write(f"Python版本: {sys.version}\n")
        f.write(f"测试结果: {test_results}\n")
    
    print(f"\n📄 详细测试报告已保存到: {report_file}")

if __name__ == "__main__":
    main()