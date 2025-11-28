#!/usr/bin/env python3
"""
Groq模型可用性测试脚本
在更新代码或部署前，先运行此脚本测试哪些模型可用
避免使用已停用的模型导致功能无法使用
"""

import os
from dotenv import load_dotenv
from groq import Groq

# 加载环境变量
load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY 未配置")
    print("请在 .env 文件中设置 GROQ_API_KEY")
    exit(1)

print("🔑 密钥已配置")
print(f"   密钥预览: {GROQ_API_KEY[:15]}...{GROQ_API_KEY[-10:]}\n")

# 初始化客户端
try:
    client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq客户端初始化成功\n")
except Exception as e:
    print(f"❌ Groq客户端初始化失败: {e}")
    exit(1)

# 要测试的模型列表（按优先级排序）
models_to_test = [
    # 最新模型（优先测试）
    'llama-3.3-70b-versatile',
    'llama-3.3-8b-instruct',
    
    # Llama 3 系列
    'llama-3.1-70b-versatile',
    'llama-3.1-8b-instruct',
    'llama-3-70b-8192',
    'llama-3-8b-8192',
    'llama3-70b-8192',
    'llama3-8b-8192',
    
    # Gemma 系列
    'gemma2-9b-it',
    'gemma-7b-it',
    
    # Mixtral 系列
    'mixtral-8x7b-32768',
    'mixtral-8x7b',
    
    # 其他可能的格式
    'llama-70b-8192',
    'llama-3-70b',
    'llama-70b',
]

print("=" * 60)
print("开始测试模型可用性...")
print("=" * 60)
print()

available_models = []
unavailable_models = []

for model in models_to_test:
    try:
        # 尝试调用API（最小请求）
        response = client.chat.completions.create(
            messages=[{'role': 'user', 'content': 'test'}],
            model=model,
            max_tokens=5
        )
        
        # 如果成功，记录可用模型
        available_models.append(model)
        print(f"✅ {model:35} - 可用")
        print(f"   响应示例: {response.choices[0].message.content[:50]}")
        print()
        
    except Exception as e:
        error_msg = str(e)
        unavailable_models.append((model, error_msg))
        
        if 'decommissioned' in error_msg.lower():
            print(f"❌ {model:35} - 已停用")
        elif 'not found' in error_msg.lower() or 'invalid' in error_msg.lower():
            print(f"⚠️ {model:35} - 不存在")
        else:
            print(f"❓ {model:35} - 错误: {error_msg[:60]}")

print()
print("=" * 60)
print("测试结果总结")
print("=" * 60)
print()

if available_models:
    print("✅ 可用的模型（推荐使用第一个）：")
    for i, model in enumerate(available_models, 1):
        marker = " ⭐ 推荐" if i == 1 else ""
        print(f"   {i}. {model}{marker}")
    print()
    
    # 推荐使用的模型
    recommended_model = available_models[0]
    print(f"💡 建议在代码中使用: {recommended_model}")
    print()
else:
    print("❌ 没有找到可用的模型！")
    print("   请检查：")
    print("   1. API密钥是否正确")
    print("   2. 网络连接是否正常")
    print("   3. Groq服务是否正常")
    print()

if unavailable_models:
    print(f"❌ 不可用的模型（共 {len(unavailable_models)} 个）")
    print("   这些模型已停用或不存在，不应在代码中使用")
    print()

print("=" * 60)
print("下一步操作")
print("=" * 60)
print()
print("1. 将推荐的模型名称更新到代码中")
print("2. 更新 sk_app.py 中的 model 参数")
print("3. 测试功能是否正常工作")
print()

