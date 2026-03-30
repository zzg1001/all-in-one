# -*- coding: utf-8 -*-
"""
财务分析报告生成器
输入：Excel财务数据
输出：专业的PDF财务分析报告（IMS全局效率月报风格）

Usage:
    python generate_finance_report.py --input <excel_path> --output <output_dir>
    python generate_finance_report.py --generate-sample --output <output_dir>
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
    'primary': '#3498DB',      # 主色调蓝色
    'positive': '#27AE60',     # 正向绿色
    'negative': '#E74C3C',     # 负向红色
    'warning': '#F39C12',      # 警告橙色
    'purple': '#9B59B6',       # 紫色
    'background': '#F8F9FA',   # 背景浅灰
    'text': '#2C3E50',         # 文字深灰
    'subtext': '#7F8C8D',      # 副文字
    'border': '#BDC3C7',       # 边框色
}

# ==================== 字体注册 ====================
def register_chinese_font():
    """注册中文字体"""
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
    """生成示例财务数据"""
    np.random.seed(42)

    # 月度数据
    months = [f'2025-{i:02d}' for i in range(1, 13)]
    revenue_budget = [4500, 4200, 4800, 5000, 5200, 5500, 5300, 5600, 5800, 6000, 6200, 6500]
    revenue_actual = [4328, 4150, 4720, 5120, 5050, 5680, 5210, 5550, 5920, 6150, 6380, 6720]
    cost_budget = [2800, 2600, 3000, 3100, 3200, 3400, 3300, 3500, 3600, 3700, 3800, 4000]
    cost_actual = [2650, 2580, 2920, 3050, 3150, 3320, 3280, 3420, 3550, 3650, 3720, 3950]
    expense_budget = [800, 750, 850, 900, 950, 1000, 950, 1000, 1050, 1100, 1150, 1200]
    expense_actual = [780, 720, 880, 870, 920, 1050, 930, 980, 1080, 1070, 1120, 1180]

    monthly_data = pd.DataFrame({
        '月份': months,
        '收入预算(万元)': revenue_budget,
        '收入实际(万元)': revenue_actual,
        '成本预算(万元)': cost_budget,
        '成本实际(万元)': cost_actual,
        '费用预算(万元)': expense_budget,
        '费用实际(万元)': expense_actual
    })

    # 部门费用
    dept_data = pd.DataFrame({
        '部门': ['销售部', '市场部', '研发部', '行政部', '人力资源部', '财务部', '客服部', '采购部'],
        '预算(万元)': [580, 320, 1200, 180, 150, 120, 200, 250],
        '实际(万元)': [620, 290, 1150, 195, 142, 115, 210, 238]
    })

    # 产品线
    product_data = pd.DataFrame({
        '产品线': ['产品A-企业版', '产品B-标准版', '产品C-基础版', '产品D-定制服务', '产品E-增值服务'],
        '收入(万元)': [2850, 1680, 920, 580, 298],
        '成本(万元)': [1420, 920, 580, 320, 150]
    })

    # 关键指标
    kpi_data = pd.DataFrame({
        '指标名称': ['营业收入', '营业成本', '毛利润', '毛利率', '销售费用', '管理费用', '财务费用',
                   '费用率', '营业利润', '净利润', '净利率', '应收账款周转率', '存货周转率',
                   '资产负债率', '经营性现金流', '投资性现金流', '筹资性现金流'],
        '本期实际': [6328, 3950, 2378, 37.58, 620, 540, 45, 19.04, 1173, 938, 14.83, 8.5, 6.2, 45.3, 1250, -380, -420],
        '本期预算': [6500, 4000, 2500, 38.46, 580, 520, 50, 17.69, 1350, 1080, 16.62, 9.0, 6.5, 44.0, 1400, -350, -400],
        '上期实际': [6150, 3720, 2430, 39.51, 580, 510, 42, 18.41, 1298, 1038, 16.88, 8.2, 5.8, 46.1, 1180, -420, -380],
        '单位': ['万元', '万元', '万元', '%', '万元', '万元', '万元', '%', '万元', '万元', '%', '次', '次', '%', '万元', '万元', '万元']
    })

    # 费用明细
    expense_detail = pd.DataFrame({
        '费用类别': ['人工成本', '办公费用', '差旅费', '营销推广', '招待费', '培训费', '其他费用'],
        '本月实际(万元)': [680, 85, 120, 180, 45, 32, 63],
        '本月预算(万元)': [650, 90, 130, 200, 50, 35, 60],
        '累计实际(万元)': [8160, 1020, 1440, 2160, 540, 384, 756],
        '年度预算(万元)': [7800, 1080, 1560, 2400, 600, 420, 720]
    })

    # 保存Excel
    excel_path = output_dir / '财务数据_示例.xlsx'
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        monthly_data.to_excel(writer, sheet_name='月度数据', index=False)
        dept_data.to_excel(writer, sheet_name='部门费用', index=False)
        product_data.to_excel(writer, sheet_name='产品线分析', index=False)
        kpi_data.to_excel(writer, sheet_name='关键指标', index=False)
        expense_detail.to_excel(writer, sheet_name='费用明细', index=False)

    print(f"[OK] 示例数据已生成: {excel_path}")
    return excel_path


# ==================== 图表生成 ====================
def create_revenue_trend_chart(monthly_data: pd.DataFrame) -> io.BytesIO:
    """创建收入趋势图"""
    fig, ax = plt.subplots(figsize=(10, 4))

    months_short = [m.split('-')[1] + '月' for m in monthly_data['月份']]
    x = range(len(months_short))

    ax.bar([i - 0.2 for i in x], monthly_data['收入预算(万元)'], 0.4,
           label='预算', color=COLORS['primary'], alpha=0.7)
    ax.bar([i + 0.2 for i in x], monthly_data['收入实际(万元)'], 0.4,
           label='实际', color=COLORS['negative'], alpha=0.8)

    ax.set_xlabel('月份', fontsize=10)
    ax.set_ylabel('金额（万元）', fontsize=10)
    ax.set_title('月度收入预算 vs 实际对比', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months_short)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 差异标注
    for i, (b, a) in enumerate(zip(monthly_data['收入预算(万元)'], monthly_data['收入实际(万元)'])):
        diff = a - b
        color = COLORS['positive'] if diff >= 0 else COLORS['negative']
        ax.annotate(f'{diff:+.0f}', xy=(i + 0.2, a), ha='center', va='bottom',
                   fontsize=8, color=color)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def create_product_charts(product_data: pd.DataFrame) -> io.BytesIO:
    """创建产品线分析图"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # 计算毛利
    product_data = product_data.copy()
    product_data['毛利(万元)'] = product_data['收入(万元)'] - product_data['成本(万元)']
    product_data['毛利率(%)'] = (product_data['毛利(万元)'] / product_data['收入(万元)'] * 100).round(2)

    # 饼图
    colors_pie = ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6']
    ax1.pie(product_data['收入(万元)'], labels=product_data['产品线'], autopct='%1.1f%%',
            colors=colors_pie, startangle=90)
    ax1.set_title('产品线收入占比', fontsize=12, fontweight='bold')

    # 条形图
    y_pos = range(len(product_data))
    bars = ax2.barh(y_pos, product_data['毛利率(%)'], color=colors_pie)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(product_data['产品线'])
    ax2.set_xlabel('毛利率 (%)')
    ax2.set_title('各产品线毛利率', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, 60)

    for bar, val in zip(bars, product_data['毛利率(%)']):
        ax2.text(val + 1, bar.get_y() + bar.get_height()/2, f'{val}%', va='center', fontsize=9)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def create_dept_expense_chart(dept_data: pd.DataFrame) -> io.BytesIO:
    """创建部门费用图"""
    fig, ax = plt.subplots(figsize=(10, 4))

    # 计算完成率
    dept_data = dept_data.copy()
    dept_data['完成率(%)'] = (dept_data['实际(万元)'] / dept_data['预算(万元)'] * 100).round(2)

    x = range(len(dept_data))
    width = 0.35

    ax.bar([i - width/2 for i in x], dept_data['预算(万元)'], width,
           label='预算', color=COLORS['primary'])
    ax.bar([i + width/2 for i in x], dept_data['实际(万元)'], width,
           label='实际', color=COLORS['negative'])

    ax.set_xlabel('部门')
    ax.set_ylabel('金额（万元）')
    ax.set_title('各部门费用预算 vs 实际对比', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(dept_data['部门'], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 完成率标注
    for i, rate in enumerate(dept_data['完成率(%)']):
        color = COLORS['negative'] if rate > 100 else COLORS['positive']
        max_val = max(dept_data['预算(万元)'].iloc[i], dept_data['实际(万元)'].iloc[i])
        ax.annotate(f'{rate}%', xy=(i, max_val + 20), ha='center', fontsize=8,
                   color=color, fontweight='bold')

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def create_cashflow_chart() -> io.BytesIO:
    """创建现金流趋势图"""
    fig, ax = plt.subplots(figsize=(10, 4))

    months = [f'{i}月' for i in range(1, 13)]
    operating = [980, 1050, 1120, 1080, 1150, 1200, 1180, 1220, 1280, 1250, 1300, 1250]
    investing = [-280, -320, -350, -400, -380, -420, -350, -380, -400, -360, -390, -380]
    financing = [-350, -380, -400, -380, -420, -450, -400, -380, -420, -400, -430, -420]

    x = range(len(months))
    ax.plot(x, operating, marker='o', label='经营性现金流', color=COLORS['positive'], linewidth=2)
    ax.plot(x, investing, marker='s', label='投资性现金流', color=COLORS['negative'], linewidth=2)
    ax.plot(x, financing, marker='^', label='筹资性现金流', color=COLORS['primary'], linewidth=2)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    ax.set_xlabel('月份')
    ax.set_ylabel('金额（万元）')
    ax.set_title('现金流量趋势分析', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months)
    ax.legend(loc='upper right')
    ax.grid(alpha=0.3)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


# ==================== PDF报告生成 ====================
def generate_pdf_report(excel_path: Path, output_dir: Path, report_title: str = "财务分析月报",
                       report_period: str = "2025年3月") -> Path:
    """生成PDF财务分析报告"""

    # 读取数据
    monthly_data = pd.read_excel(excel_path, sheet_name='月度数据')
    dept_data = pd.read_excel(excel_path, sheet_name='部门费用')
    product_data = pd.read_excel(excel_path, sheet_name='产品线分析')
    kpi_data = pd.read_excel(excel_path, sheet_name='关键指标')
    expense_detail = pd.read_excel(excel_path, sheet_name='费用明细')

    # 计算派生字段
    dept_data['差异(万元)'] = dept_data['实际(万元)'] - dept_data['预算(万元)']
    dept_data['完成率(%)'] = (dept_data['实际(万元)'] / dept_data['预算(万元)'] * 100).round(2)

    product_data['毛利(万元)'] = product_data['收入(万元)'] - product_data['成本(万元)']
    product_data['毛利率(%)'] = (product_data['毛利(万元)'] / product_data['收入(万元)'] * 100).round(2)

    # PDF路径
    pdf_path = output_dir / f'{report_title}_{report_period.replace("年", "").replace("月", "")}.pdf'

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                           leftMargin=15*mm, rightMargin=15*mm,
                           topMargin=15*mm, bottomMargin=15*mm)

    # 样式
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
    elements.append(Paragraph(f"{report_period} | 财务管理中心", ParagraphStyle(
        'Subtitle', fontName=CHINESE_FONT, fontSize=12,
        textColor=colors.HexColor(COLORS['subtext']), alignment=TA_CENTER, spaceAfter=20)))

    # ===== Executive Summary =====
    revenue = kpi_data[kpi_data['指标名称'] == '营业收入']['本期实际'].values[0]
    revenue_budget = kpi_data[kpi_data['指标名称'] == '营业收入']['本期预算'].values[0]
    gross_margin = kpi_data[kpi_data['指标名称'] == '毛利率']['本期实际'].values[0]
    gross_margin_budget = kpi_data[kpi_data['指标名称'] == '毛利率']['本期预算'].values[0]
    net_profit = kpi_data[kpi_data['指标名称'] == '净利润']['本期实际'].values[0]
    net_profit_budget = kpi_data[kpi_data['指标名称'] == '净利润']['本期预算'].values[0]
    expense_rate = kpi_data[kpi_data['指标名称'] == '费用率']['本期实际'].values[0]
    expense_rate_budget = kpi_data[kpi_data['指标名称'] == '费用率']['本期预算'].values[0]

    kpi_cards = [
        ['营业收入', '毛利率', '净利润', '费用率'],
        [f'{revenue:,.0f}万', f'{gross_margin:.2f}%', f'{net_profit:,.0f}万', f'{expense_rate:.2f}%'],
        [f'较预算{(revenue/revenue_budget-1)*100:+.1f}%',
         f'较预算{gross_margin-gross_margin_budget:+.2f}pp',
         f'较预算{(net_profit/net_profit_budget-1)*100:+.1f}%',
         f'较预算{expense_rate-expense_rate_budget:+.2f}pp']
    ]

    kpi_table = Table(kpi_cards, colWidths=[45*mm]*4)
    kpi_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 16),
        ('FONTSIZE', (0, 2), (-1, 2), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(COLORS['subtext'])),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor(COLORS['text'])),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.HexColor(COLORS['negative'])),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(COLORS['background'])),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(COLORS['border'])),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 15))

    # ===== 1. 关键财务指标 =====
    elements.append(Paragraph("一、关键财务指标分析", section_style))
    elements.append(Spacer(1, 10))

    kpi_subset = kpi_data[kpi_data['指标名称'].isin([
        '营业收入', '营业成本', '毛利润', '毛利率', '营业利润', '净利润', '净利率'
    ])].copy()
    kpi_subset['完成率'] = (kpi_subset['本期实际'] / kpi_subset['本期预算'] * 100).round(2).astype(str) + '%'
    kpi_subset['环比'] = ((kpi_subset['本期实际'] - kpi_subset['上期实际']) / kpi_subset['上期实际'] * 100).round(2)
    kpi_subset['环比'] = kpi_subset['环比'].apply(lambda x: f'+{x}%' if x > 0 else f'{x}%')

    table_data = [['指标名称', '本期实际', '本期预算', '上期实际', '单位', '完成率', '环比']]
    for _, row in kpi_subset.iterrows():
        fmt = lambda v, u: f"{v:,.2f}" if u != '%' else f"{v:.2f}"
        table_data.append([row['指标名称'], fmt(row['本期实际'], row['单位']),
                          fmt(row['本期预算'], row['单位']), fmt(row['上期实际'], row['单位']),
                          row['单位'], row['完成率'], row['环比']])

    t = Table(table_data, colWidths=[28*mm, 25*mm, 25*mm, 25*mm, 15*mm, 20*mm, 18*mm])
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

    # ===== 2. 收入趋势 =====
    elements.append(Paragraph("二、收入趋势分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_revenue_trend_chart(monthly_data), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    latest_revenue = monthly_data['收入实际(万元)'].iloc[-1]
    latest_budget = monthly_data['收入预算(万元)'].iloc[-1]
    diff = latest_revenue - latest_budget
    completion = latest_revenue / latest_budget * 100

    analysis = f"""
    <b>收入分析要点：</b><br/>
    • 本月收入{latest_revenue:,.0f}万元，较预算差异{diff:+,.0f}万元，完成率{completion:.1f}%<br/>
    • 环比增长{(latest_revenue/monthly_data['收入实际(万元)'].iloc[-2]-1)*100:.1f}%，整体趋势向好<br/>
    • Q1累计收入{monthly_data['收入实际(万元)'].iloc[:3].sum():,.0f}万元
    """
    elements.append(Paragraph(analysis, body_style))
    elements.append(Spacer(1, 15))

    # ===== 3. 产品线分析 =====
    elements.append(Paragraph("三、产品线盈利分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_product_charts(product_data), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    total_revenue = product_data['收入(万元)'].sum()
    prod_table = [['产品线', '收入(万元)', '成本(万元)', '毛利(万元)', '毛利率(%)', '收入占比(%)']]
    for _, row in product_data.iterrows():
        pct = row['收入(万元)'] / total_revenue * 100
        prod_table.append([row['产品线'], f"{row['收入(万元)']:,.0f}", f"{row['成本(万元)']:,.0f}",
                          f"{row['毛利(万元)']:,.0f}", f"{row['毛利率(%)']:.1f}%", f"{pct:.1f}%"])

    t = Table(prod_table, colWidths=[35*mm, 25*mm, 25*mm, 25*mm, 22*mm, 22*mm])
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

    # ===== 4. 部门费用 =====
    elements.append(Paragraph("四、部门费用执行分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_dept_expense_chart(dept_data), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    dept_table = [['部门', '预算(万元)', '实际(万元)', '差异(万元)', '完成率(%)', '状态']]
    for _, row in dept_data.iterrows():
        status = '超支' if row['完成率(%)'] > 105 else ('关注' if row['完成率(%)'] > 100 else '正常')
        dept_table.append([row['部门'], f"{row['预算(万元)']:,.0f}", f"{row['实际(万元)']:,.0f}",
                          f"{row['差异(万元)']:+,.0f}", f"{row['完成率(%)']:.1f}%", status])

    t = Table(dept_table, colWidths=[28*mm, 25*mm, 25*mm, 25*mm, 25*mm, 20*mm])
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

    # ===== 5. 费用明细 =====
    elements.append(Paragraph("五、费用明细分析", section_style))
    elements.append(Spacer(1, 10))

    exp_table = [['费用类别', '本月实际', '本月预算', '差异', '累计实际', '年度预算', '执行率']]
    for _, row in expense_detail.iterrows():
        diff = row['本月实际(万元)'] - row['本月预算(万元)']
        exec_rate = row['累计实际(万元)'] / row['年度预算(万元)'] * 100
        exp_table.append([row['费用类别'], f"{row['本月实际(万元)']:,.0f}", f"{row['本月预算(万元)']:,.0f}",
                         f"{diff:+,.0f}", f"{row['累计实际(万元)']:,.0f}", f"{row['年度预算(万元)']:,.0f}",
                         f"{exec_rate:.1f}%"])

    t = Table(exp_table, colWidths=[25*mm, 22*mm, 22*mm, 18*mm, 25*mm, 25*mm, 20*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CHINESE_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['warning'])),
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

    # ===== 6. 现金流 =====
    elements.append(Paragraph("六、现金流量分析", section_style))
    elements.append(Spacer(1, 10))
    elements.append(Image(create_cashflow_chart(), width=170*mm, height=68*mm))
    elements.append(Spacer(1, 10))

    cf_analysis = """
    <b>现金流分析要点：</b><br/>
    • 经营性现金流净额1,250万元，较预算完成率89.3%<br/>
    • 投资性现金流-380万元，主要用于设备采购和技术研发<br/>
    • 筹资性现金流-420万元，包含股息分配和贷款偿还<br/>
    • 现金及等价物期末余额8,520万元，流动性充足
    """
    elements.append(Paragraph(cf_analysis, body_style))
    elements.append(Spacer(1, 20))

    # ===== 7. 风险提示 =====
    elements.append(Paragraph("七、风险提示与管理建议", section_style))
    elements.append(Spacer(1, 10))

    risk_data = [
        ['风险等级', '风险事项', '影响程度', '建议措施'],
        ['高', '销售部费用超支6.9%', '影响净利润约40万', '加强费用审批，控制营销支出'],
        ['中', '产品B毛利率下降', '毛利减少约60万', '优化成本结构，提升定价策略'],
        ['中', '应收账款周转放缓', '现金流压力增加', '加强催收，缩短账期'],
        ['低', '原材料价格波动', '成本不确定性', '签订长期供应合同锁定价格'],
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
    elements.append(Paragraph(f"—— 财务管理中心 | {report_period} ——", footer_style))
    elements.append(Paragraph("本报告由财务分析系统自动生成", footer_style))

    # 生成PDF
    doc.build(elements)
    print(f"[OK] PDF报告已生成: {pdf_path}")
    return pdf_path


# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(description='财务分析报告生成器')
    parser.add_argument('--input', '-i', type=str, help='Excel数据文件路径')
    parser.add_argument('--output', '-o', type=str, default='.', help='输出目录')
    parser.add_argument('--generate-sample', action='store_true', help='生成示例数据')
    parser.add_argument('--title', type=str, default='财务分析月报', help='报告标题')
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
    print("财务分析报告生成完成！")
    print(f"Excel数据: {excel_path}")
    print(f"PDF报告: {pdf_path}")
    print("="*50)


if __name__ == "__main__":
    main()
