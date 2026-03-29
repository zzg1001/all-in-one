# Agent Service v2 - 使用 Claude Agent SDK
# 替代原有的 agent_service.py

import json
import asyncio
from pathlib import Path
from typing import AsyncIterator, Optional, List, Dict, Any

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    StreamEvent,
    AssistantMessage,
    ResultMessage,
)

from sqlalchemy.orm import Session
from models.skill import Skill
from config import get_settings, get_outputs_dir, get_uploads_dir, get_skills_storage_dir

# 路径常量
OUTPUTS_DIR = get_outputs_dir()
UPLOADS_DIR = get_uploads_dir()
SKILLS_STORAGE_DIR = get_skills_storage_dir()


# ==================== 自定义工具定义 ====================

@tool("execute_skill", "执行指定的技能脚本", {
    "skill_id": str,
    "params": dict
})
async def execute_skill_tool(args):
    """执行技能的自定义工具"""
    skill_id = args.get("skill_id")
    params = args.get("params", {})

    # 这里需要访问数据库获取技能信息
    # 在实际使用时，可以通过闭包或全局变量传入 db session
    try:
        # 执行技能脚本逻辑
        skill_folder = SKILLS_STORAGE_DIR / skill_id
        script_path = skill_folder / "main.py"

        if script_path.exists():
            import subprocess
            import sys

            result = subprocess.run(
                [sys.executable, str(script_path), json.dumps(params)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(skill_folder),
                encoding='utf-8'
            )

            return {
                "content": [{
                    "type": "text",
                    "text": f"执行完成:\n{result.stdout or result.stderr}"
                }]
            }
        else:
            return {
                "content": [{"type": "text", "text": f"技能脚本不存在: {script_path}"}],
                "is_error": True
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"执行错误: {str(e)}"}],
            "is_error": True
        }


@tool("list_skills", "列出所有可用的技能", {})
async def list_skills_tool(args):
    """列出可用技能"""
    skills = []
    for folder in SKILLS_STORAGE_DIR.iterdir():
        if folder.is_dir():
            config_path = folder / "config.json"
            if config_path.exists():
                try:
                    config = json.loads(config_path.read_text(encoding='utf-8'))
                    skills.append({
                        "id": folder.name,
                        "name": config.get("name", folder.name),
                        "description": config.get("description", "")
                    })
                except:
                    pass

    return {
        "content": [{
            "type": "text",
            "text": json.dumps(skills, ensure_ascii=False, indent=2)
        }]
    }


@tool("read_uploaded_file", "读取用户上传的文件内容", {
    "file_path": str
})
async def read_uploaded_file_tool(args):
    """读取上传的文件"""
    file_path = args.get("file_path", "")

    # 解析路径
    if file_path.startswith('/uploads/'):
        full_path = UPLOADS_DIR / file_path[len('/uploads/'):]
    elif file_path.startswith('uploads/'):
        full_path = UPLOADS_DIR / file_path[len('uploads/'):]
    else:
        full_path = Path(file_path)

    if not full_path.exists():
        return {
            "content": [{"type": "text", "text": f"文件不存在: {file_path}"}],
            "is_error": True
        }

    try:
        # 根据文件类型处理
        suffix = full_path.suffix.lower()

        if suffix in ['.xlsx', '.xls']:
            import pandas as pd
            df = pd.read_excel(full_path)
            preview = df.head(10).to_string()
            return {
                "content": [{
                    "type": "text",
                    "text": f"Excel文件预览 (前10行):\n{preview}\n\n总行数: {len(df)}"
                }]
            }
        elif suffix == '.csv':
            import pandas as pd
            df = pd.read_csv(full_path)
            preview = df.head(10).to_string()
            return {
                "content": [{
                    "type": "text",
                    "text": f"CSV文件预览 (前10行):\n{preview}\n\n总行数: {len(df)}"
                }]
            }
        else:
            content = full_path.read_text(encoding='utf-8')[:5000]
            return {
                "content": [{"type": "text", "text": content}]
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"读取文件失败: {str(e)}"}],
            "is_error": True
        }


# ==================== Agent Service V2 ====================

class AgentServiceV2:
    """使用 Claude Agent SDK 的 Agent 服务"""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def _get_base_options(
        self,
        skill: Optional[Skill] = None,
        system_prompt: Optional[str] = None,
    ) -> ClaudeAgentOptions:
        """获取基础配置选项"""

        # 构建系统提示
        default_system_prompt = """你是 AI Skills Platform 的智能助手。

你可以帮助用户：
1. 执行各种技能（使用 execute_skill 工具）
2. 查看可用技能列表（使用 list_skills 工具）
3. 读取用户上传的文件（使用 read_uploaded_file 工具）
4. 执行 bash 命令和文件操作

请根据用户的需求，选择合适的工具来完成任务。
"""

        # 如果有技能，添加技能说明
        if skill:
            skill_folder = SKILLS_STORAGE_DIR / skill.folder_path if skill.folder_path else None
            if skill_folder:
                skill_md_path = skill_folder / "SKILL.md"
                if skill_md_path.exists():
                    skill_content = skill_md_path.read_text(encoding='utf-8')
                    default_system_prompt += f"\n\n当前技能说明:\n{skill_content}"

        final_prompt = system_prompt or default_system_prompt

        # 创建 MCP 服务器用于自定义工具
        mcp_server = create_sdk_mcp_server(
            "skills_tools",
            [execute_skill_tool, list_skills_tool, read_uploaded_file_tool]
        )

        return ClaudeAgentOptions(
            model=self.settings.claude_model or "claude-opus-4-5",
            system_prompt=final_prompt,
            # 使用内置工具
            tools=["Bash", "Read", "Write", "Edit", "Glob", "Grep"],
            # 添加自定义工具服务器
            mcp_servers={"skills": mcp_server},
            # 权限模式 - 绕过确认（生产环境可能需要调整）
            permission_mode="bypassPermissions",
            # 最大轮次
            max_turns=20,
            # 工作目录
            cwd=str(SKILLS_STORAGE_DIR),
        )

    async def chat_stream(
        self,
        message: str,
        skill_id: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        conversation: Optional[List[Dict]] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        enable_rag: bool = True,
    ) -> AsyncIterator[str]:
        """
        流式对话接口（支持 RAG）

        Args:
            message: 用户消息
            skill_id: 可选的技能ID
            file_paths: 可选的文件路径列表
            conversation: 可选的对话历史
            session_id: 可选的会话ID
            agent_id: Agent ID（用于 RAG 数据隔离）
            user_id: 用户ID
            enable_rag: 是否启用 RAG 检索

        Yields:
            JSON 格式的流式响应
        """

        # 加载技能
        skill = None
        if skill_id:
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()

        # 构建提示
        prompt = message

        # 添加文件信息
        if file_paths:
            file_info = "\n".join([f"- {fp}" for fp in file_paths])
            prompt = f"用户上传了以下文件:\n{file_info}\n\n用户请求: {message}"

        # RAG: 从向量数据库检索相关上下文
        rag_context = ""
        if enable_rag and (agent_id or user_id):
            try:
                from services.vector_service import get_vector_service
                vector_service = get_vector_service()
                rag_context = await vector_service.get_context_for_chat(
                    query=message,
                    agent_id=agent_id,
                    user_id=user_id,
                    max_context_length=4000
                )
                if rag_context:
                    prompt = f"""以下是与用户问题相关的文档内容：

{rag_context}

---

用户问题: {message}

请基于上述文档内容回答用户的问题。如果文档中没有相关信息，请如实告知。"""
            except Exception as e:
                print(f"[AgentServiceV2] RAG retrieval failed: {e}")
                # RAG 失败不阻塞主流程

        # 获取配置
        options = self._get_base_options(skill=skill)

        # 如果有会话ID，继续对话
        if session_id:
            options.resume = session_id

        try:
            # 使用 SDK 的 query 函数
            async for event in query(prompt=prompt, options=options):

                # 处理不同类型的消息
                if isinstance(event, AssistantMessage):
                    # 助手消息
                    for block in event.content:
                        if hasattr(block, 'text'):
                            yield json.dumps({
                                "type": "message",
                                "content": block.text
                            })
                        elif hasattr(block, 'name'):
                            # 工具调用
                            yield json.dumps({
                                "type": "tool_use",
                                "tool": block.name,
                                "input": getattr(block, 'input', {})
                            })

                elif isinstance(event, ResultMessage):
                    # 结果消息
                    yield json.dumps({
                        "type": "result",
                        "content": str(event.result) if hasattr(event, 'result') else str(event)
                    })

                elif isinstance(event, StreamEvent):
                    # 流式事件
                    if event.type == "text":
                        yield json.dumps({
                            "type": "stream",
                            "content": event.text if hasattr(event, 'text') else ""
                        })
                    elif event.type == "thinking":
                        yield json.dumps({
                            "type": "thinking",
                            "content": event.text if hasattr(event, 'text') else ""
                        })

                await asyncio.sleep(0)  # 让出控制权

            # 完成
            yield json.dumps({"type": "done", "message": "完成"})

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            })

    async def chat(
        self,
        message: str,
        skill_id: Optional[str] = None,
        file_paths: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        enable_rag: bool = True,
    ) -> Dict[str, Any]:
        """
        非流式对话接口（支持 RAG）

        Returns:
            完整的响应字典
        """
        result_content = []

        async for chunk in self.chat_stream(
            message=message,
            skill_id=skill_id,
            file_paths=file_paths,
            agent_id=agent_id,
            user_id=user_id,
            enable_rag=enable_rag
        ):
            data = json.loads(chunk)
            if data.get("type") == "message":
                result_content.append(data.get("content", ""))
            elif data.get("type") == "stream":
                result_content.append(data.get("content", ""))

        return {
            "status": "success",
            "content": "".join(result_content)
        }

    async def execute_skill_direct(
        self,
        skill_id: str,
        file_paths: List[str],
    ) -> AsyncIterator[str]:
        """
        直接执行技能（不经过 AI 分析）

        用于 exec_mode == "direct" 的技能
        """
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            yield json.dumps({"type": "error", "message": "技能不存在"})
            return

        # 检查是否是直接执行模式
        if skill.folder_path:
            config_path = SKILLS_STORAGE_DIR / skill.folder_path / "config.json"
            if config_path.exists():
                config = json.loads(config_path.read_text(encoding='utf-8'))
                if config.get("exec_mode") == "direct" and skill.entry_script:
                    # 直接执行脚本
                    script_path = SKILLS_STORAGE_DIR / skill.folder_path / skill.entry_script

                    if script_path.exists():
                        yield json.dumps({
                            "type": "message",
                            "content": f"正在执行 {skill.name}..."
                        })

                        try:
                            import subprocess
                            import sys

                            # 获取输入文件
                            input_file = None
                            if file_paths:
                                fp = file_paths[0]
                                if fp.startswith('/uploads/'):
                                    input_file = str(UPLOADS_DIR / fp[len('/uploads/'):])
                                elif fp.startswith('uploads/'):
                                    input_file = str(UPLOADS_DIR / fp[len('uploads/'):])
                                else:
                                    input_file = fp

                            if not input_file:
                                yield json.dumps({"type": "error", "message": "请上传文件"})
                                return

                            # 执行脚本
                            clean_env = {k: v for k, v in __import__('os').environ.items()
                                        if not k.startswith('PYTHON') and k != '__PYVENV_LAUNCHER__'}

                            result = subprocess.run(
                                [sys.executable, str(script_path), input_file],
                                capture_output=True,
                                text=True,
                                timeout=120,
                                cwd=str(SKILLS_STORAGE_DIR / skill.folder_path),
                                env=clean_env,
                                encoding='utf-8'
                            )

                            if result.returncode == 0:
                                yield json.dumps({
                                    "type": "message",
                                    "content": f"[OK] {result.stdout.strip() if result.stdout else '执行完成'}"
                                })

                                # 检查输出文件
                                import time
                                for ext in ['.xlsx', '.csv', '.json', '.pdf']:
                                    for f in OUTPUTS_DIR.glob(f"*{ext}"):
                                        if time.time() - f.stat().st_mtime < 30:
                                            yield json.dumps({
                                                "type": "output_file",
                                                "name": f.name,
                                                "url": f"/outputs/{f.name}"
                                            })
                                            break
                            else:
                                yield json.dumps({
                                    "type": "error",
                                    "message": f"执行失败: {result.stderr or result.stdout}"
                                })

                        except Exception as e:
                            yield json.dumps({"type": "error", "message": f"执行错误: {str(e)}"})

                        yield json.dumps({"type": "done", "message": "完成"})
                        return

        # 如果不是直接执行模式，走正常的 AI 流程
        async for chunk in self.chat_stream(
            f"请执行技能并处理文件",
            skill_id=skill_id,
            file_paths=file_paths
        ):
            yield chunk


# ==================== 工厂函数 ====================

def create_agent_service(db: Session) -> AgentServiceV2:
    """创建 Agent 服务实例"""
    return AgentServiceV2(db)
