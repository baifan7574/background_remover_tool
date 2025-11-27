# 🚀 Oracle Cloud 快速部署指南 - 跨境工具网站

## ✅ 您的账户状态

根据您的截图，您的 Oracle Cloud 账户已经激活！

**账户信息：**
- ✅ 租户名称：`baifan7574`
- ✅ 状态：**Active**（激活）
- ✅ 账户类型：**免费等级账户（Free Tier account）**
- ✅ 区域：新加坡（SIN）

**这意味着：**
- ✅ 您的账户已经可以使用
- ✅ 可以创建免费资源（2 个实例 + 2 个数据库）
- ✅ 可以开始部署您的网站了！

---

## 📋 重要说明

### 截图显示的是什么？

**您看到的页面是：**
- ✅ **租户详情页面**（Tenancy details）
- ✅ 显示您的账户信息
- ✅ 证明账户已激活

**但还需要：**
- ⚠️ **创建计算实例**（虚拟服务器）
- ⚠️ **创建数据库**
- ⚠️ **部署网站代码**

**简单说：** 您有了账户，但还需要创建服务器和数据库！

---

## 🎯 您的需求

### 1. 部署跨境工具网站

**可以！** ✅

**Oracle Cloud 免费版可以：**
- ✅ 创建 2 个实例（虚拟服务器）
- ✅ 创建 2 个数据库
- ✅ 部署您的跨境工具网站
- ✅ 绑定自定义域名

---

### 2. 以后挂其他网站

**可以！** ✅

**Oracle Cloud 免费版可以：**
- ✅ 在一个实例上托管多个网站（使用 Nginx 虚拟主机）
- ✅ 2 个实例可以托管 **6-10 个网站**
- ✅ 完全够用！

---

### 3. 替代其他服务器和数据库

**可以！** ✅

**Oracle Cloud 免费版可以替代：**
- ✅ PythonAnywhere（服务器）
- ✅ Supabase（数据库）
- ✅ Render（服务器）
- ✅ 其他云服务商

**优势：**
- ✅ 完全免费
- ✅ 服务器 + 数据库都有
- ✅ 功能更强大
- ✅ 一个平台解决所有问题

---

## 🚀 下一步操作步骤

### 第1步：创建计算实例（虚拟服务器）

1. **登录 Oracle Cloud**
   - 访问：https://cloud.oracle.com
   - 登录您的账户

2. **进入计算服务**
   - 点击左侧菜单 "Compute"（计算）
   - 点击 "Instances"（实例）

3. **创建实例**
   - 点击 "Create instance"（创建实例）按钮
   - 配置实例：
     - **Name（名称）**：输入 `cross-border-tool` 或您喜欢的名称
     - **Image（镜像）**：选择 Ubuntu 22.04 或 Oracle Linux
     - **Shape（形状）**：选择 "Always Free eligible"（始终免费）
       - 选择 "VM.Standard.A1.Flex"（Arm 架构）
       - 或 "VM.Standard.E2.1.Micro"（AMD 架构）
     - **Networking（网络）**：使用默认 VCN
     - **SSH keys（SSH 密钥）**：上传您的 SSH 公钥（用于远程连接）

4. **创建**
   - 点击 "Create"（创建）按钮
   - 等待 2-5 分钟，实例创建完成

**完成后，您就有了 1 台虚拟服务器！**

---

### 第2步：创建数据库

1. **进入数据库服务**
   - 点击左侧菜单 "Oracle Database" → "Autonomous Database"
   - 或直接搜索 "Autonomous Database"

2. **创建数据库**
   - 点击 "Create Autonomous Database"（创建自治数据库）
   - 配置数据库：
     - **Compartment（区间）**：选择 `baifan7574 (root)`
     - **Display name（显示名称）**：输入 `cross-border-tool-db`
     - **Database type（数据库类型）**：选择 "Transaction Processing"（事务处理）
     - **Deployment type（部署类型）**：选择 "Shared Infrastructure"（共享基础设施）
     - **Always Free（始终免费）**：✅ 勾选此选项
     - **Database name（数据库名称）**：输入 `CROSSBORDERTOOL`
     - **Password（密码）**：设置管理员密码

3. **创建**
   - 点击 "Create Autonomous Database"（创建自治数据库）
   - 等待 5-10 分钟，数据库创建完成

**完成后，您就有了 1 个数据库！**

---

### 第3步：部署跨境工具网站

#### 3.1 连接到服务器

1. **获取实例的公网 IP**
   - 在 "Instances" 页面，找到您创建的实例
   - 复制 "Public IP address"（公网 IP 地址）

2. **SSH 连接到服务器**
   ```bash
   ssh opc@您的公网IP地址
   ```
   - 使用您上传的 SSH 私钥连接

---

#### 3.2 安装必要软件

**在服务器上执行：**

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Nginx（Web 服务器）
sudo apt install nginx -y

# 安装 Python 和 pip
sudo apt install python3 python3-pip -y

# 安装其他依赖
sudo apt install git -y
```

---

#### 3.3 部署网站代码

**方法1：使用 Git 部署**

```bash
# 创建项目目录
mkdir -p /var/www/cross-border-tool
cd /var/www/cross-border-tool

# 克隆您的代码（如果有 GitHub 仓库）
git clone https://github.com/您的用户名/您的仓库.git .

# 或直接上传代码文件
```

**方法2：上传代码文件**

1. 使用 SFTP 工具（如 FileZilla）上传代码
2. 或使用 `scp` 命令上传

---

#### 3.4 配置 Nginx

**创建 Nginx 配置文件：**

```bash
sudo nano /etc/nginx/sites-available/cross-border-tool
```

**配置文件内容：**

```nginx
server {
    listen 80;
    server_name 您的域名.com www.您的域名.com;

    location / {
        proxy_pass http://127.0.0.1:5000;  # 您的应用端口
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 静态文件
    location /static {
        alias /var/www/cross-border-tool/static;
    }
}
```

**启用配置：**

```bash
sudo ln -s /etc/nginx/sites-available/cross-border-tool /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl restart nginx  # 重启 Nginx
```

---

#### 3.5 配置数据库连接

**在您的应用代码中配置数据库连接：**

```python
# 使用 Oracle Cloud Autonomous Database
import cx_Oracle

# 数据库连接信息（从 Oracle Cloud 控制台获取）
db_user = "admin"
db_password = "您的密码"
db_service_name = "您的数据库服务名"
db_host = "您的数据库连接字符串"

# 连接数据库
connection = cx_Oracle.connect(
    user=db_user,
    password=db_password,
    dsn=f"{db_host}/{db_service_name}"
)
```

**获取数据库连接信息：**
1. 在 Oracle Cloud 控制台，进入您的数据库
2. 点击 "DB Connection"（数据库连接）
3. 复制连接字符串

---

#### 3.6 运行应用

**使用 systemd 创建服务：**

```bash
sudo nano /etc/systemd/system/cross-border-tool.service
```

**服务文件内容：**

```ini
[Unit]
Description=Cross Border Tool
After=network.target

[Service]
User=opc
WorkingDirectory=/var/www/cross-border-tool
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /var/www/cross-border-tool/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**启动服务：**

```bash
sudo systemctl daemon-reload
sudo systemctl enable cross-border-tool
sudo systemctl start cross-border-tool
sudo systemctl status cross-border-tool  # 查看状态
```

---

### 第4步：配置域名

1. **在 Oracle Cloud 配置安全组**
   - 进入 "Networking" → "Security Lists"
   - 添加入站规则：允许 HTTP (80) 和 HTTPS (443)

2. **在域名服务商配置 DNS**
   - 登录您的域名服务商（如 Cloudflare）
   - 添加 A 记录：
     - **名称**：`@` 或 `www`
     - **值**：您的实例公网 IP 地址
     - **TTL**：自动

3. **配置 SSL 证书（HTTPS）**
   ```bash
   # 安装 Certbot
   sudo apt install certbot python3-certbot-nginx -y
   
   # 获取 SSL 证书
   sudo certbot --nginx -d 您的域名.com -d www.您的域名.com
   ```

---

## 📊 资源使用情况

### Oracle Cloud 免费版资源

**您可以使用：**
- ✅ **2 个计算实例**（虚拟服务器）
  - 当前使用：1 个（跨境工具网站）
  - 剩余：1 个（可以部署其他网站）

- ✅ **2 个数据库**
  - 当前使用：1 个（跨境工具网站）
  - 剩余：1 个（可以用于其他网站）

- ✅ **10 TB 对象存储/月**
- ✅ **10 TB 网络流量/月**

---

## 💡 部署多个网站

### 方案1：一个实例托管多个网站（推荐）

**使用 Nginx 虚拟主机：**

```bash
# 为每个网站创建配置文件
sudo nano /etc/nginx/sites-available/website1
sudo nano /etc/nginx/sites-available/website2
sudo nano /etc/nginx/sites-available/website3

# 启用配置
sudo ln -s /etc/nginx/sites-available/website1 /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/website2 /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/website3 /etc/nginx/sites-enabled/

# 重启 Nginx
sudo systemctl restart nginx
```

**可以托管：**
- ✅ **5-8 个小型网站**
- ✅ **3-5 个中型网站**

---

### 方案2：使用两个实例

**配置：**
- ✅ 实例1：托管 5 个网站
- ✅ 实例2：托管 5 个网站

**可以托管：**
- ✅ **10 个网站**

---

## ⚠️ 重要提醒

### 1. 免费试用期

**根据您的截图：**
- ⚠️ 您目前处于**免费试用期**
- ⚠️ 试用期结束后，账户将仅限于使用**永久免费资源（Always Free）**

**永久免费资源包括：**
- ✅ 2 个计算实例（Always Free）
- ✅ 2 个数据库（Always Free）
- ✅ 10 TB 对象存储/月
- ✅ 10 TB 网络流量/月

**这些资源是永久免费的，不会过期！** ✅

---

### 2. 停止使用其他服务

**可以停止使用：**
- ✅ PythonAnywhere（服务器）
- ✅ Supabase（数据库）
- ✅ Render（服务器）
- ✅ 其他云服务商

**Oracle Cloud 免费版可以替代它们！**

---

### 3. 数据迁移

**如果之前使用其他服务：**

1. **从 PythonAnywhere 迁移：**
   - 下载代码文件
   - 上传到 Oracle Cloud 实例

2. **从 Supabase 迁移：**
   - 导出数据库数据
   - 导入到 Oracle Cloud 数据库

---

## 🎯 总结

### 回答您的问题：

1. **这张截图是否证明已经有了云服务器？**
   - ✅ **部分正确**
   - ✅ 截图证明您的账户已激活
   - ⚠️ 但还需要创建计算实例（虚拟服务器）

2. **是否可以把跨境工具网站挂到上面？**
   - ✅ **可以！** 完全支持

3. **以后也可以挂别的网站？**
   - ✅ **可以！** 2 个实例可以托管 6-10 个网站

4. **是否可以用 Oracle Cloud 替代其他服务器和数据库？**
   - ✅ **可以！** Oracle Cloud 免费版可以替代：
     - PythonAnywhere（服务器）
     - Supabase（数据库）
     - Render（服务器）
     - 其他云服务商

---

## 💡 最终建议

### 对于您的项目：

✅ **强烈推荐使用 Oracle Cloud 免费版！**

**优势：**
- ✅ 完全免费
- ✅ 服务器 + 数据库都有
- ✅ 可以部署跨境工具网站
- ✅ 可以部署其他网站（6-10 个）
- ✅ 一个平台解决所有问题
- ✅ 可以替代其他服务

**总成本：** **¥0/月** 🎉

**下一步：**
1. 创建计算实例（虚拟服务器）
2. 创建数据库
3. 部署跨境工具网站
4. 配置域名

---

**最后更新：** 2025年1月
**状态：** ✅ 账户已激活，可以开始部署！

