@echo off
chcp 65001 >nul
title 杀掉所有Python进程

echo ========================================
echo 杀掉所有Python进程
echo ========================================
echo.

echo [第1步] 检查占用5000端口的进程...
echo.
netstat -ano | findstr ":5000"
echo.

echo [第2步] 检查所有Python进程...
echo.
tasklist | findstr /i "python"
echo.

echo [第3步] 杀掉所有Python进程...
echo.
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.exe"') do (
    echo 正在杀掉进程: %%i
    taskkill /F /PID %%i >nul 2>&1
)
echo.

echo [第4步] 检查8000端口...
echo.
netstat -ano | findstr ":8000"
echo.

echo ========================================
echo 操作完成
echo ========================================
echo.

echo [重要提示]
echo   所有Python进程已被杀掉
echo   现在请重新启动服务器：
echo     1. 双击运行 "start_dev_servers.bat"
echo     2. 或分别运行：
echo        - "启动后端服务器.bat"
echo        - "启动前端服务器.bat"
echo.

pause

