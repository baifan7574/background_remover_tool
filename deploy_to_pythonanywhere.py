"""
一键部署脚本 - 从本地直接同步到PythonAnywhere
使用方法：python deploy_to_pythonanywhere.py
"""

import os
import subprocess
import sys
from pathlib import Path
import shutil
import zipfile
from datetime import datetime

class OneClickDeployer:
    def __init__(self):
        self.project_root = Path.cwd()
        self.deployment_package = self.project_root / "pythonanywhere_deployment_package"
        self.deploy_zip = self.project_root / "deployment_package.zip"
        
    def update_deployment_package(self):
        """自动更新部署包内容"""
        print("🔄 更新部署包...")
        
        # 源文件映射
        source_files = {
            "backend/app_test_standalone.py": "pythonanywhere_deployment_package/flask_app.py",
            "backend/templates/index.html": "pythonanywhere_deployment_package/templates/index.html",
            "requirements.txt": "pythonanywhere_deployment_package/requirements.txt"
        }
        
        # 更新文件
        for source, target in source_files.items():
            source_path = self.project_root / source
            target_path = self.project_root / target
            
            if source_path.exists():
                # 读取并处理源文件
                try:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(source_path, 'r', encoding='gbk') as f:
                        content = f.read()
                
                # 如果是flask_app.py，需要调整路径
                if target.endswith('flask_app.py'):
                    content = self.adjust_flask_app_for_pythonanywhere(content)
                
                # 确保目标目录存在
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 写入文件
                target_path.write_text(content, encoding='utf-8')
                print(f"✅ 已更新: {target}")
            else:
                print(f"⚠️  源文件不存在: {source}")
        
        print("✅ 部署包更新完成")
    
    def adjust_flask_app_for_pythonanywhere(self, content):
        """调整Flask应用适配PythonAnywhere路径"""
        # 替换路径配置
        content = content.replace(
            'app = Flask(__name__, static_folder="../frontend", template_folder="templates")',
            'app = Flask(__name__, static_folder="static", template_folder="templates")'
        )
        
        # 添加PythonAnywhere特定配置
        if "pythonanywhere" not in content.lower():
            content = content.replace(
                'app = Flask(__name__',
                '# PythonAnywhere部署配置\napp = Flask(__name__'
            )
        
        return content
    
    def create_deployment_zip(self):
        """创建部署压缩包"""
        print("📦 创建部署压缩包...")
        
        # 删除旧的压缩包
        if self.deploy_zip.exists():
            self.deploy_zip.unlink()
        
        # 创建新的压缩包
        with zipfile.ZipFile(self.deploy_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.deployment_package.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.deployment_package)
                    zipf.write(file_path, arcname)
                    print(f"📄 已打包: {arcname}")
        
        print(f"✅ 部署包已创建: {self.deploy_zip}")
        return self.deploy_zip
    
    def generate_upload_instructions(self):
        """生成上传说明"""
        instructions = f"""
# 🚀 PythonAnywhere一键部署指南

## 📋 当前时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📁 部署文件
部署包已创建: `{self.deploy_zip.name}`

## 🎯 上传步骤

### 方法1: 上传压缩包（推荐）
1. 登录 PythonAnywhere: https://baifan7574.pythonanywhere.com
2. 进入 Files → /home/baifan7574/mysite/
3. 点击 "Upload a file"
4. 选择 `{self.deploy_zip.name}` 上传
5. 上传后，在Console中运行:
   ```bash
   cd /home/baifan7574/mysite/
   unzip -o deployment_package.zip
   rm deployment_package.zip
   ```

### 方法2: 逐个文件上传
上传以下文件到 `/home/baifan7574/mysite/`:
- `flask_app.py`
- `requirements.txt`
- `templates/index.html`

## 🔧 部署后配置
1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 重启Web应用:
   - 在Web页面点击 "Reload" 按钮

## 🌐 访问地址
http://baifan7574.pythonanywhere.com

## 📝 自动化说明
- 本脚本自动同步最新代码到部署包
- 每次本地修改后，运行此脚本即可快速部署
- 无需手动拷贝文件，一键完成
"""
        
        with open(self.project_root / "deployment_instructions.md", "w", encoding="utf-8") as f:
            f.write(instructions.strip())
        
        print("✅ 部署说明已生成: deployment_instructions.md")
    
    def deploy(self):
        """执行一键部署"""
        print("🚀 开始一键部署...")
        print("=" * 50)
        
        try:
            # 1. 更新部署包
            self.update_deployment_package()
            
            # 2. 创建压缩包
            zip_file = self.create_deployment_zip()
            
            # 3. 生成说明
            self.generate_upload_instructions()
            
            print("\n🎉 一键部署准备完成！")
            print(f"📦 部署包: {zip_file}")
            print("📋 说明文档: deployment_instructions.md")
            print("\n👆 按照说明文档上传到PythonAnywhere即可")
            
            return True
            
        except Exception as e:
            print(f"❌ 部署失败: {e}")
            return False

if __name__ == "__main__":
    deployer = OneClickDeployer()
    deployer.deploy()