import os
import shutil

# 定义要清理的文件类型和目录
CLEANUP_EXTENSIONS = ['.md', '.txt', '.bat', '.sh', '.html', '.js', '.py']
KEEP_FILES = [
    'sk_app.py', 'data_manager.py', 'supabase_db.py', 'requirements.txt', 
    'deploy.bat', 'start_dev_servers.bat', '启动前端服务器.bat'
]
KEEP_DIRS = ['frontend', 'backend', 'data', 'uploads', 'venv', '.venv', '.git', '__pycache__']

# 创建备份目录
BACKUP_DIR = '_old_website_backup'
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def cleanup():
    count = 0
    # 获取当前目录下的所有文件和文件夹
    for item in os.listdir('.'):
        # 跳过备份目录本身
        if item == BACKUP_DIR:
            continue
            
        # 检查是否应该保留
        if item in KEEP_FILES or item in KEEP_DIRS:
            print(f"保留: {item}")
            continue
            
        # 如果是前端/后端目录下的文件，不要动（虽然list中已经排除了目录）
        
        # 移动其他所有 .md, .txt, .bat, .sh, test_*, debug_* 文件
        # 或者是之前提到的那些长文件名的 .md
        
        should_move = False
        
        if os.path.isdir(item):
            # 如果是其他文件夹（比如 manual_health_fix 等），移动
            should_move = True
        else:
            # 是文件
            ext = os.path.splitext(item)[1].lower()
            if item.startswith('test_') or item.startswith('debug_') or \
               item.startswith('文章') or item.endswith('说明.md') or \
               item.endswith('指南.md') or item.endswith('报告.md'):
                should_move = True
            elif ext in ['.md', '.txt'] and item not in KEEP_FILES:
                should_move = True
            elif ext in ['.bat', '.sh'] and item not in KEEP_FILES:
                should_move = True
        
        if should_move:
            try:
                shutil.move(item, os.path.join(BACKUP_DIR, item))
                print(f"已移动到备份: {item}")
                count += 1
            except Exception as e:
                print(f"移动失败 {item}: {e}")

    print(f"\n清理完成! 共移动了 {count} 个文件/文件夹到 {BACKUP_DIR}")
    print("核心系统文件已保留。")

if __name__ == "__main__":
    cleanup()
