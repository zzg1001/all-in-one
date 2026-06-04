"""
OCR 识别路由 - 支持图片、PDF、PPT、Word 文档的文字提取
"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from portal.services.ocr_service import OCRService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ocr", tags=["Portal - OCR"])

# 支持的文件类型
ALLOWED_EXTENSIONS = {
    # 图片
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp',
    # 文档
    'pdf', 'ppt', 'pptx', 'doc', 'docx'
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/recognize")
async def recognize_file(file: UploadFile = File(...)):
    """
    识别上传文件中的文字内容

    支持格式：
    - 图片：JPG, PNG, GIF, BMP, WebP
    - 文档：PDF, PPT, PPTX, DOC, DOCX
    """
    # 验证文件扩展名
    filename = file.filename or ""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 读取文件内容
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        raise HTTPException(status_code=400, detail="文件读取失败")

    # 验证文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)"
        )

    # 执行识别
    try:
        ocr_service = OCRService()
        result = await ocr_service.recognize(content, ext, filename)
        return {"text": result, "filename": filename}
    except Exception as e:
        logger.error(f"OCR 识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")
