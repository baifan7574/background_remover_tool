# 🌐 PythonAnywhere 自定义域名配置说明

## ⚠️ 重要发现

**PythonAnywhere 免费账户不支持自定义域名！**

- ❌ 免费账户：只能使用 `用户名.pythonanywhere.com`
- ✅ 付费账户：可以绑定自定义域名

---

## 💰 升级账户方案

### PythonAnywhere 付费计划

1. **Hacker 计划** - $5/月
   - ✅ 支持自定义域名
   - ✅ 3GB 存储空间
   - ✅ 可以安装更多依赖包（如 rembg）

2. **Web Developer 计划** - $12/月
   - ✅ 支持自定义域名
   - ✅ 更多资源

### 升级步骤

1. **登录 PythonAnywhere**
   - 访问：https://www.pythonanywhere.com
   - 登录您的账户

2. **进入 Account 页面**
   - 点击顶部导航栏的 **"Account"**

3. **选择付费计划**
   - 选择 **Hacker** 或 **Web Developer** 计划
   - 完成支付

4. **添加自定义域名**
   - 升级后，进入 **"Web"** 页面
   - 找到 **"Custom domains"** 部分
   - 点击 **"Add a new custom domain"**
   - 输入您的域名（如 `nbfive.com`）
   - 点击 **"Add"**

5. **配置 DNS**
   - 在 Cloudflare 配置 DNS 记录
   - 指向 PythonAnywhere 提供的 IP 地址

---

## 🎯 替代方案（不升级账户）

### 方案A：使用 Cloudflare Workers（需要重写代码）

**说明：**
- Cloudflare Workers 支持 Python（但有限制）
- 需要将 Flask 应用改为 Workers 格式
- 工作量大，需要重写代码

**不推荐**，因为需要大量修改代码。

---

### 方案B：使用反向代理（Cloudflare Workers Proxy）

**说明：**
- 使用 Cloudflare Workers 作为反向代理
- 将请求转发到 `baifan7574.pythonanywhere.com`
- 用户访问的是您的域名，但实际运行在 PythonAnywhere

**步骤：**

1. **在 Cloudflare Workers 创建代理脚本**
   ```javascript
   addEventListener('fetch', event => {
     event.respondWith(handleRequest(event.request))
   })

   async function handleRequest(request) {
     const url = new URL(request.url)
     url.hostname = 'baifan7574.pythonanywhere.com'
     
     const modifiedRequest = new Request(url, {
       method: request.method,
       headers: request.headers,
       body: request.body
     })
     
     return fetch(modifiedRequest)
   }
   ```

2. **在 Cloudflare Pages 部署**
   - 创建新的 Worker
   - 部署上述代码
   - 绑定您的域名

**优点：**
- ✅ 不需要升级 PythonAnywhere 账户
- ✅ 可以使用自定义域名
- ✅ 配置相对简单

**缺点：**
- ⚠️ 需要配置 Cloudflare Workers
- ⚠️ 可能有一些限制

---

### 方案C：使用子域名重定向（简单但不完美）

**说明：**
- 在 Cloudflare 配置页面规则
- 将 `nbfive.com` 重定向到 `baifan7574.pythonanywhere.com`

**步骤：**

1. **在 Cloudflare 配置页面规则**
   - 进入 **"Rules"** → **"Page Rules"**
   - 创建规则：
     - URL：`*nbfive.com/*`
     - 设置：**Forwarding URL** → `https://baifan7574.pythonanywhere.com/$1`

**缺点：**
- ❌ URL 会显示 PythonAnywhere 的地址
- ❌ 不是真正的域名绑定

---

## 🎯 推荐方案对比

| 方案 | 成本 | 难度 | 效果 | 推荐度 |
|------|------|------|------|--------|
| 升级 PythonAnywhere | $5/月 | ⭐ 简单 | ⭐⭐⭐⭐⭐ 完美 | ⭐⭐⭐⭐⭐ |
| Cloudflare Workers 代理 | 免费 | ⭐⭐ 中等 | ⭐⭐⭐⭐ 良好 | ⭐⭐⭐⭐ |
| 子域名重定向 | 免费 | ⭐ 简单 | ⭐⭐ 一般 | ⭐⭐ |

---

## 💡 我的建议

### 如果预算允许：
**推荐：升级到 PythonAnywhere Hacker 计划（$5/月）**
- ✅ 最简单、最稳定
- ✅ 支持自定义域名
- ✅ 有更多存储空间（可以安装 rembg）
- ✅ 官方支持，不会出问题

### 如果不想付费：
**推荐：使用 Cloudflare Workers 反向代理**
- ✅ 免费
- ✅ 可以使用自定义域名
- ⚠️ 需要配置 Workers

---

## 📋 下一步操作

### 如果您选择升级账户：

1. **升级 PythonAnywhere 账户**
   - 访问：https://www.pythonanywhere.com/account/
   - 选择 Hacker 计划（$5/月）
   - 完成支付

2. **添加自定义域名**
   - 进入 Web 页面
   - 找到 "Custom domains" 部分
   - 添加您的域名

3. **配置 DNS**
   - 在 Cloudflare 配置 DNS 记录
   - 指向 PythonAnywhere 提供的 IP

---

### 如果您选择 Cloudflare Workers 代理：

告诉我，我会为您创建详细的配置步骤。

---

## ❓ 您想选择哪个方案？

1. **升级 PythonAnywhere 账户**（$5/月，推荐）
2. **使用 Cloudflare Workers 代理**（免费，需要配置）
3. **暂时不绑定域名**（继续使用 `baifan7574.pythonanywhere.com`）

告诉我您的选择，我会提供详细的配置步骤！

---

**更新时间**：2025-11-26  
**状态**：等待用户选择方案

