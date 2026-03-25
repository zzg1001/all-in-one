#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HR Excel数据解析器
解析员工花名册或招聘数据Excel文件，输出结构化JSON
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def check_dependencies():
    """检查并提示安装依赖"""
    missing = []
    try:
        import pandas
    except ImportError:
        missing.append('pandas')
    try:
        import openpyxl
    except ImportError:
        missing.append('openpyxl')

    if missing:
        print(f"缺少依赖库: {', '.join(missing)}")
        print(f"请运行: pip install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

import pandas as pd

# 常见HR字段的中英文映射
FIELD_MAPPINGS = {
    # 员工基本信息
    '姓名': 'name', '员工姓名': 'name', 'name': 'name',
    '工号': 'employee_id', '员工工号': 'employee_id', 'id': 'employee_id',
    '部门': 'department', 'dept': 'department', 'department': 'department',
    '职位': 'position', '岗位': 'position', 'title': 'position', 'position': 'position',
    '入职日期': 'hire_date', '入职时间': 'hire_date', 'hire_date': 'hire_date',
    '离职日期': 'leave_date', '离职时间': 'leave_date', 'leave_date': 'leave_date',
    '状态': 'status', '在职状态': 'status', 'status': 'status',
    '性别': 'gender', 'gender': 'gender',
    '学历': 'education', 'education': 'education',
    '年龄': 'age', 'age': 'age',

    # 招聘相关
    '岗位名称': 'job_title', '招聘岗位': 'job_title',
    '岗位要求': 'requirements', '任职要求': 'requirements',
    '岗位职责': 'responsibilities', '工作职责': 'responsibilities',
    '候选人': 'candidate', '应聘者': 'candidate',
    '面试状态': 'interview_status', '面试结果': 'interview_status',
    '招聘渠道': 'channel', '来源渠道': 'channel',
}


def detect_data_type(df):
    """根据列名检测数据类型"""
    columns_lower = [str(c).lower() for c in df.columns]

    # 招聘数据特征列
    recruitment_keywords = ['候选人', '应聘者', '面试', '招聘', 'candidate', 'interview', 'recruitment']
    # 员工花名册特征列
    roster_keywords = ['入职', '工号', '员工', 'hire', 'employee', '在职']

    recruitment_score = sum(1 for kw in recruitment_keywords if any(kw in c for c in columns_lower))
    roster_score = sum(1 for kw in roster_keywords if any(kw in c for c in columns_lower))

    if recruitment_score > roster_score:
        return 'recruitment'
    elif roster_score > 0:
        return 'employee_roster'
    else:
        return 'unknown'


def normalize_columns(df):
    """标准化列名"""
    new_columns = {}
    for col in df.columns:
        col_str = str(col).strip().lower()
        for cn_name, en_name in FIELD_MAPPINGS.items():
            if cn_name.lower() == col_str or cn_name.lower() in col_str:
                new_columns[col] = en_name
                break
    return new_columns


def generate_summary(df, data_type):
    """生成数据摘要统计"""
    summary = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': list(df.columns),
        'data_type': data_type,
    }

    # 根据数据类型生成特定统计
    if data_type == 'employee_roster':
        # 部门统计
        dept_col = None
        for col in df.columns:
            if '部门' in str(col) or 'department' in str(col).lower():
                dept_col = col
                break
        if dept_col:
            summary['department_distribution'] = df[dept_col].value_counts().to_dict()

        # 在职状态统计
        status_col = None
        for col in df.columns:
            if '状态' in str(col) or 'status' in str(col).lower():
                status_col = col
                break
        if status_col:
            summary['status_distribution'] = df[status_col].value_counts().to_dict()

        # 入职日期统计
        hire_col = None
        for col in df.columns:
            if '入职' in str(col) or 'hire' in str(col).lower():
                hire_col = col
                break
        if hire_col:
            try:
                df[hire_col] = pd.to_datetime(df[hire_col], errors='coerce')
                df['hire_year'] = df[hire_col].dt.year
                summary['hire_year_distribution'] = df['hire_year'].value_counts().sort_index().to_dict()
            except:
                pass

    elif data_type == 'recruitment':
        # 岗位统计
        job_col = None
        for col in df.columns:
            if '岗位' in str(col) or 'job' in str(col).lower() or '职位' in str(col):
                job_col = col
                break
        if job_col:
            summary['job_distribution'] = df[job_col].value_counts().to_dict()

        # 面试状态统计
        status_col = None
        for col in df.columns:
            if '面试' in str(col) or 'interview' in str(col).lower():
                status_col = col
                break
        if status_col:
            summary['interview_status_distribution'] = df[status_col].value_counts().to_dict()

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
    df = df.dropna(how='all')  # 删除全空行
    df = df.fillna('')  # 空值填充为空字符串

    # 转换日期列为字符串（便于JSON序列化）
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            df[col] = df[col].dt.strftime('%Y-%m-%d').fillna('')

    # 生成摘要
    summary = generate_summary(df, data_type)

    # 构建结果
    result = {
        'success': True,
        'file_path': str(file_path),
        'data_type': data_type,
        'columns': list(df.columns),
        'column_mapping': normalize_columns(df),
        'data': df.to_dict(orient='records'),
        'summary': summary,
        'parsed_at': datetime.now().isoformat()
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='HR Excel数据解析器')
    parser.add_argument('excel_file', help='Excel文件路径')
    parser.add_argument('--output', '-o', help='输出JSON文件路径（不指定则输出到stdout）')
    parser.add_argument('--sheet', '-s', default=0, help='工作表名称或索引，默认为第一个')
    parser.add_argument('--pretty', '-p', action='store_true', help='格式化JSON输出')

    args = parser.parse_args()

    # 检查文件存在
    if not Path(args.excel_file).exists():
        print(json.dumps({'error': f'文件不存在: {args.excel_file}'}, ensure_ascii=False))
        sys.exit(1)

    # 解析Excel
    result = parse_excel(args.excel_file, args.sheet)

    # 输出结果
    indent = 2 if args.pretty else None
    json_output = json.dumps(result, ensure_ascii=False, indent=indent, default=str)

    if args.output:
        Path(args.output).write_text(json_output, encoding='utf-8')
        print(f'已保存到: {args.output}')
    else:
        print(json_output)


if __name__ == '__main__':
    main()
