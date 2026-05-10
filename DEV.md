# 开发环境命令手册

## 快速开始

| 模式 | 说明 | 命令 |
|------|------|------|
| **本地开发** | 数据库 Docker，代码本地运行 | 见下方「本地开发」 |
| **Docker 开发** | 全部服务 Docker 运行 | `docker compose --profile frontend up -d` |


========================================
# 本地开发
========================================

> 推荐方式：数据库用 Docker，后端和前端本地运行，支持热更新和断点调试

## 1. 启动数据库

```bash
docker compose up -d mysql
```

## 2. 启动后端

```bash
cd backend
pip install -r requirements.txt    # 首次需要
uvicorn main:app --reload --port 8001
```

## 3. 启动前端

**用户端：**
```bash
cd frontend/portal
npm install    # 首次需要
npm run dev    # http://localhost:5173
```

**管理端：**
```bash
cd frontend/admin
npm install    # 首次需要
npm run dev    # http://localhost:5174
```

## 4. 环境配置

`backend/.env` 配置：
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root123456
DB_NAME=ai_agent
```

## 5. 初始化数据库

```bash
cd backend
python init_db.py
```


========================================
# Docker 开发
========================================

> 全部服务运行在 Docker 中，适合测试完整环境或部署

## 启动服务

```bash
# 后端 + 数据库
docker compose up -d

# 全部服务（含前端）
docker compose --profile frontend up -d

# 全部服务（含 Nginx）
docker compose --profile frontend --profile gateway up -d
```

## 单独启动

```bash
docker compose up -d mysql
docker compose up -d backend
docker compose --profile frontend up -d portal-web
docker compose --profile frontend up -d admin-web
```

## 重新构建

```bash
# 重建后端
docker compose up -d --build backend

# 重建用户端前端
docker compose --profile frontend up -d --build portal-web

# 重建管理端前端
docker compose --profile frontend up -d --build admin-web

# 强制重建（不用缓存）
docker compose build --no-cache backend && docker compose up -d backend
```

## 停止服务

```bash
docker compose down              # 停止所有
docker compose down -v           # 停止并删除数据（慎用！）
docker compose stop backend      # 停止单个
```

## 查看日志

```bash
docker logs -f all-in-one-backend-1       # 后端
docker logs -f all-in-one-mysql-1         # MySQL
docker logs -f all-in-one-portal-web-1    # 用户端
docker logs -f all-in-one-admin-web-1     # 管理端

docker logs --tail 100 all-in-one-backend-1   # 最近100行
```

## 查看状态

```bash
docker compose ps        # 运行中的容器
docker compose ps -a     # 所有容器
docker stats             # 资源使用
```

## 进入容器

```bash
docker exec -it all-in-one-backend-1 /bin/bash
docker exec -it all-in-one-mysql-1 /bin/bash
```


========================================
# 数据库操作
========================================

```bash
# 执行 SQL
docker exec all-in-one-mysql-1 mysql -uroot -proot123456 ai_agent -e "SHOW TABLES;"

# 导出
docker exec all-in-one-mysql-1 mysqldump -uroot -proot123456 ai_agent > backup.sql

# 导入
docker exec -i all-in-one-mysql-1 mysql -uroot -proot123456 ai_agent < backup.sql
```


========================================
# 访问地址
========================================

| 服务 | 地址 |
|------|------|
| 用户端 Portal | http://localhost:5173 |
| 管理端 Admin | http://localhost:5174 |
| 后端 API | http://localhost:8001 |
| API 文档 | http://localhost:8001/docs |


========================================
# 日志文件
========================================

```bash
# 宿主机日志目录
tail -f logs/app_$(date +%Y%m%d).log
```
