"""
Agent Service SDK - 基于 Anthropic SDK 的 Agent 服务

简化版：一切问题都交给 AI 处理，像 Claude CLI 一样
- 不再遇事不决就上 skill
- 不再自动生成 skill
- 直接用 AI 的能力解决问题
"""

import json
import asyncio
import os
import sys
import subprocess
import time
from functools import partial
import anthropic


def _run_subprocess_sync(cmd, **kwargs):
    """同步执行子进程（用于在线程中运行）"""
    return subprocess.run(cmd, **kwargs)


async def _run_subprocess_async(cmd, **kwargs):
    """异步执行子进程，不阻塞事件循环"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # 使用默认线程池
        partial(_run_subprocess_sync, cmd, **kwargs)
    )
from pathlib import Path
from typing import AsyncIterator, Optional, List, Dict, Any

from sqlalchemy.orm import Session

from config import (
    get_settings,
    get_skills_storage_dir,
    get_uploads_dir,
    get_outputs_dir,
    get_server_dir,
    get_file_manage_dir
)
from models.skill import Skill
from models.ccconfig import CCConfig
from models.agent import Agent

# 路径常量
settings = get_settings()
SERVER_DIR = get_server_dir()
OUTPUTS_DIR = get_outputs_dir()
UPLOADS_DIR = get_uploads_dir()
SKILLS_STORAGE_DIR = get_skills_storage_dir()
FILE_MANAGE_DIR = get_file_manage_dir()


# ==================== 工具函数 ====================

def _resolve_file_path(file_path: str) -> str:
    """将 URL 路径或相对路径转换为完整的文件系统路径"""
    if not file_path:
        return file_path

    p = Path(file_path)
    if p.is_absolute() and p.exists():
        return file_path

    # 处理 /file-manage/xxx 格式
    if file_path.startswith('/file-manage/') or file_path.startswith('\\file-manage\\'):
        filename = file_path.replace('/file-manage/', '').replace('\\file-manage\\', '')
        full_path = FILE_MANAGE_DIR / filename
        if full_path.exists():
            return str(full_path)

    # 处理 /uploads/xxx 格式
    if file_path.startswith('/uploads/') or file_path.startswith('\\uploads\\'):
        filename = file_path.replace('/uploads/', '').replace('\\uploads\\', '')
        full_path = UPLOADS_DIR / filename
        if full_path.exists():
            return str(full_path)

    # 处理 /outputs/xxx 格式
    if file_path.startswith('/outputs/') or file_path.startswith('\\outputs\\'):
        filename = file_path.replace('/outputs/', '').replace('\\outputs\\', '')
        full_path = OUTPUTS_DIR / filename
        if full_path.exists():
            return str(full_path)

    # 尝试在 uploads 目录中查找
    uploads_path = UPLOADS_DIR / Path(file_path).name
    if uploads_path.exists():
        return str(uploads_path)

    # 尝试在 file_manage 目录中查找
    file_manage_path = FILE_MANAGE_DIR / Path(file_path).name
    if file_manage_path.exists():
        return str(file_manage_path)

    return file_path


def _resolve_params_paths(params: dict) -> dict:
    """解析 params 中的所有文件路径"""
    resolved = params.copy()
    if resolved.get("file_path"):
        resolved["file_path"] = _resolve_file_path(resolved["file_path"])
    if resolved.get("file_paths"):
        resolved["file_paths"] = [_resolve_file_path(fp) for fp in resolved["file_paths"]]
    return resolved


def _create_output_file_info(file_path: Path, file_type: str = None) -> Dict[str, Any]:
    """创建输出文件信息"""
    if not file_path.exists():
        return None

    if file_type is None:
        ext = file_path.suffix.lower()
        file_type_map = {
            '.json': 'json', '.xlsx': 'excel', '.xls': 'excel',
            '.csv': 'csv', '.pdf': 'pdf', '.html': 'html',
            '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
            '.gif': 'image', '.svg': 'image', '.txt': 'text',
            '.md': 'markdown', '.docx': 'word', '.pptx': 'pptx'
        }
        file_type = file_type_map.get(ext, 'file')

    if settings.storage_type == "minio":
        try:
            from services.storage.utils import upload_local_file_to_storage_sync
            result = upload_local_file_to_storage_sync(file_path)
            return result
        except Exception as e:
            print(f"[Output] 上传到存储失败: {e}, 使用本地路径")

    return {
        "path": str(file_path),
        "type": file_type,
        "name": file_path.name,
        "url": f"/outputs/{file_path.name}",
        "size": file_path.stat().st_size,
        "storage": "local"
    }


def _read_files_for_ai(file_paths: list, max_total_chars: int = 250000) -> str:
    """读取上传的文件内容，转换为 AI 可以处理的文本格式"""
    import pandas as pd

    contents = []
    total_chars = 0
    num_files = len(file_paths)
    per_file_limit = max(10000, max_total_chars // max(num_files, 1))

    for file_path in file_paths:
        if total_chars >= max_total_chars:
            contents.append(f"\n[已达到总字符限制，跳过剩余文件]")
            break

        try:
            resolved_path = _resolve_file_path(file_path)
            path = Path(resolved_path)

            if not path.exists():
                contents.append(f"\n### 文件: {file_path}\n[文件不存在]")
                continue

            suffix = path.suffix.lower()

            if suffix in ['.xlsx', '.xls']:
                xl = pd.ExcelFile(path)
                sheet_names = xl.sheet_names
                file_content = [f"\n### Excel文件: {path.name}"]
                file_content.append(f"Sheet列表: {sheet_names}")

                for sheet_name in sheet_names[:5]:
                    df = pd.read_excel(xl, sheet_name=sheet_name)
                    file_content.append(f"\n#### Sheet: {sheet_name}")
                    file_content.append(f"行数: {len(df)}, 列数: {len(df.columns)}")
                    file_content.append(f"列名: {df.columns.tolist()}")
                    preview_rows = min(20, len(df))
                    preview = df.head(preview_rows).to_string(index=False)
                    file_content.append(f"\n数据预览（前{preview_rows}行）:\n{preview}")
                content = "\n".join(file_content)

            elif suffix == '.csv':
                df = pd.read_csv(path)
                content = f"\n### CSV文件: {path.name}\n"
                content += f"行数: {len(df)}, 列数: {len(df.columns)}\n"
                content += f"列名: {df.columns.tolist()}\n"
                preview = df.head(20).to_string(index=False)
                content += f"\n数据预览（前20行）:\n{preview}"

            elif suffix == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                content = f"\n### JSON文件: {path.name}\n"
                content += json.dumps(data, ensure_ascii=False, indent=2)[:per_file_limit]

            else:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    text = f.read()
                content = f"\n### 文件: {path.name}\n{text[:per_file_limit]}"

            if len(content) > per_file_limit:
                content = content[:per_file_limit] + "\n[内容已截断]"

            contents.append(content)
            total_chars += len(content)

        except Exception as e:
            contents.append(f"\n### 文件: {file_path}\n[读取错误: {str(e)}]")

    return "\n".join(contents)


# ==================== Agent SDK Service ====================

class AgentSDKService:
    """
    基于 Anthropic SDK 的 Agent 服务

    核心原则：一切问题都交给 AI 处理
    - 像 Claude CLI 一样，直接让 AI 解决问题
    - 不自动规划技能
    - 不自动生成技能
    """

    def __init__(self, db: Session):
        self.db = db
        self._skills_cache = {}  # 技能缓存
        self._agents_cache = {}  # Agent 缓存
        self._init_config()
        self._init_client()

    def preload_data(self, skill_ids: List[str] = None, agent_id: str = None):
        """预加载数据到缓存，之后可以安全关闭 DB 连接"""
        from models.skill import Skill
        from models.agent import Agent

        # 预加载技能
        if skill_ids:
            skills = self.db.query(Skill).filter(
                Skill.id.in_(skill_ids),
                Skill.status == "active",
                Skill.deleted_at.is_(None)
            ).all()
            for skill in skills:
                self._skills_cache[skill.id] = {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "skill_path": skill.skill_path,
                    "parameters": skill.parameters
                }
        else:
            # 加载所有活跃技能
            skills = self.db.query(Skill).filter(
                Skill.status == "active",
                Skill.deleted_at.is_(None)
            ).all()
            for skill in skills:
                self._skills_cache[skill.id] = {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "skill_path": skill.skill_path,
                    "parameters": skill.parameters
                }

        # 预加载 Agent
        if agent_id:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                self._agents_cache[agent_id] = {
                    "id": agent.id,
                    "name": agent.name,
                    "skill_ids": agent.skill_ids
                }

        print(f"[AgentSDKService] 预加载完成: {len(self._skills_cache)} 个技能, {len(self._agents_cache)} 个 Agent")

    def get_cached_skill(self, skill_id: str):
        """从缓存获取技能信息"""
        return self._skills_cache.get(skill_id)

    def get_cached_agent(self, agent_id: str):
        """从缓存获取 Agent 信息"""
        return self._agents_cache.get(agent_id)

    def _init_config(self):
        """初始化配置（优先数据库，回退环境变量）"""
        active_config = self.db.query(CCConfig).filter(CCConfig.is_active == True).first()

        if active_config:
            self.model = active_config.model_id
            self.api_key = active_config.api_key
            self.base_url = active_config.base_url
            self.max_tokens = active_config.max_tokens or 16384
            self.temperature = active_config.temperature or 0.7
            self.system_prompt_prefix = active_config.system_prompt or ""
            print(f"[AgentSDKService] 使用数据库配置: {active_config.name} ({active_config.model_id})")
        else:
            self.model = settings.claude_model
            self.api_key = settings.anthropic_auth_token
            self.base_url = settings.anthropic_base_url
            self.max_tokens = 16384
            self.temperature = 0.7
            self.system_prompt_prefix = ""
            print(f"[AgentSDKService] 使用环境变量配置: {settings.claude_model}")

    def _init_client(self):
        """初始化 Anthropic 客户端"""
        # 检测是否使用 Azure 代理
        is_azure = self.base_url and 'azure' in self.base_url.lower()

        if is_azure:
            # Azure 代理模式
            self.client = anthropic.Anthropic(
                api_key="placeholder",  # Azure 不使用这个
                base_url=self.base_url,
                default_headers={"Authorization": f"Bearer {self.api_key}"}
            )
        elif self.base_url:
            # 自定义 base_url
            self.client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            # 直接使用 Anthropic API
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        base_prompt = """你是一个企业数据分析助手。你有专业的报告生成工具可以使用。

【何时调用工具生成报告】
只有当用户**明确要求生成/创建报告**时才调用工具，例如：
- "生成报告"、"出一份报告"、"做个分析报告"
- "看看公司运营情况"、"给我看整体数据"
- "老板报告"、"月报"、"周报"

【何时直接文字回答】
当用户是在**提问或讨论**时，直接用文字回答，不要调用工具：
- "这个报告中的XX是什么意思？" → 解释报告内容
- "HR数据为什么这样？" → 分析原因
- "报告里有什么问题？" → 回答问题
- "怎么看这个数据？" → 给出解读
- 任何带"？"的问题 → 回答问题

【简单判断】
- 用户想要**新的输出/报告** → 调用工具
- 用户想要**答案/解释** → 文字回答

工具会自动读取系统中已有的数据文件，无需用户上传。
"""

        # 添加路径信息
        base_prompt += f"""
## 环境信息

- 上传目录（用户文件）: {UPLOADS_DIR}
- 输出目录（生成文件）: {OUTPUTS_DIR}
"""

        # 添加自定义前缀
        if self.system_prompt_prefix:
            base_prompt = f"{self.system_prompt_prefix}\n\n{base_prompt}"

        return base_prompt

    def _get_skills_as_tools(self, skill_ids: Optional[List[str]] = None) -> List[Dict]:
        """将技能转换为 Claude Tool Use 格式的工具定义"""
        try:
            query = self.db.query(Skill).filter(
                Skill.status == "active",
                Skill.deleted_at.is_(None)
            )

            # 如果提供了 skill_ids，严格按 ID 过滤（只用选中的技能）
            if skill_ids:
                # 过滤掉明显不是有效 UUID 的 ID（如 fallback-1）
                valid_ids = [sid for sid in skill_ids if not sid.startswith('fallback-')]
                if valid_ids:
                    query = query.filter(Skill.id.in_(valid_ids))
                    skills = query.all()
                    print(f"[_get_skills_as_tools] 按 skill_ids 找到 {len(skills)} 个技能")
                else:
                    # 全是无效 ID（如 fallback-1,2,3），不返回任何工具
                    print(f"[_get_skills_as_tools] skill_ids 全是无效 ID，不返回任何工具")
                    skills = []
            else:
                # 没有指定 skill_ids，也不返回任何工具（必须由 Agent 配置指定）
                print(f"[_get_skills_as_tools] 未指定 skill_ids，不返回任何工具")
                skills = []

            if not skills:
                print(f"[_get_skills_as_tools] 未找到任何技能")
                return []

            print(f"[_get_skills_as_tools] 找到 {len(skills)} 个技能:")
            for s in skills:
                print(f"  - {s.name} (ID: {s.id}, folder: {s.folder_path})")

            tools = []
            for skill in skills:
                # 读取 SKILL.md 获取更详细的描述
                skill_description = skill.description or "执行技能任务"
                if skill.folder_path:
                    skill_md_path = SKILLS_STORAGE_DIR / skill.folder_path / "SKILL.md"
                    if skill_md_path.exists():
                        try:
                            content = skill_md_path.read_text(encoding='utf-8')
                            # 提取 YAML front matter 中的 description
                            if content.startswith('---'):
                                end_marker = content.find('---', 3)
                                if end_marker != -1:
                                    front_matter = content[3:end_marker]
                                    # 提取 description 字段
                                    desc_start = front_matter.find('description:')
                                    if desc_start != -1:
                                        desc_content = front_matter[desc_start + len('description:'):].strip()
                                        # 处理多行描述
                                        if desc_content.startswith('|'):
                                            desc_content = desc_content[1:].strip()
                                        # 取到下一个顶级字段为止
                                        lines = []
                                        for line in desc_content.split('\n'):
                                            if line and not line.startswith(' ') and ':' in line:
                                                break
                                            lines.append(line.strip())
                                        skill_description = ' '.join(lines)
                        except:
                            pass

                # 构建工具定义
                tool = {
                    "name": f"skill_{skill.id.replace('-', '_')}",
                    "description": f"""{skill.name}: {skill_description}

当用户的请求符合此技能的触发场景时，直接调用此工具。
无需用户上传文件，工具会自动扫描系统中已有的数据文件。""",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "要处理的文件路径（可选）。如果不传，工具会自动扫描 File Manage 目录下的数据文件。"
                            }
                        },
                        "required": []
                    }
                }
                tools.append(tool)

                # 保存技能 ID 映射（用于执行时查找）
                if not hasattr(self, '_skill_tool_map'):
                    self._skill_tool_map = {}
                self._skill_tool_map[tool["name"]] = skill.id

            return tools
        except Exception as e:
            print(f"[AgentSDKService] 获取技能工具失败: {e}")
            return []

    async def _execute_tool(self, tool_name: str, tool_input: Dict, file_paths: List[str] = None) -> Dict:
        """执行工具调用"""
        # 获取技能 ID
        skill_id = getattr(self, '_skill_tool_map', {}).get(tool_name)
        if not skill_id:
            return {"success": False, "error": f"未找到工具: {tool_name}"}

        # 准备参数
        params = tool_input.copy()

        # 如果有上传的文件，添加到参数中
        if file_paths:
            resolved_paths = [_resolve_file_path(fp) for fp in file_paths]
            params["file_paths"] = resolved_paths
            if not params.get("file_path") and resolved_paths:
                params["file_path"] = resolved_paths[0]

        # 如果工具输入中有 file_path，也需要解析
        if params.get("file_path"):
            params["file_path"] = _resolve_file_path(params["file_path"])

        print(f"[AgentSDKService] 执行工具: {tool_name}, 参数: {params}")

        # 调用技能执行
        result = await self.execute_skill(skill_id, params)
        return result

    async def chat_stream(
        self,
        message: str,
        skill_ids: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        file_paths: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        enable_rag: bool = True,
    ) -> AsyncIterator[str]:
        """
        流式对话接口 - 使用 Tool Use 自动执行技能

        SDK 自动处理工具调用，前端只需展示最终结果
        """
        system_prompt = self._build_system_prompt()

        # 获取可用工具 - 优先使用 Agent 配置的 skills
        print(f"\n[chat_stream] ========== 调试信息 ==========")
        print(f"[chat_stream] agent_id: {agent_id}")
        print(f"[chat_stream] skill_ids (from frontend): {skill_ids}")
        print(f"[chat_stream] file_paths: {file_paths}")

        # 如果有 agent_id，从数据库获取该 Agent 配置的 skills
        actual_skill_ids = skill_ids
        if agent_id:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                print(f"[chat_stream] 找到 Agent: {agent.name} (ID: {agent.id})")
                print(f"[chat_stream] Agent.skills 字段值: {agent.skills}")
                if agent.skills and len(agent.skills) > 0:
                    actual_skill_ids = agent.skills
                    print(f"[chat_stream] 使用 Agent 配置的 skills: {actual_skill_ids}")
                else:
                    print(f"[chat_stream] Agent.skills 为空，使用前端传入的 skill_ids")
            else:
                print(f"[chat_stream] 未找到 Agent (ID: {agent_id})")
        else:
            print(f"[chat_stream] 未提供 agent_id")

        tools = self._get_skills_as_tools(actual_skill_ids)
        print(f"[chat_stream] 获取到 {len(tools)} 个工具")
        for t in tools:
            print(f"[chat_stream] 工具: {t['name']}")
            print(f"[chat_stream] 描述前200字: {t['description'][:200]}...")

        # 构建用户消息
        prompt = message

        # 解析文件路径
        resolved_file_paths = []
        if file_paths:
            resolved_file_paths = [_resolve_file_path(fp) for fp in file_paths]
            file_content = _read_files_for_ai(resolved_file_paths)
            if file_content:
                prompt = f"用户上传了以下文件：\n{file_content}\n\n用户请求：{message}"

        # RAG 检索
        if enable_rag and settings.vector_db_enabled and (agent_id or user_id):
            try:
                from services.vector_service import get_vector_service
                vector_service = get_vector_service()
                if vector_service:
                    rag_context = await vector_service.get_context_for_chat(
                        query=message,
                        agent_id=agent_id,
                        user_id=user_id,
                        max_context_length=4000
                    )
                    if rag_context:
                        prompt = f"""以下是与问题相关的文档内容：

{rag_context}

---

用户问题：{message}

请基于上述内容回答用户的问题。"""
            except Exception as e:
                print(f"[AgentSDKService] RAG 检索失败: {e}")

        # 构建消息列表
        messages = []
        if history:
            for h in history:
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": prompt})

        try:
            # Agent 循环 - 处理工具调用
            max_iterations = 5
            iteration = 0
            # 跟踪已成功执行的技能，防止重复执行
            executed_skills = set()

            while iteration < max_iterations:
                iteration += 1

                # 调用 Claude API
                api_params = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "system": system_prompt,
                    "messages": messages
                }

                # 只有在有工具时才添加 tools 参数
                if tools:
                    api_params["tools"] = tools
                    print(f"[chat_stream] 传递工具给 Claude: {[t['name'] for t in tools]}")

                    # 检测是否应该强制使用工具
                    # 只有明确要求生成报告时才强制，提问时不强制
                    generate_keywords = ['生成报告', '出报告', '做报告', '看看运营', '看运营', '整体情况', '老板报告', '月报', '周报', '出一份', '给我看']
                    question_indicators = ['？', '?', '什么', '为什么', '怎么', '如何', '是否', '能不能', '这个', '那个', '里面', '中的', '意思']

                    # 如果是提问，不强制使用工具
                    is_question = any(q in message for q in question_indicators)
                    has_generate_intent = any(kw in message for kw in generate_keywords)

                    should_force_tool = has_generate_intent and not is_question

                    if should_force_tool and iteration == 1:
                        # 第一次迭代时，如果是明确的生成请求，强制使用工具
                        api_params["tool_choice"] = {"type": "any"}
                        print(f"[chat_stream] 检测到生成报告请求，强制使用工具")
                    elif is_question:
                        print(f"[chat_stream] 检测到提问，让 Claude 自行判断是否需要工具")
                else:
                    print(f"[chat_stream] 没有工具可用，Claude 将直接回答")

                print(f"[chat_stream] 调用 Claude API, model={self.model}")
                # 使用线程池执行同步 API 调用，避免阻塞事件循环
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    **api_params
                )
                print(f"[chat_stream] Claude 响应 stop_reason: {response.stop_reason}")

                # 处理响应
                tool_use_blocks = []
                text_content = ""
                print(f"[chat_stream] 响应内容块数量: {len(response.content)}")

                for block in response.content:
                    print(f"[chat_stream] 内容块类型: {block.type}")
                    if block.type == "text":
                        text_content += block.text
                    elif block.type == "tool_use":
                        tool_use_blocks.append(block)

                # 如果有文本内容，先输出
                if text_content:
                    yield text_content

                # 如果没有工具调用，结束循环
                if not tool_use_blocks:
                    break

                # 处理工具调用
                tool_results = []
                for tool_use in tool_use_blocks:
                    # 获取技能信息
                    skill_id = getattr(self, '_skill_tool_map', {}).get(tool_use.name)
                    skill = self.db.query(Skill).filter(Skill.id == skill_id).first() if skill_id else None
                    skill_key = skill_id or tool_use.name
                    skill_info = {
                        "id": skill_key,
                        "name": skill.name if skill else tool_use.name,
                        "icon": skill.icon if skill else "🔧",
                        "description": skill.description if skill else "执行技能"
                    }

                    # 检查技能是否已经执行过（无论成功失败），防止重复执行
                    if skill_key in executed_skills:
                        print(f"[chat_stream] 技能 {skill_key} 已执行过，跳过重复执行")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": f"该技能已在本次对话中执行过，无需重复执行。请直接使用之前的执行结果，或者告诉用户执行情况。"
                        })
                        continue

                    # 标记技能已执行（在执行前标记，防止并发重复）
                    executed_skills.add(skill_key)

                    # 发送技能开始事件 (使用 ensure_ascii=True 确保所有字符被正确转义)
                    yield f"__SKILL_START__{json.dumps(skill_info)}__SKILL_START__"

                    # 执行工具
                    result = await self._execute_tool(
                        tool_use.name,
                        tool_use.input,
                        resolved_file_paths
                    )

                    # 发送技能结果事件 (使用 ensure_ascii=True 确保所有字符被正确转义)
                    skill_result = {
                        "id": skill_key,
                        "success": result.get("success", False),
                        "output": result.get("output", ""),
                        "error": result.get("error"),
                        "output_file": result.get("_output_file")
                    }
                    yield f"__SKILL_RESULT__{json.dumps(skill_result)}__SKILL_RESULT__"

                    # 构建结果消息给 Claude
                    if result.get("success"):
                        result_text = result.get("output", "执行成功")
                        if result.get("_output_file"):
                            output_file = result["_output_file"]
                            file_url = output_file.get("url", "")
                            file_name = output_file.get("name", "output")
                            result_text += f"\n\n生成的文件: {file_name} ({file_url})"
                    else:
                        result_text = f"执行失败: {result.get('error', '未知错误')}"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result_text
                    })

                # 将助手消息和工具结果添加到消息列表
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            # 如果达到最大迭代次数，输出提示
            if iteration >= max_iterations:
                yield "\n\n⚠️ 达到最大处理轮次"

        except Exception as e:
            print(f"[AgentSDKService] 流式对话错误: {e}")
            import traceback
            traceback.print_exc()
            yield f"\n\n[错误] {str(e)}"

    async def chat(
        self,
        message: str,
        skill_ids: Optional[List[str]] = None,
        history: Optional[List[Dict]] = None,
        file_paths: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        enable_rag: bool = True,
    ) -> str:
        """非流式对话"""
        result = []
        async for chunk in self.chat_stream(
            message=message,
            skill_ids=skill_ids,
            history=history,
            file_paths=file_paths,
            agent_id=agent_id,
            user_id=user_id,
            enable_rag=enable_rag
        ):
            result.append(chunk)
        return "".join(result)

    async def execute_skill(
        self,
        skill_id: str,
        params: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        执行技能

        优先直接执行 main.py，否则使用 AI 基于 SKILL.md 执行
        """
        params = params or {}
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()

        if not skill:
            return {"success": False, "error": "技能不存在", "output": None, "result": None}

        if not skill.folder_path:
            return {"success": False, "error": "技能没有配置文件夹", "output": None, "result": None}

        skill_folder = SKILLS_STORAGE_DIR / skill.folder_path
        main_script = skill_folder / "main.py"

        # ========== 直接执行 main.py ==========
        if main_script.exists():
            print(f"[AgentSDKService] 直接执行 main.py: {main_script}")

            resolved_params = _resolve_params_paths(params)
            params_with_config = {
                **resolved_params,
                "_config": {
                    "server_dir": str(SERVER_DIR),
                    "outputs_dir": str(OUTPUTS_DIR),
                    "uploads_dir": str(UPLOADS_DIR),
                    "file_manage_dir": str(FILE_MANAGE_DIR),
                    "skills_storage_dir": str(SKILLS_STORAGE_DIR),
                    "skill_folder": str(skill_folder)
                }
            }

            try:
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'

                # 将参数通过环境变量传递，避免命令行转义问题
                params_json = json.dumps(params_with_config, ensure_ascii=False)
                env['SKILL_PARAMS'] = params_json

                # 使用异步执行，避免阻塞事件循环
                result = await _run_subprocess_async(
                    [sys.executable, str(main_script), "--from-env"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=180,
                    cwd=str(skill_folder),
                    env=env,
                )

                stdout = result.stdout.strip() if result.stdout else ""
                stderr = result.stderr.strip() if result.stderr else ""

                print(f"[AgentSDKService] 执行完成, returncode={result.returncode}")

                output_data = None
                try:
                    output_data = json.loads(stdout)
                except json.JSONDecodeError:
                    # 查找最后一个完整的 JSON 对象（从最后一个 { 开始）
                    # 技能输出通常是：多行日志 + 最后一行 JSON
                    json_start = stdout.rfind('{"success":')
                    if json_start == -1:
                        json_start = stdout.rfind('{')
                    if json_start != -1:
                        try:
                            output_data = json.loads(stdout[json_start:])
                        except json.JSONDecodeError:
                            # 尝试逐行查找 JSON
                            for line in reversed(stdout.split('\n')):
                                line = line.strip()
                                if line.startswith('{') and line.endswith('}'):
                                    try:
                                        output_data = json.loads(line)
                                        break
                                    except json.JSONDecodeError:
                                        continue

                if output_data:
                    output_file_info = output_data.get("_output_file")

                    if output_file_info:
                        original_path = output_file_info.get("path")
                        if original_path and Path(original_path).exists():
                            try:
                                from services.storage.utils import upload_local_file_to_storage_sync
                                output_file_info = upload_local_file_to_storage_sync(Path(original_path))
                            except Exception as e:
                                print(f"[AgentSDKService] 上传失败: {e}")
                        else:
                            for ext in ['.pdf', '.xlsx', '.csv', '.json', '.png', '.html', '.docx', '.pptx']:
                                for f in OUTPUTS_DIR.glob(f"*{ext}"):
                                    if time.time() - f.stat().st_mtime < 60:
                                        output_file_info = _create_output_file_info(f)
                                        break
                                if output_file_info:
                                    break

                    # 使用技能返回的 output 字段，而不是整个 stdout
                    clean_output = output_data.get("output") or output_data.get("message") or "执行完成"
                    print(f"[AgentSDKService] 技能输出: {clean_output[:100]}...")

                    return {
                        "success": output_data.get("success", True),
                        "error": output_data.get("error"),
                        "output": clean_output,
                        "result": output_data.get("result"),
                        "_output_file": output_file_info
                    }
                else:
                    if result.returncode == 0:
                        return {"success": True, "error": None, "output": stdout or "执行完成", "result": None}
                    else:
                        return {"success": False, "error": stderr or stdout or "执行失败", "output": stdout, "result": None}

            except subprocess.TimeoutExpired:
                return {"success": False, "error": "执行超时", "output": None, "result": None}
            except Exception as e:
                return {"success": False, "error": str(e), "output": None, "result": None}

        # ========== AI 执行（基于 SKILL.md）==========
        skill_md_path = skill_folder / "SKILL.md"
        if not skill_md_path.exists():
            return {"success": False, "error": "技能没有 main.py 或 SKILL.md", "output": None, "result": None}

        print(f"[AgentSDKService] 使用 AI 执行技能: {skill.name}")

        skill_md_content = skill_md_path.read_text(encoding='utf-8')

        context = params.get("context", "") or params.get("skillDescription", "")
        file_paths = params.get("file_paths", [])
        file_path = params.get("file_path", "")
        if file_path and file_path not in file_paths:
            file_paths.append(file_path)

        user_message = context or "请根据技能说明执行任务"
        if file_paths:
            file_content = _read_files_for_ai(file_paths)
            user_message = f"用户上传了以下文件：\n{file_content}\n\n用户请求: {user_message}"

        system_prompt = f"""{skill_md_content}

## 工作目录
当前工作目录: {skill_folder}
输出目录: {OUTPUTS_DIR}
上传目录: {UPLOADS_DIR}

## 执行要求
1. 严格按照 SKILL.md 中的指示执行
2. 输出文件必须保存到 {OUTPUTS_DIR} 目录
"""

        try:
            # 使用线程池执行同步 API 调用，避免阻塞事件循环
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            final_output = response.content[0].text

            # 检查输出文件
            output_files = []
            for ext in ['.pdf', '.xlsx', '.csv', '.json', '.png', '.html']:
                for f in OUTPUTS_DIR.glob(f"*{ext}"):
                    if time.time() - f.stat().st_mtime < 60:
                        output_files.append(_create_output_file_info(f))

            return {
                "success": True,
                "error": None,
                "output": final_output,
                "result": {"content": final_output},
                "_output_file": output_files[0] if output_files else None
            }

        except Exception as e:
            print(f"[AgentSDKService] AI 执行失败: {e}")
            return {"success": False, "error": str(e), "output": None, "result": None}

    async def execute_temp_skill(
        self,
        temp_folder: Path,
        skill_name: str,
        script_name: Optional[str] = None,
        params: Dict[str, Any] = None,
    ) -> tuple:
        """执行临时技能（用于测试）"""
        params = params or {}
        script_name = script_name or "main.py"
        script_path = temp_folder / script_name

        if not script_path.exists():
            return False, None, f"脚本不存在: {script_name}", None

        resolved_params = _resolve_params_paths(params)
        params_with_config = {
            **resolved_params,
            "_config": {
                "server_dir": str(SERVER_DIR),
                "outputs_dir": str(OUTPUTS_DIR),
                "uploads_dir": str(UPLOADS_DIR),
                "file_manage_dir": str(FILE_MANAGE_DIR),
                "skills_storage_dir": str(SKILLS_STORAGE_DIR),
                "skill_folder": str(temp_folder)
            }
        }

        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            # 使用异步执行，避免阻塞事件循环
            result = await _run_subprocess_async(
                [sys.executable, str(script_path), json.dumps(params_with_config)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120,
                cwd=str(temp_folder),
                env=env,
            )

            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""

            if result.returncode == 0:
                try:
                    output_data = json.loads(stdout)
                    return True, output_data.get("result"), None, output_data.get("output") or stdout
                except json.JSONDecodeError:
                    return True, None, None, stdout
            else:
                return False, None, stderr or stdout or "执行失败", stdout

        except subprocess.TimeoutExpired:
            return False, None, "执行超时", None
        except Exception as e:
            return False, None, str(e), None

    def _read_files_for_ai(self, file_paths: list, max_total_chars: int = 250000) -> str:
        """读取文件内容供 AI 使用"""
        return _read_files_for_ai(file_paths, max_total_chars)

    async def skill_chat_stream(
        self,
        skill_id: str,
        context: str,
        conversation: Optional[List[Dict]] = None,
        file_paths: Optional[List[str]] = None,
        user_choice: Optional[str] = None,
        pending_actions: Optional[List[Dict]] = None,
        current_action_index: int = 0,
        agent_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """交互式技能执行"""
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            yield json.dumps({"type": "error", "message": "技能不存在"})
            return

        prompt = context or "请执行技能"
        if file_paths:
            file_content = _read_files_for_ai(file_paths)
            prompt = f"用户上传了以下文件：\n{file_content}\n\n用户请求：{prompt}"

        async for chunk in self.chat_stream(
            message=prompt,
            skill_ids=[skill_id],
            file_paths=file_paths,
            agent_id=agent_id
        ):
            yield json.dumps({"type": "content", "content": chunk})

        yield json.dumps({"type": "done"})

    async def skill_execute_interactive(
        self,
        skill_id: str,
        context: str,
        file_paths: Optional[List[str]] = None,
        confirmed_step: Optional[int] = None,
        auto_confirm: bool = False,
        skip_current: bool = False,
    ) -> AsyncIterator[str]:
        """交互式技能执行"""
        result = await self.execute_skill(skill_id, {
            "context": context,
            "file_paths": file_paths or []
        })

        if result.get("success"):
            yield json.dumps({
                "type": "all_done",
                "success": True,
                "output": result.get("output"),
                "output_file": result.get("_output_file")
            })
        else:
            yield json.dumps({
                "type": "error",
                "message": result.get("error", "执行失败")
            })

    async def agent_loop(
        self,
        skill_id: str,
        context: str,
        file_paths: Optional[List[str]] = None,
        conversation: Optional[List[Dict]] = None,
        pending_tool_call: Optional[Dict] = None,
        tool_confirmed: bool = False,
        tool_rejected: bool = False,
        user_edit: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Agent 循环"""
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            yield json.dumps({"type": "error", "message": "技能不存在"})
            return

        prompt = context or "请执行技能"
        if file_paths:
            file_content = _read_files_for_ai(file_paths)
            prompt = f"用户上传了以下文件：\n{file_content}\n\n用户请求：{prompt}"

        yield json.dumps({"type": "thinking", "content": "正在分析任务..."})

        async for chunk in self.chat_stream(
            message=prompt,
            skill_ids=[skill_id],
            file_paths=file_paths
        ):
            yield json.dumps({"type": "message", "content": chunk})

        yield json.dumps({"type": "done"})


# ==================== 工厂函数 ====================

def create_agent_service(db: Session) -> AgentSDKService:
    """创建 Agent 服务实例"""
    return AgentSDKService(db)
