-- ============================================
-- AI Skills Platform - 数据库表结构
-- 数据库: MySQL 8.0+
-- 字符集: utf8mb4
-- ============================================

-- 删除旧表（按依赖顺序）
DROP TABLE IF EXISTS `user_data_notes`;
DROP TABLE IF EXISTS `workflow_executions`;
DROP TABLE IF EXISTS `workflows`;
DROP TABLE IF EXISTS `skills`;

-- ============================================
-- 1. 技能表 (skills)
-- 基本信息存数据库，脚本文件存文件系统
-- ============================================
CREATE TABLE `skills` (
    `id` VARCHAR(36) NOT NULL COMMENT '技能ID (UUID)',
    `group_id` VARCHAR(36) NOT NULL COMMENT '版本组ID（同一技能的所有版本共用）',
    `name` VARCHAR(100) NOT NULL COMMENT '技能名称',
    `description` TEXT COMMENT '技能描述',
    `icon` VARCHAR(50) DEFAULT '⚡' COMMENT '图标（emoji或图标名）',
    `tags` JSON COMMENT '标签列表，如 ["Expert", "Public"]',
    `folder_path` VARCHAR(255) COMMENT '技能文件夹相对路径',
    `entry_script` VARCHAR(100) DEFAULT 'main.py' COMMENT '入口脚本文件名',
    `author` VARCHAR(50) COMMENT '作者',
    `version` VARCHAR(20) DEFAULT '1.0.0' COMMENT '版本号',
    `status` ENUM('active', 'deprecated') DEFAULT 'active' COMMENT '状态：active=当前版本，deprecated=历史版本',
    `interactions` JSON COMMENT '交互配置列表',
    `output_config` JSON COMMENT '输出文件配置: {enabled: bool, preferred_type: string, filename_template: string}',
    `original_created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '原始创建时间（首个版本的创建时间，用于排序）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '本版本创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_skills_group_id` (`group_id`),
    INDEX `idx_skills_name` (`name`),
    INDEX `idx_skills_status` (`status`),
    INDEX `idx_skills_original_created_at` (`original_created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技能表';


-- ============================================
-- 2. 工作流表 (workflows)
-- ============================================
CREATE TABLE `workflows` (
    `id` VARCHAR(50) NOT NULL COMMENT '工作流ID（如 wf-xxx）',
    `name` VARCHAR(100) NOT NULL COMMENT '工作流名称',
    `description` TEXT COMMENT '工作流描述',
    `icon` VARCHAR(50) DEFAULT '🔄' COMMENT '图标',
    `nodes` JSON COMMENT '节点列表',
    `edges` JSON COMMENT '边列表',
    `input_count` INT DEFAULT 0 COMMENT '输入数量（开头节点的interactions数）',
    `output_type` VARCHAR(50) COMMENT '输出类型（结尾节点的output类型）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_workflows_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流表';


-- ============================================
-- 3. 工作流执行实例表 (workflow_executions)
-- ============================================
CREATE TABLE `workflow_executions` (
    `id` VARCHAR(50) NOT NULL COMMENT '执行ID (exec-xxx)',
    `workflow_id` VARCHAR(50) NOT NULL COMMENT '工作流ID',
    `workflow_name` VARCHAR(100) COMMENT '工作流名称快照',
    `status` ENUM('pending', 'running', 'paused', 'completed', 'failed') DEFAULT 'pending' COMMENT '执行状态',
    `current_step` INT DEFAULT 0 COMMENT '当前步骤',
    `total_steps` INT DEFAULT 0 COMMENT '总步骤数',
    `completed_steps` JSON COMMENT '已完成步骤列表',
    `pending_interaction` JSON COMMENT '等待的交互信息',
    `pre_inputs` JSON COMMENT '预收集的输入',
    `error` TEXT COMMENT '错误信息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_executions_workflow_id` (`workflow_id`),
    INDEX `idx_executions_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作流执行实例表';


-- ============================================
-- 4. 用户数据便签表 (user_data_notes)
-- 用于保存AI生成的数据文件，支持文件夹（最多3层）
-- ============================================
CREATE TABLE `user_data_notes` (
    `id` VARCHAR(50) NOT NULL COMMENT '便签ID (UUID)',
    `user_id` VARCHAR(50) NOT NULL COMMENT '用户ID',
    `agent_id` VARCHAR(36) COMMENT '关联的Agent ID（用于数据隔离）',
    `name` VARCHAR(100) NOT NULL COMMENT '便签名称',
    `description` TEXT COMMENT '描述',
    `file_type` VARCHAR(20) NOT NULL COMMENT '文件类型 (xlsx, pdf, json, folder等)',
    `file_url` VARCHAR(500) COMMENT '文件URL（文件夹时为空）',
    `file_size` VARCHAR(20) COMMENT '文件大小',
    `source_skill` VARCHAR(100) COMMENT '来源技能名称',
    `is_favorited` TINYINT(1) DEFAULT 0 COMMENT '是否收藏',
    `parent_id` VARCHAR(50) COMMENT '父文件夹ID（NULL表示根目录）',
    `level` INT DEFAULT 0 COMMENT '层级：0=根目录，最大3层',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_data_notes_user_id` (`user_id`),
    INDEX `idx_data_notes_agent_id` (`agent_id`),
    INDEX `idx_data_notes_parent_id` (`parent_id`),
    INDEX `idx_data_notes_favorited` (`user_id`, `is_favorited`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户数据便签表';


CREATE TABLE `agents` (
  `id` varchar(36) COLLATE utf8mb4_general_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `description` text COLLATE utf8mb4_general_ci,
  `icon` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `category` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `system_prompt` text COLLATE utf8mb4_general_ci,
  `model` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `temperature` float NOT NULL,
  `max_tokens` int NOT NULL,
  `tools` json DEFAULT NULL,
  `skills` json DEFAULT NULL,
  `module_configs` json DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_general_ci NOT NULL,
  `author` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `version` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `usage_count` int NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;