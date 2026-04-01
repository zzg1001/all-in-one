#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Skills Platform 使用手册 PDF 生成脚本
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# PDF生成
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def register_fonts():
    """注册中文字体"""
    font_paths = [
        # Windows
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return 'ChineseFont'
            except:
                continue

    return 'Helvetica'


def create_styles(font_name):
    """创建样式"""
    styles = getSampleStyleSheet()

    # 标题样式
    styles.add(ParagraphStyle(
        name='ChineseTitle',
        fontName=font_name,
        fontSize=28,
        leading=36,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#1A237E'),
    ))

    styles.add(ParagraphStyle(
        name='ChineseSubTitle',
        fontName=font_name,
        fontSize=14,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=50,
        textColor=colors.HexColor('#666666'),
    ))

    styles.add(ParagraphStyle(
        name='ChineseH1',
        fontName=font_name,
        fontSize=20,
        leading=28,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor('#1A237E'),
    ))

    styles.add(ParagraphStyle(
        name='ChineseH2',
        fontName=font_name,
        fontSize=16,
        leading=22,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#303F9F'),
    ))

    styles.add(ParagraphStyle(
        name='ChineseH3',
        fontName=font_name,
        fontSize=13,
        leading=18,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor('#3F51B5'),
    ))

    styles.add(ParagraphStyle(
        name='ChineseBody',
        fontName=font_name,
        fontSize=11,
        leading=18,
        spaceBefore=4,
        spaceAfter=4,
        alignment=TA_JUSTIFY,
    ))

    styles.add(ParagraphStyle(
        name='ChineseBullet',
        fontName=font_name,
        fontSize=11,
        leading=16,
        leftIndent=20,
        spaceBefore=2,
        spaceAfter=2,
    ))

    styles.add(ParagraphStyle(
        name='ChineseNote',
        fontName=font_name,
        fontSize=10,
        leading=14,
        leftIndent=15,
        spaceBefore=5,
        spaceAfter=5,
        textColor=colors.HexColor('#666666'),
        backColor=colors.HexColor('#F5F5F5'),
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName=font_name,
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.white,
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        fontName=font_name,
        fontSize=9,
        leading=12,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        fontName=font_name,
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#999999'),
    ))

    return styles


def create_table(data, col_widths=None, header=True):
    """创建表格"""
    if col_widths is None:
        col_widths = [120, 350]

    table = Table(data, colWidths=col_widths)

    style_commands = [
        ('FONTNAME', (0, 0), (-1, -1), 'ChineseFont'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]

    if header and len(data) > 0:
        style_commands.extend([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A237E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ])

        # 斑马纹
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#F8F9FA')))

    table.setStyle(TableStyle(style_commands))
    return table


def generate_manual(output_path):
    """生成使用手册PDF"""
    font_name = register_fonts()
    styles = create_styles(font_name)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    story = []

    # ========== 封面 ==========
    story.append(Spacer(1, 80))
    story.append(Paragraph("AI Skills Platform", styles['ChineseTitle']))
    story.append(Paragraph("智能技能平台", styles['ChineseTitle']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("使用手册", styles['ChineseSubTitle']))
    story.append(Spacer(1, 60))
    story.append(Paragraph(f"版本: 1.0.0", styles['ChineseBody']))
    story.append(Paragraph(f"日期: {datetime.now().strftime('%Y年%m月%d日')}", styles['ChineseBody']))
    story.append(PageBreak())

    # ========== 目录 ==========
    story.append(Paragraph("目录", styles['ChineseH1']))
    story.append(Spacer(1, 10))

    toc_items = [
        "1. 产品概述",
        "2. 系统架构",
        "3. 快速开始",
        "4. 用户端 (Portal) 功能指南",
        "    4.1 Agent 市场",
        "    4.2 Agent Studio",
        "    4.3 技能面板",
        "    4.4 AI 对话",
        "    4.5 File Manage 文件管理",
        "5. 管理端 (Admin) 功能指南",
        "    5.1 驾驶舱",
        "    5.2 模型配置",
        "    5.3 Token 用量",
        "    5.4 用户管理",
        "    5.5 权限管理",
        "    5.6 日志审计",
        "6. 预设 Agent 介绍",
        "7. 技能库介绍",
        "8. 常见问题 (FAQ)",
    ]

    for item in toc_items:
        story.append(Paragraph(item, styles['ChineseBody']))

    story.append(PageBreak())

    # ========== 1. 产品概述 ==========
    story.append(Paragraph("1. 产品概述", styles['ChineseH1']))
    story.append(Paragraph(
        "AI Skills Platform（智能技能平台）是一个企业级AI应用平台，旨在帮助企业快速构建、部署和管理AI驱动的自动化技能。"
        "平台集成了多种AI模型（Claude系列），支持自定义Agent创建、技能开发、工作流编排等功能。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("核心价值", styles['ChineseH3']))
    features = [
        "• <b>降低AI应用门槛</b>：无需编程即可创建AI助手",
        "• <b>提升工作效率</b>：自动化报告生成、数据分析、文档处理",
        "• <b>统一管理平台</b>：集中管理AI模型、用户权限、使用量",
        "• <b>企业级安全</b>：完善的权限控制和审计日志",
    ]
    for f in features:
        story.append(Paragraph(f, styles['ChineseBullet']))

    story.append(Spacer(1, 15))

    story.append(Paragraph("适用场景", styles['ChineseH3']))
    scenarios = [
        "• 人力资源：员工数据分析、招聘文案生成、离职分析报告",
        "• 销售部门：销售数据分析、客户管理、业绩报表",
        "• 财务部门：财务报表生成、成本分析、现金流预测",
        "• 采购部门：采购分析、供应商评估、成本节约分析",
        "• 行政部门：费用管理、资产盘点、会议室预约分析",
        "• 管理层：跨部门综合分析、总裁仪表盘、决策支持",
    ]
    for s in scenarios:
        story.append(Paragraph(s, styles['ChineseBullet']))

    story.append(PageBreak())

    # ========== 2. 系统架构 ==========
    story.append(Paragraph("2. 系统架构", styles['ChineseH1']))
    story.append(Paragraph(
        "平台采用前后端分离架构，包含用户端（Portal）和管理端（Admin）两个子系统。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 10))

    arch_data = [
        ['组件', '技术栈', '端口', '说明'],
        ['Portal Web', 'Vue 3 + TypeScript + Vite', '5173', '用户端前端'],
        ['Portal Server', 'FastAPI + SQLAlchemy', '8000', '用户端后端API'],
        ['Admin Web', 'Vue 3 + TypeScript + Vite', '5174', '管理端前端'],
        ['Admin Server', 'FastAPI + SQLAlchemy', '8001', '管理端后端API'],
        ['Database', 'MySQL 8+', '3306', '数据存储'],
        ['Storage', 'MinIO / 本地', '9000', '文件对象存储'],
        ['AI Model', 'Claude (Anthropic)', '-', 'AI推理服务'],
    ]
    story.append(create_table(arch_data, col_widths=[90, 160, 50, 150]))

    story.append(PageBreak())

    # ========== 3. 快速开始 ==========
    story.append(Paragraph("3. 快速开始", styles['ChineseH1']))

    story.append(Paragraph("3.1 环境要求", styles['ChineseH2']))
    req_data = [
        ['组件', '版本要求'],
        ['Node.js', '18.x 或更高'],
        ['Python', '3.10 或更高'],
        ['MySQL', '8.0 或更高'],
        ['MinIO (可选)', '最新版'],
    ]
    story.append(create_table(req_data, col_widths=[150, 300]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3.2 启动步骤", styles['ChineseH2']))
    steps = [
        "1. <b>启动数据库</b>：确保 MySQL 服务运行，创建数据库 product_background",
        "2. <b>配置环境变量</b>：复制 .env.example 为 .env，填写数据库和API密钥",
        "3. <b>启动 Portal 后端</b>：cd portal/server && uvicorn main:app --reload",
        "4. <b>启动 Portal 前端</b>：cd portal/web && npm install && npm run dev",
        "5. <b>启动 Admin 后端</b>：cd admin/server && uvicorn main:app --port 8001 --reload",
        "6. <b>启动 Admin 前端</b>：cd admin/web && npm install && npm run dev",
        "7. <b>访问系统</b>：Portal http://localhost:5173 | Admin http://localhost:5174",
    ]
    for step in steps:
        story.append(Paragraph(step, styles['ChineseBullet']))

    story.append(PageBreak())

    # ========== 4. Portal 功能指南 ==========
    story.append(Paragraph("4. 用户端 (Portal) 功能指南", styles['ChineseH1']))

    # 4.1 Agent 市场
    story.append(Paragraph("4.1 Agent 市场", styles['ChineseH2']))
    story.append(Paragraph(
        "Agent 市场展示所有可用的 AI Agent，用户可以浏览、搜索和使用各类预设或自定义的 Agent。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("功能说明：", styles['ChineseH3']))
    agent_market_features = [
        "• <b>Agent 卡片展示</b>：以网格形式展示 Agent，包含图标、名称、描述、使用次数",
        "• <b>分类筛选</b>：支持按 企业服务/市场营销/管理决策/自定义 分类筛选",
        "• <b>搜索功能</b>：支持按名称或描述搜索 Agent",
        "• <b>状态管理</b>：Agent 分为 已发布/草稿/已弃用 三种状态",
        "• <b>快捷操作</b>：点击「使用」进入对话界面，「编辑」进入 Agent Studio",
    ]
    for f in agent_market_features:
        story.append(Paragraph(f, styles['ChineseBullet']))
    story.append(Spacer(1, 10))

    # 4.2 Agent Studio
    story.append(Paragraph("4.2 Agent Studio", styles['ChineseH2']))
    story.append(Paragraph(
        "Agent Studio 是创建和编辑 Agent 的工作台，通过 4 个步骤即可完成 Agent 配置。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    studio_steps = [
        ['步骤', '说明'],
        ['1. 基本信息', '设置 Agent 名称、图标（15种emoji可选）、描述、分类'],
        ['2. 系统提示词', '定义 Agent 的角色和行为准则，支持 AI 智能生成'],
        ['3. 技能管理', '选择 Agent 可使用的技能，支持创建、编辑、上传技能'],
        ['4. 高级设置', '模型选择、温度参数、最大Token、记忆功能、推理模式'],
    ]
    story.append(create_table(studio_steps, col_widths=[100, 350]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("模型选项：", styles['ChineseH3']))
    model_options = [
        "• <b>Claude Opus 4.5 (PRO)</b>：最强大的模型，适合复杂任务",
        "• <b>Claude Sonnet 4</b>：平衡性能和成本，适合日常任务",
        "• <b>Claude Haiku (FAST)</b>：最快速的模型，适合简单任务",
    ]
    for m in model_options:
        story.append(Paragraph(m, styles['ChineseBullet']))
    story.append(Spacer(1, 10))

    # 4.3 技能面板
    story.append(Paragraph("4.3 技能面板", styles['ChineseH2']))
    story.append(Paragraph(
        "技能面板提供技能管理和 AI 对话的统一入口，包含三个主要标签页。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    skill_tabs = [
        ['标签页', '功能说明'],
        ['技能', '展示所有可用技能的网格卡片，支持搜索和分类筛选'],
        ['Agent', 'AI 对话界面，可选择 Agent 进行对话'],
        ['工作流', '工作流构建器，支持多技能串联执行'],
    ]
    story.append(create_table(skill_tabs, col_widths=[100, 350]))
    story.append(Spacer(1, 10))

    # 4.4 AI 对话
    story.append(Paragraph("4.4 AI 对话", styles['ChineseH2']))
    story.append(Paragraph(
        "与 AI Agent 进行实时对话，支持文件上传、技能调用、流式响应等功能。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    chat_features = [
        "• <b>流式响应</b>：AI 回复实时显示，无需等待完整响应",
        "• <b>文件上传</b>：支持上传 Excel、CSV、PDF 等文件供 AI 分析",
        "• <b>技能调用</b>：AI 可自动识别并调用合适的技能生成报告",
        "• <b>历史记录</b>：自动保存对话历史，支持查看历史会话",
        "• <b>RAG 增强</b>：基于 File Manage 中的文件进行知识检索增强",
    ]
    for f in chat_features:
        story.append(Paragraph(f, styles['ChineseBullet']))
    story.append(Spacer(1, 10))

    # 4.5 File Manage
    story.append(Paragraph("4.5 File Manage 文件管理", styles['ChineseH2']))
    story.append(Paragraph(
        "File Manage 是每个 Agent 的专属文件存储空间，支持上传和管理数据文件。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    file_features = [
        "• <b>文件上传</b>：支持 Excel、CSV、PDF、TXT 等格式",
        "• <b>文件夹管理</b>：支持创建文件夹，最多3层嵌套",
        "• <b>Agent 隔离</b>：每个 Agent 的文件独立存储，互不干扰",
        "• <b>数据共享</b>：老板视角 Agent 可访问所有部门 Agent 的文件",
        "• <b>ZIP 下载</b>：支持将文件夹打包下载",
    ]
    for f in file_features:
        story.append(Paragraph(f, styles['ChineseBullet']))

    story.append(PageBreak())

    # ========== 5. Admin 功能指南 ==========
    story.append(Paragraph("5. 管理端 (Admin) 功能指南", styles['ChineseH1']))

    # 5.1 驾驶舱
    story.append(Paragraph("5.1 驾驶舱", styles['ChineseH2']))
    story.append(Paragraph(
        "驾驶舱提供系统运行状态的实时监控，展示关键指标和统计数据。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    dashboard_metrics = [
        ['指标', '说明'],
        ['今日调用量', '当日 AI 接口调用总次数'],
        ['Token 消耗', '当日消耗的 Token 总数'],
        ['活跃用户', '当日使用系统的用户数'],
        ['成功率', 'AI 调用成功率百分比'],
    ]
    story.append(create_table(dashboard_metrics, col_widths=[120, 330]))
    story.append(Spacer(1, 10))

    # 5.2 模型配置
    story.append(Paragraph("5.2 模型配置", styles['ChineseH2']))
    story.append(Paragraph(
        "管理 AI 模型的 API 配置，包括 API Key、Base URL 等设置。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    model_config = [
        "• <b>API Key</b>：配置 Anthropic API 密钥",
        "• <b>Base URL</b>：配置 API 代理地址（如 Azure 代理）",
        "• <b>默认模型</b>：设置系统默认使用的 Claude 模型版本",
    ]
    for c in model_config:
        story.append(Paragraph(c, styles['ChineseBullet']))
    story.append(Spacer(1, 10))

    # 5.3 Token 用量
    story.append(Paragraph("5.3 Token 用量", styles['ChineseH2']))
    story.append(Paragraph(
        "查看 Token 消耗统计，了解 AI 使用成本和配额使用情况。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    token_features = [
        "• <b>月度消耗</b>：本月 Token 消耗总量",
        "• <b>预估成本</b>：基于 Token 用量估算的费用",
        "• <b>配额使用率</b>：当前配额使用百分比",
        "• <b>按用户统计</b>：各用户的 Token 使用量排行",
        "• <b>按技能统计</b>：各技能的 Token 使用量排行",
        "• <b>时间趋势</b>：Token 使用量的时间趋势图",
    ]
    for f in token_features:
        story.append(Paragraph(f, styles['ChineseBullet']))
    story.append(Spacer(1, 10))

    # 5.4 用户管理
    story.append(Paragraph("5.4 用户管理", styles['ChineseH2']))
    story.append(Paragraph(
        "管理系统用户，包括用户状态、权限分配等。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    user_features = [
        "• <b>用户列表</b>：查看所有系统用户",
        "• <b>状态管理</b>：启用/禁用用户账号",
        "• <b>角色分配</b>：为用户分配不同角色",
    ]
    for f in user_features:
        story.append(Paragraph(f, styles['ChineseBullet']))
    story.append(Spacer(1, 10))

    # 5.5 权限管理
    story.append(Paragraph("5.5 权限管理", styles['ChineseH2']))
    story.append(Paragraph(
        "配置系统角色和权限，实现细粒度的访问控制。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    perm_tabs = [
        ['标签页', '功能说明'],
        ['角色管理', '创建和编辑角色，配置角色权限'],
        ['用户权限', '查看和修改用户的权限设置'],
        ['API 权限', '管理 API 接口的访问权限'],
    ]
    story.append(create_table(perm_tabs, col_widths=[120, 330]))
    story.append(Spacer(1, 10))

    # 5.6 日志审计
    story.append(Paragraph("5.6 日志审计", styles['ChineseH2']))
    story.append(Paragraph(
        "查看系统操作日志，支持多维度筛选和导出。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 8))

    log_tabs = [
        ['日志类型', '说明'],
        ['操作日志', '记录用户的操作行为，如创建/编辑/删除'],
        ['调用日志', '记录 AI 接口调用详情，包括输入输出'],
        ['错误日志', '记录系统错误和异常信息'],
    ]
    story.append(create_table(log_tabs, col_widths=[120, 330]))

    story.append(PageBreak())

    # ========== 6. 预设 Agent ==========
    story.append(Paragraph("6. 预设 Agent 介绍", styles['ChineseH1']))
    story.append(Paragraph(
        "系统预设了 8 个部门级 Agent，覆盖企业核心业务场景。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 10))

    agents_data = [
        ['Agent 名称', '图标', '分类', '主要功能'],
        ['HR部门 Agent', '👥', '企业服务', '人事数据分析、入离职流程、招聘文案生成'],
        ['销售部门 Agent', '📈', '企业服务', '销售数据分析、客户管理、销售物料生成'],
        ['采购部门 Agent', '🛒', '企业服务', '采购成本分析、采购流程、供应商管理'],
        ['行政部门 Agent', '🏢', '企业服务', '行政数据分析、会议室/车辆预约、会议纪要'],
        ['财务部门 Agent', '💰', '企业服务', '财务数据分析、费用报销审核、财务文书'],
        ['智能体自定义', '🧩', '自定义', '自然语言指令训练、个性化流程自动化'],
        ['商业线索 Agent', '🔍', '市场营销', '智能分级推送、全网智能抓取、转化管理'],
        ['老板视角', '👔', '管理决策', '跨部门数据分析、总裁仪表盘、综合报告'],
    ]
    story.append(create_table(agents_data, col_widths=[100, 40, 70, 240]))
    story.append(Spacer(1, 15))

    story.append(Paragraph("老板视角 Agent 特殊功能：", styles['ChineseH3']))
    boss_features = [
        "• 可访问所有部门 Agent 的 File Manage 数据",
        "• 自动汇总 HR/销售/采购/行政/财务 五大部门数据",
        "• 生成跨部门综合分析报告（总裁仪表盘）",
        "• 识别各部门风险指标并给出决策建议",
    ]
    for f in boss_features:
        story.append(Paragraph(f, styles['ChineseBullet']))

    story.append(PageBreak())

    # ========== 7. 技能库 ==========
    story.append(Paragraph("7. 技能库介绍", styles['ChineseH1']))
    story.append(Paragraph(
        "系统内置多个专业技能，可自动从 Excel 数据生成 PDF 分析报告。",
        styles['ChineseBody']
    ))
    story.append(Spacer(1, 10))

    skills_data = [
        ['技能名称', '输入', '输出', '功能说明'],
        ['sales-report', 'Excel', 'PDF', '销售分析报告：趋势分析、区域分布、产品排名、客户分析'],
        ['hr-report', 'Excel', 'PDF', '人力资源报告：员工结构、流动分析、招聘、薪酬、绩效'],
        ['finance-report', 'Excel', 'PDF', '财务分析报告：收入趋势、产品线盈利、部门费用、现金流'],
        ['procurement-report', 'Excel', 'PDF', '采购分析报告：采购趋势、分类分析、供应商绩效、集中度'],
        ['admin-report', 'Excel', 'PDF', '行政分析报告：费用趋势、资产管理、会议室、车辆、办公用品'],
        ['executive-dashboard', 'Excel', 'PDF', '总裁仪表盘：整合五大部门数据的高管综合报告'],
    ]
    story.append(create_table(skills_data, col_widths=[110, 45, 40, 255]))
    story.append(Spacer(1, 15))

    story.append(Paragraph("报告通用特点：", styles['ChineseH3']))
    report_features = [
        "• <b>执行摘要</b>：核心 KPI 卡片展示关键指标",
        "• <b>专业图表</b>：饼图、柱状图、折线图、散点图、面积图等",
        "• <b>数据表格</b>：详细的数据明细表",
        "• <b>风险提示</b>：自动识别异常指标并给出预警",
        "• <b>示例数据</b>：无需上传文件时自动生成示例数据",
    ]
    for f in report_features:
        story.append(Paragraph(f, styles['ChineseBullet']))
    story.append(Spacer(1, 15))

    story.append(Paragraph("使用技能生成报告：", styles['ChineseH3']))
    usage_steps = [
        "1. 进入对应部门的 Agent 对话界面",
        "2. 上传 Excel 数据文件（或直接使用示例数据）",
        "3. 输入「生成XX报告」或「帮我分析数据」",
        "4. AI 自动调用技能生成 PDF 报告",
        "5. 点击下载报告文件",
    ]
    for step in usage_steps:
        story.append(Paragraph(step, styles['ChineseBullet']))

    story.append(PageBreak())

    # ========== 8. FAQ ==========
    story.append(Paragraph("8. 常见问题 (FAQ)", styles['ChineseH1']))
    story.append(Spacer(1, 10))

    faqs = [
        ("Q: 如何创建新的 Agent？",
         "A: 进入 Agent 市场页面，点击「创建 Agent」按钮，按照 4 个步骤（基本信息、系统提示词、技能管理、高级设置）完成配置。"),

        ("Q: 上传的文件大小有限制吗？",
         "A: 单个文件最大支持 50MB，建议 Excel 文件保持在 10MB 以内以获得最佳处理速度。"),

        ("Q: 为什么生成的报告是 Excel 而不是 PDF？",
         "A: 请检查技能的 SKILL.md 文件中是否配置了 output_config: preferred_type: pdf。"),

        ("Q: 老板视角 Agent 如何访问各部门数据？",
         "A: 各部门 Agent 需要先在各自的 File Manage 中上传数据文件，然后老板视角 Agent 会自动聚合这些数据进行分析。"),

        ("Q: 如何自定义技能？",
         "A: 在 Agent Studio 的技能管理步骤中，点击「创建技能」，编写 SKILL.md 描述文件和 main.py 执行脚本，或上传 ZIP 包。"),

        ("Q: Token 消耗太快怎么办？",
         "A: 可以选择使用 Claude Haiku 模型（速度快、成本低），或者在对话中减少历史消息长度。"),

        ("Q: 如何备份数据？",
         "A: 系统支持 MinIO 对象存储，建议配置 MinIO 进行数据持久化和备份。"),

        ("Q: 系统支持哪些文件格式？",
         "A: 支持 Excel (.xlsx/.xls)、CSV、PDF、TXT、Markdown、JSON 等常见格式。"),
    ]

    for q, a in faqs:
        story.append(Paragraph(q, styles['ChineseH3']))
        story.append(Paragraph(a, styles['ChineseBody']))
        story.append(Spacer(1, 8))

    story.append(PageBreak())

    # ========== 尾页 ==========
    story.append(Spacer(1, 100))
    story.append(Paragraph("AI Skills Platform", styles['ChineseTitle']))
    story.append(Spacer(1, 30))
    story.append(Paragraph("感谢使用本产品", styles['ChineseSubTitle']))
    story.append(Spacer(1, 50))
    story.append(Paragraph(f"文档生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Footer']))

    # 生成PDF
    doc.build(story)
    print(f"使用手册已生成: {output_path}")
    return output_path


if __name__ == "__main__":
    # 输出目录
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"AI_Skills_Platform_使用手册_{datetime.now().strftime('%Y%m%d')}.pdf"
    generate_manual(output_file)
