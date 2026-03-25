#!/usr/bin/env python3
"""JSON to Excel converter - 可独立运行或被系统调用"""

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

def json_to_excel(input_path, output_path=None):
    """
    将 JSON 文件转换为 Excel

    Args:
        input_path: JSON 文件路径
        output_path: 输出 Excel 文件路径（可选，不提供则自动生成）

    Returns:
        dict: 包含状态、消息和输出文件信息
    """
    import pandas as pd

    # 确保输出目录存在
    OUTPUTS_DIR.mkdir(exist_ok=True)

    # 读取 JSON（尝试多种编码）
    data = None
    for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']:
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    if data is None:
        return {'status': 'error', 'message': '无法读取 JSON 文件，请检查文件编码或格式'}

    # 转换为 DataFrame
    if isinstance(data, list):
        if len(data) == 0:
            return {'status': 'error', 'message': 'JSON 数组为空'}
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        # 如果是单个对象，转换为单行
        df = pd.DataFrame([data])
    else:
        return {'status': 'error', 'message': 'JSON 格式不支持，需要数组或对象'}

    # 生成输出路径
    if output_path is None:
        output_name = generate_unique_filename('output', 'xlsx')
        output_path = OUTPUTS_DIR / output_name
    else:
        output_path = Path(output_path)
        output_name = output_path.name

    # 写入 Excel
    df.to_excel(output_path, index=False, engine='openpyxl')

    print(f"[OK] 转换完成: {output_path}")
    print(f"    共 {len(df)} 行数据")

    return {
        'status': 'success',
        'message': f'转换完成，共 {len(df)} 行数据',
        'content': f'已将 JSON 转换为 Excel，共 {len(df)} 行',
        '_output_file': {
            'path': str(output_path),
            'type': 'excel',
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
        return {'status': 'error', 'message': '请上传 JSON 文件'}

    # 处理路径
    if input_file.startswith('/uploads/'):
        input_file = str(UPLOADS_DIR / input_file[len('/uploads/'):])
    elif input_file.startswith('uploads/'):
        input_file = str(UPLOADS_DIR / input_file[len('uploads/'):])
    elif input_file.startswith('/outputs/'):
        input_file = str(OUTPUTS_DIR / input_file[len('/outputs/'):])
    elif input_file.startswith('outputs/'):
        input_file = str(OUTPUTS_DIR / input_file[len('outputs/'):])

    return json_to_excel(input_file)


if __name__ == "__main__":
    # 命令行模式
    if len(sys.argv) < 2:
        print("用法: python main.py <input.json> [output.xlsx]")
        print("示例: python main.py data.json output.xlsx")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # 处理相对路径
    if not os.path.isabs(input_path):
        if input_path.startswith('uploads/'):
            input_path = str(UPLOADS_DIR / input_path[len('uploads/'):])
        elif input_path.startswith('outputs/'):
            input_path = str(OUTPUTS_DIR / input_path[len('outputs/'):])
        elif os.path.exists(UPLOADS_DIR / input_path):
            input_path = str(UPLOADS_DIR / input_path)
        elif os.path.exists(OUTPUTS_DIR / input_path):
            input_path = str(OUTPUTS_DIR / input_path)

    result = json_to_excel(input_path, output_path)

    if result['status'] == 'error':
        print(f"错误: {result['message']}")
        sys.exit(1)
