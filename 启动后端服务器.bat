@echo off
chcp 65001 >nul
echo ============================================
echo 启动后端服务器（端口5000）
echo ============================================
echo.
echo 注意：不要关闭这个窗口！
echo.
python sk_app.py
pause
