@echo off
echo ========================================
echo 🎨 启动前端服务器
echo ========================================
echo.
echo 正在启动前端服务器 (端口 8000)...
echo.
echo 📱 启动后请在浏览器访问: http://localhost:8000
echo.
echo ⚠️  注意：不要关闭这个窗口！
echo.
cd /d %~dp0frontend
python -m http.server 8000
pause

