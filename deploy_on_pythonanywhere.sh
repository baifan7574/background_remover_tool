#!/bin/bash
# PythonAnywhere自动部署脚本

cd /home/baifan7574/mysite

# 拉取最新代码
git pull origin main

# 安装/更新依赖
pip install -r requirements.txt

# 重启Web应用
touch /var/www/baifan7574_pythonanywhere_com_wsgi.py

echo "✅ 部署完成！"
