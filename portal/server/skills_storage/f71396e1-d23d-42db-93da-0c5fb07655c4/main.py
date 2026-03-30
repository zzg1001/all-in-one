#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务分析报告生成技能 - 入口脚本
将 Excel 财务数据转换为专业的 PDF 分析报告
"""

import sys
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

# 设置 stdout/stderr 编码为 UTF-8，避免 Windows 上的编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent
SCRIPTS_DIR = SCRIPT_DIR / "scripts"
ASSETS_DIR = SCRIPT_DIR / "assets"
# 服务器根目录 (skills_storage 的父目录)
SERVER_DIR = Path(__file__).parent.parent.parent
OUTPUTS_DIR = SERVER_DIR / "outputs"
UPLOADS_DIR = SERVER_DIR / "uploads"

# 确保输出目录存在
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def resolve_file_path(file_path: str) -> str:
    """将 URL 路径或相对路径转换为完整的文件系统路径"""
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

    # 处理 /outputs/xxx 格式的路径
    if file_path.startswith('/outputs/') or file_path.startswith('\\outputs\\'):
        filename = file_path.replace('/outputs/', '').replace('\\outputs\\', '')
        full_path = OUTPUTS_DIR / filename
        if full_path.exists():
            return str(full_path)

    # 尝试在 uploads 目录查找
    uploads_path = UPLOADS_DIR / Path(file_path).name
    if uploads_path.exists():
        return str(uploads_path)

    # 返回原始路径
    return file_path


def log(msg):
    """输出日志到 stderr，避免污染 JSON 输出"""
    print(msg, file=sys.stderr)


def main(params: dict = None):
    """
    主入口函数

    Args:
        params: 包含以下字段：
            - file_path / file_paths: Excel 文件路径
            - context: 用户需求描述
    """
    params = params or {}

    # 获取输入文件
    file_paths = params.get("file_paths", [])
    file_path = params.get("file_path", "")
    if file_path and file_path not in file_paths:
        file_paths.append(file_path)

    # 取第一个 Excel 文件
    excel_file = None
    for fp in file_paths:
        if fp.lower().endswith(('.xlsx', '.xls', '.csv')):
            # 解析文件路径
            excel_file = resolve_file_path(fp)
            break

    # 如果没有提供文件，检查是否有示例数据
    if not excel_file:
        # 尝试多个可能的示例文件名
        sample_names = ["财务数据_示例.xlsx", "sample_finance_data.xlsx", "sample.xlsx"]
        for name in sample_names:
            sample_file = ASSETS_DIR / name
            if sample_file.exists():
                log(f"[finance-report] 未提供 Excel 文件，使用示例数据: {sample_file}")
                excel_file = str(sample_file)
                break
        else:
            return {
                "success": False,
                "error": "请提供 Excel 财务数据文件",
                "output": "未找到输入文件，请上传 Excel 文件（.xlsx 或 .xls）"
            }

    log(f"[finance-report] 输入文件: {excel_file}")

    # 调用报告生成脚本
    generator_script = SCRIPTS_DIR / "generate_finance_report.py"

    if not generator_script.exists():
        return {
            "success": False,
            "error": "报告生成脚本不存在",
            "output": f"脚本路径: {generator_script}"
        }

    # 生成报告参数
    report_title = "财务分析月报"
    report_period = datetime.now().strftime('%Y年%m月')

    log(f"[finance-report] 运行脚本: {generator_script}")
    log(f"[finance-report] 输出目录: {OUTPUTS_DIR}")

    try:
        # 注意：--output 是输出目录，不是文件路径
        # 脚本会自动生成文件名: {title}_{period}.pdf
        result = subprocess.run(
            [
                sys.executable, str(generator_script),
                "--input", str(excel_file),
                "--output", str(OUTPUTS_DIR),
                "--title", report_title,
                "--period", report_period
            ],
            capture_output=True,
            timeout=180,
            cwd=str(SCRIPT_DIR),
        )

        # 安全解码输出
        try:
            stdout = result.stdout.decode('utf-8', errors='replace').strip() if result.stdout else ""
        except:
            stdout = str(result.stdout) if result.stdout else ""

        try:
            stderr = result.stderr.decode('utf-8', errors='replace').strip() if result.stderr else ""
        except:
            stderr = str(result.stderr) if result.stderr else ""

        log(f"[finance-report] returncode: {result.returncode}")
        if stdout:
            log(f"[finance-report] stdout: {stdout[:500]}")
        if stderr:
            log(f"[finance-report] stderr: {stderr[:500]}")

        if result.returncode != 0:
            return {
                "success": False,
                "error": "报告生成失败",
                "output": stderr or stdout or "未知错误"
            }

        # 脚本生成的文件名格式: {title}_{period去掉年月}.pdf
        # 例如: 财务分析月报_202503.pdf
        expected_filename = f"{report_title}_{report_period.replace('年', '').replace('月', '')}.pdf"
        pdf_path = OUTPUTS_DIR / expected_filename

        # 检查 PDF 是否生成
        if pdf_path.exists():
            return {
                "success": True,
                "output": f"财务分析报告已生成: {expected_filename}",
                "result": {
                    "input_file": str(excel_file),
                    "output_file": str(pdf_path)
                },
                "_output_file": {
                    "name": expected_filename,
                    "type": "pdf",
                    "url": f"/outputs/{expected_filename}",
                    "path": str(pdf_path)
                }
            }
        else:
            # PDF 没有生成到预期路径，检查输出目录中是否有新的 PDF
            import time
            for f in OUTPUTS_DIR.glob("*.pdf"):
                if time.time() - f.stat().st_mtime < 60:
                    return {
                        "success": True,
                        "output": f"财务分析报告已生成: {f.name}",
                        "_output_file": {
                            "name": f.name,
                            "type": "pdf",
                            "url": f"/outputs/{f.name}",
                            "path": str(f)
                        }
                    }

            return {
                "success": False,
                "error": "PDF 文件未生成",
                "output": stdout or "脚本执行完成但未找到输出文件"
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "报告生成超时",
            "output": "处理时间超过3分钟限制"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"执行错误: {str(e)}",
            "output": str(e)
        }


if __name__ == "__main__":
    # 命令行调用
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            # 假设是文件路径
            params = {"file_path": sys.argv[1]}
    else:
        params = {}

    result = main(params)
    # 只输出 JSON 到 stdout，日志已输出到 stderr
    print(json.dumps(result, ensure_ascii=False))
