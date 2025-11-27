@echo off
chcp 65001 >nul
title 修复rembg依赖问题

echo ========================================
echo 修复rembg依赖问题
echo ========================================
echo.

echo [问题诊断]
echo rembg虽然已安装，但导入时出现numpy/cv2兼容性错误
echo 这通常是因为numpy和opencv-python版本不兼容
echo.

echo [解决方案] 重新安装依赖
echo.

echo [第1步] 卸载可能有问题的依赖...
echo.
pip uninstall -y opencv-python opencv-contrib-python numpy rembg
echo.

echo [第2步] 重新安装numpy（稳定版本）...
echo.
pip install numpy==1.24.3
echo.

echo [第3步] 重新安装opencv-python...
echo.
pip install opencv-python
echo.

echo [第4步] 重新安装rembg...
echo.
pip install rembg
echo.

echo [第5步] 验证安装...
echo.
python -c "from rembg import remove; print('[成功] rembg可以正常导入')" 2>&1
if errorlevel 1 (
    echo.
    echo [失败] rembg仍然无法导入
    echo 尝试安装opencv-python-headless...
    pip install opencv-python-headless
    python -c "from rembg import remove; print('[成功] rembg可以正常导入')" 2>&1
)
echo.

echo ========================================
echo 修复完成
echo ========================================
echo.

echo [下一步]
echo   1. 如果看到"成功"，重启后端服务器
echo   2. 查看后端启动日志，应该看到：
echo      "rembg库已安装并可用，背景移除功能将使用AI处理"
echo   3. 测试背景移除功能
echo.

pause

