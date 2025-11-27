"""
Git自动化部署脚本
功能：将本地代码直接同步到PythonAnywhere服务器
使用方法：python git_deploy_to_pythonanywhere.py
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import datetime

def print_title(text):
    """打印带边框的标题"""
    print("=" * 60)
    print(f"🚀 {text}")
    print("=" * 60)

def print_success(text):
    """打印成功信息"""
    print(f"✅ {text}")

def print_info(text):
    """打印提示信息"""
    print(f"ℹ️ {text}")

def print_error(text):
    """打印错误信息"""
    print(f"❌ {text}")

class GitDeployer:
    def __init__(self):
        # 配置信息
        self.pythonanywhere_username = "baifan7574"
        self.pythonanywhere_project_path = f"/home/{self.pythonanywhere_username}/mysite"
        
        # 本地项目配置
        self.local_project_root = Path.cwd()
        self.git_repo_name = "cross-border-tools"
        self.server_git_path = os.path.join(self.pythonanywhere_project_path, self.git_repo_name)
        
        # 部署相关配置
        self.deploy_branch = "main"
        self.deploy_files = [
            "flask_app.py",
            "requirements.txt",
            "templates/index.html"
        ]
    
    def check_git_installed(self):
        """检查Git是否已安装"""
        try:
            subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def setup_local_git(self):
        """设置本地Git仓库"""
        try:
            # 检查是否已有Git仓库
            if not os.path.exists(".git"):
                print_info("初始化本地Git仓库...")
                subprocess.run(["git", "init"], check=True)
                
                # 创建.gitignore文件
                if not os.path.exists(".gitignore"):
                    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDEs and editors
.vscode/
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log

# Virtual environments
venv/
.env/

# Build files
deployment_package.zip
server_deploy.zip
                """
                    with open(".gitignore", "w", encoding="utf-8") as f:
                        f.write(gitignore_content.strip())
                    print_success("创建了 .gitignore 文件")
            
            # 从backend目录复制文件到根目录
            print_info("从backend目录复制文件...")
            
            # 确保templates目录存在
            templates_dir = Path("templates")
            templates_dir.mkdir(exist_ok=True)
            
            # 复制flask_app.py
            if os.path.exists("backend/app_test_standalone.py"):
                shutil.copy2("backend/app_test_standalone.py", "flask_app.py")
                print_success("复制了 flask_app.py")
            
            # 复制index.html
            if os.path.exists("backend/templates/index.html"):
                shutil.copy2("backend/templates/index.html", "templates/index.html")
                print_success("复制了 templates/index.html")
            
            # 确保requirements.txt存在
            if not os.path.exists("requirements.txt"):
                requirements_content = """
flask==3.1.2
flask-cors==6.0.1
pillow==12.0.0
werkzeug==3.1.3
requests==2.32.3
"""
                with open("requirements.txt", "w", encoding="utf-8") as f:
                    f.write(requirements_content.strip())
                print_success("创建了 requirements.txt")
            
            # 创建.env.example文件
            if not os.path.exists(".env") and os.path.exists(".env.example"):
                shutil.copy2(".env.example", ".env")
                print_success("创建了 .env 文件（但不会提交到Git）")
            
            # 只添加存在的文件
            files_to_add = []
            for file in self.deploy_files:
                if os.path.exists(file):
                    files_to_add.append(file)
            
            # 添加文件到暂存区
            if files_to_add:
                print_info(f"将文件添加到Git: {', '.join(files_to_add)}")
                # 使用--force参数忽略.gitignore
                subprocess.run(["git", "add", "--force"] + files_to_add, check=True, shell=True)
                
                # 提交更改
                commit_message = f"Deploy at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                try:
                    subprocess.run(["git", "commit", "-m", commit_message], check=True)
                    print_success(f"提交成功: {commit_message}")
                except subprocess.CalledProcessError:
                    print_info("没有需要提交的更改")
            else:
                print_error("没有找到需要添加的文件")
            
            return True
        except Exception as e:
            print_error(f"设置本地Git失败: {str(e)}")
            return False
    
    def show_server_setup_commands(self):
        """显示服务器端设置命令"""
        print_title("服务器端Git设置指南")
        print("请在PythonAnywhere控制台执行以下命令:")
        print("\n📋 PythonAnywhere 控制台命令:")
        
        server_commands = [
            f"cd {self.pythonanywhere_project_path}",
            f"git clone --bare https://github.com/您的GitHub用户名/{self.git_repo_name}.git {self.git_repo_name}.git",
            f"cd {self.git_repo_name}.git",
            "git config --bool core.bare false",
            "git config receive.denyCurrentBranch ignore",
            "mkdir -p hooks",
            ">".join(["cat", ">", "hooks/post-receive"]),
            "#!/bin/sh",
            "cd /home/baifan7574/mysite/cross-border-tools.git",
            "git checkout -f",
            "cp flask_app.py /home/baifan7574/mysite/",
            "cp -r templates/* /home/baifan7574/mysite/templates/ 2>/dev/null || mkdir -p /home/baifan7574/mysite/templates && cp -r templates/* /home/baifan7574/mysite/templates/",
            "cp requirements.txt /home/baifan7574/mysite/",
            "cp .env /home/baifan7574/mysite/ 2>/dev/null || echo 'No .env file to copy'",
            "pip install -r /home/baifan7574/mysite/requirements.txt --user",
            "touch /var/www/baifan7574_pythonanywhere_com_wsgi.py",
            "echo 'Deployment completed successfully!'",
            "chmod +x hooks/post-receive"
        ]
        
        for cmd in server_commands:
            print(f"  {cmd}")
        
        print("\n💡 提示:")
        print("1. 首先在GitHub上创建仓库")
        print("2. 在PythonAnywhere上执行上述命令设置Git接收")
        print("3. 本地添加远程仓库并推送")
    
    def show_local_deploy_commands(self):
        """显示本地部署命令"""
        print_title("本地部署命令")
        print("设置完成后，每次修改代码后执行这些命令部署:")
        
        deploy_commands = [
            "git add flask_app.py requirements.txt templates/*",
            "git commit -m 'Update deployment'",
            "git push origin main"
        ]
        
        for cmd in deploy_commands:
            print(f"  {cmd}")
    
    def create_deploy_script(self):
        """创建一键部署脚本"""
        script_content = """
@echo off
REM Git一键部署脚本
REM 使用方法：双击运行或在命令行执行 deploy.bat

echo 🚀 开始部署到PythonAnywhere...

REM 首先从backend目录复制最新文件
echo 📁 复制最新代码文件...
copy /Y backend\app_test_standalone.py flask_app.py
echo ✓ 已更新 flask_app.py

if not exist templates mkdir templates
copy /Y backend\templates\index.html templates\index.html
if %ERRORLEVEL% EQU 0 (
    echo ✓ 已更新 templates\index.html
) else (
    echo ⚠️  无法复制index.html，但继续部署
)

REM 添加文件并部署
git add flask_app.py requirements.txt templates/*
git commit -m "Auto deploy at %date% %time%"
git push origin main
echo ✅ 部署完成！代码已自动同步到服务器并生效
pause
        """
        
        with open("deploy.bat", "w", encoding="utf-8") as f:
            f.write(script_content.strip())
        
        print_success("创建了 deploy.bat 一键部署脚本")
    
    def deploy(self):
        """执行Git部署流程"""
        print_title("Git自动化部署 - 本地设置")
        
        # 检查Git
        if not self.check_git_installed():
            print_error("Git未安装！请先安装Git")
            print_info("下载地址: https://git-scm.com/downloads")
            return False
        
        # 设置本地Git
        if not self.setup_local_git():
            return False
        
        # 创建部署脚本
        self.create_deploy_script()
        
        # 显示服务器设置指南
        self.show_server_setup_commands()
        self.show_local_deploy_commands()
        
        print_title("Git部署流程完成")
        print("\n🎉 Git自动化部署系统已配置完成！")
        print("📋 部署流程:")
        print("1. 在GitHub创建仓库")
        print("2. 在PythonAnywhere设置Git接收")
        print("3. 本地运行 deploy.bat 一键部署")
        print("4. 代码会自动同步到服务器并生效")
        
        return True

if __name__ == "__main__":
    deployer = GitDeployer()
    deployer.deploy()