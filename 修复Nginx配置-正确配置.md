# 🔧 修复Nginx配置 - 正确配置

## 📋 问题分析

**当前配置的问题：**
- 所有请求（包括静态文件）都被代理到后端Flask应用
- 但后端服务没有运行，所以静态文件也访问不了
- 需要让静态文件直接从文件系统提供，API请求才代理到后端

---

## 🚀 修复步骤

### 步骤1：编辑配置文件

```bash
sudo nano /etc/nginx/sites-available/background_remover_tool
```

### 步骤2：修改配置

**找到这部分：**
```nginx
# 应用
location / {
    proxy_pass http://127.0.0.1:5000;
    ...
}
```

**替换为：**
```nginx
# 静态文件（前端）
location / {
    root /var/www/background_remover_tool/frontend;
    try_files $uri $uri/ /index.html;
}

# API代理（后端）
location /api/ {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 增加超时时间
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}
```

---

## 📝 完整配置（参考）

**修改后的完整配置应该是：**

```nginx
server {
    server_name nbfive.com www.nbfive.com;

    # 增加请求体大小限制（允许上传大图片，5MB）
    client_max_body_size 5M;

    # 静态文件（前端）
    location / {
        root /var/www/background_remover_tool/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API代理（后端）
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # 静态资源
    location /static {
        alias /var/www/background_remover_tool/static;
    }

    # 上传文件
    location /uploads {
        alias /var/www/background_remover_tool/uploads;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/nbfive.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/nbfive.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = www.nbfive.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    if ($host = nbfive.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    listen 80;
    server_name nbfive.com www.nbfive.com;
    client_max_body_size 5M;
    return 404; # managed by Certbot
}
```

---

## 🔧 操作步骤

### 1. 编辑配置文件

```bash
sudo nano /etc/nginx/sites-available/background_remover_tool
```

### 2. 找到这部分并修改：

**原来的：**
```nginx
# 应用
location / {
    proxy_pass http://127.0.0.1:5000;
    ...
}
```

**改为：**
```nginx
# 静态文件（前端）
location / {
    root /var/www/background_remover_tool/frontend;
    try_files $uri $uri/ /index.html;
}

# API代理（后端）
location /api/ {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 增加超时时间
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
}
```

### 3. 保存文件

- 按 `Ctrl + O` 保存
- 按 `Enter` 确认
- 按 `Ctrl + X` 退出

### 4. 测试配置

```bash
sudo nginx -t
```

**应该看到：**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 5. 重新加载Nginx

```bash
sudo systemctl reload nginx
```

### 6. 启动后端服务

```bash
sudo systemctl start background_remover_tool
sudo systemctl enable background_remover_tool  # 设置开机自启
```

### 7. 测试

```bash
# 测试静态文件
curl -I https://nbfive.com/terms.html

# 测试API
curl https://nbfive.com/api/auth/profile
```

---

## 🎯 关键修改

**最重要的修改：**

1. **静态文件直接从文件系统提供**
   ```nginx
   location / {
       root /var/www/background_remover_tool/frontend;
       try_files $uri $uri/ /index.html;
   }
   ```

2. **只有API请求才代理到后端**
   ```nginx
   location /api/ {
       proxy_pass http://127.0.0.1:5000;
       ...
   }
   ```

---

## 📝 总结

**修改后：**
- ✅ 静态文件（HTML、CSS、JS）直接从 `frontend` 目录提供
- ✅ API请求（`/api/`）代理到后端Flask应用
- ✅ 页脚页面可以正常访问
- ✅ 其他功能也正常

**现在按照上面的步骤修改配置，然后测试！**

