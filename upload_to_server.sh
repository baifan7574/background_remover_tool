#!/bin/bash
# PythonAnywhere上传脚本
# 在PythonAnywhere控制台中运行

cd /home/baifan7574/mysite/

# 备份当前文件
if [ -f flask_app.py ]; then
    cp flask_app.py flask_app.py.backup
fi

# 上传新文件（需要手动上传server_deploy.zip后运行）
echo "请先上传server_deploy.zip文件，然后运行此脚本"
echo "上传完成后，运行以下命令："
echo "unzip -o server_deploy.zip"
echo "pip install -r requirements.txt"
echo "touch /var/www/${USER}_pythonanywhere_com_wsgi.py"
echo "echo ✅ 部署完成！"
