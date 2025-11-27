# Git自动化部署系统使用指南

## 概述

本文档详细介绍了背景移除工具的Git自动化部署系统。通过这个系统，您可以实现代码的版本控制和自动化部署，极大地简化了从本地开发到线上更新的流程。

## 系统架构

我们的Git自动化部署系统采用了以下架构：

1. **本地开发环境**：您进行代码开发和测试的地方
2. **Git仓库**：存储代码版本的地方
3. **PythonAnywhere服务器**：运行生产环境应用的地方
4. **Git钩子（Hooks）**：自动化部署的关键组件

## 本地环境设置（已完成）

我们已经为您完成了以下本地设置：

1. 创建了Git仓库
2. 配置了`.gitignore`文件，排除不需要提交的文件
3. 初始化了仓库并添加了基础文件
4. 创建了`deploy.bat`一键部署脚本

## 服务器端设置步骤

请按照以下步骤在PythonAnywhere服务器端设置Git接收端：

### 步骤1：连接到PythonAnywhere服务器

使用PythonAnywhere的SSH控制台或Web终端登录到您的账户。

### 步骤2：创建Git裸仓库

```bash
# 进入home目录
cd ~

# 创建Git裸仓库目录
mkdir -p mysite.git
cd mysite.git

# 初始化裸仓库
git init --bare
```

### 步骤3：配置Git钩子

```bash
# 创建post-receive钩子
cd ~/mysite.git/hooks
touch post-receive
chmod +x post-receive

# 编辑post-receive钩子
nano post-receive
```

在编辑器中粘贴以下内容：

```bash
#!/bin/bash

declare -A file_operations

# 定义文件操作映射（源路径 -> 目标路径）
file_operations["flask_app.py"]="$HOME/mysite/flask_app.py"
file_operations["requirements.txt"]="$HOME/mysite/requirements.txt"
file_operations["templates/index.html"]="$HOME/mysite/templates/index.html"

# 设置工作目录
DEPLOY_DIR="$HOME/mysite/deploy_temp"
mkdir -p "$DEPLOY_DIR"

# 检出代码到临时目录
git --work-tree="$DEPLOY_DIR" --git-dir="$HOME/mysite.git" checkout -f

# 复制文件到目标位置
for src_file in "${!file_operations[@]}"; do
  dest_file="${file_operations[$src_file]}"
  dest_dir="$(dirname "$dest_file")"
  
  mkdir -p "$dest_dir"
  
  if [ -f "$DEPLOY_DIR/$src_file" ]; then
    echo "复制 $src_file 到 $dest_file"
    cp "$DEPLOY_DIR/$src_file" "$dest_file"
  else
    echo "警告: 源文件 $src_file 不存在"
  fi
done

# 删除临时目录
rm -rf "$DEPLOY_DIR"

# 安装依赖
echo "更新依赖..."
cd "$HOME/mysite"
pip install -r requirements.txt --user

# 重启Web应用
echo "重启Web应用..."
/home/$USER/.virtualenvs/myvirtualenv/bin/python -m flask --app flask_app.py run --port=8000 &

# 清理旧进程
pkill -f "flask_app.py"

# 启动新进程
/home/$USER/.virtualenvs/myvirtualenv/bin/python -m flask --app flask_app.py run --port=8000 &

echo "部署完成！"
```

保存并退出编辑器（Ctrl+O，Enter，Ctrl+X）。

### 步骤4：确保mysite目录存在

```bash
mkdir -p ~/mysite/templates
```

## 本地部署流程

### 方法1：使用deploy.bat一键部署（推荐）

1. 在Windows上，双击运行`d:\background_remover_tool\deploy.bat`
2. 脚本会自动完成以下操作：
   - 从backend目录复制最新文件
   - 添加所有更改到Git
   - 提交更改
   - 推送到服务器
   - 触发自动部署

### 方法2：手动Git命令部署

如果您想手动控制部署过程，可以使用以下Git命令：

```bash
# 从backend复制最新文件到根目录
copy d:\background_remover_tool\backend\flask_app.py d:\background_remover_tool\
mkdir -p d:\background_remover_tool\templates
copy d:\background_remover_tool\backend\templates\index.html d:\background_remover_tool\templates\

# 添加更改到Git
git add --force flask_app.py requirements.txt templates/index.html

# 提交更改
git commit -m "更新：$(date)"

# 推送到服务器
git push origin master
```

## 日常维护与更新

1. **更新代码**：在backend目录中修改代码
2. **部署更新**：运行deploy.bat一键部署
3. **监控部署**：检查PythonAnywhere的日志确认部署是否成功

## 常见问题与解决方案

### 问题1：部署后应用未更新

**解决方案**：
- 检查PythonAnywhere的错误日志
- 确认Git钩子是否有执行权限
- 验证文件路径是否正确

### 问题2：依赖安装失败

**解决方案**：
- 更新requirements.txt文件，确保依赖版本兼容
- 尝试手动在PythonAnywhere上安装依赖

### 问题3：Git推送被拒绝

**解决方案**：
- 确保本地仓库是最新的：`git pull origin master`
- 解决可能的合并冲突

## 安全考虑

1. **不要提交敏感信息**：确保.env文件等包含API密钥的文件已在.gitignore中配置
2. **定期备份**：定期备份PythonAnywhere上的文件和数据库
3. **限制访问**：确保只有授权用户可以访问Git仓库和服务器

## 总结

这个Git自动化部署系统大大简化了从本地开发到线上部署的流程。您只需在backend目录中进行开发，然后运行deploy.bat脚本，系统会自动完成所有部署工作，让您专注于代码开发而非繁琐的部署操作。

祝您使用愉快！