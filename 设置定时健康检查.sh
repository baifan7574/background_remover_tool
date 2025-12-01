#!/bin/bash
# 设置定时健康检查脚本
# 功能：将健康检查脚本添加到crontab，每5分钟执行一次

echo "=========================================="
echo "设置定时健康检查"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEALTH_CHECK_SCRIPT="$SCRIPT_DIR/网站健康检查.sh"

# 检查健康检查脚本是否存在
if [ ! -f "$HEALTH_CHECK_SCRIPT" ]; then
    echo "❌ 健康检查脚本不存在: $HEALTH_CHECK_SCRIPT"
    exit 1
fi

# 确保脚本有执行权限
chmod +x "$HEALTH_CHECK_SCRIPT"
echo "✅ 已设置脚本执行权限"

# 检查crontab中是否已存在
CRON_JOB="*/5 * * * * $HEALTH_CHECK_SCRIPT"
if crontab -l 2>/dev/null | grep -q "$HEALTH_CHECK_SCRIPT"; then
    echo "✅ 定时任务已存在"
    echo ""
    echo "当前crontab配置："
    crontab -l | grep "$HEALTH_CHECK_SCRIPT"
    exit 0
fi

# 添加到crontab
echo "📋 添加到crontab..."
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "✅ 定时任务已添加"

# 显示当前crontab
echo ""
echo "当前crontab配置："
crontab -l

echo ""
echo "=========================================="
echo "设置完成！"
echo "=========================================="
echo ""
echo "✅ 健康检查脚本将每5分钟执行一次"
echo ""
echo "💡 查看日志："
echo "   tail -f /var/log/website_health_check.log"
echo ""
echo "💡 手动执行健康检查："
echo "   $HEALTH_CHECK_SCRIPT"

