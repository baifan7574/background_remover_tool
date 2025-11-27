@echo off
chcp 65001 >nul
title 快速修复rembg依赖

echo ========================================
echo 快速修复rembg依赖问题
echo ========================================
echo.

echo [原因] rembg导入失败是因为numpy/opencv版本不兼容
echo [解决] 重新安装兼容的版本
echo.

echo 正在重新安装依赖...
echo.

pip install --upgrade --force-reinstall numpy opencv-python rembg

echo.
echo 验证安装...
python -c "from rembg import remove; print('[成功] rembg可以正常导入')" 2>&1

echo.
echo ========================================
echo 修复完成
echo ========================================
echo.

echo [下一步] 重启后端服务器并测试
echo.

pause

