# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Skills Platform** - A full-stack application for managing AI skills and workflows.

- **Portal**: User-facing application for skills and workflows
- **Admin**: Management system for models, permissions, tokens, and monitoring
- **Unified Server**: Portal + Admin backend merged into single service

## Project Structure

```
ai-skills-platform/
│
├── portal/                        # 用户端 (Portal)
│   └── web/                       # Vue 3 前端
│       ├── src/
│       │   ├── api/               # API client
│       │   ├── components/        # Vue 组件
│       │   ├── views/             # 页面视图
│       │   ├── stores/            # Pinia 状态
│       │   └── config.ts          # 配置文件
│       ├── .env.development       # 开发环境配置
│       └── .env.production        # 生产环境配置
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
│   └── server/                    # 统一后端 (Portal + Admin)
│       ├── main.py                # 统一入口
│       ├── app/                   # Admin 核心
│       │   ├── api/v1/            # Admin API 路由
│       │   ├── core/              # 核心配置 (config.py, database.py)
│       │   └── models/            # Admin ORM 模型
│       ├── portal/                # Portal 代码
│       │   ├── routers/           # Portal API 路由
│       │   ├── services/          # Portal 业务逻辑
│       │   ├── models/            # Portal ORM 模型
│       │   └── schemas/           # Portal Pydantic 模式
│       ├── skills_storage/        # 技能文件存储
│       ├── outputs/               # 输出文件
│       ├── uploads/               # 上传文件
│       └── requirements.txt       # 合并后的依赖
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

### Admin Web (管理端前端)

```bash
cd admin/web

npm install          # 安装依赖
npm run dev          # 开发服务器 (localhost:5174)
npm run build        # 生产构建
```

### Unified Server (统一后端 - Portal + Admin)

```bash
cd admin/server

pip install -r requirements.txt    # 安装依赖
uvicorn main:app --reload          # 开发服务器 (localhost:8001)
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

## API Endpoints (Unified Server - port 8001)

### Portal API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST/PUT/DELETE | `/api/skills` | 技能 CRUD |
| GET/POST/PUT/DELETE | `/api/workflows` | 工作流 CRUD |
| POST | `/api/agent/chat` | AI 对话 |
| POST | `/api/agent/chat/stream` | AI 流式对话 |
| POST | `/api/agent/execute` | 执行技能 |
| GET/POST/PUT/DELETE | `/api/sessions` | 聊天会话 |
| GET/POST/DELETE | `/api/favorites` | 用户收藏 |
| GET/POST/PUT/DELETE | `/api/data-notes` | 数据便签 |
| WS | `/api/logs/ws` | 实时日志 WebSocket |

### Admin API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | 驾驶舱统计 |
| GET/POST/PUT/DELETE | `/api/models` | 模型配置 |
| GET | `/api/tokens/summary` | Token 用量统计 |
| GET/POST/PUT/DELETE | `/api/users` | 用户管理 |
| GET/POST/PUT/DELETE | `/api/permissions/roles` | 权限管理 |
| GET | `/api/logs` | 日志审计 |
| GET/POST/PUT | `/api/ccswitch` | Claude 配置热切换 |

### Static Files

| Path | Description |
|------|-------------|
| `/outputs/{filename}` | 输出文件下载 |
| `/uploads/{filename}` | 上传文件访问 |
| `/file-manage/{path}` | File Manage 文件访问 |
| `/storage/{category}/{path}` | 存储 API (MinIO/本地) |

## Environment Configuration

### Unified Server (.env)

```env
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ai_agent

# AI 模型 (Azure 代理)
ANTHROPIC_AUTH_TOKEN=your_azure_token
ANTHROPIC_BASE_URL=https://your-azure-proxy-url
CLAUDE_MODEL=claude-opus-4-5

# JWT
SECRET_KEY=your-secret-key

# 调试
DEBUG=true
```

### Portal Web (.env.development)

```env
VITE_APP_TITLE=AI Skills Platform (Dev)
VITE_API_BASE_URL=http://localhost:8001/api
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

### SSE Streaming
AI responses use Server-Sent Events. Frontend uses `AsyncGenerator` pattern in `agentApi.chatStream()`.

## Agent Architecture (Claude Agent SDK)

基于 Claude Agent SDK 的 Agent 服务，类似 Claude CLI 的工作方式：

### 核心原则
- **一切交给 SDK 处理**：不再遇事不决就调用 skill
- **不自动生成 skill**：去掉没有 skill 就自动生成的逻辑
- **直接用工具解决问题**：使用 SDK 内置工具（Bash, Read, Write, Edit, Glob, Grep）

### 工作流程
1. 用户发送请求到 `/api/agent/chat/stream`
2. AgentSDKService 构建系统提示，包含工作目录信息
3. Claude Agent SDK 自动使用工具完成任务
4. 流式返回结果给前端

### 可用工具
- **Bash**: 执行命令行操作
- **Read**: 读取文件内容
- **Write**: 创建或覆盖文件
- **Edit**: 编辑现有文件
- **Glob**: 按模式搜索文件
- **Grep**: 搜索文件内容

### 保留的技能功能
- 已存在的技能（有 main.py 或 SKILL.md）仍可通过 `/api/agent/execute` 执行
- 技能作为可复用的工具，而不是 AI 解决问题的唯一方式
