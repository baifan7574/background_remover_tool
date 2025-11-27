# 🚀 PythonAnywhere 部署完整指南

**适用场景**: 将本地完成的网站上传到 PythonAnywhere 服务器

---

## 📋 重要说明

### ⚠️ 当前版本使用本地 JSON 文件存储

**重要**: 您当前完成的版本（`sk_app.py`）使用的是**本地 JSON 文件存储**，**不需要 Supabase 数据库**。

这意味着：
- ✅ **不需要**修改 Supabase 数据库
- ✅ **不需要**配置数据库连接
- ✅ 数据存储在服务器上的 `data/` 目录中

---

## 🎯 部署步骤

### 步骤1: 准备上传的文件

**需要上传的核心文件**:

```
background_remover_tool/
├── sk_app.py              # ⭐ 主应用文件（最重要）
├── data_manager.py        # ⭐ 数据管理器（必须）
├── requirements.txt       # ⭐ 依赖包列表（必须）
├── frontend/              # ⭐ 前端文件（必须）
│   ├── index.html
│   ├── payment.html
│   ├── admin_login.html
│   ├── admin_orders.html
│   ├── payment.js
│   ├── js/
│   │   ├── app.js
│   │   └── auth.js
│   ├── css/
│   │   └── style.css
│   └── images/            # ⚠️ 收款码图片
│       ├── alipay_qrcode.png
│       └── wechat_qrcode.png
└── data/                  # ⚠️ 数据目录（会自动创建，但可以上传空目录）
```

---

### 步骤2: 登录 PythonAnywhere

1. 访问 [www.pythonanywhere.com](https://www.pythonanywhere.com)
2. 使用您的账号登录（baifan7574）
3. 进入 Dashboard

---

### 步骤3: 上传文件到 PythonAnywhere

#### 方法一：使用 Files 页面上传（推荐新手）

1. **打开 Files 页面**
   - 点击顶部导航栏的 **"Files"**
   - 进入 `/home/baifan7574/` 目录

2. **创建项目目录**（如果还没有）
   - 点击 **"New directory"**
   - 输入目录名：`background_remover_tool`
   - 点击 **"Create"**

3. **进入项目目录**
   - 点击 `background_remover_tool` 进入

4. **上传文件**
   - 点击 **"Upload a file"**
   - 选择要上传的文件，依次上传：
     - `sk_app.py`
     - `data_manager.py`
     - `requirements.txt`
   - 上传完成后，创建 `frontend` 目录并上传前端文件

#### 方法二：使用 Git（推荐，更快）

如果您使用 Git，可以在 Console 中执行：

```bash
# 1. 打开 Console（点击 "Consoles" → "Bash console"）

# 2. 进入主目录
cd ~

# 3. 如果已有项目目录，先删除（可选）
# rm -rf background_remover_tool

# 4. 克隆或创建项目目录
mkdir -p background_remover_tool
cd background_remover_tool

# 5. 如果您使用 Git，可以：
# git clone https://您的仓库地址.git .

# 或者直接上传文件（见方法一）
```

---

### 步骤4: 安装依赖包

1. **打开 Console**
   - 点击顶部导航栏的 **"Consoles"**
   - 点击 **"Bash console"** 或 **"Start a new console"** → **"Bash"**

2. **进入项目目录**
   ```bash
   cd ~/background_remover_tool
   ```

3. **安装依赖**
   ```bash
   pip3.10 install --user -r requirements.txt
   ```
   
   **注意**: PythonAnywhere 使用 Python 3.10，所以用 `pip3.10`

4. **如果安装失败，可以逐个安装**
   ```bash
   pip3.10 install --user Flask==2.3.3
   pip3.10 install --user flask-cors==4.0.0
   pip3.10 install --user Pillow==10.0.1
   pip3.10 install --user rembg==2.0.67
   pip3.10 install --user numpy==1.24.3
   pip3.10 install --user opencv-python==4.8.1.78
   pip3.10 install --user python-dotenv==1.0.0
   pip3.10 install --user groq==0.4.1
   pip3.10 install --user pytrends==4.9.2
   pip3.10 install --user requests==2.31.0
   ```

---

### 步骤5: 创建数据目录

在 Console 中执行：

```bash
cd ~/background_remover_tool
mkdir -p data
chmod 755 data
```

---

### 步骤6: 配置 Web App

1. **打开 Web 页面**
   - 点击顶部导航栏的 **"Web"**

2. **如果已有 Web App，点击 "Reload"**
   - 如果还没有，点击 **"Add a new web app"**

3. **配置 Web App**
   - **Python version**: 选择 **Python 3.10**
   - **Flask**: 选择 **Flask**
   - **Python path**: `/home/baifan7574/background_remover_tool`
   - **Working directory**: `/home/baifan7574/background_remover_tool`
   - **Source code**: `/home/baifan7574/background_remover_tool`
   - **WSGI configuration file**: 点击链接编辑

4. **编辑 WSGI 配置文件**
   
   找到类似这样的内容：
   ```python
   import sys
   path = '/home/baifan7574/background_remover_tool'
   if path not in sys.path:
       sys.path.append(path)
   
   from flask_app import app as application
   ```
   
   **修改为**：
   ```python
   import sys
   path = '/home/baifan7574/background_remover_tool'
   if path not in sys.path:
       sys.path.append(path)
   
   from sk_app import app as application
   ```
   
   **保存**（点击右上角的绿色按钮）

5. **配置静态文件**
   - 在 Web 页面找到 **"Static files"** 部分
   - 点击 **"Add a new static files mapping"**
   - **URL**: `/static/`
   - **Directory**: `/home/baifan7574/background_remover_tool/frontend/`
   - 点击 **"Add"**

6. **配置静态文件（CSS/JS）**
   - 再次点击 **"Add a new static files mapping"**
   - **URL**: `/css/`
   - **Directory**: `/home/baifan7574/background_remover_tool/frontend/css/`
   - 点击 **"Add"**
   
   - 再次点击 **"Add a new static files mapping"**
   - **URL**: `/js/`
   - **Directory**: `/home/baifan7574/background_remover_tool/frontend/js/`
   - 点击 **"Add"**
   
   - 再次点击 **"Add a new static files mapping"**
   - **URL**: `/images/`
   - **Directory**: `/home/baifan7574/background_remover_tool/frontend/images/`
   - 点击 **"Add"**

---

### 步骤7: 修改代码（生产环境）

1. **打开 `sk_app.py` 文件**
   - 在 Files 页面找到 `sk_app.py`
   - 点击打开

2. **找到最后几行**（大约第 4700 行）
   ```python
   if __name__ == '__main__':
       app.run(debug=True, host='0.0.0.0', port=5000)
   ```

3. **修改为**（生产环境）:
   ```python
   if __name__ == '__main__':
       # 生产环境：关闭调试模式
       app.run(debug=False, host='0.0.0.0', port=5000)
   ```

   **注意**: PythonAnywhere 使用 WSGI，所以这行代码实际上不会执行，但为了安全还是修改一下。

---

### 步骤8: 配置环境变量（可选）

如果需要修改配置（如管理员密码、邮箱等），可以：

1. **在项目目录创建 `.env` 文件**
   - 在 Files 页面，进入项目目录
   - 点击 **"New file"**
   - 文件名：`.env`

2. **添加配置**（可选）
   ```
   EMAIL_SENDER=825146419@qq.com
   EMAIL_PASSWORD=qzgpgjnwpyudbdib
   ADMIN_EMAIL=825146419@qq.com
   EMAIL_ENABLED=true
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=您的强密码
   ```

---

### 步骤9: 重启 Web App

1. **返回 Web 页面**
   - 点击顶部导航栏的 **"Web"**

2. **点击绿色的 "Reload" 按钮**
   - 等待几秒钟，直到显示 "Reloading..."

3. **检查状态**
   - 如果显示绿色勾号 ✅，说明启动成功
   - 如果显示红色 ❌，点击查看错误日志

---

### 步骤10: 测试网站

1. **访问您的网站**
   - 在 Web 页面找到您的网站地址
   - 通常是：`https://baifan7574.pythonanywhere.com`
   - 点击打开

2. **测试功能**
   - 访问首页
   - 测试用户注册/登录
   - 测试工具使用
   - 测试支付流程
   - 测试后台管理

---

## ⚠️ 常见问题

### 1. 导入错误

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
# 在 Console 中执行
pip3.10 install --user 模块名
```

---

### 2. 静态文件无法加载

**错误**: CSS/JS/图片无法显示

**解决**:
- 检查 Web 页面的静态文件配置
- 确保 URL 和目录路径正确
- 确保文件已上传到正确位置

---

### 3. 数据目录权限错误

**错误**: `Permission denied` 或无法写入数据

**解决**:
```bash
# 在 Console 中执行
cd ~/background_remover_tool
chmod 755 data
chmod 644 data/*.json  # 如果已有文件
```

---

### 4. 网站无法访问

**错误**: 500 Internal Server Error

**解决**:
1. 在 Web 页面点击 **"Error log"** 查看错误
2. 检查 WSGI 配置文件是否正确
3. 检查代码是否有语法错误
4. 检查依赖是否安装完整

---

## 📋 部署检查清单

### 上传文件 ✅
- [ ] `sk_app.py` 已上传
- [ ] `data_manager.py` 已上传
- [ ] `requirements.txt` 已上传
- [ ] `frontend/` 目录及所有文件已上传
- [ ] 收款码图片已上传

### 配置 ✅
- [ ] 依赖包已安装
- [ ] `data/` 目录已创建
- [ ] WSGI 配置文件已修改
- [ ] 静态文件映射已配置
- [ ] 代码已修改（debug=False）

### 测试 ✅
- [ ] 网站可以访问
- [ ] 首页正常显示
- [ ] 用户注册/登录正常
- [ ] 工具使用正常
- [ ] 支付流程正常
- [ ] 后台管理正常

---

## 🎯 关于数据库

### ❓ 还需要 Supabase 吗？

**答案**: **不需要**

**原因**:
- 当前版本（`sk_app.py`）使用本地 JSON 文件存储
- 数据存储在服务器上的 `data/` 目录中
- 不需要数据库连接

**如果您之前使用过 Supabase**:
- Supabase 数据库可以保留（不影响）
- 但当前版本不会使用它
- 所有数据都在 `data/` 目录的 JSON 文件中

---

## 🚀 快速部署命令（参考）

```bash
# 1. 进入项目目录
cd ~/background_remover_tool

# 2. 安装依赖
pip3.10 install --user -r requirements.txt

# 3. 创建数据目录
mkdir -p data && chmod 755 data

# 4. 检查文件
ls -la
ls -la frontend/
ls -la data/
```

---

## 📞 需要帮助？

如果遇到问题：
1. 查看 Web 页面的 **"Error log"**
2. 查看 Console 中的错误信息
3. 检查文件是否上传完整
4. 检查路径配置是否正确

---

**部署完成时间**: 2025-11-25  
**状态**: ✅ 准备部署

