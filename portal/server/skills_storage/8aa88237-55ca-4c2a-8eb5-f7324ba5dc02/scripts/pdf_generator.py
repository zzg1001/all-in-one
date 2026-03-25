#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HR PDF报告生成器
根据内容和图表数据生成专业的PDF报告
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import io

def check_dependencies():
    """检查并提示安装依赖"""
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
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import matplotlib
matplotlib.use('Agg')  # 非GUI模式
import matplotlib.pyplot as plt

# 配色方案
COLORS = {
    'primary': HexColor('#1a73e8'),      # 主色-蓝
    'secondary': HexColor('#34a853'),    # 辅助-绿
    'accent': HexColor('#ea4335'),       # 强调-红
    'warning': HexColor('#fbbc04'),      # 警告-黄
    'dark': HexColor('#202124'),         # 深色文字
    'light': HexColor('#f8f9fa'),        # 浅色背景
    'border': HexColor('#dadce0'),       # 边框
}

# 图表配色
CHART_COLORS = ['#1a73e8', '#34a853', '#ea4335', '#fbbc04', '#673ab7', '#00bcd4', '#ff5722', '#795548']


def register_chinese_font():
    """注册中文字体"""
    font_paths = [
        # Windows
        'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑
        'C:/Windows/Fonts/simsun.ttc',    # 宋体
        'C:/Windows/Fonts/simhei.ttf',    # 黑体
        # macOS
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        # Linux
        '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    ]

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                return 'ChineseFont'
            except:
                continue

    # 如果没有找到中文字体，使用默认字体
    return 'Helvetica'


def create_styles(font_name):
    """创建样式"""
    styles = getSampleStyleSheet()

    # 标题样式
    styles.add(ParagraphStyle(
        name='ReportTitle',
        fontName=font_name,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=COLORS['dark'],
        spaceAfter=20,
    ))

    # 副标题
    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        fontName=font_name,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=HexColor('#5f6368'),
        spaceAfter=30,
    ))

    # 章节标题
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName=font_name,
        fontSize=16,
        leading=22,
        textColor=COLORS['primary'],
        spaceBefore=20,
        spaceAfter=10,
        borderPadding=(0, 0, 5, 0),
    ))

    # 正文 - 修改默认BodyText样式
    styles['BodyText'].fontName = font_name
    styles['BodyText'].fontSize = 11
    styles['BodyText'].leading = 18
    styles['BodyText'].alignment = TA_JUSTIFY
    styles['BodyText'].textColor = COLORS['dark']
    styles['BodyText'].spaceAfter = 10

    # 表格标题
    styles.add(ParagraphStyle(
        name='TableTitle',
        fontName=font_name,
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=COLORS['dark'],
        spaceAfter=8,
    ))

    return styles


def create_chart(chart_data, output_path):
    """创建图表并保存为图片"""
    chart_type = chart_data.get('type', 'bar')
    title = chart_data.get('title', '')
    labels = chart_data.get('labels', [])
    values = chart_data.get('values', [])

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'Heiti SC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(8, 5))

    colors = CHART_COLORS[:len(labels)]

    if chart_type == 'bar':
        bars = ax.bar(labels, values, color=colors)
        ax.set_ylabel('数量')
        # 在柱子上显示数值
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                   str(val), ha='center', va='bottom', fontsize=10)

    elif chart_type == 'pie':
        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors,
                                          autopct='%1.1f%%', startangle=90)
        ax.axis('equal')

    elif chart_type == 'line':
        ax.plot(labels, values, marker='o', color=CHART_COLORS[0], linewidth=2)
        ax.set_ylabel('数量')
        ax.grid(True, linestyle='--', alpha=0.7)
        # 在点上显示数值
        for i, (x, y) in enumerate(zip(labels, values)):
            ax.annotate(str(y), (x, y), textcoords="offset points",
                       xytext=(0, 10), ha='center')

    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    return output_path


def build_table(data, styles):
    """构建表格"""
    if not data or len(data) == 0:
        return None

    # 计算列宽
    col_count = len(data[0])
    col_width = (A4[0] - 4*cm) / col_count

    table = Table(data, colWidths=[col_width] * col_count)

    # 表格样式
    table_style = TableStyle([
        # 表头
        ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), styles['BodyText'].fontName),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        # 数据行
        ('FONTNAME', (0, 1), (-1, -1), styles['BodyText'].fontName),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),

        # 边框
        ('GRID', (0, 0), (-1, -1), 0.5, COLORS['border']),

        # 斑马纹
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, COLORS['light']]),
    ])

    table.setStyle(table_style)
    return table


def generate_pdf(title, content_data, output_path, charts_data=None, subtitle=None):
    """生成PDF报告"""

    # 注册中文字体
    font_name = register_chinese_font()
    styles = create_styles(font_name)

    # 创建文档
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    story = []

    # 封面标题
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph(title, styles['ReportTitle']))

    if subtitle:
        story.append(Paragraph(subtitle, styles['ReportSubtitle']))

    # 生成日期
    date_str = datetime.now().strftime('%Y年%m月%d日')
    story.append(Paragraph(f"生成日期：{date_str}", styles['ReportSubtitle']))

    story.append(PageBreak())

    # 处理图表
    chart_images = {}
    if charts_data and 'charts' in charts_data:
        for i, chart in enumerate(charts_data['charts']):
            chart_path = Path(output_path).parent / f"_temp_chart_{i}.png"
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
                # 支持多段落（用\n\n分隔）
                paragraphs = content.split('\n\n') if '\n\n' in content else [content]
                for para in paragraphs:
                    if para.strip():
                        # 将单个换行转换为<br/>
                        para = para.replace('\n', '<br/>')
                        story.append(Paragraph(para, styles['BodyText']))

            elif section_type == 'table':
                data = section.get('data', [])
                if data:
                    table = build_table(data, styles)
                    if table:
                        story.append(Spacer(1, 0.5*cm))
                        story.append(table)
                        story.append(Spacer(1, 0.5*cm))

            elif section_type == 'chart':
                chart_title = section.get('chart_title', section_title)
                if chart_title in chart_images:
                    img_path = chart_images[chart_title]
                    img = Image(img_path, width=14*cm, height=9*cm)
                    story.append(Spacer(1, 0.5*cm))
                    story.append(img)
                    story.append(Spacer(1, 0.5*cm))

            story.append(Spacer(1, 0.3*cm))

    # 如果没有sections，检查是否有直接的charts要显示
    if charts_data and 'charts' in charts_data:
        for chart in charts_data['charts']:
            chart_title = chart.get('title', '')
            if chart_title in chart_images and chart_title not in [s.get('chart_title', s.get('title', '')) for s in content_data.get('sections', [])]:
                story.append(Paragraph(chart_title, styles['SectionTitle']))
                img = Image(chart_images[chart_title], width=14*cm, height=9*cm)
                story.append(img)
                story.append(Spacer(1, 0.5*cm))

    # 生成PDF
    doc.build(story)

    # 清理临时图表文件
    for img_path in chart_images.values():
        try:
            Path(img_path).unlink()
        except:
            pass

    return output_path


def main():
    parser = argparse.ArgumentParser(description='HR PDF报告生成器')
    parser.add_argument('--title', '-t', required=True, help='报告标题')
    parser.add_argument('--content', '-c', required=True, help='内容JSON文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出PDF文件路径')
    parser.add_argument('--charts', help='图表数据JSON文件路径（可选）')
    parser.add_argument('--subtitle', '-s', help='报告副标题（可选）')

    args = parser.parse_args()

    # 读取内容
    content_path = Path(args.content)
    if not content_path.exists():
        print(f"错误：内容文件不存在: {args.content}")
        sys.exit(1)

    with open(content_path, 'r', encoding='utf-8') as f:
        content_data = json.load(f)

    # 读取图表数据（如果有）
    charts_data = None
    if args.charts:
        charts_path = Path(args.charts)
        if charts_path.exists():
            with open(charts_path, 'r', encoding='utf-8') as f:
                charts_data = json.load(f)

    # 生成PDF
    output_path = generate_pdf(
        title=args.title,
        content_data=content_data,
        output_path=args.output,
        charts_data=charts_data,
        subtitle=args.subtitle
    )

    print(f"PDF已生成: {output_path}")


if __name__ == '__main__':
    main()
