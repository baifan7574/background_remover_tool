#!/bin/bash
# ========================================
# 修复 Groq 库安装和配置
# ========================================

echo "🔧 开始修复 Groq 配置..."
echo ""

# 进入项目目录
cd /var/www/background_remover_tool

# 步骤1：安装 groq 库
echo "📦 步骤1：安装 groq 库..."
echo "----------------------------------------"

# 检查是否有虚拟环境
if [ -d "venv" ]; then
    echo "✅ 检测到虚拟环境 venv，使用虚拟环境安装"
    source venv/bin/activate
    pip install groq==0.4.1
elif [ -d ".venv" ]; then
    echo "✅ 检测到虚拟环境 .venv，使用虚拟环境安装"
    source .venv/bin/activate
    pip install groq==0.4.1
else
    echo "⚠️ 未检测到虚拟环境，使用系统Python安装"
    pip3 install groq==0.4.1
fi

# 验证安装
echo ""
echo "🔍 验证 groq 库安装..."
python3 -c "import groq; print('✅ Groq库安装成功！')" 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Groq库安装失败，尝试使用pip3安装..."
    pip3 install --user groq==0.4.1
    python3 -c "import groq; print('✅ Groq库安装成功！')" 2>&1
fi

echo ""
echo "----------------------------------------"

# 步骤2：配置 .env 文件
echo ""
echo "🔐 步骤2：配置 GROQ_API_KEY..."
echo "----------------------------------------"

# 确保 .env 文件存在
if [ ! -f .env ]; then
    touch .env
    chmod 600 .env
    echo "✅ 创建了 .env 文件"
fi

# 设置密钥（用户提供的密钥）
GROQ_KEY="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"

# 检查是否已存在 GROQ_API_KEY
if grep -q "^GROQ_API_KEY=" .env; then
    # 更新现有密钥
    sed -i "s|^GROQ_API_KEY=.*|GROQ_API_KEY=$GROQ_KEY|" .env
    echo "✅ 已更新 GROQ_API_KEY"
else
    # 添加新密钥
    echo "GROQ_API_KEY=$GROQ_KEY" >> .env
    echo "✅ 已添加 GROQ_API_KEY"
fi

# 设置文件权限
chmod 600 .env

# 验证配置
echo ""
echo "🔍 验证配置..."
if grep -q "^GROQ_API_KEY=" .env; then
    echo "✅ GROQ_API_KEY 已配置"
    # 显示密钥前10个字符和后10个字符（安全显示）
    KEY_PREVIEW=$(grep "^GROQ_API_KEY=" .env | cut -d'=' -f2)
    echo "   密钥预览: ${KEY_PREVIEW:0:10}...${KEY_PREVIEW: -10}"
else
    echo "❌ GROQ_API_KEY 配置失败"
fi

echo ""
echo "----------------------------------------"

# 步骤3：重启服务
echo ""
echo "🔄 步骤3：重启服务..."
echo "----------------------------------------"

# 检查服务是否存在
if systemctl list-units --type=service | grep -q "background_remover_tool"; then
    echo "✅ 检测到 systemd 服务，正在重启..."
    sudo systemctl restart background_remover_tool
    sleep 2
    
    # 检查服务状态
    if systemctl is-active --quiet background_remover_tool; then
        echo "✅ 服务重启成功"
    else
        echo "⚠️ 服务可能未正常运行，请检查日志"
    fi
else
    echo "⚠️ 未检测到 systemd 服务，请手动重启应用"
fi

echo ""
echo "----------------------------------------"

# 步骤4：查看日志
echo ""
echo "📋 步骤4：查看服务日志（最后30行）..."
echo "----------------------------------------"

if systemctl list-units --type=service | grep -q "background_remover_tool"; then
    sudo journalctl -u background_remover_tool -n 30 --no-pager | grep -i -E "(groq|Groq|GROQ|初始化|配置|error|Error|ERROR)" || echo "未找到相关日志"
else
    echo "⚠️ 无法查看systemd日志，请手动检查应用日志"
fi

echo ""
echo "========================================"
echo "✅ 修复完成！"
echo ""
echo "📝 下一步："
echo "1. 检查上面的日志，确认看到 '✅ Groq API已配置'"
echo "2. 如果看到 '⚠️ Groq API密钥未配置'，请检查 .env 文件"
echo "3. 测试 Listing 文案生成功能"
echo "========================================"

