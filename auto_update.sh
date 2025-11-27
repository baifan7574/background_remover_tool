#!/bin/bash
# 自动更新脚本 - 检查GitHub是否有更新，如果有则自动拉取
# 使用方法：可以手动执行，也可以添加到定时任务

# 项目目录
PROJECT_DIR="/var/www/background_remover_tool"
LOG_FILE="/var/www/background_remover_tool/auto_update.log"

# 记录日志函数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "=========================================="
log_message "开始检查更新..."

# 进入项目目录
cd "$PROJECT_DIR" || {
    log_message "❌ 无法进入项目目录: $PROJECT_DIR"
    exit 1
}

# 获取当前分支的最新提交
git fetch origin

# 检查是否有更新
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/master)

if [ "$LOCAL" != "$REMOTE" ]; then
    log_message "发现更新，开始拉取..."
    log_message "本地提交: $LOCAL"
    log_message "远程提交: $REMOTE"
    
    # 拉取更新
    git pull origin master
    
    if [ $? -eq 0 ]; then
        log_message "✅ 代码更新成功"
        
        # 重启服务
        log_message "重启服务..."
        sudo systemctl restart background_remover_tool
        
        if [ $? -eq 0 ]; then
            log_message "✅ 服务重启成功"
        else
            log_message "❌ 服务重启失败"
        fi
    else
        log_message "❌ 代码更新失败"
    fi
else
    log_message "没有更新（本地和远程一致）"
fi

log_message "=========================================="

