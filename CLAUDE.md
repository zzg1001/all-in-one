# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Skills Platform** - A full-stack application for managing AI skills and workflows, with a separate admin system for management.

- **Portal**: User-facing application for skills and workflows
- **Admin**: Management system for models, permissions, tokens, and monitoring

## Project Structure

```
ai-skills-platform/
│
├── portal/                        # 用户端 (Portal)
│   ├── web/                       # Vue 3 前端
│   │   ├── src/
│   │   │   ├── api/               # API client
│   │   │   ├── components/        # Vue 组件
│   │   │   ├── views/             # 页面视图
│   │   │   ├── stores/            # Pinia 状态
│   │   │   └── config.ts          # 配置文件
│   │   ├── .env.development       # 开发环境配置
│   │   └── .env.production        # 生产环境配置
│   │
│   └── server/                    # FastAPI 后端
│       ├── main.py                # 入口
│       ├── config.py              # 配置
│       ├── models/                # ORM 模型
│       ├── schemas/               # Pydantic 模式
│       ├── services/              # 业务逻辑
│       ├── routers/               # API 路由
│       ├── skills_storage/        # 技能文件存储
│       ├── .env                   # 环境配置
│       └── .env.example           # 配置模板
│
├── admin/                         # 管理端 (Admin)
│   ├── web/                       # Vue 3 前端
│   │   ├── src/
│   │   │   ├── api/               # API client
│   │   │   ├── views/             # 页面 (dashboard, models, etc.)
│   │   │   └── config.ts          # 配置
│   │   ├── .env.development
│   │   └── .env.production
│   │
│   └── server/                    # FastAPI 后端
│       ├── main.py
│       ├── app/
│       │   ├── api/v1/            # API 路由
│       │   ├── core/              # 核心配置
│       │   ├── models/            # ORM 模型
│       │   └── schemas/           # Pydantic 模式
│       └── .env.example
│
├── nginx/                         # Nginx 配置
├── docker-compose.yml             # Docker 编排
└── docker-compose.dev.yml         # 开发环境 (仅数据库)
```

## Commands

### Portal Web (用户端前端)

```bash
cd portal/web

npm install          # 安装依赖
npm run dev          # 开发服务器 (localhost:5173)
npm run build        # 生产构建
npm run type-check   # 类型检查
npm run lint         # 代码检查
npm run format       # 代码格式化
```

### Portal Server (用户端后端)

```bash
cd portal/server

pip install -r requirements.txt    # 安装依赖
uvicorn main:app --reload          # 开发服务器 (localhost:8000)
```

### Admin Web (管理端前端)

```bash
cd admin/web

npm install          # 安装依赖
npm run dev          # 开发服务器 (localhost:5174)
npm run build        # 生产构建
```

### Admin Server (管理端后端)

```bash
cd admin/server

pip install -r requirements.txt    # 安装依赖
uvicorn main:app --reload --port 8001    # 开发服务器 (localhost:8001)
```

### Docker 部署

```bash
# 开发环境 - 仅启动数据库
docker-compose -f docker-compose.dev.yml up -d

# 生产环境 - 启动所有服务
docker-compose up -d

# 带 Nginx 网关
docker-compose --profile gateway up -d
```

## Tech Stack

### Frontend (Vue 3)
- **Framework**: Vue 3 (Composition API, `<script setup>`)
- **Build**: Vite 6+
- **State**: Pinia
- **Router**: Vue Router 4
- **Language**: TypeScript

### Backend (FastAPI)
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: MySQL 8+ (via PyMySQL)
- **AI**: Anthropic Claude SDK
- **Validation**: Pydantic v2

## API Endpoints

### Portal API (port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST/PUT/DELETE | `/api/skills` | 技能 CRUD |
| GET/POST/PUT/DELETE | `/api/workflows` | 工作流 CRUD |
| POST | `/api/agent/chat` | AI 对话 |
| POST | `/api/agent/chat/stream` | AI 流式对话 |
| POST | `/api/agent/execute` | 执行技能 |

### Admin API (port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | 驾驶舱统计 |
| GET/POST/PUT/DELETE | `/api/models` | 模型配置 |
| GET | `/api/tokens/summary` | Token 用量统计 |
| GET/POST/PUT/DELETE | `/api/users` | 用户管理 |
| GET/POST/PUT/DELETE | `/api/permissions/roles` | 权限管理 |
| GET | `/api/logs` | 日志审计 |

## Environment Configuration

### Portal Server (.env)

```env
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=product_background

# AI 模型
ANTHROPIC_API_KEY=your_key
ANTHROPIC_BASE_URL=        # Azure 代理 URL (可选)
CLAUDE_MODEL=claude-opus-4-5

# 调试
DEBUG=true
```

### Portal Web (.env.development)

```env
VITE_APP_TITLE=AI Skills Platform (Dev)
VITE_API_BASE_URL=http://localhost:8000/api
```

### Admin Server (.env)

```env
# 数据库 (与 Portal 共享)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=product_background

# JWT
SECRET_KEY=your-secret-key
```

### Admin Web (.env.development)

```env
VITE_APP_TITLE=AI Skills Admin (Dev)
VITE_API_BASE_URL=http://localhost:8001/api
```

## Key Patterns

### Vue Reactivity
```typescript
// Don't: messages.value[i].skillPlan = plan
// Do: messages.value[i] = { ...messages.value[i], skillPlan: plan }
```

### AI Skill Planning
```
<!--SKILL_PLAN:[{"skill":"skill-name","action":"description","exists":true/false}]-->
```

### SSE Streaming
AI responses use Server-Sent Events. Frontend uses `AsyncGenerator` pattern in `agentApi.chatStream()`.
