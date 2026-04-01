#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户使用手册生成器 - 8个Agent操作指南
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from pathlib import Path
from datetime import datetime
import os

# 注册中文字体
def register_fonts():
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('Chinese', fp))
                return 'Chinese'
            except:
                continue
    return 'Helvetica'

FONT_NAME = register_fonts()

# 样式定义
def get_styles():
    return {
        'cover_title': ParagraphStyle(
            'CoverTitle', fontName=FONT_NAME, fontSize=32, leading=48,
            alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor('#1a1a2e')
        ),
        'cover_subtitle': ParagraphStyle(
            'CoverSubtitle', fontName=FONT_NAME, fontSize=14, leading=20,
            alignment=TA_CENTER, textColor=colors.HexColor('#666666')
        ),
        'h1': ParagraphStyle(
            'H1', fontName=FONT_NAME, fontSize=20, leading=30,
            spaceBefore=20, spaceAfter=12, textColor=colors.HexColor('#1a1a2e')
        ),
        'h2': ParagraphStyle(
            'H2', fontName=FONT_NAME, fontSize=14, leading=22,
            spaceBefore=15, spaceAfter=8, textColor=colors.HexColor('#2d3748')
        ),
        'body': ParagraphStyle(
            'Body', fontName=FONT_NAME, fontSize=11, leading=18,
            spaceBefore=4, spaceAfter=4, textColor=colors.HexColor('#333333')
        ),
        'tip': ParagraphStyle(
            'Tip', fontName=FONT_NAME, fontSize=10, leading=16,
            spaceBefore=8, spaceAfter=8, textColor=colors.HexColor('#059669'),
            leftIndent=10, borderPadding=5
        ),
    }

def generate_manual():
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"AI智能助手_使用指南.pdf"

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        topMargin=25*mm, bottomMargin=20*mm,
        leftMargin=20*mm, rightMargin=20*mm
    )

    styles = get_styles()
    story = []

    # === 封面 ===
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("AI 智能助手", styles['cover_title']))
    story.append(Paragraph("使用指南", styles['cover_title']))
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph("— 让AI成为您的工作伙伴 —", styles['cover_subtitle']))
    story.append(Spacer(1, 40*mm))
    story.append(Paragraph(f"版本 1.0 · {datetime.now().strftime('%Y年%m月')}", styles['cover_subtitle']))

    # === 快速开始 ===
    story.append(Spacer(1, 30*mm))
    story.append(Paragraph("快速开始", styles['h1']))
    story.append(Paragraph("1. 打开系统，在左侧选择您需要的 Agent（智能助手）", styles['body']))
    story.append(Paragraph("2. 在对话框中输入您的问题或需求", styles['body']))
    story.append(Paragraph("3. 如需上传文件，点击对话框旁的上传按钮", styles['body']))
    story.append(Paragraph("4. AI会自动分析并给出结果，支持导出Excel/PDF", styles['body']))

    # === 8个Agent介绍 ===
    agents = [
        {
            'name': '1. HR部门 Agent',
            'desc': '人事数据分析 · 入离职流程 · 招聘文案',
            'examples': [
                '"帮我分析这份员工名单的部门分布"',
                '"生成一份Java开发工程师的招聘JD"',
                '"统计本月入职和离职人数"',
            ]
        },
        {
            'name': '2. 财务部门 Agent',
            'desc': '财务数据分析 · 费用报销 · 财务文书',
            'examples': [
                '"分析这份财务报表的收支情况"',
                '"帮我审核这张报销单是否合规"',
                '"生成本季度财务分析报告"',
            ]
        },
        {
            'name': '3. 销售部门 Agent',
            'desc': '销售数据分析 · 客户管理 · 销售物料',
            'examples': [
                '"分析本月销售数据，找出TOP10客户"',
                '"根据产品信息生成销售话术"',
                '"统计各区域的销售完成率"',
            ]
        },
        {
            'name': '4. 采购部门 Agent',
            'desc': '采购成本分析 · 采购流程 · 供应商管理',
            'examples': [
                '"对比这几家供应商的报价"',
                '"分析本季度采购成本变化趋势"',
                '"生成采购需求汇总表"',
            ]
        },
        {
            'name': '5. 行政部门 Agent',
            'desc': '行政数据分析 · 资源预约 · 会议纪要',
            'examples': [
                '"统计本月会议室使用情况"',
                '"帮我整理这份会议录音的纪要"',
                '"分析办公用品消耗数据"',
            ]
        },
        {
            'name': '6. 商业线索 Agent',
            'desc': '线索分级 · 商机筛选 · 转化管理',
            'examples': [
                '"从这份数据中筛选消防相关商机"',
                '"对这批线索进行质量评分"',
                '"分析线索的行业分布"',
            ]
        },
        {
            'name': '7. 老板视角',
            'desc': '经营概览 · 战略分析 · 决策支持',
            'examples': [
                '"汇总各部门本月工作数据"',
                '"分析公司整体经营状况"',
                '"对比各业务线的盈利情况"',
            ]
        },
        {
            'name': '8. 智能体自定义',
            'desc': '个性化配置 · 专属流程 · 灵活扩展',
            'examples': [
                '"创建一个专门处理合同审核的助手"',
                '"上传知识库文档让AI学习"',
                '"自定义工作流程和输出格式"',
            ]
        },
    ]

    for agent in agents:
        story.append(Paragraph(agent['name'], styles['h2']))
        story.append(Paragraph(agent['desc'], styles['body']))
        story.append(Paragraph("<b>示例问法：</b>", styles['body']))
        for ex in agent['examples']:
            story.append(Paragraph(f"• {ex}", styles['body']))

    # === 常用操作 ===
    story.append(Paragraph("常用操作说明", styles['h1']))

    operations = [
        ("上传文件", "点击对话框左侧的📎按钮，支持Excel、PDF、Word等格式"),
        ("导出结果", "AI生成的报表可直接点击下载，支持Excel和PDF格式"),
        ("知识库", "在Agent设置中上传文档，AI会基于文档内容回答问题"),
        ("历史记录", "对话记录自动保存，可随时查看历史对话"),
    ]

    for op, desc in operations:
        story.append(Paragraph(f"<b>{op}：</b>{desc}", styles['body']))

    # === 小提示 ===
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("💡 小提示", styles['h2']))
    tips = [
        "问题描述越具体，AI回答越准确",
        "上传数据文件时，确保表头清晰规范",
        "复杂任务可分步骤提问，逐步完成",
        "遇到问题可以说'帮我重新分析'让AI重试",
    ]
    for tip in tips:
        story.append(Paragraph(f"• {tip}", styles['body']))

    # 生成PDF
    doc.build(story)
    print(f"使用手册已生成: {output_path}")
    return str(output_path)

if __name__ == '__main__':
    generate_manual()
