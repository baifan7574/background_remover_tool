#!/usr/bin/env python3
"""
检查云服务器状态
"""

import requests
import time
from datetime import datetime

def check_server_status():
    """检查服务器状态"""
    print("🔍 检查云服务器状态...")
    print("=" * 50)
    
    # 您的网站地址
    website_url = "https://baifan7574.pythonanywhere.com"
    health_url = f"{website_url}/health"
    
    print(f"📡 检查网站: {website_url}")
    print(f"🏥 健康检查: {health_url}")
    print("-" * 50)
    
    # 检查主页面
    try:
        print("🌐 检查主页面...")
        response = requests.get(website_url, timeout=10)
        if response.status_code == 200:
            print("✅ 主页面访问正常")
            print(f"   状态码: {response.status_code}")
            print(f"   响应时间: {response.elapsed.total_seconds():.2f}秒")
        else:
            print(f"⚠️  主页面响应异常: {response.status_code}")
    except requests.exceptions.Timeout:
        print("❌ 主页面访问超时")
    except requests.exceptions.ConnectionError:
        print("❌ 主页面连接失败 - 服务器可能未运行")
    except Exception as e:
        print(f"❌ 主页面检查错误: {e}")
    
    print()
    
    # 检查健康接口
    try:
        print("🏥 检查健康接口...")
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print("✅ 健康接口正常")
            print(f"   状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:100]}...")
        else:
            print(f"⚠️  健康接口异常: {response.status_code}")
    except requests.exceptions.Timeout:
        print("❌ 健康接口访问超时")
    except requests.exceptions.ConnectionError:
        print("❌ 健康接口连接失败")
    except Exception as e:
        print(f"❌ 健康接口检查错误: {e}")
    
    print()
    print("📋 检查完成时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def check_local_server():
    """检查本地服务器"""
    print("\n🏠 检查本地服务器...")
    print("-" * 30)
    
    local_url = "http://localhost:5000"
    health_url = "http://localhost:5000/health"
    
    try:
        response = requests.get(local_url, timeout=5)
        if response.status_code == 200:
            print("✅ 本地服务器运行中")
    except:
        print("❌ 本地服务器未运行")

if __name__ == "__main__":
    check_server_status()
    check_local_server()
    
    print("\n💡 提示:")
    print("- 如果云服务器❌，需要重新部署")
    print("- 如果本地服务器✅，说明开发环境正常")
    print("- 用户应该访问云服务器，不是本地服务器")