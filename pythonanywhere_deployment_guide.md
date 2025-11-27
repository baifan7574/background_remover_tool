# PythonAnywhere 部署指南

## 🎯 第1天任务：配置 PythonAnywhere 环境

### 📋 当前状态
✅ Supabase 数据库已配置完成  
✅ PythonAnywhere 账号已注册  
🔄 正在进行：环境兼容性测试

---

## 🚀 PythonAnywhere 操作步骤

### 1. 登录 PythonAnywhere 控制台
1. 访问 [www.pythonanywhere.com](https://www.pythonanywhere.com)
2. 使用注册的邮箱和密码登录
3. 进入 Dashboard（控制台）

### 2. 打开 Web 控制台
1. 在 Dashboard 点击 "Consoles" 
2. 点击 "Start a new console"
3. 选择 "Bash" 或默认的 "Python 3.10"
4. 等待控制台启动完成

### 3. 上传项目文件
**方法一：使用 Web 界面上传**
1. 点击 "Files" 标签页
2. 进入 `/home/你的用户名/` 目录
3. 点击 "Upload a file"
4. 上传以下文件：
   - `pythonanywhere_compatibility_test.py`
   - `install_pythonanywhere_deps.py`

**方法二：使用 Git（推荐）**
```bash
# 在控制台中执行
git clone https://github.com/你的用户名/background_remover_tool.git
cd background_remover_tool
```

### 4. 安装项目依赖
在 PythonAnywhere 控制台中执行：

```bash
# 运行依赖安装脚本
python install_pythonanywhere_deps.py

# 或者手动安装核心依赖
pip install flask requests pillow supabase python-dotenv
pip install rembg opencv-python numpy pandas
```

### 5. 运行兼容性测试
```bash
# 运行环境测试
python pythonanywhere_compatibility_test.py

# 查看测试报告
cat pythonanywhere_compatibility_test.txt
```

---

## 📊 免费版限制说明

### PythonAnywhere 免费版限制
- **CPU 时间**: 每天 3 小时
- **Web 应用**: 1 个
- **数据库**: 无（需要外部数据库）
- **存储空间**: 512MB
- **带宽**: 100GB/月

### Supabase 免费版限制
- **数据库**: 500MB
- **带宽**: 2GB/月
- **API 调用**: 50,000/月
- **存储**: 1GB
- **实时连接**: 100个

---

## 🔧 环境配置检查清单

### ✅ 基础环境检查
- [ ] Python 3.8+ 版本
- [ ] pip 包管理器可用
- [ ] 网络访问正常
- [ ] 文件写入权限

### ✅ 核心依赖检查
- [ ] Flask Web框架
- [ ] Supabase客户端
- [ ] Pillow图片处理
- [ ] rembg背景移除
- [ ] requests HTTP库

### ✅ 功能测试检查
- [ ] 图片处理功能
- [ ] 数据库连接
- [ ] 文件上传下载
- [ ] API调用测试

---

## 🚨 常见问题解决

### 1. 依赖安装失败
```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ 包名

# 单独安装问题包
pip install --no-cache-dir 包名
```

### 2. 内存不足错误
- 重启控制台释放内存
- 减少同时运行的进程
- 使用轻量级版本包

### 3. 网络访问限制
- 检查防火墙设置
- 使用代理（如果需要）
- 确认API端点可访问

---

## 📈 下一步计划

### 完成环境测试后：
1. **第2天**: 修改项目代码支持 Supabase
2. **第2天**: 本地测试 Supabase 集成功能  
3. **第3天**: 部署项目到 PythonAnywhere 免费版
4. **第3天**: 配置生产环境和域名

### 性能优化建议：
- 使用图片压缩减少存储
- 实现缓存机制
- 优化数据库查询
- 监控资源使用情况

---

## 📞 技术支持

如果在部署过程中遇到问题：
1. 查看错误日志
2. 检查依赖版本兼容性
3. 确认配置文件正确
4. 联系技术支持

---

**当前进度**: 第1天 - PythonAnywhere 环境配置中  
**预计完成时间**: 今天内完成环境测试  
**下一步**: 等待您的测试结果反馈