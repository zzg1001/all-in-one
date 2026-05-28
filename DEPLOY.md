# AI Skills Platform 部署指南

## 服务器要求

- Linux (CentOS/Ubuntu) 或 Windows Server / Windows Desktop
- Docker + Docker Compose
- 2GB+ 内存
- 开放端口: 80, 443, 3306(可选), 8001(可选)

---

## Windows Docker Desktop 部署

### 1. 安装 Docker Desktop

下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

确保：
- 启用 WSL 2 或 Hyper-V
- Docker Desktop 已启动并切换到 Linux 容器模式

### 2. 复制项目到本地

将项目文件夹复制到目标位置，例如：`D:\projects\ai-platform`

### 3. 配置环境变量

编辑 `deploy.env`：

```env
# 数据库
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root123456
DB_NAME=ai_agent

# AI 模型（必须修改）
ANTHROPIC_API_KEY=【你的 API Key】
ANTHROPIC_AUTH_TOKEN=【你的 API Key】
ANTHROPIC_BASE_URL=【你的 API 地址】
CLAUDE_MODEL=claude-opus-4-5

# JWT 密钥
SECRET_KEY=ai-skills-platform-secret-2024

# 跨域（本地测试）
CORS_ORIGINS_STR=["*"]

# 环境模式
DEBUG=false
```

### 4. 启动服务

```powershell
cd D:\projects\ai-platform
docker-compose -f docker-compose.prod.yml up -d --build
```

### 5. 初始化数据库

**首次部署必须执行**，确保数据库表结构与代码一致：

```powershell
# 方式一：通过 SQL 文件初始化（推荐）
docker cp backend/init_db.sql ai-mysql:/tmp/
docker exec ai-mysql mysql -uroot -proot123456 ai_agent -e "source /tmp/init_db.sql"

# 方式二：通过 Python 脚本
docker exec ai-backend python init_db.py

# 重启后端使配置生效
docker restart ai-backend
```

### 6. 访问地址

| 页面 | 地址 |
|------|------|
| 用户端 | http://localhost/ |
| 管理端 | http://localhost/admin/ |
| API 文档 | http://localhost/api/docs |

### 7. 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| superadmin | super123 | 超级管理员 |
| boss | boss123 | 领导 |
| test | test123 | 测试用户 |

---

## Linux 服务器部署

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
ANTHROPIC_API_KEY=【你的 API Key】
ANTHROPIC_AUTH_TOKEN=【你的 API Key】
ANTHROPIC_BASE_URL=https://your-azure-proxy-url
CLAUDE_MODEL=claude-opus-4-5

# JWT 密钥（64字符随机串）
SECRET_KEY=【生成随机密钥】

# 跨域（改为你的域名）
CORS_ORIGINS_STR=["https://your-domain.com"]
```

> 生成 SECRET_KEY：`python3 -c "import secrets; print(secrets.token_hex(32))"`

### 3. 配置域名

编辑 `nginx/conf.d/default.conf`，将 `infortest.ike-data.com` 替换为你的实际域名。

### 4. 启动服务

```bash
cd /opt/ai-platform
docker-compose -f docker-compose.prod.yml up -d --build
```

### 5. 初始化数据库

**首次部署必须执行**：

```bash
# 方式一：通过 SQL 文件初始化（推荐）
docker cp backend/init_db.sql ai-mysql:/tmp/
docker exec ai-mysql mysql -uroot -p【密码】 ai_agent -e "source /tmp/init_db.sql"

# 方式二：通过 Python 脚本
docker exec ai-backend python init_db.py

# 重启后端
docker restart ai-backend
```

---

## 服务说明

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| MySQL | ai-mysql | 3306 | 数据库 |
| Backend | ai-backend | 8001, 4000 | 后端 API + 代理 |
| Portal | ai-portal | - | 用户端前端 |
| Admin | ai-admin | - | 管理端前端 |
| Nginx | ai-nginx | 80 | 反向代理 |

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

# 完全重置（删除数据）
docker-compose -f docker-compose.prod.yml down -v

# 进入容器
docker exec -it ai-backend bash
docker exec -it ai-mysql mysql -uroot -p
```

---

## 数据库管理

### 初始化数据库（首次部署）

```bash
# 复制 SQL 到容器
docker cp backend/init_db.sql ai-mysql:/tmp/

# 执行初始化
docker exec ai-mysql mysql -uroot -proot123456 ai_agent -e "source /tmp/init_db.sql"

# 重启后端
docker restart ai-backend
```

### 更新数据库（表结构变更后）

如果代码更新后出现字段缺失错误，重新执行初始化：

```bash
# 注意：会清空所有数据，请先备份
docker cp backend/init_db.sql ai-mysql:/tmp/
docker exec ai-mysql mysql -uroot -proot123456 ai_agent -e "source /tmp/init_db.sql"
docker restart ai-backend
```

### 备份数据库

```bash
docker exec ai-mysql mysqldump -uroot -p【密码】 ai_agent > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
docker exec -i ai-mysql mysql -uroot -p【密码】 ai_agent < backup.sql
```

---

## 宿主机已有 Nginx 的部署

如果服务器上已经安装了 Nginx，需要让 Docker 内的 Nginx 使用非 80 端口。

### 1. 修改 Docker Nginx 端口

编辑 `docker-compose.prod.yml`，将 nginx 端口改为 8096：

```yaml
nginx:
  ports:
    - "8096:80"  # 改为非 80 端口
```

### 2. 配置宿主机 Nginx

创建配置文件 `/etc/nginx/conf.d/ai-platform.conf`：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 改为你的域名

    location / {
        proxy_pass http://127.0.0.1:8096;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式响应支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

### 3. 重载宿主机 Nginx

```bash
nginx -t && nginx -s reload
```

---

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

### 3. 修改端口映射

编辑 `docker-compose.prod.yml`：

```yaml
nginx:
  ports:
    - "80:80"
    - "443:443"  # 取消注释
```

### 4. 重启 Nginx

```bash
docker-compose -f docker-compose.prod.yml up -d nginx
```

---

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

---

## 故障排查

### 后端启动失败

```bash
# 查看详细日志
docker logs ai-backend

# 常见问题：
# 1. 数据库字段缺失 - 重新执行 init_db.sql
# 2. 数据库连接失败 - 检查 DB_HOST 和密码
# 3. 端口被占用 - 检查 8001 端口
```

### 数据库字段缺失错误

错误示例：`Unknown column 'skills.minio_synced' in 'field list'`

解决方法：
```bash
docker cp backend/init_db.sql ai-mysql:/tmp/
docker exec ai-mysql mysql -uroot -proot123456 ai_agent -e "source /tmp/init_db.sql"
docker restart ai-backend
```

### 前端页面空白

```bash
# 检查 Nginx 日志
docker logs ai-nginx

# 检查前端容器
docker logs ai-portal
docker logs ai-admin
```

### 登录失败

1. 确认使用正确的账号密码（admin / admin123）
2. 检查数据库是否已初始化
3. 查看后端日志：`docker logs ai-backend`

### 端口 80 被占用

```bash
# Windows
netstat -ano | findstr :80

# Linux
lsof -i :80
```

解决：修改 `docker-compose.prod.yml` 中 nginx 端口为其他值（如 8080）
