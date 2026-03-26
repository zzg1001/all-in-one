#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
消防商业机会筛选工具
从招标Excel文件中筛选消防相关的项目
"""

import pandas as pd
import argparse
import sys
import json
from pathlib import Path


# 消防关键词列表
FIRE_KEYWORDS = [
    # 核心关键词
    '消防', '灭火', '火灾', '防火',
    # 设备类
    '灭火器', '消火栓', '喷淋', '烟感', '温感', '报警器',
    '防火门', '防火卷帘', '消防泵', '消防水箱', '消防车',
    '应急照明', '疏散指示', '防火涂料', '防火封堵',
    # 工程/服务类
    '消防工程', '消防设施', '消防系统', '消防改造', '消防维保',
    '消防检测', '消防验收', '消防培训', '消防演练', '消防安全评估',
    # 资质/管理类
    '119', '消防站', '消防队', '消防救援', '消防监控'
]


def read_excel(file_path):
    """读取Excel文件并处理标题行"""
    df = pd.read_excel(file_path)

    # 检查是否需要调整标题行
    if 'Unnamed' in str(df.columns[0]) or pd.isna(df.columns[0]):
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

    return df


def find_title_column(df):
    """识别标题列"""
    candidates = ['标题', '项目名称', '名称', '招标名称', '项目标题']
    for col in candidates:
        if col in df.columns:
            return col
    # 默认使用第一列
    return df.columns[0]


def filter_by_keywords(df, title_col, keywords=None):
    """根据关键词筛选数据"""
    if keywords is None:
        keywords = FIRE_KEYWORDS

    pattern = '|'.join(keywords)
    mask = df[title_col].astype(str).str.contains(pattern, case=False, na=False)
    return df[mask].copy()


def format_output_markdown(original_df, filtered_df, title_col):
    """格式化输出为Markdown"""
    output = []
    output.append("## 消防相关商业机会筛选结果\n")
    output.append(f"**数据概览：**")
    output.append(f"- 原始数据总数：{len(original_df)} 条")
    output.append(f"- 消防相关项目：{len(filtered_df)} 条\n")

    if len(filtered_df) == 0:
        output.append("未找到消防相关的招标信息。")
        return '\n'.join(output)

    output.append("**匹配的项目列表：**\n")

    # 常用列名映射
    col_map = {
        '标讯类型': ['标讯类型', '类型', '招标类型'],
        '省份': ['省份', '省'],
        '城市': ['城市', '市'],
        '区县': ['区县', '区', '县'],
        '招采单位': ['招采单位', '采购单位', '招标单位', '采购人'],
        '预算金额': ['预算金额', '预算', '金额', '项目金额'],
        '发布时间': ['发布时间', '发布日期', '公告时间'],
        '投标截止时间': ['投标截止时间', '截止时间', '报名截止'],
        '联系人': ['联系人', '联系方式', '联系电话'],
        '链接': ['寻标宝标讯链接', '链接', '详情链接', '原文链接']
    }

    def get_col_value(row, key):
        """获取列值，尝试多个可能的列名"""
        for col_name in col_map.get(key, [key]):
            if col_name in row.index:
                val = row[col_name]
                if pd.notna(val):
                    return str(val)
        return None

    for i, (idx, row) in enumerate(filtered_df.iterrows(), 1):
        title = row[title_col]
        output.append(f"### {i}. {title}")

        # 标讯类型
        val = get_col_value(row, '标讯类型')
        if val:
            output.append(f"- 标讯类型：{val}")

        # 地区
        province = get_col_value(row, '省份') or ''
        city = get_col_value(row, '城市') or ''
        district = get_col_value(row, '区县') or ''
        location = ' '.join(filter(None, [province, city, district]))
        if location:
            output.append(f"- 地区：{location}")

        # 招采单位
        val = get_col_value(row, '招采单位')
        if val:
            output.append(f"- 招采单位：{val}")

        # 预算金额
        val = get_col_value(row, '预算金额')
        if val and val != 'nan':
            output.append(f"- 预算金额：{val}")

        # 发布时间
        val = get_col_value(row, '发布时间')
        if val:
            output.append(f"- 发布时间：{val}")

        # 投标截止
        val = get_col_value(row, '投标截止时间')
        if val:
            output.append(f"- 投标截止：{val}")

        # 联系人
        val = get_col_value(row, '联系人')
        if val:
            output.append(f"- 联系人：{val}")

        # 链接
        val = get_col_value(row, '链接')
        if val and val.startswith('http'):
            output.append(f"- 链接：[查看详情]({val})")

        output.append("")

    return '\n'.join(output)


def format_output_json(original_df, filtered_df, title_col):
    """格式化输出为JSON"""
    result = {
        'summary': {
            'total_records': len(original_df),
            'matched_records': len(filtered_df)
        },
        'opportunities': []
    }

    for idx, row in filtered_df.iterrows():
        item = {}
        for col in filtered_df.columns:
            val = row[col]
            if pd.notna(val):
                item[col] = str(val) if not isinstance(val, (int, float)) else val
        result['opportunities'].append(item)

    return json.dumps(result, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='从Excel中筛选消防相关招标信息')
    parser.add_argument('file', help='Excel文件路径')
    parser.add_argument('--format', '-f', choices=['markdown', 'json', 'csv'],
                        default='markdown', help='输出格式 (默认: markdown)')
    parser.add_argument('--output', '-o', help='输出文件路径 (默认输出到stdout)')
    parser.add_argument('--keywords', '-k', nargs='+', help='额外的关键词')
    parser.add_argument('--list-keywords', action='store_true', help='列出所有关键词')

    args = parser.parse_args()

    if args.list_keywords:
        print("消防关键词列表：")
        for kw in FIRE_KEYWORDS:
            print(f"  - {kw}")
        return

    # 读取Excel
    try:
        df = read_excel(args.file)
    except Exception as e:
        print(f"错误：无法读取文件 {args.file}", file=sys.stderr)
        print(f"详情：{e}", file=sys.stderr)
        sys.exit(1)

    # 识别标题列
    title_col = find_title_column(df)

    # 合并关键词
    keywords = FIRE_KEYWORDS.copy()
    if args.keywords:
        keywords.extend(args.keywords)

    # 筛选
    filtered = filter_by_keywords(df, title_col, keywords)

    # 格式化输出
    if args.format == 'markdown':
        output = format_output_markdown(df, filtered, title_col)
    elif args.format == 'json':
        output = format_output_json(df, filtered, title_col)
    elif args.format == 'csv':
        if args.output:
            filtered.to_csv(args.output, index=False, encoding='utf-8-sig')
            print(f"已保存到 {args.output}")
            return
        else:
            output = filtered.to_csv(index=False)

    # 输出
    if args.output and args.format != 'csv':
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"已保存到 {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
