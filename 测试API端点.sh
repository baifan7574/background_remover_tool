#!/bin/bash
# 测试API端点 - 用于排查"处理失败"问题

echo "=========================================="
echo "API端点测试脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 测试健康检查端点
echo -e "${YELLOW}1. 测试健康检查端点...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" https://www.nbfive.com/api/health 2>/dev/null)
if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ 健康检查通过 (状态码: $response)${NC}"
else
    echo -e "${RED}❌ 健康检查失败 (状态码: $response)${NC}"
fi
echo ""

# 2. 测试压缩API端点（不需要认证）
echo -e "${YELLOW}2. 测试压缩API端点（检查路由是否存在）...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://www.nbfive.com/api/tools/compress-image \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' 2>/dev/null)
echo "状态码: $response"
if [ "$response" = "401" ]; then
    echo -e "${GREEN}✅ API路由存在，但需要认证（这是正常的）${NC}"
elif [ "$response" = "404" ]; then
    echo -e "${RED}❌ API路由不存在（404错误）${NC}"
elif [ "$response" = "500" ]; then
    echo -e "${RED}❌ 服务器内部错误（500错误）${NC}"
else
    echo -e "${YELLOW}⚠️  未知状态码: $response${NC}"
fi
echo ""

# 3. 检查Nginx配置
echo -e "${YELLOW}3. 检查Nginx配置...${NC}"
if [ -f "/etc/nginx/sites-available/background_remover_tool" ]; then
    echo "✅ Nginx配置文件存在"
    echo ""
    echo "API代理配置："
    grep -A 10 "location /api" /etc/nginx/sites-available/background_remover_tool | head -15
else
    echo -e "${RED}❌ Nginx配置文件不存在${NC}"
fi
echo ""

# 4. 检查服务状态
echo -e "${YELLOW}4. 检查服务状态...${NC}"
status=$(systemctl is-active background_remover_tool)
if [ "$status" = "active" ]; then
    echo -e "${GREEN}✅ 服务正在运行${NC}"
else
    echo -e "${RED}❌ 服务未运行 (状态: $status)${NC}"
fi
echo ""

# 5. 检查最近的错误日志
echo -e "${YELLOW}5. 检查最近的错误日志（最后20条）...${NC}"
errors=$(sudo journalctl -u background_remover_tool -n 50 --no-pager | grep -i error | tail -5)
if [ -z "$errors" ]; then
    echo -e "${GREEN}✅ 最近没有错误日志${NC}"
else
    echo -e "${RED}❌ 发现错误日志：${NC}"
    echo "$errors"
fi
echo ""

# 6. 测试本地API（如果服务在运行）
echo -e "${YELLOW}6. 测试本地API（127.0.0.1:5000）...${NC}"
local_response=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/health 2>/dev/null)
if [ "$local_response" = "200" ]; then
    echo -e "${GREEN}✅ 本地API正常 (状态码: $local_response)${NC}"
else
    echo -e "${RED}❌ 本地API异常 (状态码: $local_response)${NC}"
    echo "   可能原因：服务未运行或端口被占用"
fi
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "💡 提示："
echo "1. 如果API路由存在但返回401，说明需要登录"
echo "2. 如果返回404，说明路由配置有问题"
echo "3. 如果返回500，查看服务日志：sudo journalctl -u background_remover_tool -n 50"
echo "4. 在前端浏览器按F12，查看Network标签，看具体错误信息"

