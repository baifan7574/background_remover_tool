#!/bin/bash
# 测试健康检查脚本是否能正常工作

echo "=========================================="
echo "测试健康检查脚本"
echo "=========================================="
echo ""

# 检查脚本是否存在
if [ ! -f "/var/www/background_remover_tool/网站健康检查.sh" ]; then
    echo "❌ 健康检查脚本不存在"
    exit 1
fi

echo "✅ 脚本文件存在"
echo ""

# 检查脚本权限
if [ ! -x "/var/www/background_remover_tool/网站健康检查.sh" ]; then
    echo "⚠️ 脚本没有执行权限，正在设置..."
    chmod +x /var/www/background_remover_tool/网站健康检查.sh
fi

echo "✅ 脚本有执行权限"
echo ""

# 手动执行一次脚本
echo "执行健康检查脚本..."
/var/www/background_remover_tool/网站健康检查.sh

echo ""
echo "=========================================="
echo "检查日志文件"
echo "=========================================="
echo ""

# 检查日志文件是否创建
if [ -f "/var/log/website_health_check.log" ]; then
    echo "✅ 日志文件已创建"
    echo ""
    echo "最近的日志内容："
    tail -10 /var/log/website_health_check.log
else
    echo "⚠️ 日志文件还未创建（可能需要等待几分钟）"
    echo ""
    echo "检查日志目录权限..."
    ls -la /var/log/ | grep website
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="

