@echo off
chcp 65001 >nul
title 快速测试rembg

echo ========================================
echo 快速测试rembg库
echo ========================================
echo.

echo [测试1] 检查rembg是否安装...
pip show rembg 2>nul | findstr /i "Name Version"
echo.

echo [测试2] 测试rembg导入...
python -c "from rembg import remove; print('OK: rembg可以正常导入')" 2>&1
echo.

echo [测试3] 运行完整测试...
python test_rembg.py
echo.

echo ========================================
echo 测试完成
echo ========================================
echo.

echo [下一步]
echo   1. 如果测试成功，重启后端服务器
echo   2. 查看后端启动日志，应该看到：
echo      "rembg库已安装并可用，背景移除功能将使用AI处理"
echo   3. 测试背景移除功能
echo.

pause

