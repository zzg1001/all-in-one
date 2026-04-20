# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Skills Platform** - A full-stack application for managing AI skills and workflows.

## Project Structure

```
ai-skills-platform/
│
├── frontend/                      # 前端项目
│   ├── portal/                    # 用户端 Vue 3 应用 (localhost:5173)
│   │   ├── src/
│   │   │   ├── api/               # API client
│   │   │   ├── components/        # Vue 组件
│   │   │   ├── views/             # 页面视图
│   │   │   ├── stores/            # Pinia 状态
│   │   │   ├── layouts/           # 布局组件
│   │   │   └── config.ts          # 配置文件
│   │   └── .env.development
│   │
│   └── admin/                     # 管理端 Vue 3 应用 (localhost:5174)
│       ├── src/
│       │   ├── api/
│       │   ├── views/
│       │   └── config.ts
│       └── .env.development
│
├── backend/                       # 后端项目 (localhost:8001)
│   ├── main.py                    # 统一入口
│   ├── app/                       # Admin API 核心
│   │   ├── api/v1/                # Admin API 路由
│   │   ├── core/                  # 核心配置
│   │   └── models/                # ORM 模型
│   ├── portal/                    # Portal API
│   │   ├── routers/               # Portal API 路由
│   │   ├── services/              # 业务逻辑
│   │   └── schemas/               # Pydantic 模式
│   ├── nginx/                     # Nginx 配置
│   ├── skills_storage/            # 技能存储
│   ├── outputs/                   # 输出文件
│   ├── uploads/                   # 上传文件
│   └── requirements.txt
│
├── docker-compose.yml             # Docker 编排
├── docker-compose.dev.yml         # 开发环境 (仅数据库)
├── docker-compose.prod.yml        # 生产环境
├── deploy.env                     # 环境变量
└── CLAUDE.md
```

## Commands

### Frontend - Portal

```bash
cd frontend/portal
npm install && npm run dev     # localhost:5173
```

### Frontend - Admin

```bash
cd frontend/admin
npm install && npm run dev     # localhost:5174
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Docker

```bash
# 开发环境 - 仅数据库
docker-compose -f docker-compose.dev.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

## Tech Stack

### Frontend
- Vue 3 + Composition API + `<script setup>`
- Vite 6+ / TypeScript / Pinia / Vue Router 4

### Backend
- FastAPI / SQLAlchemy 2.0 / MySQL 8+ / Pydantic v2
- Anthropic Claude SDK

## API Endpoints (port 8001)

### Portal API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST/PUT/DELETE | `/api/skills` | 技能 CRUD |
| GET/POST/PUT/DELETE | `/api/workflows` | 工作流 CRUD |
| POST | `/api/agent/chat/stream` | AI 流式对话 |
| POST | `/api/agent/execute` | 执行技能 |
| GET/POST/PUT/DELETE | `/api/sessions` | 聊天会话 |
| GET/POST/DELETE | `/api/favorites` | 用户收藏 |

### Admin API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | 驾驶舱统计 |
| GET/POST/PUT/DELETE | `/api/models` | 模型配置 |
| GET/POST/PUT/DELETE | `/api/users` | 用户管理 |
| GET/POST/PUT/DELETE | `/api/permissions/roles` | 权限管理 |

## Environment Configuration

### Backend (.env)
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ai_agent

ANTHROPIC_AUTH_TOKEN=your_azure_token
ANTHROPIC_BASE_URL=https://your-azure-proxy-url
CLAUDE_MODEL=claude-opus-4-5

SECRET_KEY=your-secret-key
DEBUG=true
```

### Frontend (.env.development)
```env
VITE_APP_TITLE=AI Skills Platform
VITE_API_BASE_URL=http://localhost:8001/api
```

## Key Patterns

### Vue Reactivity
```typescript
// Don't: messages.value[i].skillPlan = plan
// Do: messages.value[i] = { ...messages.value[i], skillPlan: plan }
```

### SSE Streaming
AI responses use Server-Sent Events via `agentApi.chatStream()`.

## Agent Architecture

基于 Claude Agent SDK，使用内置工具（Bash, Read, Write, Edit, Glob, Grep）直接解决问题。
