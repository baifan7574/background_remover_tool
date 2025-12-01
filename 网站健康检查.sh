#!/bin/bash
# 网站健康检查脚本
# 功能：检查服务状态、API可用性、资源使用情况
# 使用方法：添加到crontab，每5分钟执行一次

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="/var/log/website_health_check.log"
MAX_LOG_SIZE=10485760  # 10MB

# 清理日志（如果太大）
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt $MAX_LOG_SIZE ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 日志文件过大，清理旧日志" > "$LOG_FILE"
fi

# 记录日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 检查服务状态
check_service() {
    log "🔍 检查Flask服务状态..."
    if systemctl is-active --quiet background_remover_tool; then
        log "${GREEN}✅ Flask服务正在运行${NC}"
        return 0
    else
        log "${RED}❌ Flask服务未运行，尝试启动...${NC}"
        sudo systemctl start background_remover_tool
        sleep 3
        if systemctl is-active --quiet background_remover_tool; then
            log "${GREEN}✅ Flask服务已成功启动${NC}"
            return 0
        else
            log "${RED}❌ Flask服务启动失败${NC}"
            return 1
        fi
    fi
}

# 检查Nginx状态
check_nginx() {
    log "🔍 检查Nginx状态..."
    if systemctl is-active --quiet nginx; then
        log "${GREEN}✅ Nginx正在运行${NC}"
        return 0
    else
        log "${RED}❌ Nginx未运行，尝试启动...${NC}"
        sudo systemctl start nginx
        sleep 2
        if systemctl is-active --quiet nginx; then
            log "${GREEN}✅ Nginx已成功启动${NC}"
            return 0
        else
            log "${RED}❌ Nginx启动失败${NC}"
            return 1
        fi
    fi
}

# 检查API可用性
check_api() {
    log "🔍 检查API可用性..."
    response=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5000/api/health 2>/dev/null)
    if [ "$response" = "200" ]; then
        log "${GREEN}✅ API健康检查通过 (状态码: $response)${NC}"
        return 0
    else
        log "${YELLOW}⚠️ API健康检查失败 (状态码: $response)${NC}"
        return 1
    fi
}

# 检查网站可访问性
check_website() {
    log "🔍 检查网站可访问性..."
    response=$(curl -s -o /dev/null -w "%{http_code}" https://www.nbfive.com 2>/dev/null)
    if [ "$response" = "200" ]; then
        log "${GREEN}✅ 网站可访问 (状态码: $response)${NC}"
        return 0
    else
        log "${YELLOW}⚠️ 网站访问异常 (状态码: $response)${NC}"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    log "🔍 检查磁盘空间..."
    disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 80 ]; then
        log "${GREEN}✅ 磁盘空间充足 (使用率: ${disk_usage}%)${NC}"
        return 0
    elif [ "$disk_usage" -lt 90 ]; then
        log "${YELLOW}⚠️ 磁盘空间警告 (使用率: ${disk_usage}%)${NC}"
        return 1
    else
        log "${RED}❌ 磁盘空间严重不足 (使用率: ${disk_usage}%)${NC}"
        return 2
    fi
}

# 检查内存使用
check_memory() {
    log "🔍 检查内存使用..."
    mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$mem_usage" -lt 80 ]; then
        log "${GREEN}✅ 内存使用正常 (使用率: ${mem_usage}%)${NC}"
        return 0
    elif [ "$mem_usage" -lt 90 ]; then
        log "${YELLOW}⚠️ 内存使用警告 (使用率: ${mem_usage}%)${NC}"
        return 1
    else
        log "${RED}❌ 内存使用严重 (使用率: ${mem_usage}%)${NC}"
        return 2
    fi
}

# 检查服务日志错误
check_logs() {
    log "🔍 检查服务日志..."
    error_count=$(sudo journalctl -u background_remover_tool -n 50 --no-pager | grep -i error | wc -l)
    if [ "$error_count" -eq 0 ]; then
        log "${GREEN}✅ 最近50条日志中无错误${NC}"
        return 0
    elif [ "$error_count" -lt 5 ]; then
        log "${YELLOW}⚠️ 最近50条日志中有 ${error_count} 个错误${NC}"
        return 1
    else
        log "${RED}❌ 最近50条日志中有 ${error_count} 个错误${NC}"
        return 2
    fi
}

# 主函数
main() {
    log "=========================================="
    log "开始网站健康检查"
    log "=========================================="
    
    # 执行各项检查
    service_ok=0
    nginx_ok=0
    api_ok=0
    website_ok=0
    disk_ok=0
    memory_ok=0
    logs_ok=0
    
    check_service && service_ok=1
    check_nginx && nginx_ok=1
    check_api && api_ok=1
    check_website && website_ok=1
    check_disk_space && disk_ok=1
    check_memory && memory_ok=1
    check_logs && logs_ok=1
    
    # 汇总结果
    log "=========================================="
    log "健康检查结果汇总："
    log "  Flask服务: $([ $service_ok -eq 1 ] && echo '✅ 正常' || echo '❌ 异常')"
    log "  Nginx: $([ $nginx_ok -eq 1 ] && echo '✅ 正常' || echo '❌ 异常')"
    log "  API: $([ $api_ok -eq 1 ] && echo '✅ 正常' || echo '❌ 异常')"
    log "  网站: $([ $website_ok -eq 1 ] && echo '✅ 正常' || echo '❌ 异常')"
    log "  磁盘: $([ $disk_ok -eq 1 ] && echo '✅ 正常' || echo '⚠️ 警告')"
    log "  内存: $([ $memory_ok -eq 1 ] && echo '✅ 正常' || echo '⚠️ 警告')"
    log "  日志: $([ $logs_ok -eq 1 ] && echo '✅ 正常' || echo '⚠️ 警告')"
    log "=========================================="
    
    # 如果关键服务异常，尝试修复
    if [ $service_ok -eq 0 ] || [ $nginx_ok -eq 0 ]; then
        log "${RED}⚠️ 关键服务异常，已尝试自动修复${NC}"
    fi
    
    log "健康检查完成"
    log ""
}

# 执行主函数
main

