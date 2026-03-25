# AI Skills Platform 部署指南

## 服务器要求

- Linux (CentOS/Ubuntu)
- Docker + Docker Compose
- Nginx
- MySQL 8+

---

## 一、目录结构

```
/data/ai-platform/
├── config/
│   ├── portal.env        # Portal 后端配置
│   └── admin.env         # Admin 后端配置
├── skills_storage/       # 技能文件存储
├── outputs/              # 输出文件
└── uploads/              # 上传文件

/var/www/
├── portal/               # Portal 前端静态文件
└── admin/                # Admin 前端静态文件
```

---

## 二、配置文件

### 1. Portal 配置 `/data/ai-platform/config/portal.env`

```env
# 环境
ENV=production
DEBUG=false

# 数据库
DB_HOST=8.153.198.194
DB_PORT=63306
DB_USER=root
DB_PASSWORD=【填写数据库密码】
DB_NAME=product_background

# AI 模型
ANTHROPIC_API_KEY=【填写 Claude API 密钥】
ANTHROPIC_BASE_URL=
CLAUDE_MODEL=claude-opus-4-5

# 跨域（改成你的域名）
CORS_ORIGINS=["https://infortest.ike-data.com"]

# Admin API 地址
ADMIN_API_URL=http://127.0.0.1:8001/api
```

### 2. Admin 配置 `/data/ai-platform/config/admin.env`

```env
# 环境
ENV=production
DEBUG=false

# 数据库（与 Portal 一致）
DB_HOST=8.153.198.194
DB_PORT=63306
DB_USER=root
DB_PASSWORD=【填写数据库密码】
DB_NAME=product_background

# JWT 认证
SECRET_KEY=【填写64字符随机串】
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 跨域（改成你的域名）
CORS_ORIGINS_STR=["https://infortest.ike-data.com"]

# Portal API 地址
PORTAL_API_URL=http://127.0.0.1:8000/api
```

> 生成 SECRET_KEY：`python3 -c "import secrets; print(secrets.token_hex(32))"`

---

## 三、部署步骤

### 步骤 1：创建目录

```bash
mkdir -p /data/ai-platform/{config,skills_storage,outputs,uploads}
mkdir -p /var/www/{portal,admin}
```

### 步骤 2：创建配置文件

```bash
vi /data/ai-platform/config/portal.env
vi /data/ai-platform/config/admin.env
```

### 步骤 3：上传代码

将项目代码上传到服务器，例如 `/opt/ai-platform/`

### 步骤 4：构建前端

```bash
cd /opt/ai-platform

# Portal 前端
cd portal/web
npm install
npm run build
cp -r dist/* /var/www/portal/

# Admin 前端
cd ../../admin/web
npm install
npm run build
cp -r dist/* /var/www/admin/
```

### 步骤 5：启动后端（Docker）

```bash
cd /opt/ai-platform
docker-compose -f docker-compose.prod.yml up -d --build
```

### 步骤 6：配置 Nginx

```nginx
server {
    listen 80;
    server_name infortest.ike-data.com;

    # Portal 前端
    location / {
        root /var/www/portal;
        try_files $uri $uri/ /index.html;
    }

    # Admin 前端
    location /admin/ {
        alias /var/www/admin/;
        try_files $uri $uri/ /admin/index.html;
    }

    # Portal API 代理
    location /portal-api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }

    # Admin API 代理
    location /admin-api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
nginx -t && nginx -s reload
```

---

## 四、验证部署

```bash
# 检查容器状态
docker ps

# 检查 API
curl http://127.0.0.1:8000/docs
curl http://127.0.0.1:8001/docs

# 查看日志
docker logs -f portal-api
docker logs -f admin-api
```

---

## 五、常用命令

| 操作 | 命令 |
|------|------|
| 查看容器 | `docker ps` |
| 查看日志 | `docker logs -f portal-api` |
| 重启服务 | `docker-compose -f docker-compose.prod.yml restart` |
| 停止服务 | `docker-compose -f docker-compose.prod.yml down` |
| 重新构建 | `docker-compose -f docker-compose.prod.yml up -d --build` |

---

## 六、必改项清单

| 配置项 | 文件 | 说明 |
|--------|------|------|
| DB_PASSWORD | portal.env / admin.env | 数据库密码 |
| ANTHROPIC_API_KEY | portal.env | Claude API 密钥 |
| SECRET_KEY | admin.env | JWT 签名密钥（64字符） |
| CORS_ORIGINS | portal.env / admin.env | 前端域名 |
| server_name | nginx.conf | 实际域名 |
