@echo off
REM Git一键部署脚本
REM 使用方法：双击运行或在命令行执行 deploy.bat

echo 🚀 开始部署到PythonAnywhere...

REM 首先从backend目录复制最新文件
echo 📁 复制最新代码文件...
copy /Y backendpp_test_standalone.py flask_app.py
echo ✓ 已更新 flask_app.py

if not exist templates mkdir templates
copy /Y backend	emplates\index.html templates\index.html
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