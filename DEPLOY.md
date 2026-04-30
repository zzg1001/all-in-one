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

### 1. 初始化数据库

首次部署需要初始化数据库表结构和默认数据：

```bash
cd backend

# 方式一：Python 脚本（推荐）
python init_db.py

# 方式二：直接执行 SQL
mysql -h localhost -P 3306 -u root -p ai_agent < init_db.sql
```

**默认账号：**

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| boss | boss123 | 领导 |
| test | test123 | 测试用户 |

> 如需修改数据库连接，编辑 `init_db.py` 中的 `DB_CONFIG`

### 2. 构建前端

```bash
cd frontend/portal && npm install && npm run build
cd ../admin && npm install && npm run build
```

### 3. 启动服务

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

## Skills 同步（MinIO）

Skills 文件通过 MinIO 在多节点间共享。

### MinIO 配置

在 `deploy.env` 中配置：

```env
MINIO_ENDPOINT=8.153.198.194
MINIO_PORT=8092
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=yourpassword123
MINIO_SECURE=false
MINIO_SKILLS_BUCKET=ai-skills
```

### 推送 Skills 到 MinIO（开发环境）

本地修改 Skills 后，推送到远程供其他节点同步：

```bash
cd backend

# 推送所有技能
python push_skills.py

# 推送指定技能
python push_skills.py <skill_id>
```

或通过 API：

```bash
# Linux / Mac / Git Bash
curl -X POST http://localhost:8001/api/skills/push-all
curl -X POST http://localhost:8001/api/skills/{skill_id}/push

# Windows PowerShell（注意用 curl.exe）
curl.exe -X POST http://localhost:8001/api/skills/push-all
curl.exe -X POST http://localhost:8001/api/skills/{skill_id}/push

# 或用 PowerShell 原生语法
Invoke-WebRequest -Method POST -Uri "http://localhost:8001/api/skills/push-all"
```

> **Windows 注意：** PowerShell 中 `curl` 是 `Invoke-WebRequest` 的别名，语法不同。使用 `curl.exe` 调用真正的 curl。

### 拉取 Skills（生产环境）

**自动同步：** 服务启动时会自动从 MinIO 拉取最新的 Skills

**手动同步：**

```bash
# Linux / Mac / Git Bash
curl -X POST http://localhost:8001/api/skills/sync-all
curl -X POST http://localhost:8001/api/skills/{skill_id}/sync

# Windows PowerShell
curl.exe -X POST http://localhost:8001/api/skills/sync-all
curl.exe -X POST http://localhost:8001/api/skills/{skill_id}/sync
```

### 同步流程

```
开发环境                      MinIO                       生产环境
    │                           │                            │
    │ 1. 修改 skill 文件         │                            │
    │                           │                            │
    │ 2. python push_skills.py ─►│                            │
    │                           │                            │
    │                           │◄─ 3. 启动时自动同步 ─────────│
    │                           │                            │
```
