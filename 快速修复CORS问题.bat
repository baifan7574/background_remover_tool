@echo off
chcp 65001 >nul
title 快速修复CORS问题

echo ========================================
echo 快速修复CORS问题
echo ========================================
echo.

echo [第1步] 检查后端服务器是否在运行...
echo.
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [未运行] 后端服务器未运行，请先启动后端服务器
    echo.
    echo 请运行: 启动后端服务器.bat
    echo.
    pause
    exit /b 1
) else (
    echo [运行中] 后端服务器正在运行
    echo.
)

echo [第2步] 检查flask-cors是否安装...
echo.
python -c "import flask_cors; print('flask-cors已安装')" 2>nul
if errorlevel 1 (
    echo [未安装] flask-cors未安装，正在安装...
    echo.
    pip install flask-cors
    echo.
) else (
    echo [已安装] flask-cors已安装
    echo.
)

echo [第3步] 重要提示！
echo.
echo ========================================
echo CORS配置已更新，但需要重启后端服务器
echo ========================================
echo.
echo 操作步骤：
echo   1. 找到运行 "python sk_app.py" 的命令窗口
echo      （窗口标题可能是 "后端服务器-端口5000"）
echo   2. 在该窗口中按 Ctrl+C 停止服务器
echo   3. 重新运行: python sk_app.py
echo      （或直接双击 "启动后端服务器.bat"）
echo   4. 等待服务器启动完成（看到 "Running on..."）
echo   5. 刷新浏览器（Ctrl+F5）
echo.
echo ========================================
echo.

pause

