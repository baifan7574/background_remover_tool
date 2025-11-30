#!/bin/bash
# HTTPS和SEO配置检查脚本
# 使用方法：在服务器上执行 bash 检查HTTPS和SEO配置.sh

echo "=========================================="
echo "🔍 HTTPS和SEO配置检查"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 网站域名
DOMAIN="nbfive.com"
BASE_URL="https://${DOMAIN}"

echo "📋 检查项目："
echo "1. HTTPS证书有效性"
echo "2. robots.txt可访问性"
echo "3. sitemap.xml可访问性"
echo "4. 百度验证码存在性"
echo "5. HTTP到HTTPS重定向"
echo ""

# 1. 检查HTTPS证书
echo "----------------------------------------"
echo "1️⃣ 检查HTTPS证书..."
echo "----------------------------------------"
if curl -s -I "${BASE_URL}" | grep -q "200 OK"; then
    echo -e "${GREEN}✅ HTTPS证书有效，网站可访问${NC}"
    
    # 检查证书详情
    echo ""
    echo "证书信息："
    echo | openssl s_client -connect "${DOMAIN}:443" -servername "${DOMAIN}" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | head -2
else
    echo -e "${RED}❌ HTTPS证书无效或网站无法访问${NC}"
fi
echo ""

# 2. 检查HTTP到HTTPS重定向
echo "----------------------------------------"
echo "2️⃣ 检查HTTP到HTTPS重定向..."
echo "----------------------------------------"
HTTP_REDIRECT=$(curl -s -I "http://${DOMAIN}" | grep -i "location\|301\|302")
if echo "$HTTP_REDIRECT" | grep -qi "https"; then
    echo -e "${GREEN}✅ HTTP自动跳转到HTTPS${NC}"
else
    echo -e "${YELLOW}⚠️  HTTP可能未自动跳转到HTTPS（需要检查Nginx配置）${NC}"
fi
echo ""

# 3. 检查robots.txt
echo "----------------------------------------"
echo "3️⃣ 检查robots.txt..."
echo "----------------------------------------"
ROBOTS_URL="${BASE_URL}/robots.txt"
ROBOTS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${ROBOTS_URL}")
if [ "$ROBOTS_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ robots.txt可访问 (HTTP ${ROBOTS_RESPONSE})${NC}"
    echo ""
    echo "robots.txt内容预览："
    curl -s "${ROBOTS_URL}" | head -10
    echo ""
    
    # 检查是否包含sitemap
    if curl -s "${ROBOTS_URL}" | grep -qi "sitemap"; then
        echo -e "${GREEN}✅ robots.txt包含sitemap声明${NC}"
    else
        echo -e "${YELLOW}⚠️  robots.txt未包含sitemap声明${NC}"
    fi
else
    echo -e "${RED}❌ robots.txt无法访问 (HTTP ${ROBOTS_RESPONSE})${NC}"
fi
echo ""

# 4. 检查sitemap.xml
echo "----------------------------------------"
echo "4️⃣ 检查sitemap.xml..."
echo "----------------------------------------"
SITEMAP_URL="${BASE_URL}/sitemap.xml"
SITEMAP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${SITEMAP_URL}")
if [ "$SITEMAP_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ sitemap.xml可访问 (HTTP ${SITEMAP_RESPONSE})${NC}"
    echo ""
    
    # 检查sitemap内容
    SITEMAP_CONTENT=$(curl -s "${SITEMAP_URL}")
    URL_COUNT=$(echo "$SITEMAP_CONTENT" | grep -c "<loc>")
    echo "sitemap.xml包含 ${URL_COUNT} 个URL"
    
    # 检查是否所有URL都是HTTPS
    HTTP_URLS=$(echo "$SITEMAP_CONTENT" | grep -c "http://")
    if [ "$HTTP_URLS" -eq 0 ]; then
        echo -e "${GREEN}✅ 所有URL都使用HTTPS${NC}"
    else
        echo -e "${YELLOW}⚠️  发现 ${HTTP_URLS} 个HTTP URL，建议改为HTTPS${NC}"
    fi
else
    echo -e "${RED}❌ sitemap.xml无法访问 (HTTP ${SITEMAP_RESPONSE})${NC}"
fi
echo ""

# 5. 检查百度验证码
echo "----------------------------------------"
echo "5️⃣ 检查百度验证码..."
echo "----------------------------------------"
BAIDU_VERIFY="codeva-ptfBSCM5JY"
HOME_PAGE=$(curl -s "${BASE_URL}")
if echo "$HOME_PAGE" | grep -q "baidu-site-verification.*${BAIDU_VERIFY}"; then
    echo -e "${GREEN}✅ 百度验证码存在${NC}"
    echo "验证码：${BAIDU_VERIFY}"
else
    echo -e "${RED}❌ 百度验证码未找到${NC}"
    echo "预期验证码：${BAIDU_VERIFY}"
fi
echo ""

# 6. 模拟百度爬虫抓取
echo "----------------------------------------"
echo "6️⃣ 模拟百度爬虫抓取..."
echo "----------------------------------------"
BAIDU_USER_AGENT="Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)"
BAIDU_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -A "${BAIDU_USER_AGENT}" "${BASE_URL}")
if [ "$BAIDU_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ 百度爬虫可以正常访问网站 (HTTP ${BAIDU_RESPONSE})${NC}"
else
    echo -e "${RED}❌ 百度爬虫无法访问网站 (HTTP ${BAIDU_RESPONSE})${NC}"
fi
echo ""

# 7. 检查Canonical标签
echo "----------------------------------------"
echo "7️⃣ 检查Canonical标签..."
echo "----------------------------------------"
if echo "$HOME_PAGE" | grep -qi "rel=\"canonical\""; then
    echo -e "${GREEN}✅ Canonical标签存在${NC}"
    CANONICAL_URL=$(echo "$HOME_PAGE" | grep -i "rel=\"canonical\"" | sed -n 's/.*href="\([^"]*\)".*/\1/p')
    echo "Canonical URL: ${CANONICAL_URL}"
else
    echo -e "${YELLOW}⚠️  Canonical标签未找到${NC}"
fi
echo ""

# 总结
echo "=========================================="
echo "📊 检查总结"
echo "=========================================="
echo ""
echo "✅ 通过的项目："
[ "$ROBOTS_RESPONSE" = "200" ] && echo "  - robots.txt可访问"
[ "$SITEMAP_RESPONSE" = "200" ] && echo "  - sitemap.xml可访问"
echo "$HOME_PAGE" | grep -q "baidu-site-verification.*${BAIDU_VERIFY}" && echo "  - 百度验证码存在"
[ "$BAIDU_RESPONSE" = "200" ] && echo "  - 百度爬虫可访问"
echo "$HOME_PAGE" | grep -qi "rel=\"canonical\"" && echo "  - Canonical标签存在"
echo ""

echo "⚠️  需要注意的项目："
[ "$ROBOTS_RESPONSE" != "200" ] && echo "  - robots.txt无法访问"
[ "$SITEMAP_RESPONSE" != "200" ] && echo "  - sitemap.xml无法访问"
! echo "$HOME_PAGE" | grep -q "baidu-site-verification.*${BAIDU_VERIFY}" && echo "  - 百度验证码未找到"
[ "$BAIDU_RESPONSE" != "200" ] && echo "  - 百度爬虫无法访问"
! echo "$HOME_PAGE" | grep -qi "rel=\"canonical\"" && echo "  - Canonical标签未找到"
echo ""

echo "📝 下一步操作："
echo "1. 在百度站长平台添加网站：https://ziyuan.baidu.com/"
echo "2. 提交sitemap：${SITEMAP_URL}"
echo "3. 使用抓取诊断工具测试首页"
echo "4. 定期检查索引量变化"
echo ""

echo "=========================================="
echo "检查完成！"
echo "=========================================="

