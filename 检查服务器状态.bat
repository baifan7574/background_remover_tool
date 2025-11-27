@echo off
chcp 65001 >nul
title 检查服务器状态

echo ========================================
echo 检查服务器运行状态
echo ========================================
echo.

echo [检查端口占用]
echo.
echo 后端服务器 (端口 5000):
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   [未运行] 端口5000没有被占用
) else (
    echo   [运行中] 端口5000已被占用
    netstat -ano | findstr ":5000" | findstr "LISTENING"
)
echo.

echo 前端服务器 (端口 8000):
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   [未运行] 端口8000没有被占用
) else (
    echo   [运行中] 端口8000已被占用
    netstat -ano | findstr ":8000" | findstr "LISTENING"
)
echo.

echo ========================================
echo [检查Python进程]
echo ========================================
echo.
tasklist | findstr /i "python"
echo.

echo ========================================
echo [如何启动服务器]
echo ========================================
echo.
echo 方法1: 双击运行 "start_dev_servers.bat"
echo 方法2: 分别运行:
echo   - "启动后端服务器.bat" (端口5000)
echo   - "启动前端服务器.bat" (端口8000)
echo.

pause

