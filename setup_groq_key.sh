#!/bin/bash
# Groq API 密钥配置脚本
# 使用方法：在服务器上执行此脚本，会自动配置Groq API密钥

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Groq API 密钥配置脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否在项目目录
if [ ! -f "sk_app.py" ]; then
    echo -e "${RED}❌ 错误：请在项目根目录执行此脚本${NC}"
    exit 1
fi

# 项目目录
PROJECT_DIR=$(pwd)
ENV_FILE="$PROJECT_DIR/.env"

echo -e "${YELLOW}📁 项目目录: $PROJECT_DIR${NC}"
echo ""

# 检查是否提供了密钥参数
if [ -z "$1" ]; then
    echo -e "${YELLOW}⚠️  未提供密钥参数${NC}"
    echo -e "${YELLOW}使用方法: $0 <您的Groq_API密钥>${NC}"
    echo ""
    echo -e "${YELLOW}或者手动编辑 .env 文件：${NC}"
    echo -e "  nano $ENV_FILE"
    echo ""
    exit 1
fi

GROQ_API_KEY="$1"

# 检查密钥格式
if [[ ! "$GROQ_API_KEY" =~ ^gsk_ ]]; then
    echo -e "${RED}❌ 错误：密钥格式不正确，应以 'gsk_' 开头${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 密钥格式验证通过${NC}"
echo ""

# 创建或更新 .env 文件
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}📝 创建新的 .env 文件...${NC}"
    touch "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    
    # 添加基本配置
    cat > "$ENV_FILE" << EOF
# 环境变量配置文件
# 此文件包含敏感信息，不会被提交到 Git 仓库

# Groq API 配置
GROQ_API_KEY=$GROQ_API_KEY
EOF
else
    echo -e "${YELLOW}📝 更新现有 .env 文件...${NC}"
    
    # 检查是否已存在 GROQ_API_KEY
    if grep -q "^GROQ_API_KEY=" "$ENV_FILE"; then
        # 更新现有密钥
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|^GROQ_API_KEY=.*|GROQ_API_KEY=$GROQ_API_KEY|" "$ENV_FILE"
        else
            # Linux
            sed -i "s|^GROQ_API_KEY=.*|GROQ_API_KEY=$GROQ_API_KEY|" "$ENV_FILE"
        fi
        echo -e "${GREEN}✅ 已更新 GROQ_API_KEY${NC}"
    else
        # 添加新密钥
        echo "" >> "$ENV_FILE"
        echo "# Groq API 配置" >> "$ENV_FILE"
        echo "GROQ_API_KEY=$GROQ_API_KEY" >> "$ENV_FILE"
        echo -e "${GREEN}✅ 已添加 GROQ_API_KEY${NC}"
    fi
    
    # 设置文件权限（仅所有者可读）
    chmod 600 "$ENV_FILE"
fi

echo ""
echo -e "${GREEN}✅ 配置完成！${NC}"
echo ""
echo -e "${YELLOW}📋 配置信息：${NC}"
echo -e "   文件路径: $ENV_FILE"
echo -e "   密钥前缀: ${GROQ_API_KEY:0:10}...${GROQ_API_KEY: -10}"
echo ""

# 检查服务是否需要重启
echo -e "${YELLOW}🔄 重启服务以应用新配置...${NC}"
if systemctl is-active --quiet background_remover_tool 2>/dev/null; then
    sudo systemctl restart background_remover_tool
    echo -e "${GREEN}✅ 服务已重启${NC}"
    
    # 等待服务启动
    sleep 2
    
    # 检查服务状态
    if systemctl is-active --quiet background_remover_tool; then
        echo -e "${GREEN}✅ 服务运行正常${NC}"
    else
        echo -e "${RED}⚠️  服务可能未正常启动，请检查日志：${NC}"
        echo -e "   sudo journalctl -u background_remover_tool -n 20"
    fi
else
    echo -e "${YELLOW}⚠️  未找到 systemd 服务，请手动重启应用${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  配置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo -e "   1. .env 文件已配置，不会被提交到 Git"
echo -e "   2. 如果服务未自动重启，请手动执行："
echo -e "      sudo systemctl restart background_remover_tool"
echo -e "   3. 查看服务日志："
echo -e "      sudo journalctl -u background_remover_tool -n 30"
echo ""

