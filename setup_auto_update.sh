#!/bin/bash
# 一键设置自动更新脚本
# 使用方法：在服务器上执行：bash setup_auto_update.sh

echo "🚀 开始设置自动更新..."

# 项目目录
PROJECT_DIR="/var/www/background_remover_tool"

# 进入项目目录
cd "$PROJECT_DIR" || {
    echo "❌ 无法进入项目目录: $PROJECT_DIR"
    exit 1
}

# 1. 确保auto_update.sh存在
if [ ! -f "auto_update.sh" ]; then
    echo "❌ auto_update.sh 文件不存在"
    echo "请先推送 auto_update.sh 到GitHub，然后在服务器上执行 git pull"
    exit 1
fi

# 2. 设置执行权限
echo "📝 设置执行权限..."
chmod +x auto_update.sh
echo "✅ 执行权限已设置"

# 3. 测试脚本（不实际执行，只检查语法）
echo "🧪 测试脚本..."
bash -n auto_update.sh
if [ $? -eq 0 ]; then
    echo "✅ 脚本语法正确"
else
    echo "❌ 脚本语法错误"
    exit 1
fi

# 4. 检查是否已有定时任务
echo "📋 检查现有定时任务..."
EXISTING_CRON=$(crontab -l 2>/dev/null | grep "auto_update.sh")

if [ -n "$EXISTING_CRON" ]; then
    echo "⚠️  发现已有自动更新定时任务，将更新..."
    # 删除旧的定时任务
    crontab -l 2>/dev/null | grep -v "auto_update.sh" | crontab -
fi

# 5. 添加新的定时任务
echo "➕ 添加定时任务..."
(crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/auto_update.sh >> $PROJECT_DIR/auto_update.log 2>&1") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ 定时任务已添加"
else
    echo "❌ 定时任务添加失败"
    exit 1
fi

# 6. 显示当前定时任务
echo ""
echo "📋 当前定时任务列表："
crontab -l

# 7. 测试执行一次（可选）
echo ""
read -p "是否立即测试执行一次自动更新？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 执行自动更新脚本..."
    bash auto_update.sh
    echo ""
    echo "📋 更新日志（最近10行）："
    tail -n 10 auto_update.log 2>/dev/null || echo "（日志文件还未创建）"
fi

echo ""
echo "✅✅✅ 自动更新设置完成！"
echo ""
echo "📝 使用说明："
echo "  1. 在本地修改代码"
echo "  2. 用GitHub Desktop推送到仓库"
echo "  3. 等待5分钟，服务器会自动更新"
echo "  4. 或手动执行：bash $PROJECT_DIR/auto_update.sh"
echo ""
echo "📋 查看日志："
echo "  tail -f $PROJECT_DIR/auto_update.log"
echo ""
echo "📋 查看定时任务："
echo "  crontab -l"

