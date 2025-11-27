# Supabase集成完整部署指南

## 📋 项目概述

本项目已完成从本地SQLite到Supabase云数据库的完整集成，支持用户管理、积分系统、工具使用记录和文件存储等功能。

## 🎯 已完成的功能

### ✅ 第2天任务：Supabase数据库集成

1. **数据库结构设计**
   - 用户扩展信息表（user_profiles）
   - 工具使用记录表（tool_usage）
   - 系统配置表（system_config）
   - 积分交易记录表（credit_transactions）
   - 支付记录表（payments）

2. **存储桶配置**
   - processed-images：处理后的图片（公开访问）
   - uploads：原始上传文件（私有访问）

3. **核心功能实现**
   - 用户认证和注册
   - 积分管理系统
   - 工具使用记录
   - 文件上传到Supabase Storage
   - 完整的API端点

## 📁 项目文件结构

```
background_remover_tool/
├── backend/
│   ├── app.py                    # 原始SQLite版本
│   └── app_supabase.py          # ✨ 新版Supabase集成版本
├── supabase_db.py               # Supabase数据库操作类
├── supabase_complete_init.py    # 数据库初始化脚本
├── test_supabase_integration.py # 集成测试脚本
├── requirements_supabase.txt    # 依赖文件
├── .env.template               # 环境变量模板
└── docs/
    └── supabase_deployment_guide.md # 本文档
```

## 🚀 部署步骤

### 第1步：Supabase项目设置

1. **创建Supabase项目**
   - 访问 [supabase.com](https://supabase.com)
   - 创建新项目
   - 选择数据库位置（推荐选择亚洲区域）

2. **获取配置信息**
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-role-key
   ```

3. **配置环境变量**
   ```bash
   # 复制模板文件
   cp .env.template .env
   
   # 编辑.env文件，填入实际配置
   nano .env
   ```

### 第2步：数据库初始化

1. **运行初始化脚本**
   ```bash
   python supabase_complete_init.py
   ```

2. **在Supabase控制台执行SQL**
   - 打开项目的SQL编辑器
   - 复制并执行脚本生成的所有SQL语句
   - 验证表和存储桶创建成功

3. **配置认证设置**
   - 在Authentication → Settings中配置：
   - 站点URL：`http://localhost:5000`
   - 重定向URL：`http://localhost:5000/auth/callback`
   - 启用邮箱注册

### 第3步：本地测试

1. **安装依赖**
   ```bash
   pip install -r requirements_supabase.txt
   ```

2. **运行集成测试**
   ```bash
   python test_supabase_integration.py
   ```

3. **启动应用**
   ```bash
   python backend/app_supabase.py
   ```

4. **访问应用**
   - 主页：`http://localhost:5000`
   - 健康检查：`http://localhost:5000/health`

### 第4步：PythonAnywhere部署

1. **准备部署文件**
   ```bash
   # 创建部署包
   tar -czf supabase_app.tar.gz \
       backend/app_supabase.py \
       supabase_db.py \
       requirements_supabase.txt \
       .env \
       static/ \
       templates/
   ```

2. **PythonAnywhere配置**
   - 上传部署包到PythonAnywhere
   - 创建虚拟环境
   - 安装依赖：`pip install -r requirements_supabase.txt`
   - 配置Web应用指向`backend/app_supabase.py`
   - 设置环境变量

## 🔧 API端点文档

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/profile` - 获取用户资料
- `POST /api/auth/logout` - 用户登出

### 工具API
- `POST /api/tools/remove-background` - 背景移除
- `POST /api/tools/currency-converter` - 汇率转换
- `POST /api/tools/unit-converter` - 单位转换
- `POST /api/tools/shipping-calculator` - 运费计算

### 文件管理
- `POST /api/upload` - 文件上传
- `GET /api/download/<filename>` - 文件下载

### 系统管理
- `GET /api/tools/usage-stats` - 使用统计
- `GET /health` - 健康检查

## 💾 数据库表结构

### user_profiles（用户资料）
```sql
- id: UUID (主键)
- user_id: UUID (关联auth.users)
- email: TEXT
- name: TEXT
- plan: TEXT (默认'free')
- credits: INTEGER (默认10)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### tool_usage（工具使用记录）
```sql
- id: UUID (主键)
- user_id: UUID
- tool_name: TEXT
- credits_used: INTEGER
- input_data: JSONB
- output_data: JSONB
- created_at: TIMESTAMP
```

### credit_transactions（积分交易）
```sql
- id: UUID (主键)
- user_id: UUID
- transaction_type: TEXT ('usage', 'purchase', 'refund', 'bonus')
- amount: INTEGER
- description: TEXT
- reference_id: UUID
- created_at: TIMESTAMP
```

## 🔒 安全配置

### RLS策略（行级安全）
- 用户只能访问自己的数据
- 文件存储按用户隔离
- API密钥权限分级

### 积分系统
- 免费用户：10初始积分
- 背景移除：2积分/次
- 转换工具：1积分/次
- 自动积分扣减和记录

## 📊 监控和维护

### 日志记录
- 用户操作日志
- API调用记录
- 错误追踪

### 性能监控
- 数据库查询性能
- 文件上传/下载速度
- API响应时间

### 备份策略
- Supabase自动备份
- 定期数据导出
- 灾难恢复计划

## 🐛 常见问题解决

### 1. 连接Supabase失败
```bash
# 检查环境变量
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# 测试连接
python -c "from supabase import create_client; print('连接成功')"
```

### 2. 积分不更新
```sql
-- 检查触发器
SELECT * FROM pg_trigger WHERE tgname LIKE '%credit%';

-- 检查函数
SELECT proname FROM pg_proc WHERE proname LIKE '%credit%';
```

### 3. 文件上传失败
```bash
# 检查存储桶权限
# 在Supabase控制台查看Storage policies
```

## 📈 性能优化建议

1. **数据库优化**
   - 添加适当的索引
   - 使用连接池
   - 实施查询缓存

2. **文件存储优化**
   - 实施CDN加速
   - 压缩图片文件
   - 定期清理临时文件

3. **API优化**
   - 实施请求限流
   - 添加响应缓存
   - 优化序列化

## 🔄 下一步计划

### 第3天：PythonAnywhere部署
- [ ] 注册PythonAnywhere账户
- [ ] 部署Supabase集成版本
- [ ] 配置域名和SSL

### 第4天：用户系统完善
- [ ] 实现邮箱验证
- [ ] 添加密码重置
- [ ] 完善用户权限管理

### 第5天：支付集成
- [ ] 集成支付宝/微信支付
- [ ] 实现积分购买
- [ ] 添加订阅管理

## 📞 技术支持

如遇到问题，请检查：
1. 环境变量配置是否正确
2. Supabase项目设置是否完整
3. 依赖包版本是否兼容
4. 网络连接是否正常

---

**部署完成后，您的应用将具备：**
✅ 云端数据库支持
✅ 用户认证系统
✅ 积分管理功能
✅ 文件存储服务
✅ 完整的API接口
✅ 生产级安全配置

🎉 **恭喜！您的应用已成功集成Supabase，准备部署到生产环境！**