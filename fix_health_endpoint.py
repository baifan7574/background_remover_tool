#!/usr/bin/env python3
"""
修复健康接口404问题
重新部署最新版本到PythonAnywhere
"""

import os
import zipfile
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class HealthFixDeployment:
    def __init__(self):
        self.api_token = os.getenv('PYTHONANYWHERE_API_TOKEN')
        self.username = os.getenv('PYTHONANYWHERE_USERNAME', 'baifan7574')
        self.domain = f'{self.username}.pythonanywhere.com'
        
    def create_fixed_deployment_package(self):
        """创建修复健康接口的部署包"""
        print("🔧 创建修复版本部署包...")
        
        # 要包含的文件列表
        files_to_include = [
            'backend/app_supabase_simple.py',
            'supabase_db.py',
            'requirements_supabase.txt',
            '.env',
            'templates/index.html',
            'static/css/style.css',
            'static/js/app.js'
        ]
        
        # 创建部署包
        zip_path = 'health_fix_deployment.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_include:
                if os.path.exists(file_path):
                    # 在zip中保持相对路径
                    arcname = file_path.replace('backend/', '').replace('static/', '')
                    zipf.write(file_path, arcname)
                    print(f"  ✅ 添加文件: {file_path} -> {arcname}")
                else:
                    print(f"  ⚠️  文件不存在: {file_path}")
        
        print(f"✅ 修复版本部署包已创建: {zip_path}")
        return zip_path
    
    def upload_fixed_version(self):
        """上传修复版本到PythonAnywhere"""
        print("📤 上传修复版本到PythonAnywhere...")
        
        zip_path = self.create_fixed_deployment_package()
        
        # 读取文件内容
        with open(zip_path, 'rb') as f:
            files = {'content': f}
            
            # 上传到PythonAnywhere
            response = requests.post(
                f'https://www.pythonanywhere.com/api/v0/user/{self.username}/files/path/home/{self.username}/',
                files=files,
                headers={'Authorization': f'Token {self.api_token}'}
            )
            
            if response.status_code == 200:
                print("✅ 修复版本上传成功")
                return True
            else:
                print(f"❌ 上传失败: {response.text}")
                return False
    
    def extract_and_configure(self):
        """解压并配置修复版本"""
        print("🔧 解压并配置修复版本...")
        
        commands = [
            f'cd /home/{self.username} && unzip -o health_fix_deployment.zip',
            f'cd /home/{self.username} && pip install -r requirements_supabase.txt',
            f'cd /home/{self.username} && mkdir -p static templates',
            f'cd /home/{self.username} && mv *.py /var/www/{self.username}_pythonanywhere_com_wsgi.py/ 2>/dev/null || true',
            f'cd /home/{self.username} && mv templates/* /var/www/{self.username}_pythonanywhere_com_wsgi.py/templates/ 2>/dev/null || true',
            f'cd /home/{self.username} && mv static/* /var/www/{self.username}_pythonanywhere_com_wsgi.py/static/ 2>/dev/null || true'
        ]
        
        for cmd in commands:
            print(f"执行: {cmd}")
            response = requests.post(
                f'https://www.pythonanywhere.com/api/v0/user/{self.username}/consoles/',
                json={'executable': 'bash'},
                headers={'Authorization': f'Token {self.api_token}'}
            )
            
            if response.status_code == 201:
                console_id = response.json()['id']
                
                # 在控制台中执行命令
                requests.post(
                    f'https://www.pythonanywhere.com/api/v0/user/{self.username}/consoles/{console_id}/send/',
                    json={'input': cmd + '\n'},
                    headers={'Authorization': f'Token {self.api_token}'}
                )
                
                print(f"  ✅ 命令已发送: {cmd}")
            else:
                print(f"  ❌ 命令执行失败: {response.text}")
        
        print("✅ 修复版本配置完成")
    
    def reload_web_app(self):
        """重新加载Web应用"""
        print("🔄 重新加载Web应用...")
        
        response = requests.post(
            f'https://www.pythonanywhere.com/api/v0/user/{self.username}/webapps/{self.domain}/reload/',
            headers={'Authorization': f'Token {self.api_token}'}
        )
        
        if response.status_code == 200:
            print("✅ Web应用重新加载成功")
            return True
        else:
            print(f"❌ 重新加载失败: {response.text}")
            return False
    
    def fix_health_endpoint(self):
        """执行完整的健康接口修复流程"""
        print("🏥 开始修复健康接口404问题...")
        print("=" * 50)
        
        if not self.api_token:
            print("❌ 错误：请设置PYTHONANYWHERE_API_TOKEN环境变量")
            return False
        
        success = True
        
        # 上传修复版本
        if not self.upload_fixed_version():
            success = False
        
        # 解压配置
        if success:
            self.extract_and_configure()
        
        # 重新加载应用
        if success:
            if not self.reload_web_app():
                success = False
        
        if success:
            print("\n🎉 健康接口修复完成！")
            print("📡 请等待1-2分钟后访问:")
            print(f"   主页: https://{self.domain}")
            print(f"   健康检查: https://{self.domain}/health")
        else:
            print("\n❌ 健康接口修复失败，请检查错误信息")
        
        return success

def main():
    """主函数"""
    print("🏥 PythonAnywhere健康接口修复工具")
    print("=" * 50)
    
    fixer = HealthFixDeployment()
    fixer.fix_health_endpoint()

if __name__ == "__main__":
    main()