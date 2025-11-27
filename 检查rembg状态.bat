@echo off
chcp 65001 >nul
title 检查rembg状态

echo ========================================
echo 检查rembg状态
echo ========================================
echo.

echo [第1步] 检查rembg安装...
pip show rembg 2>nul | findstr /i "Name Version Location"
echo.

echo [第2步] 测试rembg导入...
python -c "from rembg import remove; print('[成功] rembg可以正常导入')" 2>&1
if errorlevel 1 (
    echo.
    echo [失败] rembg导入失败！
    echo.
    echo [原因] 通常是numpy/opencv版本不兼容
    echo [解决] 运行：快速修复rembg依赖.bat
    echo.
) else (
    echo.
    echo [成功] rembg可以正常导入！
    echo.
    echo [下一步] 如果后端还是显示模拟模式：
    echo   1. 确认后端服务器已重启
    echo   2. 查看后端启动日志，应该看到：
    echo      "rembg库已安装并可用，背景移除功能将使用AI处理"
    echo   3. 如果没有看到，运行：快速修复rembg依赖.bat
    echo.
)
echo.

echo [第3步] 检查numpy和opencv版本...
python -c "import numpy; print('[numpy版本]', numpy.__version__)" 2>&1
python -c "import cv2; print('[opencv版本]', cv2.__version__)" 2>&1
echo.

echo ========================================
echo 检查完成
echo ========================================
echo.

pause

