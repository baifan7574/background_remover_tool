@echo off
echo ========================================
echo 测试依赖库是否已安装
echo ========================================
echo.

python -c "try:
    import groq
    print('✅ groq 已安装')
except ImportError:
    print('❌ groq 未安装')"

python -c "try:
    import pytrends
    print('✅ pytrends 已安装')
except ImportError:
    print('❌ pytrends 未安装')"

echo.
echo ========================================
echo 测试完成
echo ========================================
echo.
echo 如果显示 ❌，请执行: pip install groq pytrends
echo.
pause

