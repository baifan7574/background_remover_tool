# 🌐 域名绑定和 Git 自动部署完整指南

## 📋 目标

1. ✅ 将域名绑定到 PythonAnywhere 上的跨境工具网站
2. ✅ 配置 Git 自动部署，修改代码后自动推送到服务器

---

## 第一部分：域名绑定到 PythonAnywhere

### 步骤1：在 PythonAnywhere 添加自定义域名

1. **登录 PythonAnywhere**
   - 访问：https://www.pythonanywhere.com
   - 登录您的账户

2. **进入 Web 配置页面**
   - 点击顶部导航栏的 **"Web"**
   - 找到您的 Web 应用（`baifan7574.pythonanywhere.com`）

3. **添加自定义域名**
   - 在 Web 页面找到 **"Custom domains"** 部分
   - 点击 **"Add a new custom domain"** 或 **"Add custom domain"**
   - 输入您的域名（例如：`nbfive.com` 或 `www.nbfive.com`）
   - 点击 **"Add"**

4. **等待验证**
   - PythonAnywhere 会显示需要配置的 DNS 记录
   - 记录下显示的 IP 地址或 CNAME 值

---

### 步骤2：在 Cloudflare 配置 DNS

1. **登录 Cloudflare**
   - 访问：https://dash.cloudflare.com
   - 登录您的账户

2. **选择域名**
   - 在左侧选择您的域名（如 `nbfive.com`）

3. **进入 DNS 设置**
   - 点击 **"DNS"** 或 **"DNS 设置"**

4. **配置 DNS 记录**

   **方法A：使用 A 记录（推荐）**
   - 点击 **"Add record"** 或 **"添加记录"**
   - **类型**：选择 **A**
   - **名称**：`@`（表示根域名）或留空
   - **IPv4 地址**：输入 PythonAnywhere 提供的 IP 地址
   - **代理状态**：选择 **仅 DNS**（灰色云朵，不开启代理）
   - 点击 **"Save"**

   **方法B：添加 www 子域名**
   - 点击 **"Add record"**
   - **类型**：选择 **A**
   - **名称**：`www`
   - **IPv4 地址**：输入相同的 IP 地址
   - **代理状态**：选择 **仅 DNS**
   - 点击 **"Save"**

5. **等待 DNS 传播**
   - DNS 更改通常需要几分钟到几小时生效
   - 可以使用 `ping nbfive.com` 检查是否生效

---

### 步骤3：配置 SSL 证书

1. **PythonAnywhere 自动配置**
   - PythonAnywhere 会自动为您的自定义域名申请 SSL 证书
   - 通常需要几分钟到几小时

2. **验证 SSL**
   - 访问 `https://您的域名.com`
   - 查看浏览器地址栏的锁图标
   - 如果显示安全，说明 SSL 配置成功

---

## 第二部分：Git 自动部署配置

### 步骤1：在本地初始化 Git 仓库

1. **打开命令行（本地电脑）**
   - 进入项目目录：`d:\background_remover_tool`

2. **初始化 Git 仓库（如果还没有）**
   ```bash
   cd d:\background_remover_tool
   git init
   ```

3. **创建 .gitignore 文件**（如果还没有）
   ```bash
   # 创建 .gitignore 文件，排除不需要上传的文件
   echo "__pycache__/" > .gitignore
   echo "*.pyc" >> .gitignore
   echo ".env" >> .gitignore
   echo "data/*.json" >> .gitignore
   echo "uploads/" >> .gitignore
   ```

4. **添加文件到 Git**
   ```bash
   git add .
   git commit -m "初始提交"
   ```

---

### 步骤2：创建 GitHub 仓库

1. **登录 GitHub**
   - 访问：https://github.com
   - 登录您的账户

2. **创建新仓库**
   - 点击右上角的 **"+"** → **"New repository"**
   - **Repository name**：输入仓库名（如 `cross-border-tools`）
   - **Description**：可选，描述项目
   - **Visibility**：选择 **Private**（私有）或 **Public**（公开）
   - 不要勾选 "Initialize this repository with a README"
   - 点击 **"Create repository"**

3. **记录仓库地址**
   - 复制显示的仓库地址（如：`https://github.com/您的用户名/cross-border-tools.git`）

---

### 步骤3：连接本地仓库到 GitHub

1. **在本地添加远程仓库**
   ```bash
   cd d:\background_remover_tool
   git remote add origin https://github.com/您的用户名/cross-border-tools.git
   ```

2. **推送代码到 GitHub**
   ```bash
   git branch -M main
   git push -u origin main
   ```
   - 如果提示输入用户名和密码，使用 GitHub 的 Personal Access Token

---

### 步骤4：在 PythonAnywhere 配置 Git 自动部署

1. **打开 PythonAnywhere Console**
   - 点击顶部导航栏的 **"Consoles"**
   - 打开一个 **Bash console**

2. **进入项目目录**
   ```bash
   cd ~/background_remover_tool
   ```

3. **初始化 Git（如果还没有）**
   ```bash
   git init
   ```

4. **添加远程仓库**
   ```bash
   git remote add origin https://github.com/您的用户名/cross-border-tools.git
   ```

5. **首次拉取代码**
   ```bash
   git pull origin main
   ```

6. **创建自动部署脚本**
   ```bash
   # 创建部署脚本
   cat > ~/background_remover_tool/deploy.sh << 'EOF'
   #!/bin/bash
   cd ~/background_remover_tool
   git pull origin main
   echo "✅ 代码更新完成"
   echo "💡 请在 Web 页面点击 Reload 重新加载网站"
   EOF
   
   # 设置执行权限
   chmod +x ~/background_remover_tool/deploy.sh
   ```

---

### 步骤5：使用自动部署

#### 方法1：手动执行部署脚本（推荐）

1. **在本地修改代码**
   - 在本地电脑上修改代码
   - 测试确保没有问题

2. **提交并推送到 GitHub**
   ```bash
   cd d:\background_remover_tool
   git add .
   git commit -m "更新说明"
   git push origin main
   ```

3. **在 PythonAnywhere 执行部署**
   - 打开 PythonAnywhere Console
   - 执行：
   ```bash
   ~/background_remover_tool/deploy.sh
   ```

4. **重新加载网站**
   - 在 Web 页面点击绿色的 **"Reload"** 按钮

---

#### 方法2：使用 Git Hooks 自动部署（高级）

1. **在 PythonAnywhere 创建 Git Hook**
   ```bash
   # 进入项目目录
   cd ~/background_remover_tool
   
   # 创建 post-merge hook
   cat > .git/hooks/post-merge << 'EOF'
   #!/bin/bash
   cd ~/background_remover_tool
   echo "✅ 代码已自动更新"
   echo "💡 请在 Web 页面点击 Reload 重新加载网站"
   EOF
   
   # 设置执行权限
   chmod +x .git/hooks/post-merge
   ```

2. **使用方式**
   - 在本地推送代码到 GitHub
   - 在 PythonAnywhere Console 执行：`git pull origin main`
   - Hook 会自动执行，提醒您重新加载网站

---

## 📝 完整工作流程

### 日常更新代码流程：

1. **在本地修改代码**
   ```bash
   cd d:\background_remover_tool
   # 修改文件...
   ```

2. **提交到 Git**
   ```bash
   git add .
   git commit -m "更新说明：修复了XX问题"
   git push origin main
   ```

3. **在 PythonAnywhere 拉取更新**
   ```bash
   # 在 PythonAnywhere Console 执行
   cd ~/background_remover_tool
   git pull origin main
   ```

4. **重新加载网站**
   - 在 Web 页面点击 **"Reload"** 按钮

---

## ⚠️ 重要注意事项

### 1. 数据文件不要上传到 Git

- `data/` 目录下的 JSON 文件包含用户数据，不要上传到 Git
- 确保 `.gitignore` 包含 `data/*.json`

### 2. 环境变量文件

- `.env` 文件包含敏感信息，不要上传到 Git
- 确保 `.gitignore` 包含 `.env`

### 3. 首次部署后

- 确保 `data/` 目录存在且有写入权限
- 确保所有依赖包已安装

---

## 🔍 故障排查

### 问题1：域名无法访问

**检查 DNS 配置**：
```bash
# 在本地命令行执行
ping 您的域名.com
nslookup 您的域名.com
```

**检查 Cloudflare 设置**：
- 确保 DNS 记录类型正确
- 确保代理状态是 **仅 DNS**（灰色云朵）

### 问题2：Git 推送失败

**检查 GitHub 认证**：
- 使用 Personal Access Token 而不是密码
- 确保 Token 有正确的权限

### 问题3：代码更新后网站没变化

**检查步骤**：
1. 确认 `git pull` 成功执行
2. 确认文件已更新（`ls -la` 查看文件时间）
3. 确认点击了 **"Reload"** 按钮
4. 清除浏览器缓存后重新访问

---

## ✅ 完成检查清单

### 域名绑定
- [ ] PythonAnywhere 已添加自定义域名
- [ ] Cloudflare DNS 已配置
- [ ] 域名可以访问（HTTP）
- [ ] SSL 证书已配置（HTTPS）
- [ ] 网站通过域名正常显示

### Git 自动部署
- [ ] GitHub 仓库已创建
- [ ] 本地代码已推送到 GitHub
- [ ] PythonAnywhere 已连接 GitHub 仓库
- [ ] 部署脚本已创建
- [ ] 测试更新流程成功

---

## 🎉 完成！

现在您可以：
1. ✅ 通过自定义域名访问网站
2. ✅ 通过 Git 自动部署更新代码
3. ✅ 不再需要手动上传文件

---

**配置完成时间**：2025-11-26  
**状态**：✅ 准备配置

