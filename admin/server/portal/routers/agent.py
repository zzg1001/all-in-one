import uuid
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
from app.core.database import get_db
from app.core.config import get_uploads_dir, get_skills_storage_temp_dir
from portal.schemas.agent import (
    ChatRequest, ChatResponse,
    ExecuteRequest, ExecuteResponse, OutputFile,
    SkillChatRequest, SkillChatMessage,
    SkillExecuteInteractiveRequest,
    AgentLoopRequest, ToolCall
)
from portal.services.agent_service_sdk import AgentSDKService
from portal.services.file_generator import generate_output_file
from portal.routers.logs import (
    log_info, log_error,
    log_skill_start, log_skill_step, log_skill_success, log_skill_error,
    log_ai_start, log_ai_done, log_file_write,
    log_session_start, log_session_end
)

router = APIRouter(prefix="/api/agent", tags=["Agent"])

# 使用统一配置的上传目录
UPLOADS_DIR = get_uploads_dir()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with AI agent (non-streaming)"""
    # 记录会话上下文
    from portal.models.skill import Skill
    skill_names = []
    if request.skill_ids:
        skills = db.query(Skill).filter(
            Skill.id.in_(request.skill_ids),
            Skill.deleted_at.is_(None)
        ).all()
        skill_names = [s.name for s in skills]

    log_session_start(
        api_name="POST /agent/chat",
        api_desc="与AI助手对话（非流式），AI会根据问题和技能给出回答",
        source="Agent对话页面",
        skills=skill_names if skill_names else None,
        user_input=request.message
    )

    service = AgentSDKService(db)
    try:
        history = [{"role": m.role, "content": m.content} for m in request.history] if request.history else []
        log_ai_start(request.message[:100])
        response = await service.chat(
            message=request.message,
            history=history,
            skill_ids=request.skill_ids
        )
        log_ai_done(response[:100] if response else None)
        log_session_end(True, "AI响应完成")
        return ChatResponse(message=response)
    except Exception as e:
        log_error(f"聊天失败: {str(e)[:50]}")
        log_session_end(False, str(e)[:50])
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    x_user_id: str = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    """Chat with AI agent (streaming via SSE, with RAG support)"""
    user_id = x_user_id or "anonymous"

    # 记录会话上下文
    from portal.models.skill import Skill
    skill_names = []
    if request.skill_ids:
        skills = db.query(Skill).filter(
            Skill.id.in_(request.skill_ids),
            Skill.deleted_at.is_(None)
        ).all()
        skill_names = [s.name for s in skills]

    log_session_start(
        api_name="POST /agent/chat/stream",
        api_desc="与AI助手实时对话（流式），文字会逐字显示",
        source="Agent对话页面",
        skills=skill_names if skill_names else None,
        user_input=request.message
    )
    log_ai_start(request.message[:100])

    # 构建带上下文的消息
    message_with_context = request.message

    # 检查是否是老板视角Agent - 获取所有部门数据
    # 使用延迟导入避免循环依赖
    from portal.services.boss_view_service import is_boss_view_agent, get_all_department_data, build_boss_view_prompt

    if request.agent_id and is_boss_view_agent(db, request.agent_id):
        log_info(f"[BossView] 检测到老板视角Agent，开始获取所有部门数据...")
        try:
            department_data = await get_all_department_data(db, user_id)
            message_with_context = build_boss_view_prompt(department_data, request.message)
            if department_data:
                log_info(f"[BossView] 获取到 {len(department_data)} 字符的部门数据")
            else:
                log_info("[BossView] 未找到部门数据")
        except Exception as e:
            import traceback
            log_error(f"[BossView] 获取部门数据失败: {str(e)[:100]}")
            traceback.print_exc()
    else:
        # 普通Agent: 使用RAG从向量数据库检索相关内容
        rag_context = ""
        from app.core.config import get_settings
        settings = get_settings()

        # 检查向量数据库是否启用
        if request.enable_rag and settings.vector_db_enabled and (request.agent_id or user_id):
            try:
                # 使用延迟导入避免循环依赖
                import importlib.util
                import os
                module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'vector_service.py')
                spec = importlib.util.spec_from_file_location('vector_service', module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                vector_service = module.get_vector_service()

                if vector_service:
                    log_info(f"RAG 检索: query={request.message[:50]}..., agent_id={request.agent_id}, user_id={user_id}")
                    rag_context = await vector_service.get_context_for_chat(
                        query=request.message,
                        agent_id=request.agent_id,
                        user_id=user_id,
                        max_context_length=4000
                    )
                    if rag_context:
                        log_info(f"RAG 检索到 {len(rag_context)} 字符的相关内容")
                    else:
                        log_info("RAG 检索: 未找到相关内容")
                else:
                    log_info("RAG: vector_service 为 None")
            except Exception as e:
                import traceback
                log_error(f"RAG 检索失败: {str(e)[:100]}")
                traceback.print_exc()

        # 构建带 RAG 上下文的消息
        if rag_context:
            message_with_context = f"""## 从知识库检索到的相关数据

以下是从用户的文件管理（File Manage）中检索到的相关内容：

{rag_context}

---

## 用户问题
{request.message}

## 回答要求
1. **如果用户在查询数据**（如"帮我看一下..."、"查找..."、"筛选..."）：
   - 直接列出检索到的相关数据
   - 按表格或列表形式展示
   - 标注数据来源和相似度

2. **如果用户在提问**：
   - 基于检索到的内容回答问题
   - 引用具体数据作为依据

3. **如果检索结果为空或不相关**：
   - 告知用户未找到相关数据
   - 建议用户先在 File Manage 中上传相关文件"""

    service = AgentSDKService(db)

    # 调试日志
    print(f"\n[/chat/stream] ========== 请求信息 ==========")
    print(f"[/chat/stream] agent_id: {request.agent_id}")
    print(f"[/chat/stream] skill_ids: {request.skill_ids}")
    print(f"[/chat/stream] file_paths: {request.file_paths}")
    print(f"[/chat/stream] message: {request.message[:100]}...")

    async def generate():
        try:
            history = [{"role": m.role, "content": m.content} for m in request.history] if request.history else []
            async for chunk in service.chat_stream(
                message=message_with_context,
                history=history,
                skill_ids=request.skill_ids,
                file_paths=request.file_paths,
                agent_id=request.agent_id
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            log_ai_done()
            yield "data: [DONE]\n\n"
        except Exception as e:
            log_error(f"流式响应失败: {str(e)[:50]}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# /plan 端点已移除 - 不再自动规划技能，一切交给 SDK 处理


@router.post("/execute", response_model=ExecuteResponse)
async def execute_skill(request: ExecuteRequest, db: Session = Depends(get_db)):
    """Execute a skill's script"""
    from pathlib import Path
    from portal.models.skill import Skill

    skill = db.query(Skill).filter(Skill.id == request.skill_id).first()
    skill_name = skill.name if skill else request.skill_id

    # 记录执行上下文
    log_session_start(
        api_name="POST /agent/execute",
        api_desc=f"执行技能脚本，运行 {skill_name} 完成具体任务",
        source="技能执行",
        skills=[skill_name]
    )

    # 【关键】处理文件路径：将相对路径转换为绝对路径
    params = dict(request.params) if request.params else {}
    base_dir = Path(__file__).parent.parent  # product-background 目录

    # 【RAG】传递 agent_id 用于向量数据库数据隔离
    if request.agent_id:
        params['agent_id'] = request.agent_id

    # 处理 file_path
    if params.get('file_path'):
        fp = params['file_path']
        if not Path(fp).is_absolute():
            abs_path = base_dir / fp
            if abs_path.exists():
                params['file_path'] = str(abs_path)
                print(f"[Execute] Converted file_path: {fp} -> {abs_path}")

    # 处理 file_paths 和 files 数组
    for key in ['file_paths', 'files']:
        if params.get(key) and isinstance(params[key], list):
            converted = []
            for fp in params[key]:
                if not Path(fp).is_absolute():
                    abs_path = base_dir / fp
                    if abs_path.exists():
                        converted.append(str(abs_path))
                        print(f"[Execute] Converted {key} item: {fp} -> {abs_path}")
                    else:
                        converted.append(fp)
                else:
                    converted.append(fp)
            params[key] = converted

    # 日志：开始（包含输入参数）
    log_skill_start(skill_name, params)

    # 调试：打印完整参数
    print(f"\n========== [Execute Skill] ==========")
    print(f"[Execute] skill_id: {request.skill_id}")
    print(f"[Execute] skill_name: {skill_name}")
    print(f"[Execute] params keys: {list(params.keys()) if params else 'None'}")
    print(f"[Execute] file_path: {params.get('file_path', 'NOT SET')}")
    print(f"[Execute] file_paths: {params.get('file_paths', 'NOT SET')}")
    print(f"[Execute] Full params: {params}")
    print(f"======================================\n")

    # 使用 Claude Agent SDK 执行技能
    service = AgentSDKService(db)
    log_skill_step(skill_name, "执行脚本", detail=f"使用 Claude Agent SDK")

    # 调用异步执行方法
    exec_result = await service.execute_skill(
        skill_id=request.skill_id,
        params=params
    )

    success = exec_result.get("success", False)
    result = exec_result.get("result")
    error = exec_result.get("error")
    output = exec_result.get("output")

    # 处理输出文件
    output_file = None
    if exec_result.get("_output_file"):
        file_info = exec_result["_output_file"]
        # size 字段需要是字符串类型
        size_value = file_info.get("size")
        if size_value is not None and not isinstance(size_value, str):
            size_value = str(size_value)
        output_file = OutputFile(
            name=file_info.get("name", "output"),
            type=file_info.get("type", "file"),
            url=file_info.get("url", ""),
            size=size_value
        )
        log_file_write(file_info.get('name'), file_info.get('size'))
    elif success and skill:
        # 尝试使用 file_generator 生成输出
        try:
            skill_output_config = skill.output_config if hasattr(skill, 'output_config') else None
            file_info = generate_output_file(
                skill_name=skill.name,
                skill_description=skill.description,
                execution_result=result,
                execution_output=output,
                params=request.params,
                output_config=skill_output_config
            )
            if file_info:
                output_file = OutputFile(**file_info)
                log_file_write(file_info['name'], file_info.get('size'))
        except Exception:
            pass

    if success:
        log_skill_success(skill_name, result)
        log_session_end(True, f"技能 {skill_name} 执行成功")
    else:
        log_skill_error(skill_name, error or "未知错误")
        log_session_end(False, error or "未知错误")

    return ExecuteResponse(
        success=success,
        result=result,
        error=error,
        output=output,
        output_file=output_file
    )


@router.post("/execute-temp", response_model=ExecuteResponse)
async def execute_temp_skill(request: ExecuteRequest, db: Session = Depends(get_db)):
    """执行临时技能（用于测试）"""
    import json as json_lib

    temp_id = request.skill_id
    temp_skills_dir = get_skills_storage_temp_dir()
    temp_folder = temp_skills_dir / temp_id

    if not temp_folder.exists():
        log_error("临时技能不存在", detail=f"ID: {temp_id}")
        return ExecuteResponse(success=False, error="临时技能不存在或已过期", output=None)

    # 读取配置
    config_path = temp_folder / "config.json"
    config = json_lib.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {"name": "temp_skill"}

    class TempSkill:
        def __init__(self, folder, cfg):
            self.id = temp_id
            self.name = cfg.get("name", "temp_skill")
            self.description = cfg.get("description", "")
            self.folder_path = str(folder)
            self.entry_script = cfg.get("entry_script")
            self.output_config = cfg.get("output_config")

    temp_skill = TempSkill(temp_folder, config)

    # 记录执行上下文
    log_session_start(
        api_name="POST /agent/execute-temp",
        api_desc=f"测试临时技能，验证 {temp_skill.name} 是否正常工作",
        source="技能测试页面",
        skills=[temp_skill.name]
    )

    # 日志：开始（包含输入参数）
    log_skill_start(f"[测试] {temp_skill.name}", request.params)

    service = AgentSDKService(db)
    log_skill_step(temp_skill.name, "执行测试", detail=f"script: {request.script_name}")

    success, result, error, output = await service.execute_temp_skill(
        temp_folder=temp_folder,
        skill_name=temp_skill.name,
        script_name=request.script_name,
        params=request.params
    )

    # 生成输出文件
    output_file = None
    if success:
        log_skill_step(temp_skill.name, "生成文件")
        try:
            file_info = generate_output_file(
                skill_name=temp_skill.name,
                skill_description=temp_skill.description,
                execution_result=result,
                execution_output=output,
                params=request.params,
                output_config=temp_skill.output_config
            )
            if file_info:
                output_file = OutputFile(**file_info)
                log_file_write(file_info['name'], file_info.get('size'))
        except Exception:
            pass

        log_skill_success(temp_skill.name, result)
        log_session_end(True, f"测试技能 {temp_skill.name} 执行成功")
    else:
        log_skill_error(temp_skill.name, error or "未知错误")
        log_session_end(False, error or "未知错误")

    return ExecuteResponse(
        success=success,
        result=result,
        error=error,
        output=output,
        output_file=output_file
    )


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件供技能处理使用

    支持的文件类型: 图片、文档、数据文件等
    返回文件路径，可传递给技能执行参数
    """
    # 验证文件类型 - 支持常见格式
    allowed_extensions = {
        # 数据文件
        ".xlsx", ".xls", ".csv", ".json", ".txt", ".xml", ".yaml", ".yml",
        # 文档
        ".md", ".pdf", ".doc", ".docx", ".ppt", ".pptx",
        # 图片
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico",
        # 代码
        ".py", ".js", ".ts", ".html", ".css", ".vue", ".jsx", ".tsx",
        # 其他
        ".zip", ".log",
    }
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}。支持: {', '.join(allowed_extensions)}"
        )

    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = str(uuid.uuid4())[:8]
    safe_filename = f"upload_{timestamp}_{short_id}{file_ext}"

    # 读取文件内容
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

    # 根据存储类型保存文件
    from app.core.config import get_settings
    settings = get_settings()

    if settings.storage_type == "minio":
        # 上传到 MinIO，同时保存本地副本供技能脚本使用
        try:
            from portal.services.storage.minio_storage import MinioStorage
            storage = MinioStorage(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                bucket=settings.minio_uploads_bucket,
                port=settings.minio_port,
                secure=settings.minio_secure
            )
            await storage.write_file(safe_filename, content)

            # 同时保存本地副本，供技能脚本直接读取
            local_path = UPLOADS_DIR / safe_filename
            local_path.write_bytes(content)

            return {
                "success": True,
                "filename": safe_filename,
                "original_name": file.filename,
                "path": str(local_path),  # 本地路径供技能脚本使用
                "url": f"/storage/uploads/{safe_filename}",  # MinIO URL
                "size": len(content),
                "type": file_ext.lstrip("."),
                "storage": "minio"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"上传到存储失败: {str(e)}")
    else:
        # 本地文件系统
        try:
            filepath = UPLOADS_DIR / safe_filename
            filepath.write_bytes(content)

            return {
                "success": True,
                "filename": safe_filename,
                "original_name": file.filename,
                "path": str(filepath),
                "url": f"/uploads/{safe_filename}",
                "size": len(content),
                "type": file_ext.lstrip("."),
                "storage": "local"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")


@router.get("/preview/{file_path:path}")
async def preview_file(file_path: str, max_rows: int = 100):
    """
    预览文件内容

    - Excel/CSV: 返回表格数据（最多 max_rows 行）
    - JSON: 返回 JSON 内容
    - 图片: 返回图片信息
    - 其他: 返回文件信息

    支持本地文件系统和 MinIO 存储
    """
    import pandas as pd
    import tempfile
    import io
    from app.core.config import get_settings, get_outputs_dir, get_uploads_dir

    settings = get_settings()

    # 解析文件路径，确定是 outputs 还是 uploads
    if file_path.startswith("/"):
        file_path = file_path.lstrip("/")

    if file_path.startswith("outputs/"):
        storage_category = "outputs"
        relative_path = file_path[8:]  # 去掉 "outputs/"
    elif file_path.startswith("uploads/"):
        storage_category = "uploads"
        relative_path = file_path[8:]  # 去掉 "uploads/"
    else:
        storage_category = "outputs"
        relative_path = file_path

    # 根据存储类型获取文件
    file_content = None
    file_size = 0
    file_name = Path(relative_path).name
    suffix = Path(relative_path).suffix.lower()

    # 获取本地目录路径（作为回退）
    base_dir = get_outputs_dir() if storage_category == "outputs" else get_uploads_dir()
    local_path = base_dir / relative_path
    found_in_minio = False

    if settings.storage_type == "minio":
        # 优先从 MinIO 读取
        try:
            from portal.services.storage.minio_storage import MinioStorage
            bucket = settings.minio_outputs_bucket if storage_category == "outputs" else settings.minio_uploads_bucket
            storage = MinioStorage(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                bucket=bucket,
                port=settings.minio_port,
                secure=settings.minio_secure
            )

            # 检查文件是否存在于 MinIO
            if await storage.exists(relative_path):
                found_in_minio = True
                file_info = await storage.get_file_info(relative_path)
                file_size = file_info.size if file_info else 0

                # 对于需要内容的文件类型，读取内容
                if suffix in ['.xlsx', '.xls', '.csv', '.json', '.md', '.html', '.htm', '.py', '.js', '.ts', '.txt']:
                    file_content = await storage.read_file(relative_path)

                # 生成访问 URL
                storage_url = f"/storage/{storage_category}/{relative_path}"

        except Exception as e:
            print(f"[Preview] MinIO 读取失败，尝试本地: {e}")

    # 如果 MinIO 没找到或不是 MinIO 模式，尝试本地文件
    if not found_in_minio:
        if not local_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

        file_size = local_path.stat().st_size
        storage_url = f"/{storage_category}/{relative_path}"

        # 对于需要内容的文件类型，读取内容
        if suffix in ['.xlsx', '.xls', '.csv', '.json', '.md', '.html', '.htm', '.py', '.js', '.ts', '.txt']:
            file_content = local_path.read_bytes()

    # Excel 文件
    if suffix in ['.xlsx', '.xls']:
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            total_rows = len(df)
            df = df.head(max_rows)
            return {
                "type": "table",
                "format": "excel",
                "columns": df.columns.tolist(),
                "data": df.fillna("").astype(str).values.tolist(),
                "total_rows": total_rows,
                "displayed_rows": len(df),
                "file_name": file_name,
                "file_size": file_size
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"解析 Excel 失败: {str(e)}")

    # CSV 文件
    elif suffix == '.csv':
        try:
            df = pd.read_csv(io.BytesIO(file_content))
            total_rows = len(df)
            df = df.head(max_rows)
            return {
                "type": "table",
                "format": "csv",
                "columns": df.columns.tolist(),
                "data": df.fillna("").astype(str).values.tolist(),
                "total_rows": total_rows,
                "displayed_rows": len(df),
                "file_name": file_name,
                "file_size": file_size
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"解析 CSV 失败: {str(e)}")

    # JSON 文件
    elif suffix == '.json':
        try:
            content = file_content.decode('utf-8')
            data = json.loads(content)
            return {
                "type": "json",
                "format": "json",
                "content": data,
                "file_name": file_name,
                "file_size": file_size
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"解析 JSON 失败: {str(e)}")

    # Markdown 文件
    elif suffix == '.md':
        try:
            content = file_content.decode('utf-8')
            return {
                "type": "markdown",
                "format": "md",
                "content": content,
                "file_name": file_name,
                "file_size": file_size
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取 Markdown 失败: {str(e)}")

    # HTML 文件
    elif suffix in ['.html', '.htm']:
        try:
            content = file_content.decode('utf-8')
            return {
                "type": "html",
                "format": "html",
                "content": content,
                "file_name": file_name,
                "file_size": file_size
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取 HTML 失败: {str(e)}")

    # 图片文件
    elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg']:
        return {
            "type": "image",
            "format": suffix.lstrip('.'),
            "url": storage_url,
            "file_name": file_name,
            "file_size": file_size
        }

    # 代码文件
    elif suffix in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.vue', '.jsx', '.tsx']:
        try:
            content = file_content.decode('utf-8')
            return {
                "type": "code",
                "format": suffix.lstrip('.'),
                "content": content,
                "file_name": file_name,
                "file_size": file_size
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取代码文件失败: {str(e)}")

    # PPT 文件
    elif suffix in ['.ppt', '.pptx']:
        return {
            "type": "ppt",
            "format": suffix.lstrip('.'),
            "file_name": file_name,
            "file_size": file_size,
            "url": storage_url,
            "download_url": storage_url
        }

    # Word 文件
    elif suffix in ['.doc', '.docx']:
        return {
            "type": "word",
            "format": suffix.lstrip('.'),
            "file_name": file_name,
            "file_size": file_size,
            "url": storage_url,
            "download_url": storage_url
        }

    # PDF 文件
    elif suffix == '.pdf':
        return {
            "type": "pdf",
            "format": "pdf",
            "file_name": file_name,
            "file_size": file_size,
            "url": storage_url,
            "download_url": storage_url
        }

    # 其他文件
    else:
        return {
            "type": "file",
            "format": suffix.lstrip('.') if suffix else "unknown",
            "file_name": file_name,
            "file_size": file_size,
            "download_url": storage_url
        }


# /analyze 和 /analyze/sync 端点已移除
# 数据分析现在直接通过 /chat/stream 完成，AI 会使用 SDK 工具自主分析


# ========== Claude Code 风格：步骤化技能执行 ==========

@router.post("/skill-chat")
async def skill_chat_stream(request: SkillChatRequest, db: Session = Depends(get_db)):
    """
    Claude Code 风格的交互式技能执行（SSE 流式）

    AI 会将任务拆分成具体操作步骤，每个步骤需要用户确认后才执行。

    SSE 事件类型:
    - content: AI 输出的文本片段
    - actions_planned: AI 规划的所有操作列表
    - action_pending: 等待用户确认的操作
    - action_executing: 正在执行的操作
    - action_result: 操作执行结果
    - action_skipped: 用户跳过的操作
    - all_actions_done: 所有操作完成
    - done: 执行完成（无操作时）
    - error: 错误信息

    Request:
    {
        "skill_id": "uuid",
        "context": "用户原始需求",
        "conversation": [{"role": "user/assistant", "content": "..."}],
        "file_paths": ["path1", "path2"],
        "user_choice": "execute" | "skip" | null,
        "pending_actions": [{"type": "write", "data": {...}}],
        "current_action_index": 0
    }
    """
    from portal.models.skill import Skill

    skill = db.query(Skill).filter(Skill.id == request.skill_id).first()
    skill_name = skill.name if skill else request.skill_id

    log_session_start(
        api_name="POST /agent/skill-chat",
        api_desc=f"交互式技能执行 - {skill_name}",
        source="技能面板",
        skills=[skill_name],
        user_input=request.context[:100] if request.context else None
    )

    service = AgentSDKService(db)

    async def generate():
        try:
            # 转换对话历史格式
            conversation = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation
            ] if request.conversation else []

            # 转换操作列表格式
            pending_actions = [
                {"type": act.type, "data": act.data}
                for act in request.pending_actions
            ] if request.pending_actions else None

            async for chunk in service.skill_chat_stream(
                skill_id=request.skill_id,
                context=request.context,
                conversation=conversation,
                file_paths=request.file_paths,
                user_choice=request.user_choice,
                pending_actions=pending_actions,
                current_action_index=request.current_action_index,
                agent_id=request.agent_id
            ):
                yield f"data: {chunk}\n\n"

            log_session_end(True, "技能执行完成")

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error(f"技能执行失败: {str(e)[:50]}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            log_session_end(False, str(e)[:50])

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ========== Claude Code 风格：系统级工具调用确认 ==========

@router.post("/execute-interactive")
async def skill_execute_interactive(request: SkillExecuteInteractiveRequest, db: Session = Depends(get_db)):
    """
    Claude Code 风格的交互式技能执行（SSE 流式）

    系统级工具调用确认 - 不需要 AI 输出 ACTION 标记，
    后端根据技能类型自动规划操作步骤，每个步骤执行前发送确认请求。

    SSE 事件类型:
    - steps_planned: 规划的所有步骤
    - step_confirm: 等待用户确认的步骤
    - step_executing: 正在执行的步骤
    - step_result: 步骤执行结果
    - all_done: 全部完成
    - error: 错误信息
    """
    from portal.models.skill import Skill

    skill = db.query(Skill).filter(Skill.id == request.skill_id).first()
    skill_name = skill.name if skill else request.skill_id

    log_session_start(
        api_name="POST /agent/execute-interactive",
        api_desc=f"交互式执行 - {skill_name}",
        source="技能面板",
        skills=[skill_name],
        user_input=request.context[:100] if request.context else None
    )

    service = AgentSDKService(db)

    async def generate():
        try:
            async for chunk in service.skill_execute_interactive(
                skill_id=request.skill_id,
                context=request.context,
                file_paths=request.file_paths,
                confirmed_step=request.confirmed_step,
                auto_confirm=request.auto_confirm,
                skip_current=request.skip_current
            ):
                yield f"data: {chunk}\n\n"

            log_session_end(True, "交互式执行完成")

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error(f"交互式执行失败: {str(e)[:50]}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            log_session_end(False, str(e)[:50])

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ========== 真正的 Claude Code 风格：多轮 AI 交互循环 ==========

@router.post("/loop")
async def agent_loop(request: AgentLoopRequest, db: Session = Depends(get_db)):
    """
    Claude Code 风格的 Agent 循环（SSE 流式）

    真正的多轮 AI 交互：
    1. AI 思考并决定使用什么工具
    2. 发送工具调用给前端，等待用户确认
    3. 用户确认后执行工具，结果返回给 AI
    4. AI 继续思考，决定下一步
    5. 循环直到任务完成

    SSE 事件类型:
    - thinking: AI 正在思考
    - tool_call: AI 要调用工具，等待确认
    - tool_result: 工具执行结果
    - message: AI 的文字消息
    - done: 任务完成
    - error: 错误
    """
    from portal.models.skill import Skill

    skill = db.query(Skill).filter(Skill.id == request.skill_id).first()
    skill_name = skill.name if skill else request.skill_id

    log_session_start(
        api_name="POST /agent/loop",
        api_desc=f"Agent Loop - {skill_name}",
        source="技能面板",
        skills=[skill_name],
        user_input=request.context[:100] if request.context else None
    )

    service = AgentSDKService(db)

    async def generate():
        try:
            async for event in service.agent_loop(
                skill_id=request.skill_id,
                context=request.context,
                file_paths=request.file_paths,
                conversation=request.conversation,
                pending_tool_call=request.pending_tool_call,
                tool_confirmed=request.tool_confirmed,
                tool_rejected=request.tool_rejected,
                user_edit=request.user_edit
            ):
                yield f"data: {event}\n\n"

            log_session_end(True, "Agent Loop 完成")

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error(f"Agent Loop 失败: {str(e)[:50]}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            log_session_end(False, str(e)[:50])

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
