#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务智能助手 - 入口脚本
自动执行完整的财务分析流程：解析 Excel -> 生成 PDF 报告
"""

import sys
import json
import subprocess
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

    if not file_paths:
        return {
            "success": False,
            "error": "请提供 Excel 文件进行分析",
            "output": "未找到输入文件，请上传 Excel 文件（.xlsx 或 .xls）"
        }

    # 取第一个 Excel 文件
    excel_file = None
    for fp in file_paths:
        if fp.lower().endswith(('.xlsx', '.xls', '.csv')):
            # 解析文件路径
            excel_file = resolve_file_path(fp)
            break

    if not excel_file:
        return {
            "success": False,
            "error": "未找到 Excel 文件",
            "output": f"提供的文件不是 Excel 格式。文件列表: {file_paths}"
        }

    # 用户上下文
    context = params.get("context", "") or params.get("skillDescription", "")

    log(f"[finance-assistant] 输入文件: {excel_file}")
    log(f"[finance-assistant] 用户需求: {context}")

    # ========== 第一步：解析 Excel ==========
    log("\n[Step 1] 解析 Excel 数据...")

    parser_script = SCRIPTS_DIR / "finance_excel_parser.py"
    parsed_json_path = OUTPUTS_DIR / f"_temp_finance_parsed_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"

    try:
        result = subprocess.run(
            [sys.executable, str(parser_script), excel_file, "-o", str(parsed_json_path), "-p"],
            capture_output=True,
            timeout=60,
        )

        # 安全解码
        stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
        stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""

        if result.returncode != 0:
            log(f"[finance-assistant] Excel 解析失败: {stderr}")
            return {
                "success": False,
                "error": "Excel 解析失败",
                "output": stderr or stdout
            }

        log(f"[finance-assistant] Excel 解析完成: {parsed_json_path}")

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Excel 解析超时",
            "output": "文件处理超时，请检查文件大小"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Excel 解析错误: {str(e)}",
            "output": str(e)
        }

    # 读取解析结果
    try:
        with open(parsed_json_path, 'r', encoding='utf-8') as f:
            parsed_data = json.load(f)
    except Exception as e:
        return {
            "success": False,
            "error": f"读取解析结果失败: {str(e)}",
            "output": str(e)
        }

    # 获取数据类型和摘要
    data_type = parsed_data.get("data_type", "unknown")
    summary = parsed_data.get("summary", {})
    indicators = parsed_data.get("indicators", {})

    log(f"[finance-assistant] 数据类型: {data_type}")
    log(f"[finance-assistant] 摘要: {summary.get('highlight', '')}")

    # ========== 第二步：生成 PDF 报告 ==========
    log("\n[Step 2] 生成 PDF 报告...")

    # 根据数据类型确定报告标题
    data_type_cn = {
        'income_expense': '收支分析',
        'reimbursement': '费用报销审核',
        'budget': '预算执行分析',
        'unknown': '财务数据分析'
    }.get(data_type, '财务分析')

    report_title = f"{data_type_cn}报告"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pdf_filename = f"财务报告_{timestamp}.pdf"
    pdf_path = OUTPUTS_DIR / pdf_filename

    # 构建报告内容
    content_data = {
        "report_type": data_type,
        "period": datetime.now().strftime('%Y年%m月'),
        "indicators": indicators,
        "sections": []
    }

    # 添加执行摘要
    content_data["sections"].append({
        "title": "执行摘要",
        "content": summary.get("highlight", "数据分析完成"),
        "type": "text"
    })

    # 根据数据类型添加不同的内容
    if data_type == "income_expense":
        # 收支分析
        if indicators.get("department_expense"):
            dept_data = [["部门", "支出金额"]]
            for dept, amount in list(indicators["department_expense"].items())[:10]:
                dept_data.append([dept, f"{amount:,.2f}"])
            content_data["sections"].append({
                "title": "部门费用统计",
                "data": dept_data,
                "type": "table"
            })

    elif data_type == "reimbursement":
        # 费用报销
        if indicators.get("expense_type_distribution"):
            type_data = [["费用类型", "金额"]]
            for t, amount in list(indicators["expense_type_distribution"].items())[:10]:
                type_data.append([t, f"{amount:,.2f}"])
            content_data["sections"].append({
                "title": "费用类型分布",
                "data": type_data,
                "type": "table"
            })

        if indicators.get("anomalies"):
            content_data["sections"].append({
                "title": "异常报销提醒",
                "content": f"发现 {len(indicators['anomalies'])} 笔异常报销，请复核。",
                "type": "text"
            })

    elif data_type == "budget":
        # 预算执行
        if indicators.get("department_comparison"):
            dept_data = [["部门", "预算", "实际", "执行率"]]
            for item in indicators["department_comparison"][:10]:
                dept_data.append([
                    str(list(item.values())[0]) if item else "",
                    f"{list(item.values())[1]:,.2f}" if len(item) > 1 else "",
                    f"{list(item.values())[2]:,.2f}" if len(item) > 2 else "",
                    str(item.get("execution_rate", "")) if "execution_rate" in item else ""
                ])
            content_data["sections"].append({
                "title": "部门预算执行情况",
                "data": dept_data,
                "type": "table"
            })

    # 保存内容 JSON
    content_json_path = OUTPUTS_DIR / f"_temp_finance_content_{timestamp}.json"
    with open(content_json_path, 'w', encoding='utf-8') as f:
        json.dump(content_data, f, ensure_ascii=False, indent=2)

    # 调用 PDF 生成脚本
    generator_script = SCRIPTS_DIR / "finance_pdf_generator.py"

    try:
        result = subprocess.run(
            [
                sys.executable, str(generator_script),
                "--title", report_title,
                "--content", str(content_json_path),
                "--output", str(pdf_path),
                "--subtitle", f"数据来源: {Path(excel_file).name}"
            ],
            capture_output=True,
            timeout=120,
        )

        # 安全解码
        pdf_stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
        pdf_stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""

        if result.returncode != 0:
            log(f"[finance-assistant] PDF 生成失败: {pdf_stderr}")
            # PDF 生成失败，返回 JSON 结果
            return {
                "success": True,
                "output": f"Excel 分析完成，但 PDF 生成失败。\n\n{summary.get('highlight', '')}",
                "result": parsed_data,
                "_output_file": {
                    "name": parsed_json_path.name,
                    "type": "json",
                    "url": f"/outputs/{parsed_json_path.name}",
                    "path": str(parsed_json_path)
                }
            }

        log(f"[finance-assistant] PDF 报告生成完成: {pdf_path}")

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "PDF 生成超时",
            "output": "报告生成超时"
        }
    except Exception as e:
        log(f"[finance-assistant] PDF 生成异常: {str(e)}")
        # 返回 JSON 结果作为备选
        return {
            "success": True,
            "output": f"分析完成。\n\n{summary.get('highlight', '')}",
            "result": parsed_data
        }

    # 清理临时文件
    try:
        parsed_json_path.unlink(missing_ok=True)
        content_json_path.unlink(missing_ok=True)
    except:
        pass

    # 返回成功结果
    return {
        "success": True,
        "output": f"财务分析报告已生成: {pdf_filename}\n\n{summary.get('highlight', '')}",
        "result": {
            "data_type": data_type,
            "summary": summary,
            "indicators": indicators
        },
        "_output_file": {
            "name": pdf_filename,
            "type": "pdf",
            "url": f"/outputs/{pdf_filename}",
            "path": str(pdf_path)
        }
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
