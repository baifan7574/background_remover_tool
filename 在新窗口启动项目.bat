@echo off
chcp 65001 >nul
title 启动新项目窗口

echo ========================================
echo 在新窗口启动项目
echo ========================================
echo.
echo 这个脚本会在新的独立窗口中启动项目
echo 您可以同时运行多个项目实例
echo.

:menu
echo 请选择要启动的服务:
echo.
echo  [1] 后端服务器 (默认端口 5000)
echo  [2] 前端服务器 (默认端口 8000)
echo  [3] 同时启动后端和前端 (新窗口)
echo  [4] 自定义端口启动后端
echo  [5] 自定义端口启动前端
echo  [6] 退出
echo.
set /p choice=请输入选项 (1-6): 

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend
if "%choice%"=="3" goto start_both
if "%choice%"=="4" goto start_backend_custom
if "%choice%"=="5" goto start_frontend_custom
if "%choice%"=="6" goto end
goto menu

:start_backend
echo.
echo 正在新窗口启动后端服务器 (端口 5000)...
start "后端服务器-端口5000" cmd /k "title 后端服务器-端口5000 && chcp 65001 >nul && cd /d %~dp0 && echo ======================================== && echo 后端服务器 (端口 5000) && echo ======================================== && echo. && python sk_app.py && pause"
echo [成功] 后端服务器窗口已打开
echo.
timeout /t 2 /nobreak >nul
goto menu

:start_frontend
echo.
echo 正在新窗口启动前端服务器 (端口 8000)...
if not exist "%~dp0frontend" (
    echo [错误] frontend文件夹不存在！
    timeout /t 3 /nobreak >nul
    goto menu
)
start "前端服务器-端口8000" cmd /k "title 前端服务器-端口8000 && chcp 65001 >nul && cd /d %~dp0frontend && echo ======================================== && echo 前端服务器 (端口 8000) && echo ======================================== && echo. && echo 访问地址: http://localhost:8000 && echo. && python -m http.server 8000 && pause"
echo [成功] 前端服务器窗口已打开
echo.
timeout /t 2 /nobreak >nul
goto menu

:start_both
echo.
echo 正在新窗口启动后端和前端服务器...
start "后端服务器-端口5000" cmd /k "title 后端服务器-端口5000 && chcp 65001 >nul && cd /d %~dp0 && echo ======================================== && echo 后端服务器 (端口 5000) && echo ======================================== && echo. && python sk_app.py && pause"
timeout /t 2 /nobreak >nul
if not exist "%~dp0frontend" (
    echo [错误] frontend文件夹不存在！
    timeout /t 3 /nobreak >nul
    goto menu
)
start "前端服务器-端口8000" cmd /k "title 前端服务器-端口8000 && chcp 65001 >nul && cd /d %~dp0frontend && echo ======================================== && echo 前端服务器 (端口 8000) && echo ======================================== && echo. && echo 访问地址: http://localhost:8000 && echo. && python -m http.server 8000 && pause"
echo [成功] 后端和前端服务器窗口已打开
echo.
timeout /t 2 /nobreak >nul
goto menu

:start_backend_custom
echo.
set /p backend_port=请输入后端端口号 (例如: 5001): 
if "%backend_port%"=="" (
    echo [错误] 端口号不能为空
    timeout /t 2 /nobreak >nul
    goto menu
)
echo 正在新窗口启动后端服务器 (端口 %backend_port%)...
start "后端服务器-端口%backend_port%" cmd /k "title 后端服务器-端口%backend_port% && chcp 65001 >nul && cd /d %~dp0 && echo ======================================== && echo 后端服务器 (端口 %backend_port%) && echo ======================================== && echo. && echo 提示: 需要修改 sk_app.py 中的端口号为 %backend_port% && echo. && python sk_app.py && pause"
echo [成功] 后端服务器窗口已打开 (端口 %backend_port%)
echo.
echo [重要提示]
echo   需要修改 sk_app.py 文件中的端口配置
echo   将最后一行的 port=5000 改为 port=%backend_port%
echo.
timeout /t 3 /nobreak >nul
goto menu

:start_frontend_custom
echo.
set /p frontend_port=请输入前端端口号 (例如: 8001): 
if "%frontend_port%"=="" (
    echo [错误] 端口号不能为空
    timeout /t 2 /nobreak >nul
    goto menu
)
echo 正在新窗口启动前端服务器 (端口 %frontend_port%)...
if not exist "%~dp0frontend" (
    echo [错误] frontend文件夹不存在！
    timeout /t 3 /nobreak >nul
    goto menu
)
start "前端服务器-端口%frontend_port%" cmd /k "title 前端服务器-端口%frontend_port% && chcp 65001 >nul && cd /d %~dp0frontend && echo ======================================== && echo 前端服务器 (端口 %frontend_port%) && echo ======================================== && echo. && echo 访问地址: http://localhost:%frontend_port% && echo. && python -m http.server %frontend_port% && pause"
echo [成功] 前端服务器窗口已打开 (端口 %frontend_port%)
echo.
timeout /t 2 /nobreak >nul
goto menu

:end
echo.
echo 退出...
exit /b


