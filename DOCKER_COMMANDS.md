# Docker 常用命令

## 启动服务

```bash
# 启动后端 + MySQL（开发常用）
docker compose up -d

# 启动全部服务（含前端）
docker compose --profile frontend up -d

# 启动全部服务（含 Nginx 网关）
docker compose --profile frontend --profile gateway up -d

# 单独启动某个服务
docker compose up -d mysql
docker compose up -d backend
docker compose --profile frontend up -d portal-web
docker compose --profile frontend up -d admin-web
```

## 重新构建

```bash
# 重新构建后端（代码更新后）
docker compose up -d --build backend

# 重新构建前端
docker compose --profile frontend up -d --build portal-web admin-web

# 强制重新构建（不使用缓存）
docker compose build --no-cache backend
docker compose up -d backend
```

## 查看日志

```bash
# 查看后端日志
docker logs all-in-one-backend-1

# 实时查看后端日志
docker logs -f all-in-one-backend-1

# 查看最近 100 行日志
docker logs all-in-one-backend-1 --tail 100

# 查看 MySQL 日志
docker logs all-in-one-mysql-1

# 查看前端日志
docker logs all-in-one-portal-web-1
docker logs all-in-one-admin-web-1
```

## 停止服务

```bash
# 停止所有服务
docker compose down

# 停止并删除数据卷（慎用！会删除数据库数据）
docker compose down -v

# 停止单个服务
docker compose stop backend
```

## 进入容器

```bash
# 进入后端容器
docker exec -it all-in-one-backend-1 /bin/bash

# 进入 MySQL 容器
docker exec -it all-in-one-mysql-1 /bin/bash

# 直接执行 MySQL 命令
docker exec all-in-one-mysql-1 mysql -uroot -proot123456 ai_agent -e "SHOW TABLES;"
```

## 查看状态

```bash
# 查看运行中的容器
docker compose ps

# 查看所有容器（包括已停止的）
docker compose ps -a

# 查看容器资源使用
docker stats
```

## 日志文件位置

后端日志文件保存在宿主机 `./logs/` 目录下：
- `app_YYYYMMDD.log` - 按日期的应用日志

```bash
# 直接查看宿主机日志文件
cat logs/app_20260429.log

# 实时查看
tail -f logs/app_20260429.log
```

## 数据库操作

```bash
# 导出数据库
docker exec all-in-one-mysql-1 mysqldump -uroot -proot123456 ai_agent > backup.sql

# 导入数据库
docker exec -i all-in-one-mysql-1 mysql -uroot -proot123456 ai_agent < backup.sql
```
