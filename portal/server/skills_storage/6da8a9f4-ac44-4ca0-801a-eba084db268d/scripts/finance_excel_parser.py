#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务Excel数据解析器
解析收支明细、费用报销、预算数据等财务Excel，输出结构化JSON和关键指标
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

def check_dependencies():
    """检查依赖"""
    missing = []
    try:
        import pandas
    except ImportError:
        missing.append('pandas')
    try:
        import openpyxl
    except ImportError:
        missing.append('openpyxl')
    try:
        import numpy
    except ImportError:
        missing.append('numpy')

    if missing:
        print(f"缺少依赖库: {', '.join(missing)}")
        print(f"请运行: pip install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

import pandas as pd
import numpy as np

# 财务字段映射
FIELD_MAPPINGS = {
    # 通用字段
    '日期': 'date', '时间': 'date', 'date': 'date',
    '摘要': 'description', '说明': 'description', '备注': 'description',
    '部门': 'department', 'dept': 'department',
    '项目': 'project', 'project': 'project',

    # 收支相关
    '收入': 'income', '收款': 'income', 'income': 'income',
    '支出': 'expense', '付款': 'expense', 'expense': 'expense',
    '金额': 'amount', 'amount': 'amount',
    '余额': 'balance', 'balance': 'balance',
    '科目': 'account', '会计科目': 'account',

    # 报销相关
    '报销人': 'applicant', '申请人': 'applicant',
    '费用类型': 'expense_type', '报销类型': 'expense_type',
    '报销金额': 'reimbursement_amount', '报销额': 'reimbursement_amount',
    '报销日期': 'apply_date', '申请日期': 'apply_date',
    '审批状态': 'approval_status', '状态': 'approval_status',
    '发票张数': 'invoice_count', '发票数': 'invoice_count',

    # 预算相关
    '预算金额': 'budget_amount', '预算': 'budget_amount',
    '实际金额': 'actual_amount', '实际': 'actual_amount',
    '预算科目': 'budget_item', '科目名称': 'budget_item',
    '剩余金额': 'remaining', '剩余': 'remaining',
}

# 费用审核规则
EXPENSE_RULES = {
    '差旅费': {'single_limit': 5000, 'monthly_limit': 20000},
    '招待费': {'single_limit': 2000, 'monthly_limit': 10000},
    '办公用品': {'single_limit': 500, 'monthly_limit': 3000},
    '交通费': {'single_limit': 300, 'monthly_limit': 2000},
    '通讯费': {'single_limit': 200, 'monthly_limit': 500},
    '培训费': {'single_limit': 3000, 'monthly_limit': 15000},
    '会议费': {'single_limit': 5000, 'monthly_limit': 20000},
}


def format_currency(value):
    """格式化金额"""
    if pd.isna(value) or value == '':
        return 0.0
    try:
        return float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except:
        return 0.0


def format_percentage(value, decimals=1):
    """格式化百分比"""
    return f"{round(value * 100, decimals)}%"


def detect_data_type(df):
    """检测财务数据类型"""
    columns_lower = [str(c).lower() for c in df.columns]
    columns_str = ' '.join([str(c) for c in df.columns])

    # 报销数据特征
    reimbursement_keywords = ['报销', '申请人', '费用类型', 'reimbursement', 'expense_type', '审批']
    # 预算数据特征
    budget_keywords = ['预算', 'budget', '实际', 'actual', '偏差', '执行率']
    # 收支数据特征
    income_expense_keywords = ['收入', '支出', 'income', 'expense', '余额', 'balance', '借', '贷']

    reimbursement_score = sum(1 for kw in reimbursement_keywords if kw in columns_str)
    budget_score = sum(1 for kw in budget_keywords if kw in columns_str)
    income_expense_score = sum(1 for kw in income_expense_keywords if kw in columns_str)

    if reimbursement_score > max(budget_score, income_expense_score):
        return 'reimbursement'
    elif budget_score > max(reimbursement_score, income_expense_score):
        return 'budget'
    elif income_expense_score > 0:
        return 'income_expense'
    else:
        return 'unknown'


def calculate_income_expense_indicators(df):
    """计算收支类指标"""
    indicators = {}

    # 查找收入和支出列
    income_col = None
    expense_col = None
    for col in df.columns:
        col_str = str(col).lower()
        if '收入' in col_str or 'income' in col_str or '收款' in col_str:
            income_col = col
        if '支出' in col_str or 'expense' in col_str or '付款' in col_str:
            expense_col = col

    if income_col:
        df[income_col] = df[income_col].apply(format_currency)
        indicators['total_income'] = format_currency(df[income_col].sum())
        indicators['avg_income'] = format_currency(df[income_col].mean())
        indicators['max_income'] = format_currency(df[income_col].max())

    if expense_col:
        df[expense_col] = df[expense_col].apply(format_currency)
        indicators['total_expense'] = format_currency(df[expense_col].sum())
        indicators['avg_expense'] = format_currency(df[expense_col].mean())
        indicators['max_expense'] = format_currency(df[expense_col].max())

    # 计算利润指标
    if income_col and expense_col:
        total_income = indicators.get('total_income', 0)
        total_expense = indicators.get('total_expense', 0)

        indicators['net_profit'] = format_currency(total_income - total_expense)

        if total_income > 0:
            indicators['profit_rate'] = format_percentage((total_income - total_expense) / total_income)
            indicators['expense_rate'] = format_percentage(total_expense / total_income)

    # 按月/部门统计
    date_col = None
    dept_col = None
    for col in df.columns:
        col_str = str(col).lower()
        if '日期' in col_str or 'date' in col_str:
            date_col = col
        if '部门' in col_str or 'dept' in col_str:
            dept_col = col

    if date_col and income_col:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df['month'] = df[date_col].dt.to_period('M')
            monthly = df.groupby('month').agg({
                income_col: 'sum',
                expense_col: 'sum' if expense_col else lambda x: 0
            }).reset_index()
            indicators['monthly_trend'] = monthly.to_dict(orient='records')
        except:
            pass

    if dept_col and expense_col:
        dept_expense = df.groupby(dept_col)[expense_col].sum().sort_values(ascending=False)
        indicators['department_expense'] = dept_expense.to_dict()

    return indicators


def calculate_reimbursement_indicators(df):
    """计算报销类指标"""
    indicators = {}

    # 查找关键列
    amount_col = None
    applicant_col = None
    type_col = None
    status_col = None
    dept_col = None

    for col in df.columns:
        col_str = str(col)
        if '金额' in col_str or '报销' in col_str and '额' in col_str:
            amount_col = col
        if '报销人' in col_str or '申请人' in col_str:
            applicant_col = col
        if '费用类型' in col_str or '类型' in col_str:
            type_col = col
        if '状态' in col_str or '审批' in col_str:
            status_col = col
        if '部门' in col_str:
            dept_col = col

    if amount_col:
        df[amount_col] = df[amount_col].apply(format_currency)
        indicators['total_reimbursement'] = format_currency(df[amount_col].sum())
        indicators['avg_reimbursement'] = format_currency(df[amount_col].mean())
        indicators['max_single'] = format_currency(df[amount_col].max())
        indicators['reimbursement_count'] = len(df)

    # 人均报销
    if amount_col and applicant_col:
        person_count = df[applicant_col].nunique()
        indicators['person_count'] = person_count
        if person_count > 0:
            indicators['per_person_amount'] = format_currency(indicators['total_reimbursement'] / person_count)

        # 个人报销排名
        person_total = df.groupby(applicant_col)[amount_col].sum().sort_values(ascending=False)
        indicators['person_ranking'] = person_total.head(10).to_dict()

    # 费用类型分布
    if amount_col and type_col:
        type_total = df.groupby(type_col)[amount_col].sum().sort_values(ascending=False)
        indicators['expense_type_distribution'] = type_total.to_dict()

    # 部门统计
    if amount_col and dept_col:
        dept_total = df.groupby(dept_col)[amount_col].sum().sort_values(ascending=False)
        indicators['department_distribution'] = dept_total.to_dict()

    # 审核状态
    if status_col:
        status_count = df[status_col].value_counts().to_dict()
        indicators['approval_status'] = status_count

        total = len(df)
        approved = sum(1 for s in df[status_col] if '通过' in str(s) or '已审' in str(s))
        indicators['approval_rate'] = format_percentage(approved / total) if total > 0 else '0%'

    # 异常检测（超标报销）
    anomalies = []
    if amount_col and type_col:
        for idx, row in df.iterrows():
            expense_type = str(row.get(type_col, ''))
            amount = row.get(amount_col, 0)

            for rule_type, limits in EXPENSE_RULES.items():
                if rule_type in expense_type:
                    if amount > limits['single_limit']:
                        anomalies.append({
                            'row': idx + 2,
                            'type': expense_type,
                            'amount': amount,
                            'limit': limits['single_limit'],
                            'reason': f'超过单笔限额{limits["single_limit"]}元'
                        })
                    break

    indicators['anomalies'] = anomalies
    indicators['anomaly_count'] = len(anomalies)

    return indicators


def calculate_budget_indicators(df):
    """计算预算类指标"""
    indicators = {}

    # 查找关键列
    budget_col = None
    actual_col = None
    item_col = None
    dept_col = None

    for col in df.columns:
        col_str = str(col)
        if '预算' in col_str and ('金额' in col_str or col_str == '预算'):
            budget_col = col
        if '实际' in col_str:
            actual_col = col
        if '科目' in col_str or '项目' in col_str:
            item_col = col
        if '部门' in col_str:
            dept_col = col

    if budget_col:
        df[budget_col] = df[budget_col].apply(format_currency)
        indicators['total_budget'] = format_currency(df[budget_col].sum())

    if actual_col:
        df[actual_col] = df[actual_col].apply(format_currency)
        indicators['total_actual'] = format_currency(df[actual_col].sum())

    if budget_col and actual_col:
        total_budget = indicators['total_budget']
        total_actual = indicators['total_actual']

        indicators['total_variance'] = format_currency(total_actual - total_budget)

        if total_budget > 0:
            indicators['execution_rate'] = format_percentage(total_actual / total_budget)
            indicators['variance_rate'] = format_percentage((total_actual - total_budget) / total_budget)
            indicators['remaining_rate'] = format_percentage((total_budget - total_actual) / total_budget)

        # 计算各项预算执行情况
        df['variance'] = df[actual_col] - df[budget_col]
        df['execution_rate'] = df.apply(
            lambda row: row[actual_col] / row[budget_col] if row[budget_col] > 0 else 0,
            axis=1
        )

        # 超支项目
        over_budget = df[df['variance'] > 0]
        indicators['over_budget_count'] = len(over_budget)
        indicators['over_budget_amount'] = format_currency(over_budget['variance'].sum())

        # 节约项目
        under_budget = df[df['variance'] < 0]
        indicators['under_budget_count'] = len(under_budget)
        indicators['saved_amount'] = format_currency(abs(under_budget['variance'].sum()))

    # 按科目/部门统计
    if item_col and budget_col and actual_col:
        item_comparison = df.groupby(item_col).agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        item_comparison['variance'] = item_comparison[actual_col] - item_comparison[budget_col]
        indicators['item_comparison'] = item_comparison.to_dict(orient='records')

    if dept_col and budget_col and actual_col:
        dept_comparison = df.groupby(dept_col).agg({
            budget_col: 'sum',
            actual_col: 'sum'
        }).reset_index()
        dept_comparison['execution_rate'] = dept_comparison.apply(
            lambda row: format_percentage(row[actual_col] / row[budget_col]) if row[budget_col] > 0 else '0%',
            axis=1
        )
        indicators['department_comparison'] = dept_comparison.to_dict(orient='records')

    return indicators


def generate_summary(df, data_type, indicators):
    """生成数据摘要"""
    summary = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': list(df.columns),
        'data_type': data_type,
        'data_type_cn': {
            'income_expense': '收支明细',
            'reimbursement': '费用报销',
            'budget': '预算数据',
            'unknown': '未识别类型'
        }.get(data_type, '未知'),
    }

    # 根据类型生成摘要文字
    if data_type == 'income_expense':
        summary['highlight'] = f"总收入: {indicators.get('total_income', 0):,.2f}元, " \
                              f"总支出: {indicators.get('total_expense', 0):,.2f}元, " \
                              f"净利润: {indicators.get('net_profit', 0):,.2f}元"
    elif data_type == 'reimbursement':
        summary['highlight'] = f"报销总额: {indicators.get('total_reimbursement', 0):,.2f}元, " \
                              f"报销{indicators.get('reimbursement_count', 0)}笔, " \
                              f"异常{indicators.get('anomaly_count', 0)}笔"
    elif data_type == 'budget':
        summary['highlight'] = f"预算总额: {indicators.get('total_budget', 0):,.2f}元, " \
                              f"实际支出: {indicators.get('total_actual', 0):,.2f}元, " \
                              f"执行率: {indicators.get('execution_rate', '0%')}"

    return summary


def parse_excel(file_path, sheet_name=0):
    """解析Excel文件"""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        return {'error': f'读取Excel失败: {str(e)}'}

    # 检测数据类型
    data_type = detect_data_type(df)

    # 清理数据
    df = df.dropna(how='all')
    df = df.fillna('')

    # 根据类型计算指标
    if data_type == 'income_expense':
        indicators = calculate_income_expense_indicators(df.copy())
    elif data_type == 'reimbursement':
        indicators = calculate_reimbursement_indicators(df.copy())
    elif data_type == 'budget':
        indicators = calculate_budget_indicators(df.copy())
    else:
        indicators = {}

    # 转换日期列
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            df[col] = df[col].dt.strftime('%Y-%m-%d').fillna('')

    # 生成摘要
    summary = generate_summary(df, data_type, indicators)

    result = {
        'success': True,
        'file_path': str(file_path),
        'data_type': data_type,
        'columns': list(df.columns),
        'data': df.to_dict(orient='records'),
        'summary': summary,
        'indicators': indicators,
        'parsed_at': datetime.now().isoformat()
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='财务Excel数据解析器')
    parser.add_argument('excel_file', help='Excel文件路径')
    parser.add_argument('--output', '-o', help='输出JSON文件路径')
    parser.add_argument('--sheet', '-s', default=0, help='工作表名称或索引')
    parser.add_argument('--pretty', '-p', action='store_true', help='格式化JSON输出')

    args = parser.parse_args()

    if not Path(args.excel_file).exists():
        print(json.dumps({'error': f'文件不存在: {args.excel_file}'}, ensure_ascii=False))
        sys.exit(1)

    result = parse_excel(args.excel_file, args.sheet)

    indent = 2 if args.pretty else None
    json_output = json.dumps(result, ensure_ascii=False, indent=indent, default=str)

    if args.output:
        Path(args.output).write_text(json_output, encoding='utf-8')
        print(f'已保存到: {args.output}')
    else:
        print(json_output)


if __name__ == '__main__':
    main()
