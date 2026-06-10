-- ============================================
-- AI Skills Platform 数据库初始化脚本
-- 执行：python init_db.py
-- 或：mysql -h localhost -P 3306 -u root -p ai_agent < init_db.sql
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 用户表
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` varchar(36) NOT NULL,
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password_hash` varchar(128) NOT NULL COMMENT '密码哈希',
  `display_name` varchar(100) DEFAULT NULL COMMENT '显示名称',
  `department` varchar(50) DEFAULT NULL COMMENT '部门',
  `role` varchar(20) NOT NULL DEFAULT 'user' COMMENT '角色: user/boss/admin',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Claude 配置表
DROP TABLE IF EXISTS `cc_configs`;
CREATE TABLE `cc_configs` (
  `id` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL COMMENT '配置名称',
  `description` varchar(500) DEFAULT NULL COMMENT '配置描述',
  `api_type` varchar(20) DEFAULT 'claude_sdk' COMMENT 'API类型',
  `model_id` varchar(50) NOT NULL COMMENT '模型ID',
  `api_key` varchar(500) NOT NULL COMMENT 'API Key',
  `base_url` varchar(200) DEFAULT NULL COMMENT '自定义 Base URL',
  `max_tokens` int DEFAULT 4096 COMMENT '最大 Token 数',
  `temperature` float DEFAULT 0.7 COMMENT '温度参数',
  `top_p` float DEFAULT 1.0 COMMENT 'Top P 参数',
  `system_prompt` text COMMENT '系统提示词',
  `extra_params` text COMMENT '额外参数 JSON',
  `is_active` tinyint(1) DEFAULT 0 COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. API 代理配置表
DROP TABLE IF EXISTS `proxy_configs`;
CREATE TABLE `proxy_configs` (
  `id` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL COMMENT '配置名称',
  `description` varchar(500) DEFAULT NULL COMMENT '配置描述',
  `proxy_type` varchar(50) DEFAULT 'anthropic_to_openai' COMMENT '代理类型',
  `target_base_url` varchar(500) NOT NULL COMMENT '目标 API Base URL',
  `target_api_key` varchar(500) NOT NULL COMMENT '目标 API Key',
  `target_model` varchar(100) NOT NULL COMMENT '目标模型 ID',
  `proxy_port` int DEFAULT 4000 COMMENT '代理监听端口',
  `proxy_path` varchar(100) DEFAULT '/v1/messages' COMMENT '代理路径',
  `proxy_url` varchar(500) DEFAULT NULL COMMENT '代理地址',
  `proxy_model` varchar(100) DEFAULT NULL COMMENT '对外模型名',
  `max_tokens` int DEFAULT 4096 COMMENT '默认最大 Token',
  `temperature` float DEFAULT 0.7 COMMENT '默认温度',
  `is_enabled` tinyint(1) DEFAULT 0 COMMENT '是否启用',
  `is_running` tinyint(1) DEFAULT 0 COMMENT '是否正在运行',
  `pid` int DEFAULT NULL COMMENT '运行中的进程PID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 技能表
DROP TABLE IF EXISTS `skills`;
CREATE TABLE `skills` (
  `id` varchar(36) NOT NULL,
  `group_id` varchar(36) NOT NULL COMMENT '版本组ID',
  `name` varchar(100) NOT NULL,
  `description` text,
  `icon` varchar(50) DEFAULT '⚡',
  `tags` json DEFAULT NULL,
  `folder_path` varchar(255) DEFAULT NULL COMMENT '技能文件夹相对路径',
  `entry_script` varchar(100) DEFAULT 'main.py' COMMENT '入口脚本',
  `author` varchar(50) DEFAULT NULL,
  `version` varchar(20) DEFAULT '1.0.0',
  `status` varchar(20) NOT NULL DEFAULT 'active',
  `interactions` json DEFAULT NULL COMMENT '交互配置',
  `output_config` json DEFAULT NULL COMMENT '输出文件配置',
  `original_created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '原始创建时间',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `minio_synced` tinyint(1) DEFAULT 0 COMMENT '是否已同步到 MinIO',
  `deleted_at` datetime DEFAULT NULL COMMENT '软删除时间戳',
  PRIMARY KEY (`id`),
  KEY `idx_skills_deleted` (`deleted_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 工作流表
DROP TABLE IF EXISTS `workflows`;
CREATE TABLE `workflows` (
  `id` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `icon` varchar(50) DEFAULT NULL,
  `nodes` json DEFAULT NULL,
  `edges` json DEFAULT NULL,
  `input_count` int DEFAULT 0,
  `output_type` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 工作流执行表
DROP TABLE IF EXISTS `workflow_executions`;
CREATE TABLE `workflow_executions` (
  `id` varchar(50) NOT NULL,
  `workflow_id` varchar(50) NOT NULL,
  `status` varchar(20) DEFAULT 'pending',
  `current_step` int DEFAULT 0,
  `total_steps` int DEFAULT 0,
  `context` json DEFAULT NULL,
  `pending_interaction` json DEFAULT NULL,
  `completed_steps` json DEFAULT NULL,
  `error` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 用户收藏表
DROP TABLE IF EXISTS `user_favorites`;
CREATE TABLE `user_favorites` (
  `id` varchar(50) NOT NULL,
  `user_id` varchar(50) NOT NULL,
  `item_type` varchar(20) NOT NULL,
  `item_id` varchar(50) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_favorite` (`user_id`,`item_type`,`item_id`),
  KEY `idx_user_favorites` (`user_id`,`item_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 数据笔记表
DROP TABLE IF EXISTS `user_data_notes`;
CREATE TABLE `user_data_notes` (
  `id` varchar(50) NOT NULL,
  `user_id` varchar(50) NOT NULL,
  `agent_id` varchar(36) DEFAULT NULL COMMENT '关联的 Agent ID',
  `name` varchar(100) NOT NULL,
  `description` text,
  `file_type` varchar(20) NOT NULL,
  `file_url` varchar(500) DEFAULT NULL,
  `file_size` varchar(20) DEFAULT NULL,
  `source_skill` varchar(100) DEFAULT NULL,
  `is_favorited` tinyint(1) DEFAULT 0,
  `parent_id` varchar(50) DEFAULT NULL COMMENT '父文件夹ID',
  `level` int DEFAULT 0 COMMENT '层级',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL COMMENT '软删除时间戳',
  PRIMARY KEY (`id`),
  KEY `idx_data_notes_user` (`user_id`),
  KEY `idx_data_notes_agent` (`agent_id`),
  KEY `idx_data_notes_parent` (`parent_id`),
  KEY `idx_data_notes_deleted` (`deleted_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. 聊天会话表
DROP TABLE IF EXISTS `chat_sessions`;
CREATE TABLE `chat_sessions` (
  `id` varchar(36) NOT NULL,
  `user_id` varchar(50) NOT NULL DEFAULT 'default',
  `title` varchar(200) DEFAULT NULL COMMENT '会话标题',
  `message_count` int DEFAULT 0,
  `skill_names` json DEFAULT NULL,
  `last_message_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sessions_user` (`user_id`),
  KEY `idx_sessions_user_time` (`user_id`,`last_message_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. 聊天消息表
DROP TABLE IF EXISTS `chat_messages`;
CREATE TABLE `chat_messages` (
  `id` varchar(36) NOT NULL,
  `session_id` varchar(36) NOT NULL,
  `role` varchar(10) NOT NULL COMMENT 'user / agent',
  `content` text NOT NULL,
  `extra_data` json DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_messages_session` (`session_id`),
  KEY `idx_messages_session_time` (`session_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Agent 主表
DROP TABLE IF EXISTS `agents`;
CREATE TABLE `agents` (
  `id` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `icon` varchar(50) DEFAULT '🤖',
  `category` varchar(50) DEFAULT '通用助手',
  `system_prompt` text,
  `model` varchar(100) NOT NULL DEFAULT 'claude-opus-4-5',
  `temperature` float NOT NULL DEFAULT 0.7,
  `max_tokens` int NOT NULL DEFAULT 4096,
  `tools` json DEFAULT NULL,
  `skills` json DEFAULT NULL,
  `module_configs` json DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'draft',
  `author` varchar(100) DEFAULT 'User',
  `version` varchar(20) DEFAULT '1.0.0',
  `usage_count` int NOT NULL DEFAULT 0,
  `accessible_agent_ids` json DEFAULT NULL COMMENT '可访问的其他 Agent ID 列表',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Agent 记忆表
DROP TABLE IF EXISTS `agent_memories`;
CREATE TABLE `agent_memories` (
  `id` varchar(36) NOT NULL,
  `agent_id` varchar(36) NOT NULL,
  `memory_type` varchar(50) NOT NULL DEFAULT 'conversation',
  `content` text NOT NULL,
  `extra_data` json DEFAULT NULL,
  `embedding` json DEFAULT NULL,
  `embedding_model` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_memories_agent` (`agent_id`),
  CONSTRAINT `fk_memories_agent` FOREIGN KEY (`agent_id`) REFERENCES `agents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Agent 执行记录表
DROP TABLE IF EXISTS `agent_executions`;
CREATE TABLE `agent_executions` (
  `id` varchar(36) NOT NULL,
  `agent_id` varchar(36) NOT NULL,
  `execution_type` varchar(50) NOT NULL DEFAULT 'chat',
  `status` varchar(20) NOT NULL DEFAULT 'running',
  `input_data` json DEFAULT NULL,
  `output_data` json DEFAULT NULL,
  `modules_used` json DEFAULT NULL,
  `module_metrics` json DEFAULT NULL,
  `input_tokens` int DEFAULT 0,
  `output_tokens` int DEFAULT 0,
  `total_tokens` int DEFAULT 0,
  `latency_ms` float DEFAULT NULL,
  `error_message` text,
  `started_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_executions_agent` (`agent_id`),
  CONSTRAINT `fk_executions_agent` FOREIGN KEY (`agent_id`) REFERENCES `agents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. 用户反馈表
DROP TABLE IF EXISTS `user_feedbacks`;
CREATE TABLE `user_feedbacks` (
  `id` varchar(50) NOT NULL,
  `user_id` varchar(50) NOT NULL,
  `session_id` varchar(50) DEFAULT NULL,
  `agent_id` varchar(50) DEFAULT NULL,
  `agent_name` varchar(100) DEFAULT NULL,
  `feedback_type` varchar(20) NOT NULL COMMENT 'bug/suggestion/other',
  `title` varchar(200) NOT NULL,
  `description` text,
  `status` varchar(20) DEFAULT 'pending',
  `admin_notes` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_feedback_user` (`user_id`),
  KEY `idx_feedback_user_status` (`user_id`,`status`),
  KEY `idx_feedback_status_created` (`status`,`created_at`),
  KEY `idx_feedback_agent` (`agent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 初始化数据
-- ============================================

-- 1. 创建管理员账号（密码: admin123）
INSERT INTO `users` (`id`, `username`, `password_hash`, `display_name`, `department`, `role`, `is_active`, `created_at`) VALUES
('admin-001', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYxCBpoE16Qy', '系统管理员', NULL, 'admin', 1, NOW());

-- 2. 创建超级管理员账号（密码: super123）
INSERT INTO `users` (`id`, `username`, `password_hash`, `display_name`, `department`, `role`, `is_active`, `created_at`) VALUES
('admin-002', 'superadmin', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', '超级管理员', NULL, 'admin', 1, NOW());

-- 3. 创建 Boss 账号（密码: boss123）
INSERT INTO `users` (`id`, `username`, `password_hash`, `display_name`, `department`, `role`, `is_active`, `created_at`) VALUES
('boss-001', 'boss', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', '张总', NULL, 'boss', 1, NOW());

-- 4. 创建测试用户（密码: test123）
INSERT INTO `users` (`id`, `username`, `password_hash`, `display_name`, `department`, `role`, `is_active`, `created_at`) VALUES
('user-001', 'test', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', '测试用户', 'HR', 'user', 1, NOW());

-- 5. 创建默认 Agent
INSERT INTO `agents` (`id`, `name`, `description`, `icon`, `category`, `system_prompt`, `model`, `temperature`, `max_tokens`, `tools`, `skills`, `status`, `author`, `version`, `accessible_agent_ids`, `created_at`) VALUES
('default-agent-001', '通用助手', '一个通用的AI助手，可以回答问题、帮助完成任务', '🤖', '通用助手', '你是一个友好、专业的AI助手。请用简洁、准确的方式回答用户的问题。', 'claude-opus-4-5', 0.7, 4096, '[]', '[]', 'active', 'System', '1.0.0', '["*"]', NOW());

-- 完成
SELECT '数据库初始化完成！' AS message;
SELECT COUNT(*) AS user_count FROM users;
SELECT COUNT(*) AS agent_count FROM agents;
