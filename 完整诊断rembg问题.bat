@echo off
chcp 65001 >nul
title 完整诊断rembg问题

echo ========================================
echo 完整诊断rembg问题
echo ========================================
echo.

echo [诊断1] 检查rembg安装状态...
pip show rembg 2>nul | findstr /i "Name Version Location"
echo.

echo [诊断2] 测试rembg导入...
python -c "try: from rembg import remove; print('[OK] rembg可以正常导入'); except Exception as e: print('[ERROR] rembg导入失败:', type(e).__name__, e)" 2>&1
echo.

echo [诊断3] 检查依赖库版本...
echo.
python -c "import numpy; print('numpy:', numpy.__version__)" 2>nul || echo "numpy: 未安装或导入失败"
python -c "import cv2; print('opencv-python:', cv2.__version__)" 2>nul || echo "opencv-python: 未安装或导入失败"
echo.

echo [诊断4] 检查Python环境...
python --version
where python
echo.

echo [诊断5] 检查后端服务器是否运行...
netstat -ano | findstr ":5000" | findstr "LISTENING"
if errorlevel 1 (
    echo [警告] 后端服务器未运行（端口5000没有被占用）
    echo.
) else (
    echo [信息] 后端服务器正在运行（端口5000被占用）
    echo.
)
echo.

echo ========================================
echo 诊断结果
echo ========================================
echo.

echo [如果rembg导入失败]
echo   运行：快速修复rembg依赖.bat
echo.

echo [如果rembg导入成功，但后端还是显示模拟模式]
echo   1. 后端服务器需要重启
echo   2. 查看后端启动日志，看是否显示：
echo      "rembg库已安装并可用，背景移除功能将使用AI处理"
echo   3. 如果后端启动时还是显示"rembg库未安装"：
echo      - 可能是后端使用的Python环境不同
echo      - 在后端使用的Python环境中安装rembg
echo      - 或者重启后端服务器
echo.

pause

