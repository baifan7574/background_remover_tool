#!/usr/bin/env python3
"""
PythonAnywhere Git部署自动化脚本
支持从本地Git仓库自动部署到PythonAnywhere
"""

import os
import subprocess
import sys
from pathlib import Path

class PythonAnywhereDeployer:
    def __init__(self, local_repo_path, pythonanywhere_path="/home/baifan7574/mysite"):
        self.local_repo = Path(local_repo_path)
        self.remote_path = pythonanywhere_path
        
    def setup_git_repo(self):
        """在本地项目初始化Git仓库"""
        print("🔧 初始化Git仓库...")
        
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.local_repo, check=True)
        
        # 创建.gitignore文件
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment variables
.env
.env.local

# Database
*.db
*.sqlite3

# Uploads
uploads/
output/

# Logs
*.log
"""
        
        with open(self.local_repo / ".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content.strip())
        
        print("✅ Git仓库初始化完成")
    
    def create_deployment_package(self):
        """创建部署包（只包含PythonAnywhere需要的文件）"""
        print("📦 创建部署包...")
        
        deployment_files = [
            "pythonanywhere_deployment_package/flask_app.py",
            "pythonanywhere_deployment_package/requirements.txt", 
            "pythonanywhere_deployment_package/templates/index.html",
            "pythonanywhere_deployment_package/README.md"
        ]
        
        # 添加到Git
        for file_path in deployment_files:
            full_path = self.local_repo / file_path
            if full_path.exists():
                subprocess.run(["git", "add", file_path], cwd=self.local_repo, check=True)
                print(f"✅ 已添加: {file_path}")
        
        # 提交更改
        subprocess.run(["git", "commit", "-m", "Update deployment package"], 
                      cwd=self.local_repo, check=True)
        
        print("✅ 部署包创建完成")
    
    def setup_remote_repo(self):
        """设置远程仓库（GitHub/GitLab）"""
        print("🌐 设置远程仓库...")
        
        # 这里需要用户创建GitHub仓库后添加remote
        print("请按以下步骤操作：")
        print("1. 访问 https://github.com 创建新仓库")
        print("2. 仓库命名为: cross-border-tools")
        print("3. 创建后运行以下命令：")
        print(f"   git remote add origin https://github.com/你的用户名/cross-border-tools.git")
        print("4. 推送代码：git push -u origin main")
        
        return True
    
    def generate_deployment_script(self):
        """生成PythonAnywhere上的部署脚本"""
        script_content = f"""#!/bin/bash
# PythonAnywhere自动部署脚本

cd {self.remote_path}

# 拉取最新代码
git pull origin main

# 安装/更新依赖
pip install -r requirements.txt

# 重启Web应用
touch /var/www/{self.remote_path.split('/')[-2]}_pythonanywhere_com_wsgi.py

echo "✅ 部署完成！"
"""
        
        with open(self.local_repo / "deploy_on_pythonanywhere.sh", "w", encoding="utf-8") as f:
            f.write(script_content)
        
        print("✅ 部署脚本生成完成: deploy_on_pythonanywhere.sh")
    
    def run_workflow(self):
        """执行完整的部署工作流"""
        print("🚀 开始Git部署流程...")
        
        try:
            self.setup_git_repo()
            self.create_deployment_package()
            self.setup_remote_repo()
            self.generate_deployment_script()
            
            print("\n🎉 Git部署设置完成！")
            print("\n📋 下一步操作：")
            print("1. 创建GitHub仓库")
            print("2. 推送代码到GitHub")
            print("3. 在PythonAnywhere上克隆仓库")
            print("4. 设置自动部署脚本")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 错误: {e}")
            return False
        
        return True

if __name__ == "__main__":
    # 使用当前项目目录
    current_dir = Path.cwd()
    deployer = PythonAnywhereDeployer(current_dir)
    
    print("🔧 PythonAnywhere Git部署工具")
    print("=" * 50)
    
    deployer.run_workflow()