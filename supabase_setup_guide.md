# Supabase数据库初始化指南

## 📋 概述
这个脚本一次性创建跨境电商工具站所需的所有数据库表、索引、权限和初始数据，避免来回修改。

## 🚀 快速执行步骤

### 1. 在Supabase控制台执行SQL
1. 登录 [Supabase Dashboard](https://app.supabase.com)
2. 选择你的项目
3. 进入 **SQL Editor**
4. 复制 `supabase_init.sql` 文件内容
5. 点击 **Run** 执行脚本

### 2. 创建存储桶
执行完SQL后，需要在控制台手动创建存储桶：

1. 进入 **Storage** 部分
2. 点击 **New bucket**
3. 填写信息：
   - **Name**: `processed-images`
   - **Public bucket**: ❌ 不勾选
   - **File size limit**: 50MB
4. 点击 **Save**

## 📊 数据库结构说明

### 核心表结构
| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `user_profiles` | 用户信息 | email, membership_type, points, invitation_code |
| `tool_usage` | 工具使用记录 | tool_type, usage_count, daily_limit |
| `payment_records` | 支付记录 | order_no, amount, membership_type |
| `invitation_records` | 邀请记录 | inviter_id, invitation_code, reward_days |
| `file_storage` | 文件存储 | storage_path, processing_status |
| `system_config` | 系统配置 | config_key, config_value |

### 会员权限配置
- **免费版**: 10张图片/天，5次分析/天
- **基础版(39元)**: 50张图片/天，25次分析/天  
- **专业版(59元)**: 100张图片/天，50次分析/天
- **旗舰版(99元)**: 无限制使用

## 🔒 安全特性
- **RLS (Row Level Security)**: 用户只能访问自己的数据
- **UUID主键**: 防止ID猜测攻击
- **索引优化**: 提升查询性能
- **操作日志**: 记录所有用户操作

## 📁 文件存储配置
- **存储桶**: `processed-images`
- **路径规则**: `{user_id}/{timestamp}_{filename}`
- **访问控制**: 用户只能访问自己的文件
- **自动清理**: 30天后自动删除

## 🔧 获取API密钥
执行完初始化后，获取以下信息用于项目配置：

1. **Project URL**: 在 Settings → API 中找到
2. **Anon Public Key**: 在 Settings → API 中找到
3. **Service Role Key**: 在 Settings → API 中找到（谨慎使用）

## ⚡ 性能优化
- 已创建所有必要索引
- 使用视图简化复杂查询
- 触发器自动更新时间戳
- 分页查询优化

## 🧪 测试验证
执行完脚本后，可以运行以下测试SQL验证：

```sql
-- 检查表是否创建成功
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 检查系统配置
SELECT * FROM system_config WHERE is_public = true;

-- 检查索引
SELECT indexname, tablename FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;
```

## 📝 注意事项
1. 脚本包含 `ON CONFLICT DO NOTHING`，可重复执行
2. 存储桶需要手动创建，SQL无法自动创建
3. RLS策略需要配合前端认证使用
4. 生产环境建议启用备份

## 🔄 下一步
数据库初始化完成后，继续执行：
1. ✅ 配置Supabase存储桶
2. ⏳ 修改项目代码支持Supabase
3. ⏳ 本地测试集成功能
4. ⏳ 部署到PythonAnywhere

---
*创建时间: 2024年*
*版本: v1.0*