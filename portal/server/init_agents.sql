-- 初始化 8 个预设 Agent（与首页一致）
-- 数据库: ai_agent

-- 先清空旧数据
TRUNCATE TABLE agents;

-- 插入 8 个预设 Agent
INSERT INTO `agents` (`id`, `name`, `description`, `icon`, `category`, `system_prompt`, `model`, `temperature`, `max_tokens`, `tools`, `skills`, `module_configs`, `status`, `author`, `version`, `usage_count`, `created_at`, `updated_at`) VALUES
(UUID(), 'HR部门 Agent', '人事数据分析 · 入离职流程自动化 · 招聘文案生成', '👥', '企业服务', '你是HR部门的智能助手，帮助处理人事数据分析、入离职流程自动化、招聘文案生成等工作。', 'claude-opus-4-5', 0.7, 4096, '["read", "write"]', '[]', '{"memory": {"enabled": true, "type": "conversation", "max_history": 20}, "reasoning": {"enabled": true, "style": "step-by-step"}}', 'active', 'System', '1.0.0', 1520, NOW(), NOW()),

(UUID(), '销售部门 Agent', '销售数据分析 · 客户管理自动化 · 销售物料生成', '📈', '企业服务', '你是销售部门的智能助手，帮助处理销售数据分析、客户管理自动化、销售物料生成等工作。', 'claude-opus-4-5', 0.7, 4096, '["read", "write", "code_exec"]', '[]', '{"memory": {"enabled": true, "type": "conversation", "max_history": 20}, "reasoning": {"enabled": true, "style": "step-by-step"}}', 'active', 'System', '1.0.0', 892, NOW(), NOW()),

(UUID(), '采购部门 Agent', '采购成本分析 · 采购流程自动化 · 供应商管理', '🛒', '企业服务', '你是采购部门的智能助手，帮助处理采购成本分析、采购流程自动化、供应商管理等工作。', 'claude-opus-4-5', 0.7, 4096, '["read", "write"]', '[]', '{"memory": {"enabled": true, "type": "conversation", "max_history": 20}, "reasoning": {"enabled": true, "style": "step-by-step"}}', 'active', 'System', '1.0.0', 756, NOW(), NOW()),

(UUID(), '行政部门 Agent', '行政数据分析 · 会议室/车辆预约自动化 · 会议纪要生成', '🏢', '企业服务', '你是行政部门的智能助手，帮助处理行政数据分析、会议室/车辆预约自动化、会议纪要生成等工作。', 'claude-opus-4-5', 0.7, 4096, '["read", "write"]', '[]', '{"memory": {"enabled": true, "type": "conversation", "max_history": 20}, "reasoning": {"enabled": true, "style": "step-by-step"}}', 'active', 'System', '1.0.0', 1203, NOW(), NOW()),

(UUID(), '财务部门 Agent', '财务数据分析 · 费用报销审核 · 财务文书生成', '💰', '企业服务', '你是财务部门的智能助手，帮助处理财务数据分析、费用报销审核、财务文书生成等工作。', 'claude-opus-4-5', 0.7, 4096, '["read", "write", "code_exec"]', '[]', '{"memory": {"enabled": true, "type": "conversation", "max_history": 20}, "reasoning": {"enabled": true, "style": "step-by-step"}}', 'active', 'System', '1.0.0', 432, NOW(), NOW()),

(UUID(), '智能体自定义', '自然语言指令训练 · 个性化流程自动化 · 适配专属需求', '🧩', '自定义', '你是一个可自定义的智能助手，可以根据用户的自然语言指令进行训练，实现个性化流程自动化。', 'claude-opus-4-5', 0.7, 4096, '["read", "write", "bash", "code_exec"]', '[]', '{"memory": {"enabled": true, "type": "conversation", "max_history": 20}, "reasoning": {"enabled": true, "style": "step-by-step"}}', 'active', 'System', '1.0.0', 567, NOW(), NOW()),

(UUID(), '商业线索 Agent', '智能分级推送 · 全网智能抓取 · 全流程转化管理', '🔍', '市场营销', '你是商业线索挖掘专家，帮助进行智能分级推送、全网智能抓取、全流程转化管理等工作。', 'claude-opus-4-5', 0.7, 4096, '["read", "write", "web_search"]', '[]', '{"memory": {"enabled": true, "type": "conversation", "max_history": 20}, "reasoning": {"enabled": true, "style": "step-by-step"}}', 'active', 'System', '1.0.0', 2341, NOW(), NOW()),

(UUID(), '老板视角', '现金流与财务健康 · 增长与战略方向 · 人才与团队', '👔', '管理决策', '你是企业管理顾问，从老板视角帮助分析现金流与财务健康、增长与战略方向、人才与团队等问题。', 'claude-opus-4-5', 0.7, 4096, '["read", "write", "code_exec"]', '[]', '{"memory": {"enabled": true, "type": "conversation", "max_history": 20}, "reasoning": {"enabled": true, "style": "step-by-step"}}', 'active', 'System', '1.0.0', 1892, NOW(), NOW());

-- 查看结果
SELECT id, name, icon, category, status FROM agents;
