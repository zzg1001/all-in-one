#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键词商机筛选器
从上传的Excel文件中按关键词筛选商机，输出Excel
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 路径配置
SCRIPT_DIR = Path(__file__).parent.parent
SERVER_DIR = SCRIPT_DIR.parent.parent
UPLOADS_DIR = SERVER_DIR / "uploads"
OUTPUTS_DIR = SERVER_DIR / "outputs"


def resolve_file_path(file_path: str) -> str:
    """将 URL 路径转换为完整的文件系统路径"""
    if not file_path:
        return file_path

    # 如果已经是完整路径且文件存在，直接返回
    p = Path(file_path)
    if p.is_absolute() and p.exists():
        return file_path

    # 处理 /uploads/xxx 格式的路径
    if file_path.startswith('/uploads/') or file_path.startswith('\\uploads\\'):
        filename = file_path.replace('/uploads/', '').replace('\\uploads\\', '')
        full_path = UPLOADS_DIR / filename
        if full_path.exists():
            return str(full_path)

    # 尝试在 uploads 目录查找
    uploads_path = UPLOADS_DIR / Path(file_path).name
    if uploads_path.exists():
        return str(uploads_path)

    # 返回原始路径
    return file_path


def main(params=None):
    """
    从上传的Excel文件中按关键词筛选商机

    params:
        - file_path/file_paths: 上传的Excel文件（必须）
        - keywords: 筛选关键词列表（必须，由Agent配置提供）
    """
    import pandas as pd

    params = params or {}

    # 获取文件路径
    file_path = params.get('file_path') or params.get('file')
    if not file_path:
        paths = params.get('file_paths') or params.get('files') or []
        if paths:
            file_path = paths[0] if isinstance(paths, list) else paths

    # 解析文件路径（处理 /uploads/xxx 格式）
    if file_path:
        file_path = resolve_file_path(file_path)

    # 获取关键词（必须由Agent配置提供）
    keywords = params.get('keywords', [])
    if isinstance(keywords, str):
        # 支持逗号分隔的字符串
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]

    # 检查关键词
    if not keywords:
        print("请配置筛选关键词")
        return {
            "message": "请配置筛选关键词（在Agent配置中设置keywords参数）",
            "_no_output_file": True
        }

    print(f"[INFO] 使用关键词: {keywords}", file=sys.stderr)

    # 检查文件是否存在
    if not file_path:
        print("请上传包含商机数据的Excel文件")
        return {
            "message": "请上传包含商机数据的Excel文件",
            "_no_output_file": True
        }

    if not Path(file_path).exists():
        print(f"[ERROR] 文件不存在: {file_path}", file=sys.stderr)
        return {
            "message": f"文件不存在: {file_path}",
            "_no_output_file": True
        }

    # 从上传文件读取
    all_data = []
    try:
        # 支持 Excel 和 CSV
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        # 处理可能的标题行问题
        if len(df.columns) > 0 and 'Unnamed' in str(df.columns[0]):
            df.columns = df.iloc[0]
            df = df[1:].reset_index(drop=True)

        all_data = df.to_dict('records')
        print(f"[INFO] 从文件读取 {len(all_data)} 条数据", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] 读取文件失败: {e}", file=sys.stderr)
        return {
            "message": f"读取文件失败: {e}",
            "_no_output_file": True
        }

    # 按关键词筛选
    filtered = filter_by_keywords(all_data, keywords)
    print(f"[INFO] 筛选出 {len(filtered)} 条匹配商机", file=sys.stderr)

    # 输出Excel
    if filtered:
        output_path, output_url = save_to_excel(filtered, keywords)
        keyword_preview = '、'.join(keywords[:3]) + ('...' if len(keywords) > 3 else '')
        print(f"找到 {len(filtered)} 条匹配商机")
        return {
            "message": f"从 {len(all_data)} 条数据中筛选出 {len(filtered)} 条【{keyword_preview}】相关商机，已导出Excel",
            "_output_file": {
                "path": output_path,
                "name": Path(output_path).name,
                "type": "excel",
                "url": output_url
            }
        }
    else:
        keyword_preview = '、'.join(keywords[:3]) + ('...' if len(keywords) > 3 else '')
        print(f"在 {len(all_data)} 条数据中未找到【{keyword_preview}】相关商机")
        return {
            "message": f"在 {len(all_data)} 条数据中未找到【{keyword_preview}】相关商机",
            "_no_output_file": True
        }


def filter_by_keywords(data, keywords):
    """按关键词筛选数据"""
    if not data or not keywords:
        return []

    filtered = []
    for item in data:
        text = json.dumps(item, ensure_ascii=False, default=str).lower()
        if any(kw.lower() in text for kw in keywords):
            filtered.append(item)

    return filtered


def save_to_excel(data, keywords):
    """保存到Excel，返回 (路径, URL)"""
    import pandas as pd

    # 确保输出目录存在
    OUTPUTS_DIR.mkdir(exist_ok=True)

    # 生成文件名（使用第一个关键词作为标识）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    keyword_tag = keywords[0] if keywords else '筛选'
    filename = f"{keyword_tag}商机_{timestamp}.xlsx"
    output_path = OUTPUTS_DIR / filename

    # 转换为DataFrame并保存
    df = pd.DataFrame(data)

    # 清理列名
    df.columns = [str(col).strip() for col in df.columns]

    # 保存
    df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"[INFO] 已保存到 {output_path}", file=sys.stderr)

    # 生成 URL
    url = f"/outputs/{filename}"

    return str(output_path), url


if __name__ == '__main__':
    # 测试用例
    result = main({
        'keywords': ['消防', '灭火'],
        'file_path': 'test.xlsx'
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))
