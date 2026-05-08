# AI Skills Platform 部署指南

## 服务器要求

- Linux (CentOS/Ubuntu) 或 Windows Server
- Docker + Docker Compose
- 2GB+ 内存
- 开放端口: 80, 443, 3306(可选)

## 快速部署

### 1. 上传代码到服务器

```bash
# 目录结构
/opt/ai-platform/
├── backend/
├── frontend/
├── nginx/
├── deploy.env
└── docker-compose.prod.yml
```

### 2. 配置环境变量

编辑 `deploy.env`：

```env
# 数据库
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=【修改为强密码】
DB_NAME=ai_agent
DB_ROOT_PASSWORD=【修改为强密码】

# AI 模型
ANTHROPIC_AUTH_TOKEN=【你的 Azure Token】
ANTHROPIC_BASE_URL=https://your-azure-proxy-url
CLAUDE_MODEL=claude-opus-4-5

# JWT 密钥（64字符随机串）
SECRET_KEY=【生成随机密钥】

# 跨域（改为你的域名）
CORS_ORIGINS=["https://your-domain.com"]
```

> 生成 SECRET_KEY：`python3 -c "import secrets; print(secrets.token_hex(32))"`

### 3. 配置域名

编辑 `nginx/conf.d/default.conf`，将 `your-domain.com` 替换为你的实际域名。

### 4. 启动服务

```bash
cd /opt/ai-platform
docker-compose -f docker-compose.prod.yml up -d --build
```

### 5. 初始化数据库

首次部署需要初始化：

```bash
# 进入后端容器
docker exec -it ai-backend bash

# 执行初始化
python init_db.py
```

**默认账号：**

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| boss | boss123 | 领导 |
| test | test123 | 测试用户 |

## 服务说明

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| MySQL | ai-mysql | 3306 | 数据库 |
| Backend | ai-backend | 8001 | 后端 API |
| Portal | ai-portal | - | 用户端前端 |
| Admin | ai-admin | - | 管理端前端 |
| Nginx | ai-nginx | 80/443 | 反向代理 |

## 访问地址

| 页面 | 地址 |
|------|------|
| 用户端 | http://your-domain.com/ |
| 管理端 | http://your-domain.com/admin |
| API 文档 | http://your-domain.com/api/docs |

## 常用命令

```bash
# 查看所有容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker logs -f ai-backend      # 后端日志
docker logs -f ai-nginx        # Nginx 日志
docker logs -f ai-mysql        # 数据库日志

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 进入容器
docker exec -it ai-backend bash
docker exec -it ai-mysql mysql -uroot -p
```

## HTTPS 配置（可选）

### 1. 准备 SSL 证书

将证书文件放到 `nginx/ssl/` 目录：
- `your-domain.com.pem` (证书)
- `your-domain.com.key` (私钥)

### 2. 启用 HTTPS

编辑 `nginx/conf.d/default.conf`：

1. 取消 HTTPS server 块的注释
2. 修改证书文件名
3. 取消 HTTP 强制跳转的注释

### 3. 重启 Nginx

```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

## Skills 同步（MinIO）

如需多节点同步 Skills，配置 MinIO：

```env
# deploy.env 添加
MINIO_ENDPOINT=your-minio-server
MINIO_PORT=9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=yourpassword
MINIO_SECURE=false
MINIO_SKILLS_BUCKET=ai-skills
```

```bash
# 推送 Skills 到 MinIO
docker exec ai-backend python push_skills.py

# 从 MinIO 拉取 Skills
docker exec ai-backend curl -X POST http://localhost:8001/api/skills/sync-all
```

## 故障排查

### 后端启动失败

```bash
# 查看详细日志
docker logs ai-backend

# 常见问题：
# 1. 数据库连接失败 - 检查 DB_HOST 和密码
# 2. 端口被占用 - 检查 8001 端口
```

### 前端页面空白

```bash
# 检查 Nginx 日志
docker logs ai-nginx

# 检查前端容器
docker logs ai-portal
docker logs ai-admin
```

### 数据库连接失败

```bash
# 检查 MySQL 状态
docker logs ai-mysql

# 测试连接
docker exec ai-mysql mysql -uroot -p -e "SHOW DATABASES;"
```

## 备份与恢复

### 备份数据库

```bash
docker exec ai-mysql mysqldump -uroot -p【密码】 ai_agent > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
docker exec -i ai-mysql mysql -uroot -p【密码】 ai_agent < backup.sql
```

### 备份 Skills

```bash
tar -czvf skills_backup.tar.gz backend/skills_storage/
```
