#!/bin/bash
# 配置服务自动重启脚本
# 功能：修改systemd服务配置，使服务崩溃后自动重启

echo "=========================================="
echo "配置服务自动重启"
echo "=========================================="
echo ""

SERVICE_FILE="/etc/systemd/system/background_remover_tool.service"

# 检查服务文件是否存在
if [ ! -f "$SERVICE_FILE" ]; then
    echo "❌ 服务文件不存在: $SERVICE_FILE"
    echo "请先确保服务已正确安装"
    exit 1
fi

# 备份原配置文件
echo "📋 备份原配置文件..."
sudo cp "$SERVICE_FILE" "${SERVICE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ 备份完成"

# 检查是否已配置自动重启
if grep -q "Restart=always" "$SERVICE_FILE"; then
    echo "✅ 服务已配置自动重启"
    echo ""
    echo "当前配置："
    grep -A 5 "\[Service\]" "$SERVICE_FILE" | grep -E "Restart|RestartSec|StartLimit"
    exit 0
fi

# 添加自动重启配置
echo "🔧 添加自动重启配置..."

# 使用sed添加配置（如果[Service]部分存在）
if grep -q "\[Service\]" "$SERVICE_FILE"; then
    # 在[Service]部分后添加配置
    sudo sed -i '/\[Service\]/a\
Restart=always\
RestartSec=10\
StartLimitInterval=300\
StartLimitBurst=5\
StartLimitAction=none' "$SERVICE_FILE"
    
    echo "✅ 自动重启配置已添加"
else
    echo "⚠️ 未找到[Service]部分，需要手动添加"
    echo ""
    echo "请在 $SERVICE_FILE 的 [Service] 部分添加以下内容："
    echo ""
    echo "Restart=always"
    echo "RestartSec=10"
    echo "StartLimitInterval=300"
    echo "StartLimitBurst=5"
    echo "StartLimitAction=none"
    exit 1
fi

# 重新加载systemd配置
echo ""
echo "🔄 重新加载systemd配置..."
sudo systemctl daemon-reload
echo "✅ 配置已重新加载"

# 重启服务
echo ""
echo "🔄 重启服务..."
sudo systemctl restart background_remover_tool
echo "✅ 服务已重启"

# 检查服务状态
echo ""
echo "📊 检查服务状态..."
sleep 2
sudo systemctl status background_remover_tool --no-pager -l

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "✅ 服务已配置自动重启"
echo "   - 服务崩溃后10秒自动重启"
echo "   - 5分钟内最多重启5次"
echo "   - 防止无限重启循环"
echo ""
echo "💡 测试方法："
echo "   sudo systemctl stop background_remover_tool"
echo "   sleep 15"
echo "   sudo systemctl status background_remover_tool"
echo "   # 应该看到服务已自动重启"

