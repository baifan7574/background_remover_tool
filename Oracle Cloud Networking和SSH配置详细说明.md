# 📝 Oracle Cloud Networking 和 SSH 配置详细说明

## 🎯 您当前的位置

根据您的截图，您需要配置两个部分：
1. **SSH keys（SSH 密钥）** - 已找到 ✅
2. **Networking（网络）** - 需要配置

---

## 🔑 第1部分：SSH keys（SSH 密钥）配置

### 根据您的截图，您已经看到了 "Add SSH keys" 页面

#### 配置步骤：

**1. 选择 SSH 密钥选项**

**推荐选择：**
- ✅ **"Generate a key pair for me"**（为我生成密钥对）
- ✅ 这个选项已经选中了（从截图可以看到）

**说明：**
- ✅ 这是最简单的方式
- ✅ Oracle 会自动生成密钥对
- ✅ 不需要您手动生成

---

**2. 下载私钥文件**

**操作：**
- ✅ 点击 **"Download private key"**（下载私钥）按钮
- ✅ 保存私钥文件到本地

**重要：**
- ⚠️ **必须下载私钥文件！**
- ⚠️ 私钥文件用于连接服务器
- ⚠️ 丢失后无法恢复，需要重新创建实例

**保存位置建议：**
- ✅ Windows：`C:\Users\您的用户名\.ssh\oracle_key.pem`
- ✅ 或保存到您容易找到的位置

---

**3. 下载公钥文件（可选）**

**操作：**
- ✅ 点击 **"Download public key"**（下载公钥）按钮（可选）
- ✅ 通常只需要私钥即可

---

**4. 其他选项（不需要选择）**

- ❌ "Upload public key file (.pub)" - 不需要
- ❌ "Paste public key" - 不需要
- ❌ "No SSH keys" - 不要选择这个！

---

## 🌐 第2部分：Networking（网络）配置

### 根据您的截图，您需要配置以下内容：

---

#### 1. Primary VNIC（主虚拟网络接口卡）

**VNIC name（VNIC 名称）：**
- ✅ 可以留空（使用默认名称）
- ✅ 或填写：`vnic-cross-border-tool`

**说明：**
- ✅ 这是网络接口的名称
- ✅ 可以自定义，也可以使用默认值

---

#### 2. Primary network（主网络）

**选择：**
- ✅ **"Create new virtual cloud network"**（创建新的虚拟云网络）- **推荐**
- ❌ 不要选择 "Select existing virtual cloud network"（除非您已经有 VCN）

**说明：**
- ✅ 如果是第一次创建，选择创建新的 VCN
- ✅ Oracle 会自动创建 VCN 和子网

**如果选择 "Create new virtual cloud network"：**
- ✅ VCN name（VCN 名称）：自动生成或自定义
- ✅ 其他选项使用默认值即可

---

#### 3. Subnet（子网）

**选择：**
- ✅ **"Create new public subnet"**（创建新的公共子网）- **推荐**
- ❌ 不要选择 "Select existing subnet"（除非您已经有子网）

**说明：**
- ✅ 公共子网允许从互联网访问
- ✅ 这是部署网站必需的

---

#### 4. Private IPv4 address assignment（私有 IPv4 地址分配）

**选择：**
- ✅ **"Automatically assign private IPv4 address"**（自动分配私有 IPv4 地址）- **推荐**
- ❌ 不要选择 "Manually assign private IPv4 address"（除非您知道具体 IP）

**说明：**
- ✅ 让 Oracle 自动分配即可
- ✅ 最简单的方式

---

#### 5. Public IPv4 address assignment（公网 IPv4 地址分配）- **最重要！**

**选择：**
- ✅ **开启 "Automatically assign public IPv4 address"**（自动分配公网 IPv4 地址）
- ✅ **必须开启！** 否则无法从外网访问服务器

**操作：**
- ✅ 找到 "Automatically assign public IPv4 address" 选项
- ✅ 将开关切换到 **"On"**（开启）位置

**说明：**
- ⚠️ **这是最重要的配置！**
- ⚠️ 如果不开启，无法从外网访问您的服务器
- ⚠️ 网站无法被访问

---

## 📋 完整配置清单

### SSH keys 配置：

1. ✅ 选择 "Generate a key pair for me"（已选中）
2. ✅ 点击 "Download private key" 下载私钥
3. ✅ 保存私钥文件到本地

---

### Networking 配置：

1. ✅ **VNIC name**：留空或自定义
2. ✅ **Primary network**：选择 "Create new virtual cloud network"
3. ✅ **Subnet**：选择 "Create new public subnet"
4. ✅ **Private IPv4 address**：选择 "Automatically assign"
5. ✅ **Public IPv4 address**：**必须开启 "Automatically assign public IPv4 address"**

---

## ⚠️ 重要提醒

### 1. SSH 私钥文件

**必须下载：**
- ⚠️ 点击 "Download private key" 按钮
- ⚠️ 保存私钥文件
- ⚠️ 以后连接服务器需要用到

**如果丢失：**
- ❌ 无法连接服务器
- ❌ 需要重新创建实例

---

### 2. 公网 IP 地址

**必须开启：**
- ⚠️ "Automatically assign public IPv4 address" 必须开启
- ⚠️ 否则无法从外网访问服务器
- ⚠️ 网站无法被访问

---

### 3. 公共子网

**必须选择：**
- ⚠️ 选择 "Create new public subnet"
- ⚠️ 公共子网允许从互联网访问
- ⚠️ 私有子网无法从外网访问

---

## 🎯 快速配置步骤

### 第1步：SSH keys

1. ✅ 确认 "Generate a key pair for me" 已选中
2. ✅ 点击 "Download private key" 下载私钥
3. ✅ 保存私钥文件

---

### 第2步：Networking

1. ✅ **VNIC name**：留空
2. ✅ **Primary network**：选择 "Create new virtual cloud network"
3. ✅ **Subnet**：选择 "Create new public subnet"
4. ✅ **Private IPv4 address**：选择 "Automatically assign"
5. ✅ **Public IPv4 address**：**开启开关（On）**

---

### 第3步：继续

1. ✅ 点击 "Next" 按钮
2. ✅ 进入下一步（Storage 或 Review）
3. ✅ 最后点击 "Create" 创建实例

---

## 💡 配置示例

### SSH keys 配置：

```
✅ Generate a key pair for me（已选中）
✅ Download private key（点击下载）
✅ 保存到：C:\Users\您的用户名\.ssh\oracle_key.pem
```

---

### Networking 配置：

```
VNIC name: （留空）

Primary network:
  ✅ Create new virtual cloud network
  VCN name: （自动生成）

Subnet:
  ✅ Create new public subnet
  Subnet name: （自动生成）

Private IPv4 address assignment:
  ✅ Automatically assign private IPv4 address（已选中）

Public IPv4 address assignment:
  ✅ Automatically assign public IPv4 address（必须开启！）
```

---

## 🎉 总结

### SSH keys 配置：

1. ✅ "Generate a key pair for me" 已选中
2. ✅ 点击 "Download private key" 下载私钥
3. ✅ 保存私钥文件

---

### Networking 配置：

1. ✅ Primary network：选择 "Create new virtual cloud network"
2. ✅ Subnet：选择 "Create new public subnet"
3. ✅ Private IPv4 address：选择 "Automatically assign"
4. ✅ **Public IPv4 address：必须开启！**

---

## 📝 下一步

配置完成后：
1. ✅ 点击 "Next" 按钮
2. ✅ 进入下一步（Storage 或 Review）
3. ✅ 检查所有配置
4. ✅ 点击 "Create" 创建实例
5. ✅ 等待 2-5 分钟，实例创建完成

---

**最后更新：** 2025年1月
**状态：** ✅ 配置指南已准备就绪

