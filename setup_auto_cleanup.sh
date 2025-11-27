#!/bin/bash
# 设置自动清理定时任务
# 功能：每天凌晨2点自动清理7天前的文件

echo "🔧 设置自动清理定时任务..."

# 脚本路径
SCRIPT_PATH="/var/www/background_remover_tool/cleanup_old_files.sh"

# 确保脚本有执行权限
chmod +x "$SCRIPT_PATH"

# 检查是否已经存在定时任务
if crontab -l 2>/dev/null | grep -q "cleanup_old_files.sh"; then
    echo "⚠️  定时任务已存在，将更新..."
    # 删除旧的定时任务
    crontab -l 2>/dev/null | grep -v "cleanup_old_files.sh" | crontab -
fi

# 添加新的定时任务（每天凌晨2点执行）
(crontab -l 2>/dev/null; echo "0 2 * * * $SCRIPT_PATH >> /var/www/background_remover_tool/cleanup.log 2>&1") | crontab -

echo "✅ 定时任务已设置！"
echo ""
echo "📋 当前定时任务列表："
crontab -l | grep -E "(cleanup|CLEANUP)" || echo "  （未找到清理任务）"
echo ""
echo "📝 定时任务详情："
echo "  - 执行时间：每天凌晨 2:00"
echo "  - 清理规则：删除 7 天前的文件"
echo "  - 日志文件：/var/www/background_remover_tool/cleanup.log"
echo ""
echo "🧪 测试执行（立即运行一次）："
read -p "是否立即测试执行清理脚本？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "执行清理脚本..."
    bash "$SCRIPT_PATH"
fi

