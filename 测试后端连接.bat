@echo off
chcp 65001 >nul
title 测试后端连接

echo ========================================
echo 测试后端服务器连接
echo ========================================
echo.

echo [第1步] 检查后端服务器端口...
echo.
netstat -ano | findstr ":5000" | findstr "LISTENING"
if errorlevel 1 (
    echo [错误] 端口5000没有被占用，后端服务器未运行！
    echo.
    echo 请先启动后端服务器：
    echo   1. 双击运行 "启动后端服务器.bat"
    echo   2. 或运行: python sk_app.py
    echo.
    pause
    exit /b 1
) else (
    echo [成功] 后端服务器正在运行（端口5000）
    echo.
)

echo [第2步] 测试健康检查接口...
echo.
curl -s http://localhost:5000/health 2>nul
if errorlevel 1 (
    echo [错误] 无法连接到后端服务器！
    echo.
    echo 可能的原因：
    echo   1. 后端服务器未启动
    echo   2. 后端服务器启动出错
    echo   3. 防火墙阻止连接
    echo.
) else (
    echo [成功] 后端服务器响应正常
    echo.
)

echo [第3步] 测试CORS配置...
echo.
echo 正在发送OPTIONS预检请求...
echo.

python -c "import requests; r = requests.options('http://localhost:5000/api/auth/register', headers={'Origin': 'http://localhost:8000', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'Content-Type,Authorization'}); print('状态码:', r.status_code); print('CORS响应头:'); cors_headers = {k: v for k, v in r.headers.items() if 'access-control' in k.lower()}; [print(f'  {k}: {v}') for k, v in sorted(cors_headers.items())] if cors_headers else print('  [错误] 没有CORS响应头！这可能是问题所在。')"
echo.

echo ========================================
echo 测试完成
echo ========================================
echo.

echo [重要提示]
echo   如果看到 "没有CORS响应头"，说明：
echo   1. 后端服务器需要重启以加载新的CORS配置
echo   2. 或者CORS配置有问题
echo.
echo   解决方法：
echo   1. 停止当前后端服务器（Ctrl+C）
echo   2. 重新启动后端服务器
echo   3. 再次运行此测试脚本
echo.

pause

