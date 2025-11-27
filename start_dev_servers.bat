@echo off
chcp 65001 >nul
title 启动开发服务器

echo ========================================
echo 启动背景移除工具 - 开发模式
echo ========================================
echo.

echo 正在检查Python...
python --version 2>nul
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    echo.
    pause
    exit /b 1
)
python --version
echo.

echo ========================================
echo 第1步：启动后端服务器 (端口 5000)
echo ========================================
echo 后端将处理所有API请求和图片处理功能
echo.

cd /d %~dp0

REM 检查后端是否已经在运行
netstat -ano | findstr ":5000" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口5000已被占用，后端服务器可能已经在运行
    echo.
) else (
    echo 正在启动后端服务器...
    start "后端服务器-端口5000" cmd /k "title 后端服务器-端口5000 && cd /d %~dp0 && echo ======================================== && echo 后端服务器 (端口 5000) && echo ======================================== && echo. && echo 正在启动... && echo. && python sk_app.py && pause"
    echo [成功] 后端服务器窗口已打开
    echo.
    
    echo 等待后端服务器启动（5秒）...
    timeout /t 5 /nobreak >nul
    echo.
)

echo ========================================
echo 第2步：启动前端服务器 (端口 8000)
echo ========================================
echo 前端提供用户界面，访问地址: http://localhost:8000
echo.

REM 检查前端是否已经在运行
netstat -ano | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口8000已被占用，前端服务器可能已经在运行
    echo.
) else (
    echo 正在启动前端服务器...
    if not exist "%~dp0frontend" (
        echo [错误] frontend文件夹不存在！
        pause
        exit /b 1
    )
    start "前端服务器-端口8000" cmd /k "title 前端服务器-端口8000 && cd /d %~dp0frontend && echo ======================================== && echo 前端服务器 (端口 8000) && echo ======================================== && echo. && echo 正在启动... && echo. && echo 访问地址: http://localhost:8000 && echo. && python -m http.server 8000 && pause"
    echo [成功] 前端服务器窗口已打开
    echo.
)

echo ========================================
echo 启动完成！
echo ========================================
echo.
echo [服务器状态检查]
echo.
netstat -ano | findstr ":5000 :8000" | findstr "LISTENING"
echo.

echo [访问地址]
echo   用户访问: http://localhost:8000
echo   后端API:  http://localhost:5000
echo   健康检查: http://localhost:5000/health
echo.

echo [重要提示]
echo   1. 请查看是否打开了两个新窗口：
echo      - "后端服务器-端口5000" 
echo      - "前端服务器-端口8000"
echo   2. 如果没有看到窗口，请检查任务栏是否有最小化的窗口
echo   3. 两个服务器窗口都不能关闭！
echo   4. 关闭后端 = 无法处理请求
echo   5. 关闭前端 = 无法访问网页
echo.

echo [如何测试]
echo   1. 打开浏览器
echo   2. 访问: http://localhost:8000
echo   3. 如果能看到网页，说明启动成功
echo.

echo 按任意键关闭此说明窗口...
echo （关闭此窗口不会影响服务器运行）
pause >nul