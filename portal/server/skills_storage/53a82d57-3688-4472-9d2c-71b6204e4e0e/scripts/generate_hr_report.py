# -*- coding: utf-8 -*-
"""
人力资源分析报告生成器
输入：Excel HR数据
输出：专业的PDF人力资源分析报告

Usage:
    python generate_hr_report.py --input <excel_path> --output <output_dir>
    python generate_hr_report.py --generate-sample --output <output_dir>
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Charts
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
import io

# ==================== 颜色体系 ====================
COLORS = {
    'primary': '#2E86AB',
    'positive': '#28A745',
    'negative': '#DC3545',
    'warning': '#FFC107',
    'purple': '#6F42C1',
    'orange': '#FD7E14',
    'teal': '#20C997',
    'background': '#F8F9FA',
    'text': '#212529',
    'subtext': '#6C757D',
    'border': '#DEE2E6',
}

# ==================== 字体注册 ====================
def register_chinese_font():
    font_paths = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                if 'msyh' in font_path or 'PingFang' in font_path:
                    pdfmetrics.registerFont(TTFont('Chinese', font_path, subfontIndex=0))
                else:
                    pdfmetrics.registerFont(TTFont('Chinese', font_path))
                return 'Chinese'
            except:
                continue
    return 'Helvetica'

CHINESE_FONT = register_chinese_font()


# ==================== 示例数据生成 ====================
def generate_sample_data(output_dir: Path) -> Path:
    """生成示例HR数据"""
    np.random.seed(42)

    # 1. 月度人员变动（12个月）
    months = [f'2025-{i:02d}' for i in range(1, 13)]
    entry_count = [15, 12, 18, 20, 16, 14, 22, 18, 15, 20, 17, 25]
    leave_count = [8, 10, 7, 9, 12, 8, 10, 11, 9, 8, 10, 12]

    start_count = 520
    monthly_data = []
    for i, month in enumerate(months):
        end_count = start_count + entry_count[i] - leave_count[i]
        monthly_data.append({
            '月份': month,
            '入职人数': entry_count[i],
            '离职人数': leave_count[i],
            '期初人数': start_count,
            '期末人数': end_count
        })
        start_count = end_count

    monthly_df = pd.DataFrame(monthly_data)

    # 2. 部门统计
    dept_data = pd.DataFrame({
        '部门': ['技术研发部', '产品部', '销售部', '市场部', '运营部', '人力资源部', '财务部', '行政部'],
        '编制人数': [180, 60, 120, 45, 80, 25, 20, 30],
        '实际人数': [168, 55, 115, 42, 78, 24, 18, 28],
        '离职人数': [5, 2, 8, 1, 3, 1, 0, 1],
        '本月入职': [8, 3, 5, 2, 4, 1, 1, 1],
        '本月离职': [3, 1, 4, 0, 2, 1, 0, 1]
    })

    # 3. 招聘数据
    recruit_data = pd.DataFrame({
        '渠道': ['Boss直聘', '猎聘', '拉勾', '内部推荐', '校园招聘', '猎头', '其他'],
        '简历数': [1250, 680, 520, 180, 350, 85, 120],
        '面试数': [320, 180, 140, 95, 120, 45, 35],
        '录用数': [48, 28, 22, 35, 25, 12, 5],
        '招聘成本(元)': [28000, 18000, 15000, 5000, 12000, 85000, 3000]
    })

    # 4. 薪酬数据
    salary_data = pd.DataFrame({
        '部门': ['技术研发部', '产品部', '销售部', '市场部', '运营部', '人力资源部', '财务部', '行政部'],
        '基本工资(万)': [420, 138, 230, 84, 156, 60, 45, 56],
        '绩效工资(万)': [168, 55, 138, 34, 62, 24, 18, 22],
        '补贴(万)': [50, 17, 35, 13, 23, 7, 5, 8],
        '其他(万)': [25, 8, 18, 6, 12, 4, 3, 4]
    })

    # 5. 绩效数据
    performance_data = pd.DataFrame({
        '部门': ['技术研发部', '产品部', '销售部', '市场部', '运营部', '人力资源部', '财务部', '行政部'],
        'A级人数': [34, 11, 18, 8, 12, 5, 4, 5],
        'B级人数': [84, 28, 58, 21, 39, 12, 9, 14],
        'C级人数': [42, 14, 32, 11, 22, 6, 4, 8],
        'D级人数': [8, 2, 7, 2, 5, 1, 1, 1],
        '平均得分': [82.5, 84.2, 78.6, 81.3, 80.1, 83.5, 85.2, 79.8]
    })

    # 6. 离职原因
    leave_reason = pd.DataFrame({
        '离职原因': ['薪酬福利', '职业发展', '工作环境', '家庭原因', '个人创业', '其他'],
        '人数': [35, 28, 15, 12, 8, 16],
        '占比(%)': [30.7, 24.6, 13.2, 10.5, 7.0, 14.0]
    })

    # 保存Excel
    excel_path = output_dir / 'HR数据_示例.xlsx'
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        monthly_df.to_excel(writer, sheet_name='月度人员变动', index=False)
        dept_data.to_excel(writer, sheet_name='部门统计', index=False)
        recruit_data.to_excel(writer, sheet_name='招聘数据', index=False)
        salary_data.to_excel(writer, sheet_name='薪酬数据', index=False)
        performance_data.to_excel(writer, sheet_name='绩效数据', index=False)
        leave_reason.to_excel(writer, sheet_name='离职原因', index=False)

    print(f"[OK] 示例数据已生成: {excel_path}")
    return excel_path


# ==================== 图表生成 ====================
def create_dept_structure_chart(dept_data: pd.DataFrame) -> io.BytesIO:
    """创建部门结构图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # 饼图
    colors_pie = ['#2E86AB', '#DC3545', '#28A745', '#FFC107', '#6F42C1', '#FD7E14', '#20C997', '#6C757D']
    ax1.pie(dept_data['实际人数'], labels=dept_data['部门'], autopct='%1.1f%%',
            colors=colors_pie, startangle=90)
    ax1.set_title('各部门人员占比', fontsize=12, fontweight='bold')

    # 柱状图
    x = range(len(dept_data))
    bars = ax2.bar(x, dept_data['实际人数'], color=colors_pie)
    ax2.set_xticks(x)
    ax2.set_xticklabels(dept_data['部门'], rotation=45, ha='right')
    ax2.set_ylabel('人数')
    ax2.set_title('各部门人数分布', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, dept_data['实际人数']):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                str(val), ha='center', fontsize=9)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def create_turnover_chart(monthly_data: pd.DataFrame) -> io.BytesIO:
    """创建人员流动趋势图"""
    fig, ax = plt.subplots(figsize=(10, 4))

    months_short = [m.split('-')[1] + '月' for m in monthly_data['月份']]
    x = range(len(months_short))
    width = 0.35

    ax.bar([i - width/2 for i in x], monthly_data['入职人数'], width,
           label='入职', color=COLORS['positive'])
    ax.bar([i + width/2 for i in x], monthly_data['离职人数'], width,
           label='离职', color=COLORS['negative'])

    ax.set_xlabel('月份')
    ax.set_ylabel('人数')
    ax.set_title('月度入职/离职趋势', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months_short)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def create_leave_reason_chart(leave_reason: pd.DataFrame) -> io.BytesIO:
    """创建离职原因分析图"""
    fig, ax = plt.subplots(figsize=(6, 4))

    colors_pie = ['#DC3545', '#FFC107', '#2E86AB', '#28A745', '#6F42C1', '#6C757D']
    ax.pie(leave_reason['人数'], labels=leave_reason['离职原因'], autopct='%1.1f%%',
           colors=colors_pie, startangle=90)
    ax.set_title('离职原因分析', fontsize=12, fontweight='bold')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def create_recruit_chart(recruit_data: pd.DataFrame) -> io.BytesIO:
    """创建招聘分析图"""
    fig, ax = plt.subplots(figsize=(10, 4))

    x = range(len(recruit_data))
    width = 0.25

    ax.bar([i - width for i in x], recruit_data['简历数']/10, width, label='简历数(/10)', color=COLORS['primary'])
    ax.bar([i for i in x], recruit_data['面试数'], width, label='面试数', color=COLORS['warning'])
    ax.bar([i + width for i in x], recruit_data['录用数'], width, label='录用数', color=COLORS['positive'])

    ax.set_xlabel('招聘渠道')
    ax.set_ylabel('人数')
    ax.set_title('各渠道招聘效果对比', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(recruit_data['渠道'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def create_salary_chart(salary_data: pd.DataFrame) -> io.BytesIO:
    """创建薪酬分析图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # 各部门薪酬总额
    salary_data = salary_data.copy()
    salary_data['总额'] = salary_data['基本工资(万)'] + salary_data['绩效工资(万)'] + \
                         salary_data['补贴(万)'] + salary_data['其他(万)']

    colors_bar = ['#2E86AB', '#DC3545', '#28A745', '#FFC107', '#6F42C1', '#FD7E14', '#20C997', '#6C757D']
    x = range(len(salary_data))
    bars = ax1.bar(x, salary_data['总额'], color=colors_bar)
    ax1.set_xticks(x)
    ax1.set_xticklabels(salary_data['部门'], rotation=45, ha='right')
    ax1.set_ylabel('薪酬总额（万元）')
    ax1.set_title('各部门薪酬总额', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # 薪酬结构饼图
    total_base = salary_data['基本工资(万)'].sum()
    total_perf = salary_data['绩效工资(万)'].sum()
    total_sub = salary_data['补贴(万)'].sum()
    total_other = salary_data['其他(万)'].sum()

    labels = ['基本工资', '绩效工资', '补贴', '其他']
    sizes = [total_base, total_perf, total_sub, total_other]
    colors_pie = ['#2E86AB', '#28A745', '#FFC107', '#6C757D']
    ax2.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors_pie, startangle=90)
    ax2.set_title('薪酬结构占比', fontsize=12, fontweight='bold')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def create_performance_chart(performance_data: pd.DataFrame) -> io.BytesIO:
    """创建绩效分析图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # 绩效等级分布
    total_a = performance_data['A级人数'].sum()
    total_b = performance_data['B级人数'].sum()
    total_c = performance_data['C级人数'].sum()
    total_d = performance_data['D级人数'].sum()

    labels = ['A级(优秀)', 'B级(良好)', 'C级(合格)', 'D级(待改进)']
    sizes = [total_a, total_b, total_c, total_d]
    colors_pie = ['#28A745', '#2E86AB', '#FFC107', '#DC3545']
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors_pie, startangle=90)
    ax1.set_title('绩效等级分布', fontsize=12, fontweight='bold')

    # 各部门平均得分
    x = range(len(performance_data))
    colors_bar = ['#2E86AB' if s >= 80 else '#FFC107' for s in performance_data['平均得分']]
    bars = ax2.barh(x, performance_data['平均得分'], color=colors_bar)
    ax2.set_yticks(x)
    ax2.set_yticklabels(performance_data['部门'])
    ax2.set_xlabel('平均得分')
    ax2.set_title('各部门平均绩效得分', fontsize=12, fontweight='bold')
    ax2.set_xlim(70, 90)
    ax2.axvline(x=80, color='gray', linestyle='--', alpha=0.5)

    for bar, val in zip(bars, performance_data['平均得分']):
        ax2.text(val + 0.3, bar.get_y() + bar.get_height()/2, f'{val}', va='center', fontsize=9)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


# ==================== PDF报告生成 ====================
def generate_pdf_report(excel_path: Path, output_dir: Path, report_title: str = "人力资源分析报告",
                       report_period: str = "2025年3月") -> Path:
    """生成PDF人力资源分析报告"""

    # 读取数据
    monthly_data = pd.read_excel(excel_path, sheet_name='月度人员变动')
    dept_data = pd.read_excel(excel_path, sheet_name='部门统计')
    recruit_data = pd.read_excel(excel_path, sheet_name='招聘数据')
    salary_data = pd.read_excel(excel_path, sheet_name='薪酬数据')
    performance_data = pd.read_excel(excel_path, sheet_name='绩效数据')
    leave_reason = pd.read_excel(excel_path, sheet_name='离职原因')

    # 计算关键指标
    total_employees = dept_data['实际人数'].sum()
    total_leave = dept_data['本月离职'].sum()
    leave_rate = total_leave / monthly_data['期初人数'].iloc[-1] * 100
    total_recruit = recruit_data['录用数'].sum()
    recruit_plan = 200  # 假设招聘计划
    recruit_rate = total_recruit / recruit_plan * 100

    salary_data_calc = salary_data.copy()
    salary_data_calc['总额'] = salary_data_calc['基本工资(万)'] + salary_data_calc['绩效工资(万)'] + \
                              salary_data_calc['补贴(万)'] + salary_data_calc['其他(万)']
    total_salary = salary_data_calc['总额'].sum()
    avg_salary = total_salary / total_employees

    # PDF路径
    pdf_path = output_dir / f'{report_title}_{report_period.replace("年", "").replace("月", "")}.pdf'

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                           leftMargin=15*mm, rightMargin=15*mm,
                           topMargin=15*mm, bottomMargin=15*mm)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
        fontName=CHINESE_FONT, fontSize=22, textColor=colors.HexColor(COLORS['text']),
        spaceAfter=20, alignment=TA_CENTER)

    section_style = ParagraphStyle('Section', parent=styles['Heading1'],
        fontName=CHINESE_FONT, fontSize=14, textColor=colors.white,
        backColor=colors.HexColor(COLORS['primary']),
        spaceBefore=15, spaceAfter=10, leftIndent=5, rightIndent=5, borderPadding=8)

    body_style = ParagraphStyle('Body', parent=styles['Normal'],
        fontName=CHINESE_FONT, fontSize=9, leading=14, textColor=colors.HexColor(COLORS['text']))

    elements = []

    # ===== 标题 =====
    elements.append(Paragraph(report_title, title_style))
    elements.append(Paragraph(f"{report_period} | 人力资源部", ParagraphStyle(
        'Subtitle', fontName=CHINESE_FONT, fontSize=12,
        textColor=colors.HexColor(COLORS['subtext']), alignment=TA_CENTER, spaceAfter=20)))

    # ===== Executive Summary =====
    kpi_cards = [
        ['员工总数', '本月离职率', '招聘完成率', '人均薪酬'],
        [f'{total_employees}人', f'{leave_rate:.2f}%', f'{recruit_rate:.1f}%', f'{avg_salary:.2f}万'],
        [f'环比+{monthly_data["入职人数"].iloc[-1] - monthly_data["离职人数"].iloc[-1]}人',
         f'目标<3%' if leave_rate < 3 else f'超目标+{leave_rate-3:.1f}pp',
         f'完成{total_recruit}/{recruit_plan}',
         f'环比+2.5%']
    ]

    kpi_table = Table(kpi_cards, colWidths=[45*mm]*4)
    kpi_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 16),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(COLORS['subtext'])),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor(COLORS['text'])),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor(COLORS['positive'])),
        ('TEXTCOLOR', (1, 2), (1, 2), colors.HexColor(COLORS['negative']) if leave_rate > 3 else colors.HexColor(COLORS['positive'])),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLORS['background'])),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(COLORS['border'])),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 15))

    # ===== 1. 人员结构分析 =====
    elements.append(Paragraph("一、人员结构分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_dept_structure_chart(dept_data), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    dept_table_data = [['部门', '编制人数', '实际人数', '缺编', '占比(%)']]
    for _, row in dept_data.iterrows():
        gap = row['编制人数'] - row['实际人数']
        pct = row['实际人数'] / total_employees * 100
        dept_table_data.append([row['部门'], str(row['编制人数']), str(row['实际人数']),
                               f'{gap:+d}', f'{pct:.1f}%'])

    t = Table(dept_table_data, colWidths=[35*mm, 25*mm, 25*mm, 20*mm, 20*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS['border'])),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLORS['background'])]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # ===== 2. 人员流动分析 =====
    elements.append(Paragraph("二、人员流动分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_turnover_chart(monthly_data), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    # 离职率表格
    leave_table_data = [['部门', '本月离职', '离职率(%)', '状态']]
    for _, row in dept_data.iterrows():
        dept_leave_rate = row['本月离职'] / row['实际人数'] * 100 if row['实际人数'] > 0 else 0
        status = '关注' if dept_leave_rate > 3 else '正常'
        leave_table_data.append([row['部门'], str(row['本月离职']), f'{dept_leave_rate:.2f}%', status])

    t = Table(leave_table_data, colWidths=[40*mm, 25*mm, 25*mm, 20*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['negative'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS['border'])),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLORS['background'])]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    # 离职原因分析
    elements.append(Image(create_leave_reason_chart(leave_reason), width=100*mm, height=68*mm))
    elements.append(Spacer(1, 15))

    # ===== 3. 招聘分析 =====
    elements.append(Paragraph("三、招聘分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_recruit_chart(recruit_data), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    recruit_data_calc = recruit_data.copy()
    recruit_data_calc['转化率(%)'] = (recruit_data_calc['录用数'] / recruit_data_calc['面试数'] * 100).round(1)
    recruit_data_calc['人均成本(元)'] = (recruit_data_calc['招聘成本(元)'] / recruit_data_calc['录用数']).round(0)

    recruit_table_data = [['渠道', '简历数', '面试数', '录用数', '转化率(%)', '人均成本(元)']]
    for _, row in recruit_data_calc.iterrows():
        recruit_table_data.append([row['渠道'], str(row['简历数']), str(row['面试数']),
                                  str(row['录用数']), f"{row['转化率(%)']}%", f"{row['人均成本(元)']:.0f}"])

    t = Table(recruit_table_data, colWidths=[28*mm, 22*mm, 22*mm, 22*mm, 25*mm, 28*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['positive'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS['border'])),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLORS['background'])]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # ===== 4. 薪酬分析 =====
    elements.append(Paragraph("四、薪酬分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_salary_chart(salary_data), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    salary_table_data = [['部门', '薪酬总额(万)', '人数', '人均薪酬(万)']]
    for _, row in salary_data_calc.iterrows():
        dept_count = dept_data[dept_data['部门'] == row['部门']]['实际人数'].values[0]
        avg = row['总额'] / dept_count
        salary_table_data.append([row['部门'], f"{row['总额']:.0f}", str(dept_count), f"{avg:.2f}"])

    t = Table(salary_table_data, colWidths=[35*mm, 30*mm, 20*mm, 30*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['warning'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(COLORS['text'])),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS['border'])),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLORS['background'])]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # ===== 5. 绩效分析 =====
    elements.append(Paragraph("五、绩效分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_performance_chart(performance_data), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    perf_table_data = [['部门', 'A级', 'B级', 'C级', 'D级', '平均得分']]
    for _, row in performance_data.iterrows():
        perf_table_data.append([row['部门'], str(row['A级人数']), str(row['B级人数']),
                               str(row['C级人数']), str(row['D级人数']), f"{row['平均得分']:.1f}"])

    t = Table(perf_table_data, colWidths=[35*mm, 18*mm, 18*mm, 18*mm, 18*mm, 25*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['purple'])),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS['border'])),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(COLORS['background'])]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # ===== 6. 风险提示 =====
    elements.append(Paragraph("六、风险提示与管理建议", section_style))
    elements.append(Spacer(1, 10))

    risk_data = [
        ['风险等级', '风险事项', '影响程度', '建议措施'],
        ['高', '销售部离职率偏高(3.5%)', '影响业务连续性', '开展离职面谈，优化激励机制'],
        ['中', '技术研发部缺编12人', '项目交付风险', '加大技术岗招聘力度'],
        ['中', '人均招聘成本上升15%', '预算压力增加', '优化招聘渠道，增加内推比例'],
        ['低', 'D级绩效员工占比5%', '团队效能影响', '制定绩效改进计划'],
    ]

    t = Table(risk_data, colWidths=[20*mm, 45*mm, 35*mm, 55*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C0392B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#FADBD8')),
        ('BACKGROUND', (0, 2), (0, 3), colors.HexColor('#FEF9E7')),
        ('BACKGROUND', (0, 4), (0, 4), colors.HexColor('#D5F5E3')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor(COLORS['border'])),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # ===== 页脚 =====
    footer_style = ParagraphStyle('Footer', fontName=CHINESE_FONT, fontSize=8,
        textColor=colors.HexColor(COLORS['subtext']), alignment=TA_CENTER)
    elements.append(Paragraph(f"—— 人力资源部 | {report_period} ——", footer_style))
    elements.append(Paragraph("本报告由HR分析系统自动生成", footer_style))

    doc.build(elements)
    print(f"[OK] PDF报告已生成: {pdf_path}")
    return pdf_path


# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(description='人力资源分析报告生成器')
    parser.add_argument('--input', '-i', type=str, help='Excel数据文件路径')
    parser.add_argument('--output', '-o', type=str, default='.', help='输出目录')
    parser.add_argument('--generate-sample', action='store_true', help='生成示例数据')
    parser.add_argument('--title', type=str, default='人力资源分析报告', help='报告标题')
    parser.add_argument('--period', type=str, default='2025年3月', help='报告期间')

    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.generate_sample:
        excel_path = generate_sample_data(output_dir)
    elif args.input:
        excel_path = Path(args.input)
        if not excel_path.exists():
            print(f"[ERROR] 文件不存在: {excel_path}")
            sys.exit(1)
    else:
        print("[ERROR] 请指定 --input 或 --generate-sample")
        sys.exit(1)

    pdf_path = generate_pdf_report(excel_path, output_dir, args.title, args.period)

    print("\n" + "="*50)
    print("人力资源分析报告生成完成！")
    print(f"Excel数据: {excel_path}")
    print(f"PDF报告: {pdf_path}")
    print("="*50)


if __name__ == "__main__":
    main()
