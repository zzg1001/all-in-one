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
├── docker-compose.yml             # Docker 编排 (开发环境)
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
# 只启动后端 + 数据库（开发常用）
docker-compose up -d mysql backend

# 启动全部服务（包含前端）
docker-compose --profile frontend up -d

# 查看后端日志
docker-compose logs -f backend

# 重新构建后端镜像（代码改动后）
docker-compose build backend && docker-compose up -d backend

# 停止所有服务
docker-compose down

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

### Proxy API（API 代理服务）
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/proxy/configs` | 获取所有代理配置 |
| POST | `/api/proxy/configs` | 创建代理配置 |
| PUT | `/api/proxy/configs/{id}` | 更新代理配置 |
| DELETE | `/api/proxy/configs/{id}` | 删除代理配置 |
| POST | `/api/proxy/configs/{id}/start` | 启动代理服务（独立进程） |
| POST | `/api/proxy/configs/{id}/stop` | 停止代理服务 |
| GET | `/api/proxy/status` | 获取代理运行状态 |
| POST | `/api/proxy/test-connection` | 测试 API 连接 |

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

## API Proxy（API 代理功能）

将 Anthropic Claude SDK 请求代理转发到其他模型（如阿里云 DashScope Qwen）。

### 工作原理
1. 启动独立代理进程，监听指定端口（如 4000）
2. 接收 Anthropic API 格式请求
3. 转换为目标 API 格式（OpenAI 或 Anthropic 兼容）
4. 返回 Anthropic 格式响应

### 使用方式
1. 在 Admin 管理端 → 模型配置 → API 代理 标签页
2. 创建代理配置（设置目标 API 地址、API Key、模型）
3. 点击"启动代理"
4. 在模型配置中使用代理：
   - Base URL: `http://localhost:4000`（代理端口）
   - Model: 代理配置中的对外模型名

### 代理配置字段
| 字段 | 说明 |
|------|------|
| proxy_port | 代理监听端口（默认 4000） |
| proxy_model | 对外模型名（如 claude-sonnet-4-20250514） |
| target_base_url | 原始 API 地址（如 https://dashscope.aliyuncs.com/apps/anthropic） |
| target_api_key | 原始 API Key |
| target_model | 原始模型名（如 qwen-plus） |

### 进程管理
- PID 持久化到数据库，后端重启后可恢复管理
- 自动清理孤儿进程
- 使用 psutil 库进行跨平台进程管理
