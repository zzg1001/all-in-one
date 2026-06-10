"""
企业信息提取路由 - 从营业执照和企业介绍中提取结构化企业信息
"""
import base64
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from portal.services.extract_service import ExtractService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/extract", tags=["Portal - Extract"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/company")
async def extract_company_info(
    company_name: Optional[str] = Form(None),
    credit_code: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    license_file: Optional[UploadFile] = File(None),
    intro_file: Optional[UploadFile] = File(None)
):
    """
    提取企业信息

    输入：
    - company_name: 企业名称（可选）
    - credit_code: 统一社会信用代码（可选）
    - website: 官网URL（可选）
    - license_file: 营业执照文件（图片/PDF）
    - intro_file: 企业介绍文件（PPT/Word）

    至少需要提供 company_name、credit_code 或 license_file 之一

    输出：
    - success: 是否成功
    - data: 提取的企业信息 JSON
    - word_file_base64: Word 文档的 base64 编码
    """
    # 验证至少有一个必填项
    if not company_name and not credit_code and not license_file:
        raise HTTPException(
            status_code=400,
            detail="请至少填写企业名称、统一社会信用代码或上传营业执照"
        )

    # 读取文件内容
    license_content = None
    license_filename = None
    if license_file:
        license_content = await license_file.read()
        license_filename = license_file.filename
        if len(license_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="营业执照文件大小超过限制")

    intro_content = None
    intro_filename = None
    if intro_file:
        intro_content = await intro_file.read()
        intro_filename = intro_file.filename
        if len(intro_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="企业介绍文件大小超过限制")

    try:
        service = ExtractService()
        result = await service.extract(
            company_name=company_name,
            credit_code=credit_code,
            website=website,
            license_content=license_content,
            license_filename=license_filename,
            intro_content=intro_content,
            intro_filename=intro_filename
        )

        return {
            "success": True,
            "data": result["data"],
            "word_file_base64": result.get("word_base64", "")
        }

    except Exception as e:
        logger.error(f"企业信息提取失败: {e}")
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")


@router.post("/word")
def generate_word_doc(data: Dict[str, Any] = Body(...)):
    """用（编辑后的）企业信息数据重新生成 Word 文档

    输入：企业信息 JSON（与提取结果同结构，可含用户编辑）
    输出：{ success, word_file_base64 }
    """
    if not data:
        raise HTTPException(status_code=400, detail="缺少企业信息数据")

    try:
        service = ExtractService()
        word_base64 = service.generate_word(data)
        return {"success": True, "word_file_base64": word_base64}
    except Exception as e:
        logger.error(f"生成 Word 文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")
