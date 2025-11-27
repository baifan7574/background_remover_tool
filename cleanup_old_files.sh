#!/bin/bash
# 自动清理旧文件脚本
# 功能：清理指定天数前的上传文件和临时文件
# 使用方法：可以手动执行，也可以添加到定时任务

# 配置参数
DAYS_TO_KEEP=7  # 保留最近7天的文件（可以根据需要修改）
UPLOAD_DIR="/var/www/background_remover_tool/uploads"
LOG_FILE="/var/www/background_remover_tool/cleanup.log"

# 创建日志函数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_message "=========================================="
log_message "开始清理旧文件..."

# 检查上传目录是否存在
if [ ! -d "$UPLOAD_DIR" ]; then
    log_message "⚠️  上传目录不存在: $UPLOAD_DIR"
    exit 1
fi

# 统计清理前的文件数量和大小
BEFORE_COUNT=$(find "$UPLOAD_DIR" -type f | wc -l)
BEFORE_SIZE=$(du -sh "$UPLOAD_DIR" 2>/dev/null | cut -f1)

log_message "清理前：文件数量=$BEFORE_COUNT, 目录大小=$BEFORE_SIZE"

# 清理指定天数前的文件
DELETED_COUNT=0
DELETED_SIZE=0

# 查找并删除旧文件
while IFS= read -r file; do
    if [ -f "$file" ]; then
        FILE_SIZE=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        DELETED_SIZE=$((DELETED_SIZE + FILE_SIZE))
        rm -f "$file"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    fi
done < <(find "$UPLOAD_DIR" -type f -mtime +$DAYS_TO_KEEP)

# 删除空目录
find "$UPLOAD_DIR" -type d -empty -delete 2>/dev/null

# 统计清理后的文件数量和大小
AFTER_COUNT=$(find "$UPLOAD_DIR" -type f | wc -l)
AFTER_SIZE=$(du -sh "$UPLOAD_DIR" 2>/dev/null | cut -f1)

# 计算释放的空间（MB）
FREED_MB=$((DELETED_SIZE / 1024 / 1024))

log_message "清理完成："
log_message "  - 删除了 $DELETED_COUNT 个文件"
log_message "  - 释放了约 ${FREED_MB}MB 空间"
log_message "  - 清理后：文件数量=$AFTER_COUNT, 目录大小=$AFTER_SIZE"
log_message "=========================================="

# 如果释放了空间，显示成功信息
if [ $DELETED_COUNT -gt 0 ]; then
    log_message "✅ 清理成功！"
else
    log_message "ℹ️  没有需要清理的文件（所有文件都在最近 ${DAYS_TO_KEEP} 天内）"
fi
