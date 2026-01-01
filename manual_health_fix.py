#!/usr/bin/env python3
"""
手动修复健康接口 - 简化版本
创建完整的部署包供手动上传
"""

import os
import zipfile
import shutil

def create_manual_deployment_package():
    """创建手动部署包"""
    print("📦 创建手动部署包...")
    
    # 创建临时目录
    deploy_dir = 'manual_health_fix'
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # 复制必要文件
    files_to_copy = [
        ('backend/app_supabase_simple.py', 'app_supabase_simple.py'),
        ('supabase_db.py', 'supabase_db.py'),
        ('requirements_supabase.txt', 'requirements.txt'),
        ('.env', '.env'),
        ('templates/index.html', 'templates/index.html'),
    ]
    
    # 复制文件
    for src, dst in files_to_copy:
        if os.path.exists(src):
            dst_path = os.path.join(deploy_dir, dst)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src, dst_path)
            print(f"  ✅ 复制: {src} -> {dst_path}")
        else:
            print(f"  ⚠️  文件不存在: {src}")
    
    # 创建静态文件目录
    static_dir = os.path.join(deploy_dir, 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    # 创建简单的CSS文件
    css_content = """
/* 基础样式 */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}
.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.btn {
    background: #007bff;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin: 5px;
}
.btn:hover {
    background: #0056b3;
}
"""
    
    with open(os.path.join(static_dir, 'style.css'), 'w') as f:
        f.write(css_content)
    
    # 创建部署说明
    readme_content = """# 健康接口修复部署说明

## 🚀 快速部署步骤（5分钟）

### 1. 上传文件到PythonAnywhere
1. 登录 https://www.pythonanywhere.com/
2. 进入 Files -> /home/baifan7574/
3. 上传这个压缩包中的所有文件

### 2. 安装依赖
在PythonAnywhere的Bash控制台中运行：
```bash
pip install -r requirements.txt
```

### 3. 配置Web应用
1. 进入 Web -> baifan7574.pythonanywhere.com
2. 设置 Source code 为: /home/baifan7574/app_supabase_simple.py
3. 设置 Working directory 为: /home/baifan7574/
4. 点击 Reload

### 4. 验证修复
等待1-2分钟后访问：
- 主页: https://baifan7574.pythonanywhere.com
- 健康检查: https://baifan7574.pythonanywhere.com/health

## 🔧 修复内容
- ✅ 修复健康接口404错误
- ✅ 更新Supabase集成
- ✅ 优化错误处理
- ✅ 添加完整API端点

## 📞 技术支持
如有问题，请检查控制台日志：Web -> baifan7574.pythonanywhere.com -> Logs
"""
    
    with open(os.path.join(deploy_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # 创建部署包
    zip_path = 'health_fix_manual.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ 手动部署包已创建: {zip_path}")
    print(f"📁 临时目录: {deploy_dir}")
    
    return zip_path, deploy_dir

def main():
    """主函数"""
    print("🏥 健康接口手动修复工具")
    print("=" * 50)
    
    zip_path, deploy_dir = create_manual_deployment_package()
    
    print("\n📋 下一步操作：")
    print("1. 解压 health_fix_manual.zip")
    print("2. 登录PythonAnywhere控制台")
    print("3. 按照README.md中的说明进行部署")
    print("4. 验证健康接口是否修复")
    
    print(f"\n📦 部署包位置: {zip_path}")
    print(f"📁 部署目录: {deploy_dir}")

if __name__ == "__main__":
    main()