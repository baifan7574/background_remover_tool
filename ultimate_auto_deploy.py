"""
终极自动化部署 - 一键同步到服务器
使用方法：python ultimate_auto_deploy.py
"""

import os
import subprocess
import sys
import ftplib
from pathlib import Path
import zipfile
from datetime import datetime

class UltimateAutoDeployer:
    def __init__(self):
        self.pythonanywhere_username = "baifan7574"
        self.project_root = Path.cwd()
        
    def create_minimal_deployment(self):
        """创建最小化部署包"""
        print("📦 创建最小化部署包...")
        
        # 直接创建服务器需要的文件
        server_files = {
            "flask_app.py": self.get_flask_app_content(),
            "requirements.txt": self.get_requirements_content(),
            "templates/index.html": self.get_index_content()
        }
        
        # 创建临时部署目录
        deploy_dir = self.project_root / "temp_deploy"
        deploy_dir.mkdir(exist_ok=True)
        
        # 创建templates目录
        templates_dir = deploy_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # 写入文件
        for file_path, content in server_files.items():
            full_path = deploy_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已创建: {file_path}")
        
        # 创建zip包
        zip_path = self.project_root / "server_deploy.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in deploy_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(deploy_dir)
                    zipf.write(file_path, arcname)
        
        # 清理临时目录
        import shutil
        shutil.rmtree(deploy_dir)
        
        print(f"✅ 部署包已创建: {zip_path}")
        return zip_path
    
    def get_flask_app_content(self):
        """获取Flask应用内容"""
        source_path = self.project_root / "backend" / "app_test_standalone.py"
        
        if source_path.exists():
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(source_path, 'r', encoding='gbk') as f:
                    content = f.read()
            
            # 调整为PythonAnywhere版本
            content = content.replace(
                'app = Flask(__name__, static_folder="../frontend", template_folder="templates")',
                'app = Flask(__name__, static_folder="static", template_folder="templates")'
            )
            
            # 添加版本标识
            if "# PythonAnywhere Auto Deploy" not in content:
                content = "# PythonAnywhere Auto Deploy\n" + content
            
            return content
        
        # 如果源文件不存在，返回基础版本
        return '''# PythonAnywhere Auto Deploy
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__, template_folder="templates")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "Auto deployed successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
'''
    
    def get_requirements_content(self):
        """获取requirements内容"""
        return '''flask==3.1.2
flask-cors==6.0.1
pillow==12.0.0
werkzeug==3.1.3
requests==2.32.3
'''
    
    def get_index_content(self):
        """获取index.html内容"""
        source_path = self.project_root / "backend" / "templates" / "index.html"
        
        if source_path.exists():
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(source_path, 'r', encoding='gbk') as f:
                    content = f.read()
            return content
        
        # 基础HTML
        return '''<!DOCTYPE html>
<html>
<head>
    <title>跨境工具API - 自动部署版</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>🚀 跨境工具API服务</h1>
    <p>✅ 自动部署成功！</p>
    <p>🌐 访问地址: https://baifan7574.pythonanywhere.com</p>
</body>
</html>
'''
    
    def create_upload_script(self):
        """创建上传脚本"""
        script_content = f'''#!/bin/bash
# PythonAnywhere上传脚本
# 在PythonAnywhere控制台中运行

cd /home/{self.pythonanywhere_username}/mysite/

# 备份当前文件
if [ -f flask_app.py ]; then
    cp flask_app.py flask_app.py.backup
fi

# 上传新文件（需要手动上传server_deploy.zip后运行）
echo "请先上传server_deploy.zip文件，然后运行此脚本"
echo "上传完成后，运行以下命令："
echo "unzip -o server_deploy.zip"
echo "pip install -r requirements.txt"
echo "touch /var/www/${{USER}}_pythonanywhere_com_wsgi.py"
echo "echo ✅ 部署完成！"
'''
        
        script_path = self.project_root / "upload_to_server.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"✅ 上传脚本已创建: {script_path}")
        return script_path
    
    def deploy(self):
        """执行终极自动部署"""
        print("🚀 终极自动部署开始...")
        print("=" * 50)
        
        try:
            # 1. 创建最小化部署包
            zip_path = self.create_minimal_deployment()
            
            # 2. 创建上传脚本
            script_path = self.create_upload_script()
            
            print("\n🎉 部署准备完成！")
            print(f"📦 部署包: {zip_path}")
            print(f"📜 上传脚本: {script_path}")
            
            print("\n📋 下一步操作（只需2步）：")
            print("1. 登录 PythonAnywhere")
            print("2. 上传 server_deploy.zip 到 /home/baifan7574/mysite/")
            print("3. 在控制台运行: unzip -o server_deploy.zip && pip install -r requirements.txt")
            print("4. 点击Web页面的Reload按钮")
            
            print("\n💡 这是最简化的方案，只需上传一个文件！")
            
            return True
            
        except Exception as e:
            print(f"❌ 部署失败: {e}")
            return False

if __name__ == "__main__":
    deployer = UltimateAutoDeployer()
    deployer.deploy()