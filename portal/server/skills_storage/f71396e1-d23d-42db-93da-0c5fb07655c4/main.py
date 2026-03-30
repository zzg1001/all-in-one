#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务分析报告生成技能 - 入口脚本
将 Excel 财务数据转换为专业的 PDF 分析报告
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# 添加 skills_storage 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入共享配置模块
from skill_config import SkillConfig, setup_encoding, log

# 设置编码（必须在最开始）
setup_encoding()

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent
SCRIPTS_DIR = SCRIPT_DIR / "scripts"
ASSETS_DIR = SCRIPT_DIR / "assets"


def main(params: dict = None):
    """
    主入口函数

    Args:
        params: 包含以下字段：
            - file_path / file_paths: Excel 文件路径
            - context: 用户需求描述
            - _config: 路径配置（由后端自动注入）
    """
    params = params or {}

    # 初始化配置（从 _config 获取路径）
    config = SkillConfig(params)
    config.ensure_dirs()

    OUTPUTS_DIR = config.outputs_dir

    # 获取 Excel 文件（自动解析路径）
    excel_file = config.get_excel_file()

    # 如果没有提供文件，检查是否有示例数据
    if not excel_file:
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
    log(f"[finance-report] 输出目录: {OUTPUTS_DIR}")

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

    try:
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

        stdout = result.stdout.decode('utf-8', errors='replace').strip() if result.stdout else ""
        stderr = result.stderr.decode('utf-8', errors='replace').strip() if result.stderr else ""

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

        # 查找生成的 PDF 文件
        expected_filename = f"{report_title}_{report_period.replace('年', '').replace('月', '')}.pdf"
        pdf_path = OUTPUTS_DIR / expected_filename

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
            # 查找最近生成的 PDF
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
        return {"success": False, "error": "报告生成超时", "output": "处理时间超过3分钟限制"}
    except Exception as e:
        return {"success": False, "error": f"执行错误: {str(e)}", "output": str(e)}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            params = {"file_path": sys.argv[1]}
    else:
        params = {}

    result = main(params)
    print(json.dumps(result, ensure_ascii=False))
