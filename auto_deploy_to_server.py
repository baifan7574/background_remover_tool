"""
全自动部署脚本 - 直接同步到PythonAnywhere服务器
使用方法：python auto_deploy_to_server.py
"""

import os
import subprocess
import sys
import requests
import json
from pathlib import Path
import zipfile
from datetime import datetime

class AutoDeployer:
    def __init__(self):
        self.pythonanywhere_username = "baifan7574"
        self.api_token = None  # 需要配置API Token
        self.project_root = Path.cwd()
        
    def setup_api_token(self):
        """设置PythonAnywhere API Token"""
        print("🔑 设置PythonAnywhere API Token...")
        print("请按以下步骤获取API Token：")
        print("1. 登录 PythonAnywhere")
        print("2. 进入 Account → API token")
        print("3. 创建新的API token")
        print("4. 复制token并粘贴到下面")
        
        token = input("请输入你的API Token: ").strip()
        if token:
            # 保存token到环境变量
            os.environ['PYTHONANYWHERE_API_TOKEN'] = token
            self.api_token = token
            print("✅ API Token已保存")
            return True
        return False
    
    def create_deployment_package(self):
        """创建部署包"""
        print("📦 创建部署包...")
        
        # 更新部署文件
        deployment_files = {
            "backend/app_test_standalone.py": "pythonanywhere_deployment_package/flask_app.py",
            "backend/templates/index.html": "pythonanywhere_deployment_package/templates/index.html",
            "requirements.txt": "pythonanywhere_deployment_package/requirements.txt"
        }
        
        for source, target in deployment_files.items():
            source_path = self.project_root / source
            target_path = self.project_root / target
            
            if source_path.exists():
                # 读取源文件
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(source_path, 'r', encoding='gbk') as f:
                        content = f.read()
                
                # 调整flask应用
                if target.endswith('flask_app.py'):
                    content = self.adjust_flask_app(content)
                
                # 确保目录存在
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 写入文件
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ 已更新: {target}")
        
        # 创建zip包
        zip_path = self.project_root / "auto_deployment.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            deployment_dir = self.project_root / "pythonanywhere_deployment_package"
            for file_path in deployment_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(deployment_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ 部署包已创建: {zip_path}")
        return zip_path
    
    def adjust_flask_app(self, content):
        """调整Flask应用适配PythonAnywhere"""
        # 替换路径配置
        content = content.replace(
            'app = Flask(__name__, static_folder="../frontend", template_folder="templates")',
            'app = Flask(__name__, static_folder="static", template_folder="templates")'
        )
        
        # 添加PythonAnywhere配置
        if "pythonanywhere" not in content.lower():
            content = content.replace(
                'app = Flask(__name__',
                '# PythonAnywhere自动部署\napp = Flask(__name__'
            )
        
        return content
    
    def upload_to_pythonanywhere(self, zip_path):
        """上传文件到PythonAnywhere"""
        print("📤 上传到PythonAnywhere...")
        
        if not self.api_token:
            if not self.setup_api_token():
                return False
        
        # 读取zip文件
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        # 上传文件
        url = f"https://www.pythonanywhere.com/api/v0/user/{self.pythonanywhere_username}/files/path/home/{self.pythonanywhere_username}/mysite/auto_deployment.zip"
        
        headers = {
            'Authorization': f'Token {self.api_token}'
        }
        
        files = {
            'content': zip_content
        }
        
        try:
            response = requests.post(url, headers=headers, files=files)
            if response.status_code == 200:
                print("✅ 文件上传成功")
                return True
            else:
                print(f"❌ 上传失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 上传错误: {e}")
            return False
    
    def extract_and_configure(self):
        """在服务器上解压和配置"""
        print("🔧 服务器配置...")
        
        if not self.api_token:
            return False
        
        # 解压文件
        commands = [
            f"cd /home/{self.pythonanywhere_username}/mysite/",
            "unzip -o auto_deployment.zip",
            "rm auto_deployment.zip",
            "pip install -r requirements.txt",
            "touch /var/www/${USER}_pythonanywhere_com_wsgi.py"  # 重启应用
        ]
        
        for cmd in commands:
            url = f"https://www.pythonanywhere.com/api/v0/user/{self.pythonanywhere_username}/consoles/{self.pythonanywhere_username}/pythonanywhere.com/"
            
            headers = {
                'Authorization': f'Token {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'command': cmd
            }
            
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    print(f"✅ 命令执行成功: {cmd}")
                else:
                    print(f"❌ 命令执行失败: {cmd} - {response.text}")
                    return False
            except Exception as e:
                print(f"❌ 命令执行错误: {e}")
                return False
        
        print("✅ 服务器配置完成")
        return True
    
    def deploy(self):
        """执行全自动部署"""
        print("🚀 开始全自动部署...")
        print("=" * 50)
        
        try:
            # 1. 创建部署包
            zip_path = self.create_deployment_package()
            
            # 2. 上传到服务器
            if not self.upload_to_pythonanywhere(zip_path):
                return False
            
            # 3. 解压和配置
            if not self.extract_and_configure():
                return False
            
            print("\n🎉 全自动部署完成！")
            print(f"🌐 访问地址: https://{self.pythonanywhere_username}.pythonanywhere.com")
            print("✅ 无需任何手动操作！")
            
            return True
            
        except Exception as e:
            print(f"❌ 部署失败: {e}")
            return False

if __name__ == "__main__":
    deployer = AutoDeployer()
    deployer.deploy()