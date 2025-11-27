@echo off
echo ========================================
echo 🔍 本地功能快速测试脚本
echo ========================================
echo.

echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 正在检查依赖包...
python -c "import flask; print('✅ Flask:', flask.__version__)" 2>nul || echo ❌ Flask未安装
python -c "import PIL; print('✅ Pillow:', PIL.__version__)" 2>nul || echo ❌ Pillow未安装
python -c "import supabase; print('✅ Supabase: 已安装')" 2>nul || echo ❌ Supabase未安装
python -c "import rembg; print('✅ rembg: 已安装')" 2>nul || echo ⚠️  rembg未安装（背景移除功能可能受限）

echo.
echo 正在检查文件...
if exist "sk_app.py" (
    echo ✅ sk_app.py 存在
) else (
    echo ❌ sk_app.py 不存在
)

if exist "frontend\index.html" (
    echo ✅ frontend\index.html 存在
) else (
    echo ❌ frontend\index.html 不存在
)

if exist "requirements.txt" (
    echo ✅ requirements.txt 存在
) else (
    echo ❌ requirements.txt 不存在
)

echo.
echo ========================================
echo 📋 测试检查清单
echo ========================================
echo.
echo 请按顺序测试：
echo 1. 双击 start_dev_servers.bat 启动服务器
echo 2. 访问 http://localhost:8000
echo 3. 测试注册功能
echo 4. 测试登录功能
echo 5. 测试图片处理功能
echo.
echo 如果发现问题，请记录错误信息告诉我！
echo.
pause

