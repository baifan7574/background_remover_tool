# 🔑 API接入说明

## ✅ 当前状态

关键词分析功能**已经完整实现**，但使用的是**模拟数据**。

功能完全正常，可以：
- ✅ 打开关键词分析工具
- ✅ 选择不同的功能（提取、竞争度查询、趋势分析等）
- ✅ 输入产品描述
- ✅ 获取分析结果
- ✅ 查看关键词列表
- ✅ 导出Excel/CSV

**数据来源**：模拟数据（测试用）

---

## 🔄 如何接入真实API

### 需要替换的函数

在 `sk_app.py` 中，有以下函数需要替换为真实API调用：

#### 1. `generate_mock_keyword_extract()` - GPT关键词提取

**当前**：使用模拟数据
**替换为**：OpenAI API

```python
# 在 sk_app.py 中替换此函数
def generate_mock_keyword_extract(product_description, platform):
    # 删除模拟数据代码
    
    # 替换为真实API调用
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个专业的跨境电商关键词分析师"},
            {"role": "user", "content": f"请为以下产品描述提取适合{platform}平台的关键词，返回JSON格式列表：{product_description}"}
        ],
        temperature=0.7
    )
    
    # 解析response并返回关键词列表
    keywords_json = response.choices[0].message.content
    keywords = json.loads(keywords_json)
    
    return {
        'keywords': keywords,
        'total_count': len(keywords)
    }
```

**需要**：
- OpenAI API密钥（在 `.env` 文件中设置：`OPENAI_API_KEY=你的密钥`）

---

#### 2. `generate_mock_competition_data()` - 亚马逊竞争度查询

**当前**：使用模拟数据
**替换为**：亚马逊SP-API

```python
# 在 sk_app.py 中替换此函数
def generate_mock_competition_data(product_description, platform):
    # 删除模拟数据代码
    
    # 替换为真实API调用
    from sp_api.api import ProductSearch
    from sp_api.base import Marketplaces, SellingApiException
    
    client = ProductSearch(
        marketplace=Marketplaces.US,
        credentials={
            'lwa_app_id': os.getenv('AMAZON_LWA_APP_ID'),
            'lwa_client_secret': os.getenv('AMAZON_LWA_CLIENT_SECRET'),
            'aws_access_key_id': os.getenv('AMAZON_AWS_ACCESS_KEY'),
            'aws_secret_access_key': os.getenv('AMAZON_AWS_SECRET_KEY'),
            'role_arn': os.getenv('AMAZON_ROLE_ARN')
        }
    )
    
    # 调用API查询竞争度
    result = client.search_items(
        keywords=product_description,
        marketplaceIds=['ATVPDKIKX0DER']
    )
    
    # 解析result并返回竞争度数据
    competition_data = []
    # ... 解析result ...
    
    return {
        'competition_data': {'keywords': competition_data},
        'keywords': competition_data
    }
```

**需要**：
- 亚马逊SP-API凭证（在 `.env` 文件中设置）
- `AMAZON_LWA_APP_ID`
- `AMAZON_LWA_CLIENT_SECRET`
- `AMAZON_AWS_ACCESS_KEY`
- `AMAZON_AWS_SECRET_KEY`
- `AMAZON_ROLE_ARN`

---

#### 3. `generate_mock_trend_data()` - 趋势分析

**当前**：使用模拟数据
**替换为**：亚马逊SP-API（历史数据）

```python
# 在 sk_app.py 中替换此函数
def generate_mock_trend_data(product_description, platform):
    # 删除模拟数据代码
    
    # 替换为真实API调用（查询历史搜索趋势）
    # 使用亚马逊SP-API或第三方数据服务
    # ...
    
    return {'trend_data': {...}}
```

**需要**：
- 亚马逊SP-API凭证（同上）
- 或第三方数据服务API（如Jungle Scout API）

---

#### 4. `generate_mock_comparison_data()` - 竞品对比

**当前**：使用模拟数据
**替换为**：亚马逊SP-API

```python
# 在 sk_app.py 中替换此函数
def generate_mock_comparison_data(competitor_asin, platform):
    # 删除模拟数据代码
    
    # 替换为真实API调用
    # 查询竞品ASIN的关键词排名
    # ...
    
    return {'comparison_data': {...}}
```

**需要**：
- 亚马逊SP-API凭证（同上）

---

#### 5. `generate_mock_longtail_keywords()` - 长尾关键词挖掘

**当前**：使用模拟数据
**替换为**：OpenAI API

```python
# 在 sk_app.py 中替换此函数
def generate_mock_longtail_keywords(product_description, platform):
    # 删除模拟数据代码
    
    # 替换为真实API调用（使用GPT生成长尾关键词）
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一个专业的跨境电商关键词分析师"},
            {"role": "user", "content": f"请为以下产品生成长尾关键词变体，适合{platform}平台：{product_description}"}
        ]
    )
    
    # 解析response并返回长尾关键词列表
    # ...
    
    return {'longtail_keywords': [...], 'total_count': ...}
```

**需要**：
- OpenAI API密钥（同上）

---

## 📝 接入步骤

### 步骤1：申请API密钥

#### OpenAI API密钥（必需 - 用于GPT功能）

1. 访问：https://platform.openai.com/
2. 注册账号
3. 进入 API Keys 页面
4. 创建新的密钥
5. 复制密钥（格式：`sk-...`）

#### 亚马逊SP-API凭证（必需 - 用于竞争度查询）

1. 访问：https://developer.amazon.com/sp-api/
2. 注册开发者账号
3. 创建应用（Application）
4. 获取以下信息：
   - `LWA Client ID`
   - `LWA Client Secret`
   - `Refresh Token`
   - `AWS Access Key ID`
   - `AWS Secret Access Key`
   - `Marketplace ID`（如：US = A1PA6795UKMFR9）

---

### 步骤2：配置环境变量

创建或编辑 `.env` 文件：

```env
# OpenAI API配置
OPENAI_API_KEY=你的openai_api_key

# 亚马逊SP-API配置
AMAZON_LWA_APP_ID=你的lwa_app_id
AMAZON_LWA_CLIENT_SECRET=你的lwa_client_secret
AMAZON_AWS_ACCESS_KEY=你的aws_access_key
AMAZON_AWS_SECRET_KEY=你的aws_secret_key
AMAZON_ROLE_ARN=你的role_arn
AMAZON_MARKETPLACE_ID=ATVPDKIKX0DER
```

---

### 步骤3：安装依赖

```bash
pip install openai
pip install python-amazon-sp-api
```

或更新 `requirements.txt`：

```txt
openai>=1.0.0
python-amazon-sp-api>=1.0.0
```

然后运行：

```bash
pip install -r requirements.txt
```

---

### 步骤4：替换模拟数据函数

在 `sk_app.py` 中，找到以下函数并替换为真实API调用：

1. `generate_mock_keyword_extract()` → 使用OpenAI API
2. `generate_mock_competition_data()` → 使用亚马逊SP-API
3. `generate_mock_trend_data()` → 使用亚马逊SP-API
4. `generate_mock_comparison_data()` → 使用亚马逊SP-API
5. `generate_mock_longtail_keywords()` → 使用OpenAI API

**注意**：
- 保持函数名称不变（只替换函数内容）
- 保持返回格式不变（确保前端能正确解析）
- 添加错误处理（API调用失败时的fallback）

---

### 步骤5：测试

1. **重启后端服务器**
2. **刷新浏览器**（Ctrl+F5）
3. **测试关键词分析功能**
4. **检查后端日志**（确认API调用是否成功）
5. **查看返回数据**（确认数据格式正确）

---

## 🔍 代码位置

### 需要修改的文件

1. **`sk_app.py`** - 后端API路由
   - 位置：约第1782行后
   - 函数：`keyword_analyzer()` 和所有 `generate_mock_*()` 函数

2. **`.env`** - 环境变量配置（需要创建）
   - 添加：OpenAI和亚马逊API密钥

3. **`requirements.txt`** - 依赖列表
   - 添加：`openai` 和 `python-amazon-sp-api`

---

## ✅ 接入后

接入真实API后：
- ✅ 数据完全真实（来自OpenAI和亚马逊API）
- ✅ 功能完全正常
- ✅ 用户体验不受影响
- ✅ 可以用于实际业务

---

## 📋 接入检查清单

- [ ] 申请OpenAI API密钥
- [ ] 申请亚马逊SP-API凭证
- [ ] 创建 `.env` 文件并配置密钥
- [ ] 安装依赖（`openai`、`python-amazon-sp-api`）
- [ ] 替换 `generate_mock_keyword_extract()` 函数
- [ ] 替换 `generate_mock_competition_data()` 函数
- [ ] 替换 `generate_mock_trend_data()` 函数
- [ ] 替换 `generate_mock_comparison_data()` 函数
- [ ] 替换 `generate_mock_longtail_keywords()` 函数
- [ ] 重启后端服务器
- [ ] 测试所有功能
- [ ] 检查后端日志确认API调用成功
- [ ] 验证返回数据格式正确

---

## 💡 提示

1. **可以先接入OpenAI API**（简单，几分钟完成）
   - 先替换关键词提取和长尾关键词挖掘
   - 这两个功能使用GPT，不需要亚马逊API

2. **亚马逊SP-API申请较复杂**
   - 需要几天到一周时间
   - 可以先使用模拟数据测试功能
   - API申请通过后再接入

3. **保持模拟数据作为fallback**
   - API调用失败时，可以fallback到模拟数据
   - 确保用户体验不受影响

4. **测试时注意API调用次数**
   - OpenAI API按token收费
   - 亚马逊SP-API有免费配额
   - 注意控制成本

---

## ✅ 现在可以做的

1. **测试完整功能**（使用模拟数据）
   - 所有6个功能都可以正常使用
   - 界面和交互都正常

2. **申请API密钥**（并行进行）
   - 申请OpenAI API密钥（简单）
   - 申请亚马逊SP-API凭证（复杂）

3. **接入真实API**（API申请通过后）
   - 替换模拟数据函数
   - 重启服务器
   - 测试功能

---

**功能已经完整实现，你现在可以测试所有功能！** 🎉

