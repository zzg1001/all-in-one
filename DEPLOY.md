# AI Skills Platform 部署指南

## 服务器要求

- Linux (CentOS/Ubuntu)
- Docker + Docker Compose
- Nginx
- MySQL 8+

## 目录结构

```
/opt/ai-platform/
├── frontend/           # 前端代码
│   ├── portal/
│   └── admin/
├── backend/            # 后端代码
├── deploy.env          # 环境变量
└── docker-compose*.yml
```

## 配置 deploy.env

```env
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=【数据库密码】
DB_NAME=ai_agent

# AI 模型
ANTHROPIC_AUTH_TOKEN=【Azure Token】
ANTHROPIC_BASE_URL=https://your-azure-proxy-url
CLAUDE_MODEL=claude-opus-4-5

# JWT
SECRET_KEY=【64字符随机串】

# 跨域
CORS_ORIGINS=["https://your-domain.com"]
```

> 生成 SECRET_KEY：`python3 -c "import secrets; print(secrets.token_hex(32))"`

## 部署步骤

### 1. 构建前端

```bash
cd frontend/portal && npm install && npm run build
cd ../admin && npm install && npm run build
```

### 2. 启动服务

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 3. 配置 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Portal 前端
    location / {
        proxy_pass http://127.0.0.1:5173;
    }

    # Admin 前端
    location /admin/ {
        proxy_pass http://127.0.0.1:5174/;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_read_timeout 300s;
    }
}
```

## 常用命令

| 操作 | 命令 |
|------|------|
| 查看日志 | `docker logs -f backend` |
| 重启 | `docker-compose -f docker-compose.prod.yml restart` |
| 重建 | `docker-compose -f docker-compose.prod.yml up -d --build` |

## 必改项

| 配置项 | 说明 |
|--------|------|
| DB_PASSWORD | 数据库密码 |
| ANTHROPIC_AUTH_TOKEN | Azure Claude Token |
| SECRET_KEY | JWT 密钥（64字符） |
| CORS_ORIGINS | 前端域名 |
