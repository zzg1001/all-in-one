"""
企业信息提取服务
先用 DashScope OCR 解析，再调用 skill 的 process_for_frontend 函数处理
"""
import base64
import io
import json
import logging
import os
import re
import sys
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

from .ocr_service import OCRService

logger = logging.getLogger(__name__)

# Skill ID（固定，便于跟踪）
SKILL_ID = "9edfed14-7f65-4997-93b4-c8c248fea984"

# OCR 服务实例
_ocr_service = OCRService()


def _parse_license_ocr(text: str) -> Dict[str, str]:
    """从 OCR 文本中解析营业执照信息"""
    result = {}

    if not text:
        return result

    # 统一社会信用代码（18位，字母+数字）
    credit_patterns = [
        r'统一社会信用代码[：:\s]*([0-9A-Z]{18})',
        r'信用代码[：:\s]*([0-9A-Z]{18})',
        r'([0-9A-Z]{18})',
    ]
    for pattern in credit_patterns:
        match = re.search(pattern, text)
        if match:
            result['统一社会信用代码'] = match.group(1)
            break

    # 企业名称
    name_patterns = [
        r'名\s*称[：:\s]*([^\n]+?)(?:类型|注册|住所|\n)',
        r'名称[：:\s]*([^\n]{4,60})',
        r'企业名称[：:\s]*([^\n]+)',
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            # 清理名称中的多余内容
            name = re.sub(r'(类型|住所|注册资本|法定代表人).*', '', name).strip()
            if len(name) >= 4 and ('有限' in name or '公司' in name or '集团' in name or '股份' in name):
                result['企业名称'] = name
                break

    # 法定代表人（支持多种格式）
    legal_patterns = [
        r'法定代表人[：:\s]*([一-龥]{2,4})',
        r'法\s*定\s*代\s*表\s*人[：:\s]*([一-龥]{2,4})',
        r'代表人[：:\s]*([一-龥]{2,4})',
    ]
    for pattern in legal_patterns:
        match = re.search(pattern, text)
        if match:
            name = match.group(1).strip()
            name = re.sub(r'\s+', '', name)  # 去除空格
            if 2 <= len(name) <= 4:
                result['法定代表人'] = name
                break

    # 注册资本
    capital_patterns = [
        r'注册资本[：:\s]*([^\n]+?)(?:成立|日期|\n)',
        r'注\s*册\s*资\s*本[：:\s]*([^\n]+?)(?:成立|\n)',
        r'资本[：:\s]*(人民币[^\n]+)',
    ]
    for pattern in capital_patterns:
        match = re.search(pattern, text)
        if match:
            capital = match.group(1).strip()
            capital = re.sub(r'(成立日期|营业期限).*', '', capital).strip()
            if '万' in capital or '元' in capital or '亿' in capital:
                result['注册资本'] = capital
                break

    # 成立日期
    date_patterns = [
        r'成立日期[：:\s]*(\d{4}年\d{1,2}月\d{1,2}日)',
        r'成立日期[：:\s]*(\d{4}-\d{2}-\d{2})',
        r'成\s*立\s*日\s*期[：:\s]*(\d{4}年\d{1,2}月\d{1,2}日)',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            result['成立时间'] = match.group(1)
            break

    # 住所/注册地址
    addr_patterns = [
        r'住\s*所[：:\s]*(.+?)(?:经营范围|\n\n)',
        r'住所[：:\s]*([^\n]+)',
        r'注册地址[：:\s]*([^\n]+)',
    ]
    for pattern in addr_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            addr = match.group(1).strip()
            addr = re.sub(r'\s+', '', addr)
            addr = re.sub(r'(经营范围|营业期限).*', '', addr).strip()
            if len(addr) > 5:
                result['注册地址'] = addr[:150]
                break

    # 类型/企业性质
    type_patterns = [
        r'类\s*型[：:\s]*(.+?)(?:法定|成立|\n)',
        r'类型[：:\s]*([^\n]+)',
        r'企业类型[：:\s]*([^\n]+)',
    ]
    for pattern in type_patterns:
        match = re.search(pattern, text)
        if match:
            etype = match.group(1).strip()
            etype = re.sub(r'(法定代表人|成立日期).*', '', etype).strip()
            if len(etype) > 2:
                result['企业性质'] = etype
                break

    # 经营范围
    scope_patterns = [
        r'经营范围[：:\s]*(.+?)(?:登记机关|核准日期|营业期限|$)',
        r'经\s*营\s*范\s*围[：:\s]*(.+?)(?:登记|核准|\n\n|$)',
    ]
    for pattern in scope_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            scope = match.group(1).strip()
            scope = re.sub(r'\s+', ' ', scope)
            if len(scope) > 10:
                result['经营范围'] = scope[:500]
                break

    return result


class ExtractService:
    """企业信息提取服务"""

    async def _ocr_license(self, content: bytes, filename: str) -> Dict[str, str]:
        """对营业执照进行 OCR 识别并解析"""
        try:
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'

            print(f"\n[OCR] 开始识别营业执照: {filename}")
            ocr_text = await _ocr_service.recognize(content, ext, filename)
            print(f"[OCR] 识别结果长度: {len(ocr_text)} 字符")
            print(f"[OCR] 识别内容:\n{ocr_text[:500]}...")

            # 解析 OCR 结果
            parsed = _parse_license_ocr(ocr_text)
            print(f"[OCR] 解析出字段: {list(parsed.keys())}")
            for k, v in parsed.items():
                print(f"  {k}: {v}")

            return parsed

        except Exception as e:
            print(f"[OCR] 识别失败: {e}")
            logger.error(f"OCR 识别失败: {e}")
            return {}

    async def extract(
        self,
        company_name: Optional[str] = None,
        credit_code: Optional[str] = None,
        website: Optional[str] = None,
        license_content: Optional[bytes] = None,
        license_filename: Optional[str] = None,
        intro_content: Optional[bytes] = None,
        intro_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提取企业信息 - 直接调用 skill 的 process_for_frontend 函数

        Returns:
            {
                "data": {...},  # 结构化的企业信息
                "word_base64": "..."  # Word 文档的 base64 编码
            }
        """
        # 获取 skill 路径
        from app.core.config import get_skills_storage_dir
        skill_folder = get_skills_storage_dir() / SKILL_ID

        if not skill_folder.exists():
            logger.error(f"Skill 文件夹不存在: {skill_folder}")
            return {
                "data": self._get_default_data(company_name, credit_code, website),
                "word_base64": "",
                "raw_ocr_text": "",
                "raw_intro_text": "",
                "error": "Skill 文件夹不存在"
            }

        # ========== 步骤1: 先用 DashScope OCR 识别营业执照 ==========
        ocr_info = {}
        if license_content and license_filename:
            ocr_info = await self._ocr_license(license_content, license_filename)

            # 如果 OCR 成功提取了信息，优先使用
            if ocr_info.get('企业名称') and not company_name:
                company_name = ocr_info.get('企业名称')
                print(f"[ExtractService] 从 OCR 获取企业名称: {company_name}")
            if ocr_info.get('统一社会信用代码') and not credit_code:
                credit_code = ocr_info.get('统一社会信用代码')
                print(f"[ExtractService] 从 OCR 获取信用代码: {credit_code}")

        # ========== 步骤2: 保存文件到临时目录 ==========
        temp_dir = tempfile.mkdtemp(prefix="extract_")
        license_path = None
        intro_path = None

        try:
            if license_content and license_filename:
                license_path = os.path.join(temp_dir, license_filename)
                with open(license_path, 'wb') as f:
                    f.write(license_content)
                print(f"\n[ExtractService] 保存营业执照到: {license_path}")

            if intro_content and intro_filename:
                intro_path = os.path.join(temp_dir, intro_filename)
                with open(intro_path, 'wb') as f:
                    f.write(intro_content)
                print(f"[ExtractService] 保存企业介绍到: {intro_path}")

            # 调用 skill 的 process_for_frontend 函数
            print("\n" + "=" * 60)
            print("【调用 Skill】企业信息提取")
            print("=" * 60)

            # 添加 skill 目录到 Python 路径
            skill_path_str = str(skill_folder)
            if skill_path_str not in sys.path:
                sys.path.insert(0, skill_path_str)

            # 动态导入 skill 的 main 模块
            try:
                # 清除可能已缓存的模块
                modules_to_remove = [m for m in sys.modules if m.startswith('main') or m.startswith('extract_') or m.startswith('claude_ocr')]
                for m in modules_to_remove:
                    del sys.modules[m]

                from main import process_for_frontend

                result = process_for_frontend(
                    license_file=license_path,
                    company_name=company_name or None,
                    credit_code=credit_code or None,
                    website_url=website or None,
                    intro_file=intro_path,
                    output_dir=temp_dir
                )

                print(f"\n[Skill 返回结果] success={result.get('success')}")

                if result.get('success'):
                    data = result.get('data', {})
                    word_base64 = result.get('wordFileBase64', '')

                    # ========== 合并 OCR 数据到结果中 ==========
                    # 将我们预先 OCR 解析的数据填充到空字段
                    data_updated = False
                    if ocr_info:
                        print("\n[合并 OCR 数据]")
                        # 字段映射：OCR 字段名 -> Skill 数据字段名
                        field_mapping = {
                            '企业名称': '企业名称',
                            '统一社会信用代码': '统一社会信用代码',
                            '法定代表人': '法定代表人',
                            '注册资本': '注册资本',
                            '成立时间': '成立时间',
                            '注册地址': '注册地址',
                            '企业性质': '企业性质',
                            '经营范围': '经营范围',
                        }
                        for ocr_key, data_key in field_mapping.items():
                            ocr_val = ocr_info.get(ocr_key)
                            data_val = data.get(data_key)
                            # 如果 skill 数据中该字段为空，使用 OCR 数据
                            if ocr_val and (not data_val or data_val == "" or data_val == "-"):
                                data[data_key] = ocr_val
                                data_updated = True
                                print(f"  填充 {data_key}: {ocr_val}")

                    # 如果数据被更新了，重新生成 Word 文档
                    if data_updated:
                        print("\n[重新生成 Word 文档]")
                        try:
                            from word_generator import generate_word

                            # 生成新的 Word 文件
                            output_name = data.get('企业名称', 'output')
                            safe_name = output_name.replace('/', '_').replace('\\', '_')
                            new_word_path = os.path.join(temp_dir, f"{safe_name}_企业档案_updated.docx")

                            if generate_word(data, new_word_path):
                                print(f"  Word 重新生成成功: {new_word_path}")
                                # 读取新的 Word 文件
                                with open(new_word_path, 'rb') as f:
                                    word_base64 = base64.b64encode(f.read()).decode('utf-8')
                            else:
                                print("  Word 重新生成失败，使用原文件")
                        except Exception as e:
                            print(f"  Word 重新生成异常: {e}，使用原文件")

                    # 打印提取的数据
                    print("\n" + "=" * 60)
                    print("【最终提取的数据】")
                    print("=" * 60)
                    for k, v in data.items():
                        if v and v != [] and v != {}:
                            print(f"  {k}: {str(v)[:100]}")
                    print("=" * 60 + "\n")

                    return {
                        "data": data,
                        "word_base64": word_base64,
                        "raw_ocr_text": "",
                        "raw_intro_text": ""
                    }
                else:
                    error = result.get('error', '未知错误')
                    logger.error(f"Skill 执行失败: {error}")
                    print(f"[Skill 错误] {error}")

                    return {
                        "data": self._get_default_data(company_name, credit_code, website),
                        "word_base64": "",
                        "raw_ocr_text": "",
                        "raw_intro_text": "",
                        "error": error
                    }

            except Exception as e:
                import traceback
                logger.error(f"调用 Skill 失败: {e}")
                traceback.print_exc()

                return {
                    "data": self._get_default_data(company_name, credit_code, website),
                    "word_base64": "",
                    "raw_ocr_text": "",
                    "raw_intro_text": "",
                    "error": str(e)
                }

            finally:
                # 从 sys.path 移除 skill 目录
                if skill_path_str in sys.path:
                    sys.path.remove(skill_path_str)

        finally:
            # 清理临时文件
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    def _get_default_data(self, company_name: str, credit_code: str, website: str) -> Dict[str, Any]:
        """返回默认数据结构"""
        return {
            "企业名称": company_name or "",
            "统一社会信用码": credit_code or "",
            "法定代表人": "",
            "注册时间": "",
            "成立时间": "",
            "注册资本": "",
            "注册地址": "",
            "办公地址": "",
            "企业性质": "",
            "单位规模": "",
            "所属行业": "",
            "经营范围": "",
            "官网": website or "",
            "简介": "",
            "核心产品": [],
            "解决方案": [],
            "成功案例": [],
            "AI能力": "",
            "生态伙伴": "",
            "能力标签": {
                "核心技术": [],
                "服务能力": []
            }
        }
