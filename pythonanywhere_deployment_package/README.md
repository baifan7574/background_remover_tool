# PythonAnywhere部署包

## 📁 文件结构（适配PythonAnywhere默认路径）

```
/home/baifan7574/mysite/
├── flask_app.py              # 主应用文件（从app_test_standalone.py适配）
├── templates/
│   └── index.html           # 前端界面（从backend/templates/复制）
├── static/
│   ├── css/
│   │   └── style.css        # 样式文件（从frontend/css/复制）
│   └── js/
│       └── app.js          # JS文件（从frontend/js/复制）
├── requirements.txt         # 依赖文件（简化版）
└── .env                    # 环境变量（可选）
```

## 🚀 部署步骤

### 1. 在PythonAnywhere控制台
```bash
# 进入项目目录
cd /home/baifan7574/mysite

# 创建必要文件夹
mkdir templates
mkdir static
mkdir static/css
mkdir static/js
```

### 2. 上传文件
- 将本地的 `backend/app_test_standalone.py` 上传为 `flask_app.py`
- 将 `backend/templates/index.html` 上传到 `templates/`
- 将 `frontend/css/style.css` 上传到 `static/css/`
- 将 `frontend/js/app.js` 上传到 `static/js/`
- 上传 `requirements.txt`

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置WSGI
在PythonAnywhere的Web标签页，修改WSGI配置文件指向：
```
/home/baifan7574/mysite/flask_app.py
```

### 5. 重启Web应用
点击"Reload"按钮重启应用

## 🌐 访问地址
你的应用将在以下地址可用：
`http://baifan7574.pythonanywhere.com`

## 📝 注意事项
- 文件路径已适配PythonAnywhere默认结构
- 移除了本地特定的路径引用
- 简化了依赖列表，只包含必需的包