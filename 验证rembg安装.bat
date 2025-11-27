@echo off
chcp 65001 >nul
title 验证rembg安装

echo ========================================
echo 验证rembg库安装
echo ========================================
echo.

echo [第1步] 检查rembg是否安装...
echo.
pip show rembg 2>nul | findstr /i "Name Version"
if errorlevel 1 (
    echo [未安装] rembg库未找到
    echo.
    echo 正在安装rembg库...
    pip install rembg
    echo.
) else (
    echo [已安装] rembg库已安装
    echo.
)

echo [第2步] 测试rembg导入...
echo.
python -c "from rembg import remove; print('[成功] rembg可以正常导入')"
if errorlevel 1 (
    echo [失败] rembg导入失败
    echo.
    echo 正在查看详细错误...
    python -c "import traceback; from rembg import remove" 2>&1
) else (
    echo [成功] rembg可以正常导入
    echo.
)

echo [第3步] 测试rembg功能...
echo.
python test_rembg.py
if errorlevel 1 (
    echo [失败] rembg功能测试失败
) else (
    echo [成功] rembg功能正常
)
echo.

echo ========================================
echo 验证完成
echo ========================================
echo.

echo [重要提示]
echo   如果rembg可以正常导入和测试，但后端还是显示"模拟模式"：
echo   1. 后端服务器需要重启（因为修改了代码）
echo   2. 检查后端控制台日志，看是否有错误
echo   3. 确保后端服务器使用的是同一个Python环境
echo.

pause
