#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务PDF报告生成器
生成专业的财务分析报告、费用报销审核报告、预算执行报告
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def check_dependencies():
    """检查依赖"""
    missing = []
    try:
        from reportlab.lib.pagesizes import A4
    except ImportError:
        missing.append('reportlab')
    try:
        import matplotlib
    except ImportError:
        missing.append('matplotlib')

    if missing:
        print(f"缺少依赖库: {', '.join(missing)}")
        print(f"请运行: pip install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, black, white, red, green
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# 财务报告配色
COLORS = {
    'primary': HexColor('#2563eb'),      # 专业蓝
    'secondary': HexColor('#059669'),    # 财务绿
    'danger': HexColor('#dc2626'),       # 警告红
    'warning': HexColor('#d97706'),      # 提醒橙
    'dark': HexColor('#1f2937'),         # 深色文字
    'light': HexColor('#f3f4f6'),        # 浅色背景
    'border': HexColor('#e5e7eb'),       # 边框
    'positive': HexColor('#10b981'),     # 正向/盈利
    'negative': HexColor('#ef4444'),     # 负向/亏损
}

# 图表配色
CHART_COLORS = ['#2563eb', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d', '#dc2626']


def register_chinese_font():
    """注册中文字体"""
    font_paths = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simsun.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        '/System/Library/Fonts/PingFang.ttc',
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return 'ChineseFont'
            except:
                continue
    return 'Helvetica'


def create_styles(font_name):
    """创建样式"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontName=font_name,
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=COLORS['dark'],
        spaceAfter=15,
    ))

    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        fontName=font_name,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=HexColor('#6b7280'),
        spaceAfter=25,
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName=font_name,
        fontSize=14,
        leading=20,
        textColor=COLORS['primary'],
        spaceBefore=15,
        spaceAfter=8,
    ))

    # 修改默认BodyText样式
    styles['BodyText'].fontName = font_name
    styles['BodyText'].fontSize = 10
    styles['BodyText'].leading = 16
    styles['BodyText'].alignment = TA_JUSTIFY
    styles['BodyText'].textColor = COLORS['dark']
    styles['BodyText'].spaceAfter = 8

    styles.add(ParagraphStyle(
        name='IndicatorLabel',
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=HexColor('#6b7280'),
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='IndicatorValue',
        fontName=font_name,
        fontSize=18,
        leading=24,
        textColor=COLORS['primary'],
        alignment=TA_CENTER,
        fontWeight='bold',
    ))

    styles.add(ParagraphStyle(
        name='PositiveValue',
        fontName=font_name,
        fontSize=18,
        leading=24,
        textColor=COLORS['positive'],
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='NegativeValue',
        fontName=font_name,
        fontSize=18,
        leading=24,
        textColor=COLORS['negative'],
        alignment=TA_CENTER,
    ))

    return styles


def create_chart(chart_data, output_path):
    """创建财务图表"""
    chart_type = chart_data.get('type', 'bar')
    title = chart_data.get('title', '')
    labels = chart_data.get('labels', [])
    values = chart_data.get('values', [])
    values2 = chart_data.get('values2', None)  # 用于对比图

    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = CHART_COLORS[:len(labels)]

    if chart_type == 'bar':
        if values2:  # 对比柱状图
            x = np.arange(len(labels))
            width = 0.35
            bars1 = ax.bar(x - width/2, values, width, label='预算', color=CHART_COLORS[0], alpha=0.8)
            bars2 = ax.bar(x + width/2, values2, width, label='实际', color=CHART_COLORS[1], alpha=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend()

            # 添加数值标签
            for bar in bars1:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01*max(values),
                       f'{bar.get_height():,.0f}', ha='center', va='bottom', fontsize=8)
            for bar in bars2:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01*max(values2),
                       f'{bar.get_height():,.0f}', ha='center', va='bottom', fontsize=8)
        else:
            bars = ax.bar(labels, values, color=colors)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01*max(values),
                       f'{val:,.0f}', ha='center', va='bottom', fontsize=9)

        ax.set_ylabel('金额 (元)')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    elif chart_type == 'pie':
        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors,
                                          autopct='%1.1f%%', startangle=90,
                                          pctdistance=0.75)
        ax.axis('equal')
        for autotext in autotexts:
            autotext.set_fontsize(9)

    elif chart_type == 'line':
        ax.plot(labels, values, marker='o', color=CHART_COLORS[0], linewidth=2, label='收入' if values2 else '')
        if values2:
            ax.plot(labels, values2, marker='s', color=CHART_COLORS[2], linewidth=2, label='支出')
            ax.legend()

        ax.set_ylabel('金额 (元)')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        # 添加数值
        for i, (x, y) in enumerate(zip(labels, values)):
            ax.annotate(f'{y:,.0f}', (x, y), textcoords="offset points",
                       xytext=(0, 8), ha='center', fontsize=8)

    elif chart_type == 'horizontal_bar':
        # 水平柱状图，适合部门排名
        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, values, color=colors)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.set_xlabel('金额 (元)')

        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values)*0.01, bar.get_y() + bar.get_height()/2,
                   f'{val:,.0f}', ha='left', va='center', fontsize=9)

    ax.set_title(title, fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    return output_path


def build_indicator_card(indicators, styles):
    """构建指标卡片"""
    cards = []

    # 定义要展示的指标
    indicator_config = [
        ('total_income', '总收入', 'positive'),
        ('total_expense', '总支出', 'negative'),
        ('net_profit', '净利润', 'auto'),
        ('profit_rate', '利润率', 'auto'),
        ('total_reimbursement', '报销总额', 'neutral'),
        ('total_budget', '预算总额', 'neutral'),
        ('total_actual', '实际支出', 'neutral'),
        ('execution_rate', '执行率', 'neutral'),
    ]

    card_data = []
    for key, label, color_type in indicator_config:
        if key in indicators:
            value = indicators[key]
            if isinstance(value, (int, float)):
                if value >= 10000:
                    display_value = f'{value/10000:,.2f}万'
                else:
                    display_value = f'{value:,.2f}'
            else:
                display_value = str(value)

            card_data.append((label, display_value, color_type, value if isinstance(value, (int, float)) else 0))

    if not card_data:
        return None

    # 每行4个指标
    rows = []
    for i in range(0, len(card_data), 4):
        row_data = card_data[i:i+4]
        row = []
        for label, display_value, color_type, raw_value in row_data:
            # 确定颜色
            if color_type == 'auto':
                if raw_value > 0:
                    value_style = 'PositiveValue'
                elif raw_value < 0:
                    value_style = 'NegativeValue'
                else:
                    value_style = 'IndicatorValue'
            elif color_type == 'positive':
                value_style = 'PositiveValue'
            elif color_type == 'negative':
                value_style = 'NegativeValue'
            else:
                value_style = 'IndicatorValue'

            cell_content = [
                Paragraph(display_value, styles[value_style]),
                Paragraph(label, styles['IndicatorLabel'])
            ]
            row.append(cell_content)

        # 补齐空列
        while len(row) < 4:
            row.append([Paragraph('', styles['IndicatorValue']), Paragraph('', styles['IndicatorLabel'])])

        rows.append(row)

    if not rows:
        return None

    # 创建表格
    col_width = (A4[0] - 4*cm) / 4
    table = Table(rows, colWidths=[col_width]*4, rowHeights=[60]*len(rows))

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS['light']),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, COLORS['border']),
        ('INNERGRID', (0, 0), (-1, -1), 1, COLORS['border']),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    return table


def build_table(data, styles, highlight_column=None):
    """构建数据表格"""
    if not data or len(data) == 0:
        return None

    col_count = len(data[0])
    col_width = (A4[0] - 4*cm) / col_count

    table = Table(data, colWidths=[col_width] * col_count)

    style_commands = [
        # 表头
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), styles['BodyText'].fontName),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),

        # 数据行
        ('FONTNAME', (0, 1), (-1, -1), styles['BodyText'].fontName),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),

        # 边框
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['border']),

        # 斑马纹
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, COLORS['light']]),
    ]

    # 高亮特定列（如超支标红）
    if highlight_column is not None:
        for row_idx in range(1, len(data)):
            try:
                value = data[row_idx][highlight_column]
                if isinstance(value, str):
                    value = value.replace('%', '').replace(',', '')
                if float(value) > 100:  # 超过100%标红
                    style_commands.append(('TEXTCOLOR', (highlight_column, row_idx), (highlight_column, row_idx), COLORS['danger']))
                elif float(value) < 80:  # 低于80%标橙
                    style_commands.append(('TEXTCOLOR', (highlight_column, row_idx), (highlight_column, row_idx), COLORS['warning']))
            except:
                pass

    table.setStyle(TableStyle(style_commands))
    return table


def generate_pdf(title, content_data, output_path, charts_data=None, subtitle=None):
    """生成财务PDF报告"""

    font_name = register_chinese_font()
    styles = create_styles(font_name)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    story = []

    # 封面
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(title, styles['ReportTitle']))

    if subtitle:
        story.append(Paragraph(subtitle, styles['ReportSubtitle']))

    date_str = datetime.now().strftime('%Y年%m月%d日')
    story.append(Paragraph(f"报告日期：{date_str}", styles['ReportSubtitle']))

    # 如果有指标数据，在封面显示核心指标
    if 'indicators' in content_data:
        story.append(Spacer(1, 1*cm))
        indicator_card = build_indicator_card(content_data['indicators'], styles)
        if indicator_card:
            story.append(indicator_card)

    story.append(PageBreak())

    # 处理图表
    chart_images = {}
    if charts_data and 'charts' in charts_data:
        for i, chart in enumerate(charts_data['charts']):
            chart_path = Path(output_path).parent / f"_temp_finance_chart_{i}.png"
            create_chart(chart, str(chart_path))
            chart_images[chart.get('title', f'chart_{i}')] = str(chart_path)

    # 处理内容
    if 'sections' in content_data:
        for section in content_data['sections']:
            section_type = section.get('type', 'text')
            section_title = section.get('title', '')

            if section_title:
                story.append(Paragraph(section_title, styles['SectionTitle']))

            if section_type == 'text':
                content = section.get('content', '')
                paragraphs = content.split('\n\n') if '\n\n' in content else [content]
                for para in paragraphs:
                    if para.strip():
                        para = para.replace('\n', '<br/>')
                        story.append(Paragraph(para, styles['BodyText']))

            elif section_type == 'table':
                data = section.get('data', [])
                highlight_col = section.get('highlight_column')
                if data:
                    table = build_table(data, styles, highlight_col)
                    if table:
                        story.append(Spacer(1, 0.3*cm))
                        story.append(table)
                        story.append(Spacer(1, 0.3*cm))

            elif section_type == 'chart':
                chart_title = section.get('chart_title', section_title)
                if chart_title in chart_images:
                    img = Image(chart_images[chart_title], width=15*cm, height=8*cm)
                    story.append(Spacer(1, 0.3*cm))
                    story.append(img)
                    story.append(Spacer(1, 0.3*cm))

            elif section_type == 'indicators':
                # 单独的指标卡片
                indicators = section.get('indicators', {})
                if indicators:
                    card = build_indicator_card(indicators, styles)
                    if card:
                        story.append(card)

            story.append(Spacer(1, 0.2*cm))

    # 添加未在sections中引用的图表
    if charts_data and 'charts' in charts_data:
        for chart in charts_data['charts']:
            chart_title = chart.get('title', '')
            referenced = any(
                s.get('chart_title', s.get('title', '')) == chart_title
                for s in content_data.get('sections', [])
            )
            if not referenced and chart_title in chart_images:
                story.append(Paragraph(chart_title, styles['SectionTitle']))
                img = Image(chart_images[chart_title], width=15*cm, height=8*cm)
                story.append(img)
                story.append(Spacer(1, 0.5*cm))

    # 生成PDF
    doc.build(story)

    # 清理临时图表
    for img_path in chart_images.values():
        try:
            Path(img_path).unlink()
        except:
            pass

    return output_path


def main():
    parser = argparse.ArgumentParser(description='财务PDF报告生成器')
    parser.add_argument('--title', '-t', required=True, help='报告标题')
    parser.add_argument('--content', '-c', required=True, help='内容JSON文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出PDF文件路径')
    parser.add_argument('--charts', help='图表数据JSON文件路径')
    parser.add_argument('--subtitle', '-s', help='报告副标题')

    args = parser.parse_args()

    content_path = Path(args.content)
    if not content_path.exists():
        print(f"错误：内容文件不存在: {args.content}")
        sys.exit(1)

    with open(content_path, 'r', encoding='utf-8') as f:
        content_data = json.load(f)

    charts_data = None
    if args.charts:
        charts_path = Path(args.charts)
        if charts_path.exists():
            with open(charts_path, 'r', encoding='utf-8') as f:
                charts_data = json.load(f)

    output_path = generate_pdf(
        title=args.title,
        content_data=content_data,
        output_path=args.output,
        charts_data=charts_data,
        subtitle=args.subtitle
    )

    print(f"财务报告已生成: {output_path}")


if __name__ == '__main__':
    main()
