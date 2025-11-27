@echo off
chcp 65001 >nul
title 杀掉占用5000端口的进程

echo ========================================
echo 杀掉占用5000端口的进程
echo ========================================
echo.

echo [第1步] 检查占用5000端口的进程...
echo.
netstat -ano | findstr ":5000"
echo.

echo [第2步] 获取进程ID并杀掉...
echo.
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    echo 找到进程ID: %%a
    echo 正在杀掉进程 %%a...
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [错误] 无法杀掉进程 %%a
    ) else (
        echo [成功] 进程 %%a 已被杀掉
    )
)
echo.

echo [第3步] 检查占用8000端口的进程（前端）...
echo.
netstat -ano | findstr ":8000"
echo.

echo [第4步] 杀掉所有Python进程（确保干净）...
echo.
tasklist | findstr /i "python.exe"
if not errorlevel 1 (
    echo.
    echo 正在杀掉所有Python进程...
    taskkill /F /IM python.exe >nul 2>&1
    taskkill /F /IM pythonw.exe >nul 2>&1
    echo [完成] 所有Python进程已被杀掉
) else (
    echo [提示] 没有找到Python进程
)
echo.

echo [第5步] 验证端口是否释放...
echo.
timeout /t 2 /nobreak >nul
netstat -ano | findstr ":5000 :8000"
if errorlevel 1 (
    echo [成功] 端口5000和8000已释放
) else (
    echo [警告] 仍有进程占用端口，可能需要管理员权限
)
echo.

echo ========================================
echo 操作完成
echo ========================================
echo.

echo [下一步操作]
echo   1. 双击运行 "start_dev_servers.bat" 重新启动服务器
echo   2. 或分别运行：
echo      - "启动后端服务器.bat" （端口5000）
echo      - "启动前端服务器.bat" （端口8000）
echo.

pause

