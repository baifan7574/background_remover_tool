#!/bin/bash
# 修复Nginx配置 - 添加请求体大小限制
# 使用方法：在服务器上执行：bash fix_nginx_config.sh

echo "🔧 开始修复Nginx配置..."

# 备份当前配置
BACKUP_FILE="/etc/nginx/sites-available/background_remover_tool.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp /etc/nginx/sites-available/background_remover_tool "$BACKUP_FILE"
echo "✅ 已备份配置到: $BACKUP_FILE"

# 检查配置中是否已经有 client_max_body_size
if grep -q "client_max_body_size" /etc/nginx/sites-available/background_remover_tool; then
    echo "⚠️  配置中已存在 client_max_body_size，将更新为 10M"
    # 更新现有的配置
    sudo sed -i 's/client_max_body_size [0-9]*[mM];/client_max_body_size 10M;/g' /etc/nginx/sites-available/background_remover_tool
else
    echo "📝 添加 client_max_body_size 配置..."
    # 在第一个 server 块的 server_name 之后添加配置
    sudo sed -i '/server_name nbfive.com www.nbfive.com;/a\    # 增加请求体大小限制（允许上传大图片，10MB）\n    client_max_body_size 10M;' /etc/nginx/sites-available/background_remover_tool
fi

# 检查是否已有超时配置
if ! grep -q "proxy_connect_timeout" /etc/nginx/sites-available/background_remover_tool; then
    echo "📝 添加超时配置..."
    # 在 location / 块的 proxy_set_header 之后添加超时配置
    sudo sed -i '/proxy_set_header X-Forwarded-Proto $scheme;/a\        \n        # 增加超时时间（处理大图片可能需要更长时间）\n        proxy_connect_timeout 300s;\n        proxy_send_timeout 300s;\n        proxy_read_timeout 300s;' /etc/nginx/sites-available/background_remover_tool
fi

echo ""
echo "📋 修改后的配置预览（前30行）："
sudo head -n 30 /etc/nginx/sites-available/background_remover_tool

echo ""
echo "🧪 测试Nginx配置..."
if sudo nginx -t; then
    echo ""
    echo "✅ 配置测试通过！"
    echo "🔄 重新加载Nginx..."
    sudo systemctl reload nginx
    echo ""
    echo "✅✅✅ Nginx配置已修复并重新加载！"
    echo ""
    echo "📊 验证配置："
    echo "   - client_max_body_size: $(grep -o 'client_max_body_size [0-9]*[mM]' /etc/nginx/sites-available/background_remover_tool | head -1)"
    echo "   - Nginx状态: $(sudo systemctl is-active nginx)"
else
    echo ""
    echo "❌ 配置测试失败！"
    echo "🔄 恢复备份配置..."
    sudo cp "$BACKUP_FILE" /etc/nginx/sites-available/background_remover_tool
    echo "✅ 已恢复备份配置"
    exit 1
fi

