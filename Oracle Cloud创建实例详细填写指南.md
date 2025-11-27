# 📝 Oracle Cloud 创建实例详细填写指南

## 🎯 您当前的位置

根据您的截图，您正在创建计算实例的第1步："Basic information"（基本信息）

**当前状态：**
- ✅ 已选择 Image（镜像）：Oracle Linux 9
- ✅ 已选择 Shape（形状）：VM.Standard.E2.1.Micro（Always Free-eligible）
- ⚠️ 需要填写其他基本信息

---

## 📋 详细填写步骤

### 第1步：Basic information（基本信息）

#### 1. Name（名称）

**填写：**
```
cross-border-tool
```
或
```
website-server-1
```

**说明：**
- ✅ 可以自定义，用于识别这个实例
- ✅ 建议使用有意义的名称
- ✅ 只能包含字母、数字、连字符

---

#### 2. Create in compartment（创建在区间）

**填写：**
```
baifan7574 (root)
```

**说明：**
- ✅ 默认选择您的根区间即可
- ✅ 不需要修改

---

#### 3. Placement（放置）

**填写：**
- ✅ **Availability domain（可用性域）**：选择任意一个（如 AD-1）
- ✅ **Fault domain（容错域）**：选择 "Let Oracle choose"（让 Oracle 选择）

**说明：**
- ✅ 免费版不需要特别配置
- ✅ 使用默认选项即可

---

#### 4. Image（镜像）- 您已选择 ✅

**当前选择：**
- ✅ **Operating system**：Oracle Linux 9
- ✅ **Image build**：2025.10.23-0
- ✅ **Security**：Shielded instance

**说明：**
- ✅ Oracle Linux 9 是很好的选择
- ✅ 如果您熟悉 Ubuntu，可以点击 "Change image" 改为 Ubuntu 22.04

**如果要改为 Ubuntu：**
1. 点击 "Change image" 按钮
2. 选择 "Canonical Ubuntu"
3. 选择 "Ubuntu 22.04"
4. 点击 "Select image"

---

#### 5. Shape（形状）- 您已选择 ✅

**当前选择：**
- ✅ **Shape**：VM.Standard.E2.1.Micro
- ✅ **标签**：Always Free-eligible（始终免费）
- ✅ **配置**：1 core OCPU, 1 GB memory, 0.48 Gbps network bandwidth

**说明：**
- ✅ 这是免费版的标准配置
- ✅ 完全够用，不需要修改

---

### 第2步：Security（安全）- 点击 "Next" 后进入

#### 1. Configure SSH keys（配置 SSH 密钥）- 最重要！

**⚠️ 这个选项可能在页面上方，请仔细查找！**

**选项1：Generate a key pair for me（为我生成密钥对）- 推荐新手 ⭐⭐⭐⭐⭐**

**操作：**
- ✅ 选择 "Generate a key pair for me"
- ✅ 点击 "Save private key" 下载私钥文件
- ⚠️ **重要：保存好私钥文件，以后连接服务器需要用到！**

**说明：**
- ✅ 最简单的方式
- ✅ Oracle 会自动生成密钥对
- ✅ 下载私钥文件保存到本地

---

**选项2：Paste SSH keys（粘贴 SSH 密钥）- 推荐有经验的用户**

**操作：**
1. 如果您已经有 SSH 密钥：
   - 打开您的公钥文件（通常是 `~/.ssh/id_rsa.pub`）
   - 复制公钥内容
   - 粘贴到 "SSH keys" 文本框中

2. 如果您没有 SSH 密钥，需要生成：
   ```bash
   # Windows (使用 Git Bash 或 PowerShell)
   ssh-keygen -t rsa -b 2048
   
   # 然后查看公钥
   cat ~/.ssh/id_rsa.pub
   ```
   - 复制公钥内容
   - 粘贴到 "SSH keys" 文本框中

**说明：**
- ✅ 更灵活的方式
- ✅ 可以使用您现有的密钥

---

#### 2. Shielded instance（屏蔽实例）

**填写：**
- ❌ **保持关闭（Off）** - 推荐

**说明：**
- ⚠️ Shielded instance 是高级安全功能
- ⚠️ 对于小型网站，不需要开启
- ✅ 保持关闭即可，不影响使用

---

#### 3. Advanced options（高级选项）

**Security attributes（安全属性）：**
- ❌ **不需要填写** - 保持空白

**说明：**
- ⚠️ 这是用于 ZPR 服务的，普通用户不需要
- ✅ 保持默认即可

---

#### 4. Boot volume（启动卷）

**填写：**
- ✅ **Use default boot volume settings**（使用默认启动卷设置）
- ✅ 不需要修改

**说明：**
- ✅ 免费版默认 50GB 存储空间
- ✅ 完全够用

---

### 第3步：Networking（网络）- 点击 "Next" 后进入

#### 1. Network（网络）

**填写：**
- ✅ **Create new virtual cloud network**（创建新的虚拟云网络）
   - 或
- ✅ **Select existing virtual cloud network**（选择现有虚拟云网络）

**推荐：**
- ✅ 如果是第一次创建，选择 "Create new virtual cloud network"
- ✅ Oracle 会自动创建 VCN 和子网

---

#### 2. Public IP address（公网 IP 地址）

**填写：**
- ✅ **Assign a public IPv4 address**（分配公网 IPv4 地址）
- ✅ **必须勾选！** 这样才能从外网访问您的服务器

**说明：**
- ✅ 免费版可以分配公网 IP
- ✅ 这是访问服务器的必需项

---

#### 3. Network security group（网络安全组）

**填写：**
- ✅ **Create new network security group**（创建新的网络安全组）
- ✅ 或使用默认设置

**说明：**
- ✅ 用于配置防火墙规则
- ✅ 创建后可以配置允许 HTTP (80) 和 HTTPS (443) 端口

---

### 第4步：Review（审查）- 最后一步

#### 检查所有配置

**确认：**
- ✅ Name（名称）：正确
- ✅ Image（镜像）：Oracle Linux 9
- ✅ Shape（形状）：VM.Standard.E2.1.Micro（Always Free）
- ✅ SSH keys（SSH 密钥）：已配置
- ✅ Public IP（公网 IP）：已分配
- ✅ Network（网络）：已配置

**如果都正确：**
- ✅ 点击 "Create"（创建）按钮
- ✅ 等待 2-5 分钟，实例创建完成

---

## 🎯 快速填写清单

### 必填项：

1. ✅ **Name（名称）**：`cross-border-tool`
2. ✅ **Image（镜像）**：Oracle Linux 9（已选择）
3. ✅ **Shape（形状）**：VM.Standard.E2.1.Micro（已选择）
4. ✅ **SSH keys（SSH 密钥）**：选择 "Generate a key pair for me" 或粘贴您的公钥
5. ✅ **Public IP（公网 IP）**：必须勾选 "Assign a public IPv4 address"
6. ✅ **Network（网络）**：选择 "Create new virtual cloud network"

---

## 💡 推荐配置（最简单）

### 对于新手：

1. **Name（名称）**：
   ```
   cross-border-tool
   ```

2. **Image（镜像）**：
   - ✅ 保持 Oracle Linux 9（或改为 Ubuntu 22.04）

3. **Shape（形状）**：
   - ✅ 保持 VM.Standard.E2.1.Micro（Always Free）

4. **SSH keys（SSH 密钥）**：
   - ✅ 选择 "Generate a key pair for me"
   - ✅ 点击 "Save private key" 下载私钥

5. **Network（网络）**：
   - ✅ 选择 "Create new virtual cloud network"
   - ✅ 勾选 "Assign a public IPv4 address"

6. **点击 "Next" → "Next" → "Create"**

---

## ⚠️ 重要提醒

### 1. SSH 密钥

**如果选择 "Generate a key pair for me"：**
- ⚠️ **必须下载私钥文件！**
- ⚠️ 私钥文件用于连接服务器
- ⚠️ 丢失后无法恢复，需要重新创建实例

**保存位置建议：**
- ✅ Windows：`C:\Users\您的用户名\.ssh\oracle_key.pem`
- ✅ 设置文件权限（Windows 可能不需要）

---

### 2. 公网 IP 地址

**必须勾选：**
- ✅ "Assign a public IPv4 address"
- ✅ 否则无法从外网访问服务器

---

### 3. 免费版限制

**确认：**
- ✅ Shape 显示 "Always Free-eligible"
- ✅ 这样才是免费的
- ⚠️ 如果选择其他形状，可能会收费

---

## 📝 完整填写示例

### 第1步：Basic information

```
Name: cross-border-tool
Create in compartment: baifan7574 (root)
Placement:
  - Availability domain: AD-1
  - Fault domain: Let Oracle choose
Image: Oracle Linux 9 (已选择)
Shape: VM.Standard.E2.1.Micro (Always Free-eligible) (已选择)
```

**点击 "Next"**

---

### 第2步：Security

```
Configure SSH keys:
  - 选择 "Generate a key pair for me"
  - 点击 "Save private key" 下载私钥

Boot volume:
  - Use default boot volume settings
```

**点击 "Next"**

---

### 第3步：Networking

```
Network:
  - Create new virtual cloud network
  - VCN name: vcn-20250101 (自动生成)
  - Subnet name: subnet-20250101 (自动生成)

Public IP address:
  - ✅ Assign a public IPv4 address (必须勾选)

Network security group:
  - Create new network security group
```

**点击 "Next"**

---

### 第4步：Review

```
检查所有配置是否正确
点击 "Create" 创建实例
```

**等待 2-5 分钟，实例创建完成！**

---

## 🎉 创建完成后

### 您会得到：

1. ✅ **实例已创建**
2. ✅ **公网 IP 地址**（在实例详情页面查看）
3. ✅ **SSH 私钥文件**（如果选择了自动生成）

### 下一步：

1. **查看实例详情**
   - 在 "Instances" 页面找到您的实例
   - 复制 "Public IP address"（公网 IP 地址）

2. **连接服务器**
   ```bash
   # 使用下载的私钥连接
   ssh -i 私钥文件路径 opc@公网IP地址
   ```

3. **开始部署网站**
   - 安装 Nginx、Python 等
   - 上传代码
   - 配置数据库

---

## 📚 相关文档

- 详细部署指南：`Oracle Cloud快速部署指南-跨境工具网站.md`
- 通俗易懂说明：`Oracle Cloud通俗易懂说明.md`

---

**最后更新：** 2025年1月
**状态：** ✅ 填写指南已准备就绪

