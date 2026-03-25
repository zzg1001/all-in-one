#!/usr/bin/env python3
"""Excel to JSON converter - 可独立运行或被系统调用"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 获取目录路径
SCRIPT_DIR = Path(__file__).parent
SERVER_DIR = SCRIPT_DIR.parent.parent
OUTPUTS_DIR = SERVER_DIR / "outputs"
UPLOADS_DIR = SERVER_DIR / "uploads"

def generate_unique_filename(prefix, ext):
    """生成唯一文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    import uuid
    return f"{prefix}_{timestamp}_{uuid.uuid4().hex[:8]}.{ext}"

def convert_value(value):
    """转换值为 JSON 兼容类型"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, 'isoformat'):  # pandas Timestamp
        return value.isoformat()
    return value

def excel_to_json(input_path, output_path=None):
    """
    将 Excel 文件转换为 JSON

    Args:
        input_path: Excel 文件路径
        output_path: 输出 JSON 文件路径（可选，不提供则自动生成）

    Returns:
        dict: 包含状态、消息和输出文件信息
    """
    import pandas as pd

    # 确保输出目录存在
    OUTPUTS_DIR.mkdir(exist_ok=True)

    # 读取 Excel
    try:
        df = pd.read_excel(input_path)
    except Exception as e:
        return {'status': 'error', 'message': f'读取 Excel 失败: {e}'}

    # 处理 NaN 和日期
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            df[col] = df[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)
        else:
            df[col] = df[col].where(pd.notna(df[col]), None)

    # 转换为字典列表
    data = df.to_dict(orient='records')

    # 生成输出路径
    if output_path is None:
        output_name = generate_unique_filename('output', 'json')
        output_path = OUTPUTS_DIR / output_name
    else:
        output_path = Path(output_path)
        output_name = output_path.name

    # 写入 JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"[OK] 转换完成: {output_path}")
    print(f"    共 {len(data)} 条记录")

    return {
        'status': 'success',
        'message': f'转换完成，共 {len(data)} 条记录',
        'content': data,
        '_output_file': {
            'path': str(output_path),
            'type': 'json',
            'name': output_name,
            'url': f'/outputs/{output_name}'
        }
    }

def main(params):
    """API 入口函数 - 被系统调用"""
    files = params.get('files', []) or params.get('file_paths', [])
    file_path = params.get('file_path', '')

    input_file = files[0] if files else file_path
    if not input_file:
        return {'status': 'error', 'message': '请上传 Excel 文件'}

    # 处理路径
    if input_file.startswith('/uploads/'):
        input_file = str(UPLOADS_DIR / input_file[len('/uploads/'):])
    elif input_file.startswith('uploads/'):
        input_file = str(UPLOADS_DIR / input_file[len('uploads/'):])

    return excel_to_json(input_file)


if __name__ == "__main__":
    # 命令行模式
    if len(sys.argv) < 2:
        print("用法: python main.py <input.xlsx> [output.json]")
        print("示例: python main.py data.xlsx output.json")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # 处理相对路径
    if not os.path.isabs(input_path):
        if input_path.startswith('uploads/'):
            input_path = str(UPLOADS_DIR / input_path[len('uploads/'):])
        elif os.path.exists(UPLOADS_DIR / input_path):
            input_path = str(UPLOADS_DIR / input_path)

    result = excel_to_json(input_path, output_path)

    if result['status'] == 'error':
        print(f"错误: {result['message']}")
        sys.exit(1)
