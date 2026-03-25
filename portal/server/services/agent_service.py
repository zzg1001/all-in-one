import json
import os
import sys
from io import StringIO
from pathlib import Path
from typing import List, Optional, Dict, Any, AsyncGenerator
from sqlalchemy.orm import Session
import anthropic
import pandas as pd
from config import (
    get_settings,
    get_skills_storage_dir,
    get_uploads_dir,
    get_outputs_dir,
    get_server_dir
)
from models.skill import Skill
from models.ccconfig import CCConfig
from schemas.agent import SkillPlanItem
from services.file_generator import generate_unique_filename
from routers.logs import log_ai_start, log_ai_done, log_error

settings = get_settings()

# 使用统一配置的路径
SKILLS_STORAGE_DIR = get_skills_storage_dir()
UPLOADS_DIR = get_uploads_dir()
OUTPUTS_DIR = get_outputs_dir()
SERVER_DIR = get_server_dir()


class AgentService:
    def __init__(self, db: Session):
        self.db = db
        self._init_client()

    def _init_client(self):
        """初始化 Claude 客户端，优先使用数据库中的配置"""
        # 尝试从数据库获取启用的配置
        active_config = self.db.query(CCConfig).filter(CCConfig.is_active == True).first()

        if active_config:
            # 使用数据库配置
            client_kwargs = {"api_key": active_config.api_key}
            if active_config.base_url:
                client_kwargs["base_url"] = active_config.base_url
            self.client = anthropic.Anthropic(**client_kwargs)
            self.model = active_config.model_id
            self.max_tokens = active_config.max_tokens or 4096
            self.temperature = active_config.temperature or 0.7
            self.system_prompt_prefix = active_config.system_prompt or ""
            print(f"[AgentService] 使用数据库配置: {active_config.name} ({active_config.model_id})")
        else:
            # 回退到环境变量配置
            client_kwargs = {"api_key": settings.anthropic_api_key}
            if settings.anthropic_base_url:
                client_kwargs["base_url"] = settings.anthropic_base_url
            self.client = anthropic.Anthropic(**client_kwargs)
            self.model = settings.claude_model
            self.max_tokens = 4096
            self.temperature = 0.7
            self.system_prompt_prefix = ""
            print(f"[AgentService] 使用环境变量配置: {settings.claude_model}")

    def _get_skills_context(self, skill_ids: Optional[List[str]] = None, load_full_content: bool = False) -> str:
        """Get skills information for AI context

        Args:
            skill_ids: List of skill IDs to filter by
            load_full_content: If True, load full SKILL.md content for each skill
        """
        query = self.db.query(Skill)
        if skill_ids:
            query = query.filter(Skill.id.in_(skill_ids))
        skills = query.all()

        if not skills:
            return "No skills available."

        skills_info = []
        for skill in skills:
            info = f"- ID: {skill.id}, Name: {skill.name}"
            if skill.description:
                info += f", Description: {skill.description}"
            if skill.tags:
                info += f", Tags: {', '.join(skill.tags)}"
            skills_info.append(info)

            # Load full SKILL.md content if requested and skill has folder
            if load_full_content and skill.folder_path:
                skill_folder = SKILLS_STORAGE_DIR / skill.folder_path
                skill_md_path = skill_folder / "SKILL.md"
                if skill_md_path.exists():
                    try:
                        skill_md_content = skill_md_path.read_text(encoding="utf-8")
                        skills_info.append(f"\n--- Full content for {skill.name} ---\n{skill_md_content}\n---\n")
                    except Exception:
                        pass

        return "Available skills:\n" + "\n".join(skills_info)

    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        skill_ids: Optional[List[str]] = None
    ) -> str:
        """Simple chat with Claude AI"""
        # Load full content when specific skills are provided
        load_full = skill_ids is not None and len(skill_ids) > 0
        skills_context = self._get_skills_context(skill_ids, load_full_content=load_full)

        system_prompt = f"""你是一个智能AI Agent，能够分析用户需求并规划技能（Skills）执行流程。

{skills_context}

## 核心职责
当用户提出**任务型请求**时，分析并规划技能执行流程。

## 技能匹配规则
**重要**：优先使用已存在的技能！匹配时注意：
- "ppt"、"PPT"、"幻灯片"、"演示文稿" → 使用 **pptx** 技能
- "excel"、"表格"、"xlsx" → 使用相关 Excel 技能
- 如果有近似名称的技能存在，使用它而不是建议创建新技能
- 只有当确实没有合适的技能时，才设置 exists: false

## 技能规划格式
如果识别到任务请求，在回复末尾添加：
<!--SKILL_PLAN:[{{"skill":"技能名","action":"操作描述","exists":true/false}}]-->

## 多文件处理规则
**重要**：当用户上传多个文件时，同一类型的文件应由**同一个技能**一次性处理，不要为每个文件创建单独的步骤。

## 回复格式
- 使用 Markdown：**粗体**、`代码`、列表
- 简洁专业，中文回复"""

        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text

    async def chat_stream(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        skill_ids: Optional[List[str]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from Claude AI"""
        # Load full content when specific skills are provided
        load_full = skill_ids is not None and len(skill_ids) > 0
        skills_context = self._get_skills_context(skill_ids, load_full_content=load_full)

        system_prompt = f"""你是一个智能AI Agent，能够分析用户需求并规划技能（Skills）执行流程。

{skills_context}

## 核心职责
当用户提出**任务型请求**（如"帮我做..."、"我想要..."、"请处理..."、"分析..."、"生成..."等），你需要：
1. 分析任务需要哪些步骤
2. 将步骤映射到可用的 Skills
3. 在回复末尾输出技能规划（使用特定格式）

## 技能匹配规则（最重要）
**必须优先使用已存在的技能！** 匹配时注意：
- "ppt"、"PPT"、"幻灯片"、"演示文稿"、"slides" → 使用 **pptx** 技能
- "excel"、"表格"、"xlsx"、"xls" → 使用相关 Excel 技能
- "word"、"文档"、"docx" → 使用相关 Word 技能
- 如果有**名称相似或功能匹配**的技能存在，**必须使用它**，设置 exists: true
- 只有当 Available skills 列表中**确实没有**任何合适的技能时，才设置 exists: false

## 技能规划格式
如果识别到任务请求，请在回复**末尾**添加如下格式（必须是最后一行）：
<!--SKILL_PLAN:[{{"skill":"技能名","action":"操作描述","exists":true/false}}]-->

- `skill`: 技能名称（**必须使用 Available skills 中存在的技能名称**，而不是自己编造的名称）
- `action`: 这一步要做什么
- `exists`: 检查 Available skills 列表判断技能是否存在


## 示例
用户: "帮我分析销售数据并生成报告"

回复:
好的，我来帮你完成这个任务！我规划了以下执行流程：

1. **数据处理** - 使用 `data-processor` 读取和清洗数据
2. **数据分析** - 使用 `data-analyzer` 进行统计分析
3. **报告生成** - 使用 `report-generator` 生成可视化报告

点击下方流程即可开始执行。

<!--SKILL_PLAN:[{{"skill":"data-processor","action":"读取销售数据","exists":true}},{{"skill":"data-analyzer","action":"统计分析","exists":false}},{{"skill":"report-generator","action":"生成报告","exists":false}}]-->

## 多文件处理规则
**重要**：当用户上传多个文件时：
- 同一类型的文件应由**同一个技能**一次性处理（技能会接收所有文件路径）
- 不要为每个文件创建单独的技能步骤
- 例如：用户上传4个Excel文件要求分析，只需要1个 `data-understanding` 技能，不是4个

## 回复格式
- 使用 Markdown：**粗体**、`代码`、列表
- 简洁专业，中文回复
- 如果不是任务请求（如闲聊、提问），正常对话，不需要 SKILL_PLAN"""

        messages = []
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        with self.client.messages.stream(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield text

    async def plan_skills(
        self,
        user_input: str,
        available_skill_ids: Optional[List[str]] = None
    ) -> tuple[List[SkillPlanItem], str]:
        """Plan which skills to use based on user input"""
        skills_context = self._get_skills_context(available_skill_ids)

        system_prompt = f"""You are a skill planning assistant. Based on user requirements,
analyze and recommend which skills to use.

{skills_context}

Respond in JSON format with:
{{
    "plan": [
        {{
            "skill_id": "<uuid>",
            "skill_name": "<name>",
            "reason": "<why this skill>",
            "params": {{}}
        }}
    ],
    "explanation": "<overall explanation>"
}}

If no suitable skills are found, return an empty plan with an explanation."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_input}]
        )

        try:
            result = json.loads(response.content[0].text)
            plan_items = [SkillPlanItem(**item) for item in result.get("plan", [])]
            explanation = result.get("explanation", "")
            return plan_items, explanation
        except json.JSONDecodeError:
            return [], "Failed to parse AI response"

    def _build_multimodal_content(self, text: str, file_content: str) -> list:
        """
        构建多模态消息内容，支持文本和图片

        从 file_content 中提取图片标记 [IMAGE:mime_type:base64_data]
        并转换为 Claude API 的多模态格式
        """
        import re

        content_parts = []

        # 添加用户文本
        if text:
            content_parts.append({"type": "text", "text": text})

        if not file_content:
            # 如果没有文件内容，返回简单格式
            return text if not content_parts else content_parts

        # 提取图片标记
        image_pattern = r'\[IMAGE:(image/[^:]+):([A-Za-z0-9+/=]+)\]'
        images = re.findall(image_pattern, file_content)

        # 移除图片标记，保留其他文本内容
        text_content = re.sub(image_pattern, '[图片已作为独立内容传递]', file_content)

        if text_content.strip():
            content_parts.append({
                "type": "text",
                "text": f"\n\n## 用户上传的文件数据\n{text_content}"
            })

        # 添加图片
        for mime_type, base64_data in images:
            content_parts.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": base64_data
                }
            })

        return content_parts if content_parts else text

    def _detect_skill_output_format(self, skill_name: str, skill_description: str, skill_md_content: str) -> str:
        """
        检测技能的输出格式

        规则很简单：
        1. 如果 SKILL.md frontmatter 中有 output_format 字段，用它
        2. 如果 SKILL.md 中有 <!--OUTPUT_FORMAT:xxx--> 声明，用它
        3. 否则默认 md
        """
        import re
        import yaml

        # 1. 尝试解析 frontmatter 中的 output_format
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', skill_md_content, re.DOTALL)
        if frontmatter_match:
            try:
                frontmatter = yaml.safe_load(frontmatter_match.group(1))
                if frontmatter and 'output_format' in frontmatter:
                    return frontmatter['output_format'].lower()
            except:
                pass

        # 2. 检查内容中是否有格式声明
        format_match = re.search(r'<!--OUTPUT_FORMAT:(\w+)-->', skill_md_content, re.IGNORECASE)
        if format_match:
            return format_match.group(1).lower()

        # 3. 默认 md
        return "md"

    def _parse_output_format(self, ai_output: str) -> tuple[Optional[str], str]:
        """
        解析 AI 输出中的格式声明标记

        AI 输出格式：
        <!--OUTPUT_FORMAT:md-->
        实际内容...

        Returns:
            (format, clean_content): 格式类型和去除标记后的内容
        """
        import re
        import base64

        # 匹配格式声明标记
        pattern = r'^<!--OUTPUT_FORMAT:(\w+)-->\s*'
        match = re.match(pattern, ai_output.strip(), re.IGNORECASE)

        if match:
            output_format = match.group(1).lower()
            clean_content = re.sub(pattern, '', ai_output.strip(), count=1, flags=re.IGNORECASE)
            return output_format, clean_content.strip()

        # 自动检测 pptxgenjs 代码（用于 PPT skill）
        # 检查是否包含 pptxgenjs 特征
        pptx_patterns = [
            (r'require\s*\(\s*["\']pptxgenjs["\']', 'require pptxgenjs'),
            (r'new\s+pptxgen\s*\(', 'new pptxgen'),
            (r'\.addSlide\s*\(', 'addSlide'),
            (r'\.writeFile\s*\(', 'writeFile'),
            (r'\.addText\s*\(', 'addText'),
            (r'\.addShape\s*\(', 'addShape'),
            (r'pres\s*=', 'pres ='),
            (r'let\s+pres\b', 'let pres'),
            (r'const\s+pres\b', 'const pres'),
        ]

        matched_patterns = []
        for pattern, name in pptx_patterns:
            if re.search(pattern, ai_output, re.IGNORECASE):
                matched_patterns.append(name)

        print(f"[_parse_output_format] AI output length: {len(ai_output)}")
        print(f"[_parse_output_format] AI output preview: {ai_output[:300]}...")
        print(f"[_parse_output_format] Matched PPTX patterns: {matched_patterns}")

        # 如果匹配到 2 个以上特征，认为是 pptxgenjs 代码
        if len(matched_patterns) >= 2:
            print(f"[_parse_output_format] ✓ Detected pptxgenjs code!")
            # 提取代码块
            code_match = re.search(r'```(?:javascript|js)?\s*\n(.*?)```', ai_output, re.DOTALL)
            if code_match:
                extracted_code = code_match.group(1).strip()
                print(f"[_parse_output_format] Extracted code from code block, length: {len(extracted_code)}")
                return "pptx_code", extracted_code
            else:
                # 没有代码块包裹，直接返回整个内容
                print(f"[_parse_output_format] No code block found, using full output")
                return "pptx_code", ai_output.strip()

        # 默认 md
        print(f"[_parse_output_format] No PPTX patterns detected, defaulting to md")
        return "md", ai_output

    def _execute_image_code(self, code: str, skill_name: str) -> Optional[dict]:
        """
        执行图片生成代码（matplotlib/PIL）

        Returns:
            {"path": ..., "type": ..., "name": ..., "url": ...} 或 None
        """
        import tempfile
        import subprocess

        try:
            # 创建临时脚本
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                # 添加保存图片的代码
                output_path = OUTPUTS_DIR / f"{skill_name}_{int(__import__('time').time())}.png"
                wrapped_code = f"""
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt

{code}

# 自动保存图片
plt.savefig(r'{output_path}', dpi=150, bbox_inches='tight')
plt.close()
print(r'{output_path}')
"""
                f.write(wrapped_code)
                script_path = f.name

            # 执行脚本
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            # 清理临时文件
            Path(script_path).unlink(missing_ok=True)

            if result.returncode == 0 and output_path.exists():
                file_size = output_path.stat().st_size
                return {
                    "path": str(output_path),
                    "type": "png",
                    "name": output_path.name,
                    "url": f"/outputs/{output_path.name}",
                    "size": file_size
                }
        except Exception as e:
            print(f"[Image Code] Execution failed: {e}")

        return None

    def _execute_img_process_code(self, code: str, skill_name: str, input_paths: list) -> Optional[dict]:
        """
        执行图片处理代码（PIL/Pillow）

        Args:
            code: PIL 处理代码
            skill_name: 技能名称
            input_paths: 输入图片路径列表

        Returns:
            {"path": ..., "type": ..., "name": ..., "url": ...} 或 None
        """
        import tempfile
        import subprocess
        import time

        if not input_paths:
            print("[Img Process] No input images provided")
            return None

        # 取第一个图片作为输入，转换 URL 路径
        raw_path = input_paths[0]
        if raw_path.startswith("/uploads/"):
            input_path = str(UPLOADS_DIR / raw_path[len("/uploads/"):])
        elif raw_path.startswith("/outputs/"):
            input_path = str(OUTPUTS_DIR / raw_path[len("/outputs/"):])
        else:
            input_path = raw_path

        if not Path(input_path).exists():
            print(f"[Img Process] Input file not found: {input_path}")
            return None

        try:
            # 生成输出路径
            timestamp = int(time.time())
            output_filename = f"{skill_name}_processed_{timestamp}.png"
            output_path = OUTPUTS_DIR / output_filename

            # 创建临时脚本
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                # 注入 INPUT_PATH 和 OUTPUT_PATH
                wrapped_code = f"""
# 系统注入的路径变量
INPUT_PATH = r'{input_path}'
OUTPUT_PATH = r'{output_path}'

{code}
"""
                f.write(wrapped_code)
                script_path = f.name

            # 执行脚本
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=120  # 图片处理可能需要更长时间
            )

            # 清理临时文件
            Path(script_path).unlink(missing_ok=True)

            if result.returncode == 0 and output_path.exists():
                file_size = output_path.stat().st_size
                return {
                    "path": str(output_path),
                    "type": "png",
                    "name": output_filename,
                    "url": f"/outputs/{output_filename}",
                    "size": file_size
                }
            else:
                print(f"[Img Process] Execution failed: {result.stderr}")

        except Exception as e:
            print(f"[Img Process] Execution failed: {e}")

        return None

    def _execute_pptx_code(self, code: str, skill_name: str, timeout: int = 120) -> Optional[dict]:
        """
        执行 pptxgenjs JavaScript 代码生成 PPT 文件

        Args:
            code: JavaScript 代码（使用 pptxgenjs）
            skill_name: 技能名称（用于生成文件名）
            timeout: 执行超时秒数

        Returns:
            成功时返回文件信息 dict，失败返回 None
        """
        import tempfile
        import subprocess
        import time
        import shutil

        try:
            timestamp = int(time.time())
            output_filename = f"{skill_name}_{timestamp}.pptx"
            output_path = OUTPUTS_DIR / output_filename

            # 检查 node 是否可用
            node_path = shutil.which('node')
            npm_path = shutil.which('npm')
            if not node_path:
                print("[PPTX Code] Node.js not found in PATH")
                return None

            # 检查并安装 pptxgenjs（在 server 目录下）
            node_modules_path = SERVER_DIR / "node_modules" / "pptxgenjs"
            if not node_modules_path.exists():
                print(f"[PPTX Code] pptxgenjs not found at {node_modules_path}, installing...")
                if npm_path:
                    # 先确保 package.json 存在，否则 npm install 可能失败
                    package_json_path = SERVER_DIR / "package.json"
                    if not package_json_path.exists():
                        print("[PPTX Code] Creating package.json...")
                        init_result = subprocess.run(
                            [npm_path, "init", "-y"],
                            capture_output=True,
                            text=True,
                            timeout=30,
                            cwd=str(SERVER_DIR)
                        )
                        if init_result.returncode != 0:
                            print(f"[PPTX Code] npm init failed: {init_result.stderr}")

                    install_result = subprocess.run(
                        [npm_path, "install", "pptxgenjs"],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        cwd=str(SERVER_DIR)
                    )
                    if install_result.returncode != 0:
                        print(f"[PPTX Code] npm install failed: {install_result.stderr}")
                        return None
                    print("[PPTX Code] pptxgenjs installed successfully")
                else:
                    print("[PPTX Code] npm not found, cannot install pptxgenjs")
                    return None
            else:
                print(f"[PPTX Code] pptxgenjs found at {node_modules_path}")

            # 清理代码：移除 markdown 代码块标记
            clean_code = code.strip()
            if clean_code.startswith('```javascript'):
                clean_code = clean_code[len('```javascript'):].strip()
            elif clean_code.startswith('```js'):
                clean_code = clean_code[len('```js'):].strip()
            elif clean_code.startswith('```'):
                clean_code = clean_code[3:].strip()
            if clean_code.endswith('```'):
                clean_code = clean_code[:-3].strip()

            # 将 Windows 路径转换为正斜杠（JavaScript 兼容）
            output_path_str = str(output_path).replace('\\', '/')

            # 修改代码中的输出文件路径
            import re
            # 替换 writeFile 调用中的文件名
            clean_code = re.sub(
                r'writeFile\s*\(\s*\{[^}]*fileName\s*:\s*["\'][^"\']*["\']',
                f'writeFile({{ fileName: "{output_path_str}"',
                clean_code
            )
            # 也处理简单的 writeFile("filename.pptx") 格式
            clean_code = re.sub(
                r'writeFile\s*\(\s*["\'][^"\']+\.pptx["\']',
                f'writeFile("{output_path_str}"',
                clean_code
            )

            # 如果代码没有 writeFile，添加一个
            if 'writeFile' not in clean_code:
                clean_code += f'\npres.writeFile({{ fileName: "{output_path_str}" }});'

            # 创建临时脚本
            # 需要包装成 async/await 以等待 writeFile 完成
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
                # 检查代码是否已经是 async 函数
                if 'async' in clean_code and 'await' in clean_code:
                    wrapped_code = f'''
const pptxgen = require("pptxgenjs");

{clean_code}
'''
                else:
                    # 将代码包装成 async 函数并等待 writeFile
                    # 替换 writeFile 为 await writeFile
                    async_code = clean_code
                    if '.writeFile(' in async_code and 'await' not in async_code:
                        async_code = re.sub(
                            r'(pres\.writeFile\s*\([^)]*\))',
                            r'await \1',
                            async_code
                        )

                    wrapped_code = f'''
const pptxgen = require("pptxgenjs");

(async () => {{
{async_code}
}})().catch(err => {{
    console.error("Error:", err);
    process.exit(1);
}});
'''
                f.write(wrapped_code)
                script_path = f.name

            print(f"[PPTX Code] Executing script: {script_path}")
            print(f"[PPTX Code] Output path: {output_path}")
            print(f"[PPTX Code] Working dir: {SERVER_DIR}")
            print(f"[PPTX Code] Script content preview: {wrapped_code[:800]}...")

            # 执行脚本（在 server 目录下执行，以便找到 node_modules）
            result = subprocess.run(
                [node_path, script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(SERVER_DIR)
            )

            # 清理临时文件
            Path(script_path).unlink(missing_ok=True)

            print(f"[PPTX Code] Return code: {result.returncode}")
            print(f"[PPTX Code] stdout: {result.stdout[:500] if result.stdout else 'empty'}")
            print(f"[PPTX Code] stderr: {result.stderr[:500] if result.stderr else 'empty'}")

            # 检查输出文件是否生成
            if output_path.exists():
                print(f"[PPTX Code] Success! File created: {output_path}")
                return {
                    "path": str(output_path),
                    "type": "pptx",
                    "name": output_filename,
                    "url": f"/outputs/{output_filename}",
                    "size": output_path.stat().st_size
                }
            else:
                # 查找 outputs 目录下任何新生成的 .pptx 文件
                for pptx_file in OUTPUTS_DIR.glob("*.pptx"):
                    if pptx_file.stat().st_mtime > timestamp - 5:  # 5秒内创建的
                        print(f"[PPTX Code] Found generated file: {pptx_file}")
                        return {
                            "path": str(pptx_file),
                            "type": "pptx",
                            "name": pptx_file.name,
                            "url": f"/outputs/{pptx_file.name}",
                            "size": pptx_file.stat().st_size
                        }

                print(f"[PPTX Code] Failed: No output file found")
                print(f"[PPTX Code] stderr: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print(f"[PPTX Code] Timeout after {timeout}s")
            return None
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[PPTX Code] Error: {e}")
            return None

    def _execute_analysis_code(self, code: str, file_paths: list, timeout: int = 120) -> dict:
        """
        执行数据分析代码（通用 Python 分析）

        支持库: pandas, numpy, matplotlib, seaborn, scipy, json, datetime
        安全机制: subprocess 隔离, 超时控制, 目录沙箱

        Args:
            code: Python 分析代码
            file_paths: 输入文件路径列表
            timeout: 执行超时秒数

        Returns:
            {
                'success': bool,
                'stdout': str,
                'stderr': str,
                'generated_files': list,
                'error': str (if failed)
            }
        """
        import tempfile
        import subprocess
        import time
        import glob

        try:
            # 生成时间戳用于输出文件
            timestamp = int(time.time())
            output_prefix = f"analysis_{timestamp}"

            # 安全检查：禁止危险操作
            dangerous_patterns = [
                'os.system', 'subprocess.', 'eval(', 'exec(',
                '__import__', 'open(', 'with open',
                'shutil.rmtree', 'os.remove', 'os.unlink',
                'importlib', 'compile('
            ]

            code_lower = code.lower()
            for pattern in dangerous_patterns:
                if pattern.lower() in code_lower:
                    # 允许 open 用于读取
                    if pattern in ['open(', 'with open']:
                        # 检查是否只是读取模式
                        if "'w'" not in code and '"w"' not in code and "'a'" not in code and '"a"' not in code:
                            continue
                    return {
                        'success': False,
                        'stdout': '',
                        'stderr': f'安全限制：禁止使用 {pattern}',
                        'generated_files': [],
                        'error': f'代码包含不允许的操作: {pattern}'
                    }

            # 转换 URL 路径为文件系统路径
            resolved_paths = []
            for fp in file_paths:
                if fp.startswith("/uploads/"):
                    resolved_paths.append(str(UPLOADS_DIR / fp[len("/uploads/"):]))
                elif fp.startswith("/outputs/"):
                    resolved_paths.append(str(OUTPUTS_DIR / fp[len("/outputs/"):]))
                else:
                    resolved_paths.append(fp)

            # 构建文件路径列表字符串
            file_paths_str = repr(resolved_paths)

            # 创建临时脚本
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                wrapped_code = f'''
# -*- coding: utf-8 -*-
import sys
import os

# 设置工作目录
os.chdir(r'{OUTPUTS_DIR}')

# 系统注入的变量
FILE_PATHS = {file_paths_str}
OUTPUT_DIR = r'{OUTPUTS_DIR}'
OUTPUT_PREFIX = '{output_prefix}'

# 导入常用库
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

# 可选导入
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    plt = None

try:
    import seaborn as sns
except ImportError:
    sns = None

try:
    from scipy import stats
except ImportError:
    stats = None

# 辅助函数：保存图表
def save_figure(name=None):
    if plt is None:
        return None
    fig_name = name or f'{{OUTPUT_PREFIX}}_figure.png'
    if not fig_name.endswith('.png'):
        fig_name += '.png'
    fig_path = os.path.join(OUTPUT_DIR, fig_name)
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'[GENERATED_FILE]{{fig_path}}')
    return fig_path

# 辅助函数：保存数据
def save_data(data, name=None, format='csv'):
    if isinstance(data, pd.DataFrame):
        file_name = name or f'{{OUTPUT_PREFIX}}_data.{{format}}'
        file_path = os.path.join(OUTPUT_DIR, file_name)
        if format == 'csv':
            data.to_csv(file_path, index=False, encoding='utf-8-sig')
        elif format == 'excel':
            data.to_excel(file_path, index=False)
        elif format == 'json':
            data.to_json(file_path, orient='records', force_ascii=False, indent=2)
        print(f'[GENERATED_FILE]{{file_path}}')
        return file_path
    elif isinstance(data, (dict, list)):
        file_name = name or f'{{OUTPUT_PREFIX}}_data.json'
        file_path = os.path.join(OUTPUT_DIR, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f'[GENERATED_FILE]{{file_path}}')
        return file_path
    return None

# ========== 用户代码开始 ==========
{code}
# ========== 用户代码结束 ==========
'''
                f.write(wrapped_code)
                script_path = f.name

            # 执行脚本
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(OUTPUTS_DIR)
            )

            # 清理临时文件
            Path(script_path).unlink(missing_ok=True)

            # 解析生成的文件
            generated_files = []
            for line in result.stdout.split('\n'):
                if line.startswith('[GENERATED_FILE]'):
                    file_path = line.replace('[GENERATED_FILE]', '').strip()
                    if Path(file_path).exists():
                        generated_files.append({
                            'path': file_path,
                            'name': Path(file_path).name,
                            'url': f"/outputs/{Path(file_path).name}",
                            'size': Path(file_path).stat().st_size
                        })

            # 清理输出中的 [GENERATED_FILE] 标记
            clean_stdout = '\n'.join([
                line for line in result.stdout.split('\n')
                if not line.startswith('[GENERATED_FILE]')
            ]).strip()

            return {
                'success': result.returncode == 0,
                'stdout': clean_stdout,
                'stderr': result.stderr,
                'generated_files': generated_files,
                'error': result.stderr if result.returncode != 0 else None
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'执行超时（{timeout}秒）',
                'generated_files': [],
                'error': f'代码执行超时，超过 {timeout} 秒限制'
            }
        except Exception as e:
            import traceback
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'generated_files': [],
                'error': f'执行错误: {str(e)}'
            }

    def execute_skill(
        self,
        skill_id: str,
        script_name: Optional[str] = None,
        params: Dict[str, Any] = None
    ) -> tuple[bool, Any, Optional[str], Optional[str]]:
        """
        Execute a skill's script from file system

        Args:
            skill_id: Skill UUID
            script_name: Script filename (default: entry_script from DB)
            params: Parameters to pass to the script

        Returns:
            (success, result, error, output)
        """
        import traceback

        # ========== 调试日志 ==========
        print(f"\n========== [AgentService.execute_skill] ==========")
        print(f"[AgentService] skill_id: {skill_id}")
        print(f"[AgentService] script_name: {script_name}")
        print(f"[AgentService] params type: {type(params)}")
        print(f"[AgentService] params keys: {list(params.keys()) if params else 'None'}")
        print(f"[AgentService] file_path: {params.get('file_path', 'NOT SET') if params else 'NO PARAMS'}")
        print(f"[AgentService] file_paths: {params.get('file_paths', 'NOT SET') if params else 'NO PARAMS'}")
        print(f"[AgentService] Full params: {params}")
        print(f"==================================================\n")

        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            log_error(f"技能不存在: {skill_id}")
            return False, None, "Skill not found", None

        # 确定要执行的脚本
        if not skill.folder_path:
            log_ai_start()
            return self._execute_skill_with_ai_fallback(skill, params)

        skill_folder = SKILLS_STORAGE_DIR / skill.folder_path

        if not skill_folder.exists():
            log_error(f"文件夹不存在: {skill.folder_path}")
            return False, None, f"Skill folder not found: {skill.folder_path}", None

        # 确定脚本文件
        script_file = script_name or skill.entry_script or "main.py"
        script_path = skill_folder / script_file

        if not script_path.exists():
            py_files = [f for f in skill_folder.glob("*.py") if f.name != "__init__.py"]
            if py_files:
                script_path = py_files[0]
            else:
                skill_md_path = skill_folder / "SKILL.md"
                if skill_md_path.exists():
                    log_ai_start()
                    return self._execute_skill_with_ai(skill, skill_folder, params)
                else:
                    log_error(f"未找到脚本: {script_file}")
                    return False, None, f"Script not found: {script_file}", None

        # 读取脚本代码
        try:
            code = script_path.read_text(encoding="utf-8")
        except Exception as e:
            log_error(f"读取脚本失败: {e}")
            traceback.print_exc()
            return False, None, f"Failed to read script: {e}", None

        # 检测代码类型
        has_main_func = "def main(params)" in code or "def main(params:" in code
        if not has_main_func:
            code = self._wrap_code_with_main(code, skill.name)
            has_main_func = True

        # Capture stdout
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        # 转换 params 中的 URL 路径为文件系统路径
        resolved_params = dict(params) if params else {}

        def resolve_path(p):
            """转换单个 URL 路径"""
            if isinstance(p, str):
                if p.startswith("/uploads/"):
                    return str(UPLOADS_DIR / p[len("/uploads/"):])
                elif p.startswith("/outputs/"):
                    return str(OUTPUTS_DIR / p[len("/outputs/"):])
            return p

        for key in ['file_path', 'file_paths', 'files']:
            if key in resolved_params:
                val = resolved_params[key]
                if isinstance(val, str):
                    resolved_params[key] = resolve_path(val)
                elif isinstance(val, list):
                    resolved_params[key] = [resolve_path(p) for p in val]

        # 兼容性：如果有 file_paths 但没有 files，复制一份
        if 'file_paths' in resolved_params and 'files' not in resolved_params:
            resolved_params['files'] = resolved_params['file_paths']
        # 兼容性：如果有 file_path 但没有 file_paths/files，创建列表
        if 'file_path' in resolved_params and resolved_params['file_path']:
            if 'file_paths' not in resolved_params:
                resolved_params['file_paths'] = [resolved_params['file_path']]
            if 'files' not in resolved_params:
                resolved_params['files'] = [resolved_params['file_path']]

        try:
            # Create execution context with params and utilities
            exec_globals = {
                "params": resolved_params,
                # Skill folder path
                "SKILL_DIR": skill_folder,
                # Simulate __file__ for scripts that use it
                "__file__": str(script_path),
                # Data processing libraries
                "pd": pd,
                "pandas": pd,
                # File utilities
                "OUTPUTS_DIR": OUTPUTS_DIR,
                "generate_unique_filename": generate_unique_filename,
                "Path": Path,
                # Built-ins
                "__builtins__": __builtins__,
            }

            # 将技能文件夹添加到 Python 路径
            import sys as _sys
            _sys.path.insert(0, str(skill_folder))

            try:
                # 先加载代码定义
                exec(code, exec_globals)

                # 调用 main(params) 函数
                if "main" in exec_globals and callable(exec_globals["main"]):
                    print(f"\n[AgentService] Calling main() with resolved_params:")
                    print(f"[AgentService] file_path: {resolved_params.get('file_path', 'NOT SET')}")
                    print(f"[AgentService] file_paths: {resolved_params.get('file_paths', 'NOT SET')}")
                    print(f"[AgentService] files: {resolved_params.get('files', 'NOT SET')}")
                    result = exec_globals["main"](resolved_params)
                    exec_globals["result"] = result

            finally:
                # 恢复 Python 路径
                if str(skill_folder) in _sys.path:
                    _sys.path.remove(str(skill_folder))

            output = sys.stdout.getvalue()
            stderr_output = sys.stderr.getvalue()
            result = exec_globals.get("result", None)

            # 后处理：如果结果是文件路径字符串，转换为标准格式
            if isinstance(result, str) and result:
                result_path = Path(result)
                if result_path.exists() and result_path.is_file():
                    try:
                        file_content = result_path.read_text(encoding='utf-8')
                        suffix = result_path.suffix.lower()
                        file_type = {
                            '.json': 'json',
                            '.html': 'html',
                            '.htm': 'html',
                            '.csv': 'csv',
                            '.txt': 'txt',
                            '.md': 'markdown'
                        }.get(suffix, 'txt')
                        result = {
                            '_output_file': {
                                'path': str(result_path),
                                'type': file_type,
                                'name': result_path.name
                            },
                            'content': file_content,
                            'message': f"文件已生成: {result_path.name}"
                        }
                        output = file_content
                    except Exception:
                        pass

            # 恢复标准输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            return True, result, None, output
        except Exception as e:
            output = sys.stdout.getvalue()
            stderr_output = sys.stderr.getvalue()

            # 恢复标准输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # 记录详细错误
            traceback.print_exc()

            error_msg = f"{type(e).__name__}: {str(e)}"

            # 即使失败也返回有用的信息
            error_result = {
                "message": f"技能执行出错: {error_msg}",
                "error": error_msg,
                "stdout": output,
                "stderr": stderr_output,
                "_error_details": True
            }

            # 仍然返回 True，让前端能显示错误详情而不是模糊提示
            return True, error_result, None, f"执行出错: {error_msg}\n{stderr_output}"
        finally:
            # 确保恢复标准输出
            if sys.stdout != old_stdout:
                sys.stdout = old_stdout
            if sys.stderr != old_stderr:
                sys.stderr = old_stderr

    def _execute_skill_with_ai(
        self,
        skill: Skill,
        skill_folder: Path,
        params: Dict[str, Any] = None
    ) -> tuple[bool, Any, Optional[str], Optional[str]]:
        """
        使用 AI 执行技能（基于 SKILL.md 的提示词型技能）

        这类技能没有可执行的 Python 脚本，而是通过 SKILL.md 提供指南，
        让 AI 根据指南和用户需求来完成任务。
        """
        try:
            # ========== 调试日志 ==========
            print(f"\n========== [_execute_skill_with_ai] ==========")
            print(f"[AI Execute] skill.name: {skill.name}")
            print(f"[AI Execute] skill_folder: {skill_folder}")
            print(f"[AI Execute] params: {params}")
            print(f"[AI Execute] file_path in params: {params.get('file_path', 'NOT SET') if params else 'NO PARAMS'}")
            print(f"[AI Execute] file_paths in params: {params.get('file_paths', 'NOT SET') if params else 'NO PARAMS'}")
            print(f"===============================================\n")

            # 读取 SKILL.md
            skill_md_path = skill_folder / "SKILL.md"
            skill_md_content = skill_md_path.read_text(encoding="utf-8")

            # 读取 reference 目录下的文档（如果有）
            reference_content = ""
            reference_dir = skill_folder / "reference"
            if reference_dir.exists():
                for ref_file in reference_dir.glob("*.md"):
                    try:
                        ref_text = ref_file.read_text(encoding="utf-8")
                        # 限制每个参考文件的大小
                        if len(ref_text) > 5000:
                            ref_text = ref_text[:5000] + "\n...[truncated]..."
                        reference_content += f"\n\n## Reference: {ref_file.name}\n{ref_text}"
                    except Exception:
                        pass

            # 获取用户上下文
            context = params.get("context", "") if params else ""
            skill_description = params.get("skillDescription", "") if params else ""
            user_input = context or skill_description or skill.description or ""

            # 获取上传的文件
            file_paths = params.get("file_paths", []) if params else []
            file_path = params.get("file_path", "") if params else ""
            if file_path and file_path not in file_paths:
                file_paths.append(file_path)

            # 读取上传文件的内容
            file_content = ""
            if file_paths:
                file_content = self._read_files_for_ai(file_paths)

            # 简化 system prompt - 像 Claude Code 一样，直接用 SKILL.md，不加格式干扰
            system_prompt = f"""{skill_md_content[:12000]}

{reference_content[:4000] if reference_content else ""}
"""

            # 构建用户消息，包含文件内容（支持多模态）
            user_message = user_input or "请根据技能说明执行默认任务"
            message_content = self._build_multimodal_content(user_message, file_content)

            # 调用 Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system_prompt,
                messages=[{"role": "user", "content": message_content}]
            )

            ai_output = response.content[0].text
            log_ai_done()

            # 解析 AI 声明的输出格式
            output_format, clean_content = self._parse_output_format(ai_output)
            print(f"[AI Execute] Detected output format: {output_format}")

            # 根据技能类型生成适当的输出文件
            result = {
                "message": f"AI 技能「{skill.name}」执行完成",
                "skill_type": "ai_prompt",
                "content": clean_content
            }

            # 根据格式生成文件（只看 output_format，不再检测内容）
            if output_format == "pptx_code":
                # 执行 pptxgenjs 代码生成 PPT
                pptx_result = self._execute_pptx_code(clean_content, skill.name)
                if pptx_result:
                    result["_output_file"] = pptx_result
                    result["content"] = f"PPT 已生成: {pptx_result['name']}"
                    result["message"] = f"AI 技能「{skill.name}」PPT 生成完成"
                else:
                    # 执行失败，保存为 js 文件供调试
                    filename = generate_unique_filename(skill.name, "js")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(clean_content, encoding="utf-8")
                    result["_output_file"] = {
                        "path": str(filepath),
                        "type": "js",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                    result["content"] = f"PPT 代码执行失败，代码已保存为: {filename}\n\n请确保已安装 pptxgenjs: npm install -g pptxgenjs"
                    result["message"] = "PPT 代码生成完成（执行失败，已保存为 .js 文件）"
            elif output_format == "html":
                result["_html"] = clean_content
            elif output_format == "png_code":
                # 执行 matplotlib 代码生成图片
                image_result = self._execute_image_code(clean_content, skill.name)
                if image_result:
                    result["_output_file"] = image_result
                    result["content"] = f"图表已生成: {image_result['name']}"
                else:
                    # 执行失败，保存为 py 文件供调试
                    filename = generate_unique_filename(skill.name, "py")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(clean_content, encoding="utf-8")
                    result["_output_file"] = {
                        "path": str(filepath),
                        "type": "py",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                    result["message"] = "图表代码生成完成（执行失败，已保存为 .py 文件）"
            elif output_format == "img_code":
                # 执行 PIL 图片处理代码
                image_result = self._execute_img_process_code(clean_content, skill.name, file_paths)
                if image_result:
                    result["_output_file"] = image_result
                    result["content"] = f"图片处理完成: {image_result['name']}"
                else:
                    # 执行失败，保存为 py 文件供调试
                    filename = generate_unique_filename(skill.name, "py")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(clean_content, encoding="utf-8")
                    result["_output_file"] = {
                        "path": str(filepath),
                        "type": "py",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                    result["message"] = "图片处理代码生成完成（执行失败，已保存为 .py 文件）"
            elif output_format == "analysis_code":
                # 执行数据分析代码
                analysis_result = self._execute_analysis_code(clean_content, file_paths)
                if analysis_result['success']:
                    result["content"] = analysis_result['stdout']
                    result["message"] = f"AI 技能「{skill.name}」分析完成"
                    result["_analysis_result"] = {
                        'stdout': analysis_result['stdout'],
                        'generated_files': analysis_result['generated_files']
                    }
                    # 如果生成了文件，返回第一个作为主输出
                    if analysis_result['generated_files']:
                        result["_output_file"] = analysis_result['generated_files'][0]
                        if len(analysis_result['generated_files']) > 1:
                            result["_additional_files"] = analysis_result['generated_files'][1:]
                else:
                    # 执行失败，保存代码供调试
                    filename = generate_unique_filename(skill.name, "py")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(clean_content, encoding="utf-8")
                    result["_output_file"] = {
                        "path": str(filepath),
                        "type": "py",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                    result["content"] = f"代码执行失败:\n{analysis_result['stderr']}\n\n代码已保存为: {filename}"
                    result["message"] = "数据分析代码执行失败（已保存代码供调试）"
            elif output_format and output_format != "txt":
                # 生成对应格式的文件
                filename = generate_unique_filename(skill.name, output_format)
                filepath = OUTPUTS_DIR / filename
                filepath.write_text(clean_content, encoding="utf-8")
                file_size = filepath.stat().st_size
                result["_output_file"] = {
                    "path": str(filepath),
                    "type": output_format,
                    "name": filename,
                    "url": f"/outputs/{filename}",
                    "size": file_size
                }

            return True, result, None, clean_content

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error(f"AI执行失败: {str(e)[:30]}")
            return False, None, f"AI skill execution failed: {str(e)}", None

    def _execute_skill_with_ai_fallback(
        self,
        skill: Skill,
        params: Dict[str, Any] = None
    ) -> tuple[bool, Any, Optional[str], Optional[str]]:
        """
        AI 回退执行 - 当技能没有代码文件夹时，使用 AI 根据技能名称和描述来执行

        这适用于 AI 自动规划的技能（只有名称和描述，没有实际代码）
        """
        try:
            # ========== 调试日志 ==========
            print(f"\n========== [_execute_skill_with_ai_fallback] ==========")
            print(f"[AI Fallback] skill.name: {skill.name}")
            print(f"[AI Fallback] params: {params}")
            print(f"[AI Fallback] file_path in params: {params.get('file_path', 'NOT SET') if params else 'NO PARAMS'}")
            print(f"[AI Fallback] file_paths in params: {params.get('file_paths', 'NOT SET') if params else 'NO PARAMS'}")
            print(f"=======================================================\n")

            # 获取用户上下文
            context = params.get("context", "") if params else ""
            skill_description = params.get("skillDescription", "") if params else ""
            user_input = context or skill_description or ""

            # 获取上传的文件
            file_paths = params.get("file_paths", []) if params else []
            file_path = params.get("file_path", "") if params else ""
            if file_path and file_path not in file_paths:
                file_paths.append(file_path)

            print(f"[AI Fallback] Final file_paths after merge: {file_paths}")

            log_ai_start()

            # 读取上传文件的内容
            file_content = ""
            if file_paths:
                file_content = self._read_files_for_ai(file_paths)

            # 简化 system prompt - 不加格式干扰
            system_prompt = f"""你是一个专业的 AI 助手，正在执行名为「{skill.name}」的任务。

{skill.description or '根据技能名称推断任务内容'}

请根据任务要求生成输出。
"""

            # 构建用户消息，包含文件内容（支持多模态）
            user_message = user_input or f"请执行「{skill.name}」任务"
            message_content = self._build_multimodal_content(user_message, file_content)

            # 调用 Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system_prompt,
                messages=[{"role": "user", "content": message_content}]
            )

            ai_output = response.content[0].text
            log_ai_done()

            # 解析 AI 声明的输出格式
            output_format, clean_content = self._parse_output_format(ai_output)
            print(f"[AI Fallback] Detected output format: {output_format}")

            # 构建结果
            result = {
                "message": f"AI 执行「{skill.name}」完成",
                "skill_type": "ai_fallback",
                "content": clean_content
            }

            # 根据格式生成文件（只看 output_format，不再检测内容）
            if output_format == "pptx_code":
                # 执行 pptxgenjs 代码生成 PPT
                pptx_result = self._execute_pptx_code(clean_content, skill.name)
                if pptx_result:
                    result["_output_file"] = pptx_result
                    result["content"] = f"PPT 已生成: {pptx_result['name']}"
                    result["message"] = f"AI 执行「{skill.name}」PPT 生成完成"
                else:
                    # 执行失败，保存为 js 文件供调试
                    filename = generate_unique_filename(skill.name, "js")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(clean_content, encoding="utf-8")
                    result["_output_file"] = {
                        "path": str(filepath),
                        "type": "js",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                    result["content"] = f"PPT 代码执行失败，代码已保存为: {filename}\n\n请确保已安装 pptxgenjs: npm install -g pptxgenjs"
                    result["message"] = "PPT 代码生成完成（执行失败，已保存为 .js 文件）"
            elif output_format == "html":
                result["_html"] = clean_content
            elif output_format == "png_code":
                # 执行 matplotlib 代码生成图片
                image_result = self._execute_image_code(clean_content, skill.name)
                if image_result:
                    result["_output_file"] = image_result
                    result["content"] = f"图表已生成: {image_result['name']}"
                else:
                    # 执行失败，保存为 py 文件
                    filename = generate_unique_filename(skill.name, "py")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(clean_content, encoding="utf-8")
                    result["_output_file"] = {
                        "path": str(filepath),
                        "type": "py",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                    result["message"] = "图表代码生成完成（执行失败，已保存为 .py 文件）"
            elif output_format == "img_code":
                # 执行 PIL 图片处理代码
                image_result = self._execute_img_process_code(clean_content, skill.name, file_paths)
                if image_result:
                    result["_output_file"] = image_result
                    result["content"] = f"图片处理完成: {image_result['name']}"
                else:
                    # 执行失败，保存为 py 文件供调试
                    filename = generate_unique_filename(skill.name, "py")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(clean_content, encoding="utf-8")
                    result["_output_file"] = {
                        "path": str(filepath),
                        "type": "py",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                    result["message"] = "图片处理代码生成完成（执行失败，已保存为 .py 文件）"
            elif output_format == "analysis_code":
                # 执行数据分析代码
                analysis_result = self._execute_analysis_code(clean_content, file_paths)
                if analysis_result['success']:
                    result["content"] = analysis_result['stdout']
                    result["message"] = f"AI 执行「{skill.name}」分析完成"
                    result["_analysis_result"] = {
                        'stdout': analysis_result['stdout'],
                        'generated_files': analysis_result['generated_files']
                    }
                    # 如果生成了文件，返回第一个作为主输出
                    if analysis_result['generated_files']:
                        result["_output_file"] = analysis_result['generated_files'][0]
                        if len(analysis_result['generated_files']) > 1:
                            result["_additional_files"] = analysis_result['generated_files'][1:]
                else:
                    # 执行失败，保存代码供调试
                    filename = generate_unique_filename(skill.name, "py")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(clean_content, encoding="utf-8")
                    result["_output_file"] = {
                        "path": str(filepath),
                        "type": "py",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                    result["content"] = f"代码执行失败:\n{analysis_result['stderr']}\n\n代码已保存为: {filename}"
                    result["message"] = "数据分析代码执行失败（已保存代码供调试）"
            elif output_format and output_format != "txt":
                # 生成对应格式的文件
                filename = generate_unique_filename(skill.name, output_format)
                filepath = OUTPUTS_DIR / filename
                filepath.write_text(clean_content, encoding="utf-8")
                file_size = filepath.stat().st_size
                result["_output_file"] = {
                    "path": str(filepath),
                    "type": output_format,
                    "name": filename,
                    "url": f"/outputs/{filename}",
                    "size": file_size
                }

            return True, result, None, clean_content

        except Exception as e:
            import traceback
            traceback.print_exc()
            log_error(f"AI执行失败: {str(e)[:30]}")
            return False, None, f"AI fallback execution failed: {str(e)}", None

    def _wrap_code_with_main(self, code: str, skill_name: str) -> str:
        """
        为没有 main(params) 的代码自动添加包装
        """
        import re

        # 查找所有定义的函数
        func_pattern = r'def\s+(\w+)\s*\([^)]*\)'
        all_funcs = re.findall(func_pattern, code)

        # 排除辅助函数
        exclude_funcs = {'convert_value', 'helper', 'utils', '__init__', 'setup', 'init'}

        candidates = []
        for func_name in all_funcs:
            if func_name.startswith('_') or func_name in exclude_funcs:
                continue

            score = 0
            func_lower = func_name.lower()

            # 优先级评分
            if 'excel' in func_lower and 'json' in func_lower:
                score = 100
            elif '_to_' in func_lower:
                score = 90
            elif any(kw in func_lower for kw in ['convert', 'transform', 'process', 'parse', 'export']):
                score = 80
            elif any(kw in func_lower for kw in ['excel', 'csv', 'json', 'pdf', 'xml']):
                score = 70
            elif func_lower in ('main', 'run', 'execute'):
                score = 50
            elif any(kw in func_lower for kw in ['read', 'write', 'load', 'save', 'get', 'create']):
                score = 40
            else:
                score = 10

            candidates.append((score, func_name))

        if not candidates:
            return code

        candidates.sort(reverse=True)
        main_func_name = candidates[0][1]

        # 生成包装代码 - 使用 _output_file 以匹配系统的检测逻辑
        wrapper = f'''

# ========== 自动生成的 API 包装 ==========
# 路径常量
_UPLOADS_DIR = r'{UPLOADS_DIR}'
_OUTPUTS_DIR = r'{OUTPUTS_DIR}'

def _resolve_path(url_path):
    """转换 URL 路径为文件系统路径"""
    import os
    if url_path.startswith("/uploads/"):
        return os.path.join(_UPLOADS_DIR, url_path[len("/uploads/"):])
    elif url_path.startswith("/outputs/"):
        return os.path.join(_OUTPUTS_DIR, url_path[len("/outputs/"):])
    return url_path

def main(params):
    import json
    # 兼容两种字段名：file_paths (前端传递) 和 files (旧格式)
    file_paths = params.get('file_paths', []) or params.get('files', [])
    file_path = params.get('file_path', '')

    print(f"[AutoWrapper] params: {{params}}")
    print(f"[AutoWrapper] file_paths: {{file_paths}}, file_path: {{file_path}}")

    if file_paths:
        input_file = _resolve_path(file_paths[0])
    elif file_path:
        input_file = _resolve_path(file_path)
    else:
        return {{'status': 'error', 'message': '请上传文件'}}

    print(f"[AutoWrapper] Calling {main_func_name} with: {{input_file}}")

    try:
        result = {main_func_name}(input_file)
        print(f"[AutoWrapper] Result type: {{type(result)}}, value: {{str(result)[:200]}}")

        if isinstance(result, str):
            try:
                json.loads(result)
                output_path = OUTPUTS_DIR / generate_unique_filename('output', 'json')
                output_path.write_text(result, encoding='utf-8')
                return {{
                    'status': 'success',
                    'message': '转换完成',
                    'content': result,
                    '_output_file': {{'path': str(output_path), 'type': 'json', 'name': output_path.name, 'url': f'/outputs/{{output_path.name}}'}}
                }}
            except json.JSONDecodeError:
                return {{'status': 'success', 'message': result, 'content': result}}
        elif isinstance(result, (dict, list)):
            json_str = json.dumps(result, ensure_ascii=False, indent=2)
            output_path = OUTPUTS_DIR / generate_unique_filename('output', 'json')
            output_path.write_text(json_str, encoding='utf-8')
            return {{
                'status': 'success',
                'message': '处理完成',
                'content': result,
                '_output_file': {{'path': str(output_path), 'type': 'json', 'name': output_path.name, 'url': f'/outputs/{{output_path.name}}'}}
            }}
        else:
            return {{'status': 'success', 'message': str(result), 'content': str(result)}}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {{'status': 'error', 'message': str(e)}}
'''
        return code + wrapper

    def _read_files_for_ai(self, file_paths: list, max_total_chars: int = 250000) -> str:
        """
        读取上传的文件内容，转换为 AI 可以处理的文本格式（增强版）

        Args:
            file_paths: 文件路径列表
            max_total_chars: 总字符数限制（默认250000，约80k tokens）

        增强功能:
        - Excel 多 Sheet 支持
        - 字段类型信息
        - 数值字段统计摘要
        - 大文件智能采样（头部 + 尾部 + 随机样本）
        """
        import numpy as np

        contents = []
        total_chars = 0

        # 根据文件数量动态调整每个文件的限制
        num_files = len(file_paths)
        per_file_limit = max(10000, max_total_chars // max(num_files, 1))

        for file_path in file_paths:
            # 检查是否已超过总限制
            if total_chars >= max_total_chars:
                contents.append(f"\n[已达到总字符限制，跳过剩余 {len(file_paths) - len(contents)} 个文件]")
                break
            try:
                print(f"[_read_files_for_ai] 处理文件路径: {file_path}")

                # URL 路径转换为文件系统路径
                path = None
                if file_path.startswith("/uploads/"):
                    filename = file_path[len("/uploads/"):]
                    path = UPLOADS_DIR / filename
                    print(f"[_read_files_for_ai] 解析为 /uploads/ 格式: {path}")
                elif file_path.startswith("uploads/"):
                    filename = file_path[len("uploads/"):]
                    path = UPLOADS_DIR / filename
                    print(f"[_read_files_for_ai] 解析为 uploads/ 格式: {path}")
                elif file_path.startswith("/outputs/"):
                    filename = file_path[len("/outputs/"):]
                    path = OUTPUTS_DIR / filename
                    print(f"[_read_files_for_ai] 解析为 /outputs/ 格式: {path}")
                elif file_path.startswith("outputs/"):
                    filename = file_path[len("outputs/"):]
                    path = OUTPUTS_DIR / filename
                    print(f"[_read_files_for_ai] 解析为 outputs/ 格式: {path}")
                else:
                    path = Path(file_path)
                    print(f"[_read_files_for_ai] 使用原始路径: {path}")
                    # 如果不存在，尝试 UPLOADS_DIR 和 OUTPUTS_DIR
                    if not path.exists():
                        test_path = UPLOADS_DIR / file_path
                        print(f"[_read_files_for_ai] 尝试 UPLOADS_DIR: {test_path}")
                        if test_path.exists():
                            path = test_path
                        else:
                            test_path = OUTPUTS_DIR / file_path
                            print(f"[_read_files_for_ai] 尝试 OUTPUTS_DIR: {test_path}")
                            if test_path.exists():
                                path = test_path

                if not path or not path.exists():
                    print(f"[_read_files_for_ai] 跳过不存在的文件: {file_path}, 解析路径: {path}")
                    continue

                print(f"[_read_files_for_ai] 找到文件: {path}")

                suffix = path.suffix.lower()

                # 计算当前文件可用的字符数
                remaining_chars = max_total_chars - total_chars
                file_limit = min(per_file_limit, remaining_chars)

                file_content = ""

                # Excel 文件 - 增强版：多 Sheet 支持 + 统计信息
                if suffix in ['.xlsx', '.xls']:
                    try:
                        file_content = self._read_excel_enhanced(file_path, path.name, file_limit)
                    except Exception as e:
                        file_content = f"### {path.name}\n[Excel 读取失败: {str(e)}]"

                # CSV 文件 - 增强版：统计信息 + 智能采样
                elif suffix == '.csv':
                    try:
                        file_content = self._read_csv_enhanced(file_path, path.name, file_limit)
                    except Exception as e:
                        file_content = f"### {path.name}\n[CSV 读取失败: {str(e)}]"

                # JSON 文件
                elif suffix == '.json':
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        # 如果是数组，尝试用 DataFrame 处理
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            df = pd.DataFrame(data)
                            file_content = self._format_dataframe_enhanced(df, path.name, "json_array", file_limit)
                        else:
                            json_str = json.dumps(data, ensure_ascii=False, indent=2)
                            if len(json_str) > file_limit:
                                json_str = json_str[:file_limit] + "\n...[truncated]..."
                            file_content = f"### {path.name}\n```json\n{json_str}\n```"
                    except Exception as e:
                        file_content = f"### {path.name}\n[JSON 读取失败: {str(e)}]"

                # 文本文件
                elif suffix in ['.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.vue', '.jsx', '.tsx', '.xml', '.yaml', '.yml', '.log']:
                    try:
                        text = path.read_text(encoding='utf-8')
                        if len(text) > file_limit:
                            text = text[:file_limit] + "\n...[truncated]..."
                        lang = suffix.lstrip('.') if suffix not in ['.txt', '.log'] else ''
                        file_content = f"### {path.name}\n```{lang}\n{text}\n```"
                    except Exception:
                        pass

                # 图片文件 - 转为 base64 供 AI 分析
                elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                    try:
                        import base64
                        img_data = path.read_bytes()
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        # 限制图片大小（base64 会增大约 33%）
                        if len(img_base64) > 500000:  # ~375KB 原图
                            file_content = f"### {path.name}\n[图片文件过大，已跳过。文件大小: {len(img_data)} bytes]"
                        else:
                            mime_type = {
                                '.png': 'image/png',
                                '.jpg': 'image/jpeg',
                                '.jpeg': 'image/jpeg',
                                '.gif': 'image/gif',
                                '.bmp': 'image/bmp',
                                '.webp': 'image/webp'
                            }.get(suffix, 'image/png')
                            # 存储图片信息供后续 API 调用使用
                            file_content = f"### {path.name}\n[IMAGE:{mime_type}:{img_base64}]"
                    except Exception as e:
                        file_content = f"### {path.name}\n[图片读取失败: {str(e)}]"

                # SVG 文件 - 作为文本处理
                elif suffix == '.svg':
                    try:
                        text = path.read_text(encoding='utf-8')
                        if len(text) > file_limit:
                            text = text[:file_limit] + "\n...[truncated]..."
                        file_content = f"### {path.name}\n```svg\n{text}\n```"
                    except Exception:
                        pass

                # PDF 文件 - 尝试提取文本
                elif suffix == '.pdf':
                    try:
                        import fitz  # PyMuPDF
                        doc = fitz.open(file_path)
                        text_parts = []
                        for page_num in range(min(10, len(doc))):  # 最多读取前10页
                            page = doc[page_num]
                            text_parts.append(f"--- Page {page_num + 1} ---\n{page.get_text()}")
                        doc.close()
                        text = "\n".join(text_parts)
                        if len(text) > file_limit:
                            text = text[:file_limit] + "\n...[truncated]..."
                        file_content = f"### {path.name}\n```\n{text}\n```"
                    except ImportError:
                        file_content = f"### {path.name}\n[PDF 文件，需要安装 PyMuPDF 库才能读取]"
                    except Exception as e:
                        file_content = f"### {path.name}\n[PDF 读取失败: {str(e)}]"

                else:
                    file_content = f"### {path.name}\n[二进制文件，类型: {suffix}]"

                # 添加内容并更新计数
                if file_content:
                    contents.append(file_content)
                    total_chars += len(file_content)

            except Exception:
                pass

        # 添加截断提示
        result = "\n\n".join(contents)
        if total_chars >= max_total_chars * 0.9:  # 接近限制时提示
            result += f"\n\n[注意：文件内容已截断以避免超过处理限制。总计 {total_chars} 字符，{len(file_paths)} 个文件]"

        return result

    def _read_excel_enhanced(self, file_path: str, file_name: str, char_limit: int) -> str:
        """
        增强版 Excel 读取：多 Sheet 支持 + 字段类型 + 统计信息
        """
        import numpy as np

        result_parts = []
        total_chars = 0

        # 读取所有 Sheet
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names

        for sheet_name in sheet_names:
            if total_chars >= char_limit:
                result_parts.append(f"\n[已达到字符限制，跳过剩余 Sheet]")
                break

            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                remaining = char_limit - total_chars
                sheet_content = self._format_dataframe_enhanced(
                    df, f"{file_name} - Sheet: {sheet_name}", "excel", remaining
                )
                result_parts.append(sheet_content)
                total_chars += len(sheet_content)
            except Exception as e:
                result_parts.append(f"### {file_name} - Sheet: {sheet_name}\n[读取失败: {str(e)}]")

        return "\n\n".join(result_parts)

    def _read_csv_enhanced(self, file_path: str, file_name: str, char_limit: int) -> str:
        """
        增强版 CSV 读取：字段类型 + 统计信息 + 智能采样
        """
        df = pd.read_csv(file_path)
        return self._format_dataframe_enhanced(df, file_name, "csv", char_limit)

    def _format_dataframe_enhanced(self, df: pd.DataFrame, file_name: str, format_type: str, char_limit: int) -> str:
        """
        格式化 DataFrame 为增强版文本输出

        包含：
        - 基本信息（行数 x 列数）
        - 字段类型信息
        - 数值字段统计摘要
        - 数据预览（智能采样）
        """
        import numpy as np

        parts = []
        total_rows, total_cols = df.shape

        # 1. 标题和基本信息
        parts.append(f"### {file_name} ({total_rows}行 x {total_cols}列)")

        # 2. 字段类型信息
        dtype_info = ", ".join([f"{col}:{df[col].dtype}" for col in df.columns[:15]])
        if len(df.columns) > 15:
            dtype_info += f"... (+{len(df.columns) - 15} 列)"
        parts.append(f"\n**字段类型:** {dtype_info}")

        # 3. 统计摘要表格
        summary_lines = ["| 字段 | 类型 | 非空 | 唯一值 | 示例/统计 |", "|------|------|------|--------|-----------|"]

        for col in df.columns[:20]:  # 最多显示20个字段
            dtype = str(df[col].dtype)
            non_null = df[col].notna().sum()
            unique_count = df[col].nunique()

            # 根据类型生成不同的示例/统计信息
            if pd.api.types.is_numeric_dtype(df[col]):
                # 数值类型：显示 min/max/mean
                try:
                    col_min = df[col].min()
                    col_max = df[col].max()
                    col_mean = df[col].mean()
                    if pd.api.types.is_integer_dtype(df[col]):
                        example = f"min={col_min}, max={col_max}, mean={col_mean:.1f}"
                    else:
                        example = f"min={col_min:.2f}, max={col_max:.2f}, mean={col_mean:.2f}"
                except Exception:
                    example = str(df[col].dropna().head(3).tolist())[:30]
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                # 日期类型：显示范围
                try:
                    date_min = df[col].min()
                    date_max = df[col].max()
                    example = f"{date_min} ~ {date_max}"
                except Exception:
                    example = str(df[col].dropna().head(2).tolist())[:30]
            else:
                # 其他类型：显示前几个示例值
                sample_vals = df[col].dropna().head(3).tolist()
                example = ", ".join([str(v)[:15] for v in sample_vals])
                if len(example) > 35:
                    example = example[:35] + "..."

            summary_lines.append(f"| {col[:20]} | {dtype} | {non_null} | {unique_count} | {example} |")

        if len(df.columns) > 20:
            summary_lines.append(f"| ... | ... | ... | ... | (+{len(df.columns) - 20} 列) |")

        parts.append("\n**统计摘要:**")
        parts.append("\n".join(summary_lines))

        # 4. 数据预览 - 智能采样
        max_preview_rows = min(500, max(100, char_limit // 300))  # 根据字符限制调整

        if total_rows <= max_preview_rows:
            # 数据量小，全部显示
            preview_df = df
            preview_note = ""
        else:
            # 智能采样：头部 + 尾部 + 随机样本
            head_rows = min(100, max_preview_rows // 3)
            tail_rows = min(50, max_preview_rows // 6)
            random_rows = max_preview_rows - head_rows - tail_rows

            head_df = df.head(head_rows)
            tail_df = df.tail(tail_rows)

            # 随机采样中间部分
            middle_indices = range(head_rows, total_rows - tail_rows)
            if len(middle_indices) > random_rows and random_rows > 0:
                sample_indices = sorted(np.random.choice(list(middle_indices), random_rows, replace=False))
                middle_df = df.iloc[sample_indices]
            else:
                middle_df = pd.DataFrame()

            # 合并预览数据
            preview_parts = [head_df]
            if not middle_df.empty:
                preview_parts.append(middle_df)
            preview_parts.append(tail_df)
            preview_df = pd.concat(preview_parts, ignore_index=False)

            preview_note = f" (智能采样: 前{head_rows}行 + 随机{len(middle_df)}行 + 后{tail_rows}行)"

        parts.append(f"\n**数据预览{preview_note}:**")
        parts.append(f"```\n{preview_df.to_string(max_rows=max_preview_rows)}\n```")

        result = "\n".join(parts)

        # 如果结果超过限制，截断
        if len(result) > char_limit:
            result = result[:char_limit] + "\n...[truncated]..."

        return result

    def execute_temp_skill(
        self,
        temp_folder: Path,
        skill_name: str,
        script_name: Optional[str] = None,
        params: Dict[str, Any] = None
    ) -> tuple[bool, Any, Optional[str], Optional[str]]:
        """
        执行临时技能（用于测试）

        Args:
            temp_folder: 临时技能文件夹路径
            skill_name: 技能名称
            script_name: 脚本文件名（可选）
            params: 执行参数

        Returns:
            (success, result, error, output)
        """
        import traceback

        if not temp_folder.exists():
            return False, None, "临时技能文件夹不存在", None

        # 查找可执行脚本
        script_file = script_name or "main.py"
        script_path = temp_folder / script_file

        if not script_path.exists():
            # 尝试查找任意 .py 文件
            py_files = [f for f in temp_folder.glob("*.py") if f.name != "__init__.py"]
            if py_files:
                script_path = py_files[0]
            else:
                # 检查 SKILL.md（AI 型技能）
                skill_md_path = temp_folder / "SKILL.md"
                if skill_md_path.exists():
                    return self._execute_temp_skill_with_ai(temp_folder, skill_name, params)
                else:
                    return False, None, "未找到可执行脚本", None

        # 读取并执行脚本
        try:
            code = script_path.read_text(encoding="utf-8")
        except Exception as e:
            return False, None, f"读取脚本失败: {e}", None

        # 执行脚本
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        try:
            exec_globals = {
                "params": params or {},
                "SKILL_DIR": temp_folder,
                "pd": pd,
                "pandas": pd,
                "OUTPUTS_DIR": OUTPUTS_DIR,
                "generate_unique_filename": generate_unique_filename,
                "Path": Path,
            }
            exec_globals["__builtins__"] = __builtins__

            # 检测代码类型
            has_main_func = "def main(params)" in code or "def main(params:" in code

            exec(code, exec_globals)

            # 如果有 main(params) 函数，调用它
            if has_main_func and "main" in exec_globals and callable(exec_globals["main"]):
                result = exec_globals["main"](params or {})
                exec_globals["result"] = result
            else:
                result = exec_globals.get("result")

            stdout_output = sys.stdout.getvalue()

            return True, result, None, stdout_output

        except Exception as e:
            stderr_output = sys.stderr.getvalue()
            stdout_output = sys.stdout.getvalue()
            output = stdout_output + ("\n" + stderr_output if stderr_output else "")
            traceback.print_exc()
            return False, None, f"{type(e).__name__}: {str(e)}", output

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _execute_temp_skill_with_ai(
        self,
        temp_folder: Path,
        skill_name: str,
        params: Dict[str, Any] = None
    ) -> tuple[bool, Any, Optional[str], Optional[str]]:
        """
        使用 AI 执行临时技能
        """
        try:
            skill_md_path = temp_folder / "SKILL.md"
            skill_md_content = skill_md_path.read_text(encoding="utf-8")

            context = params.get("context", "") if params else ""
            user_input = context or params.get("input", "") if params else ""

            # 获取上传的文件
            file_paths = params.get("file_paths", []) if params else []
            file_path = params.get("file_path", "") if params else ""
            if file_path and file_path not in file_paths:
                file_paths.append(file_path)

            # 读取上传文件的内容
            file_content = ""
            if file_paths:
                file_content = self._read_files_for_ai(file_paths)

            # 检测期望的输出格式
            combined_text = f"{skill_name} {skill_md_content[:500]} {user_input}".lower()
            output_format_hint = ""
            if "json" in combined_text:
                output_format_hint = "用户需要 JSON 格式输出，请直接输出有效的 JSON 数据。"
            elif "excel" in combined_text or "xlsx" in combined_text:
                output_format_hint = "请输出 JSON 数组格式的数据。"

            system_prompt = f"""你是一个专业的 AI 助手，正在测试名为「{skill_name}」的技能。

## 技能说明
{skill_md_content[:8000]}

## 任务要求
根据技能说明和用户需求，生成高质量的输出。
{output_format_hint}

## 输出格式
直接输出结果内容。
"""

            # 构建用户消息，包含文件内容
            user_message = user_input or "请根据技能说明执行测试任务"
            if file_content:
                user_message = f"{user_message}\n\n## 用户上传的文件数据\n{file_content}"

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            ai_output = response.content[0].text
            result = {
                "message": f"AI 测试「{skill_name}」完成",
                "skill_type": "ai_temp",
                "content": ai_output
            }

            return True, result, None, ai_output

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, None, f"AI 执行失败: {str(e)}", None

    # ========== Claude Code 风格：步骤化技能执行 ==========

    async def skill_execute_interactive(
        self,
        skill_id: str,
        context: str,
        file_paths: List[str] = None,
        confirmed_step: int = -1,  # 已确认执行到哪一步，-1 表示还没开始
        auto_confirm: bool = False,  # 自动确认所有步骤
        skip_current: bool = False  # 跳过当前步骤（不执行 confirmed_step）
    ) -> AsyncGenerator[str, None]:
        """
        Claude Code 风格的交互式技能执行

        不需要 AI 输出 ACTION 标记，而是后端根据技能类型自动规划操作步骤，
        每个步骤执行前发送确认请求给前端。

        Yields:
            {"type": "step_planned", "steps": [...]}  - 规划的所有步骤
            {"type": "step_confirm", "index": 0, "step": {...}}  - 等待确认
            {"type": "step_executing", "index": 0}  - 正在执行
            {"type": "step_result", "index": 0, "success": true, "output": "..."}  - 执行结果
            {"type": "all_done", "output_file": {...}}  - 全部完成
        """
        import re

        # 初始化步骤间共享的状态
        self._last_ai_output = ""
        self._last_output_file = None

        # 加载技能
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            yield json.dumps({"type": "error", "message": "技能不存在"})
            return

        # 读取 SKILL.md 获取 output_format
        skill_md_content = ""
        output_format = "text"  # 默认
        if skill.folder_path:
            skill_folder = SKILLS_STORAGE_DIR / skill.folder_path
            skill_md_path = skill_folder / "SKILL.md"
            if skill_md_path.exists():
                try:
                    skill_md_content = skill_md_path.read_text(encoding="utf-8")
                    # 解析 frontmatter 获取 output_format
                    fm_match = re.match(r'^---\s*\n(.*?)\n---', skill_md_content, re.DOTALL)
                    if fm_match:
                        import yaml
                        try:
                            fm = yaml.safe_load(fm_match.group(1))
                            output_format = fm.get('output_format', 'text')
                        except:
                            pass
                except Exception:
                    pass

        # ========== 简化版：一次性执行所有步骤，流式返回进度 ==========
        import asyncio

        # 步骤1: AI 生成
        yield json.dumps({
            "type": "step_start",
            "step": "generate",
            "message": f"● **Generate({skill.name})**\n  ⎿  AI 正在生成代码..."
        })
        await asyncio.sleep(0)  # 确保事件被发送

        gen_result = await self._step_generate_ai_content(skill, context, file_paths)

        if not gen_result.get("success"):
            yield json.dumps({
                "type": "step_error",
                "step": "generate",
                "message": f"● **Generate({skill.name})** ❌\n  ⎿  {gen_result.get('output', 'AI 生成失败')}"
            })
            return

        yield json.dumps({
            "type": "step_done",
            "step": "generate",
            "message": f"● **Generate({skill.name})**\n  ⎿  代码生成完成"
        })

        # 规划后续步骤
        steps = self._plan_execution_steps(skill, output_format, context, file_paths)

        # 执行每个步骤
        for i, step in enumerate(steps):
            step_name = step.get("name", f"Step {i+1}")

            # 显示步骤开始
            yield json.dumps({
                "type": "step_start",
                "index": i,
                "step": step,
                "message": f"● **{step_name}**\n  ⎿  执行中..."
            })
            await asyncio.sleep(0)  # 确保事件被发送

            # 执行步骤
            result = await self._execute_step(step, skill, context, file_paths)

            if result.get("success"):
                yield json.dumps({
                    "type": "step_done",
                    "index": i,
                    "step": step,
                    "message": f"● **{step_name}**\n  ⎿  {result.get('output', '完成')}",
                    "output_file": result.get("output_file")
                })
            else:
                yield json.dumps({
                    "type": "step_error",
                    "index": i,
                    "step": step,
                    "message": f"● **{step_name}** ❌\n  ⎿  {result.get('output', '失败')}"
                })
                return

        # 全部完成
        yield json.dumps({"type": "all_done"})

    def _plan_execution_steps(
        self,
        skill,
        output_format: str,
        context: str,
        file_paths: List[str] = None
    ) -> List[Dict]:
        """
        根据技能类型规划执行步骤 - Claude Code 风格

        注意：Generate 步骤是自动执行的，不需要用户确认。
        用户只需要确认 Write 和 Bash 操作。
        """
        import hashlib
        # 使用 context 的 hash 生成稳定的文件名（跨请求一致）
        context_hash = hashlib.md5(context.encode()).hexdigest()[:8]
        steps = []

        # 根据 output_format 添加步骤（不包含 generate，generate 会自动执行）
        if output_format == "pptx_code":
            filename = f"{skill.name}-{context_hash}.js"
            steps.append({
                "type": "write",
                "name": f"Write({filename})",
                "description": "将生成的 pptxgenjs 代码保存为文件",
                "filename": filename
            })
            steps.append({
                "type": "run",
                "name": f"Bash(node {filename})",
                "description": f"执行脚本生成 PPT",
                "command": f"node {filename}",
                "filename": filename
            })
        elif output_format == "html":
            filename = f"{skill.name}-{context_hash}.html"
            steps.append({
                "type": "write",
                "name": f"Write({filename})",
                "description": "将生成的 HTML 保存到文件",
                "filename": filename
            })
        elif output_format in ("analysis_code", "png_code", "img_code"):
            filename = f"{skill.name}-{context_hash}.py"
            steps.append({
                "type": "write",
                "name": f"Write({filename})",
                "description": "将生成的 Python 代码保存为文件",
                "filename": filename
            })
            steps.append({
                "type": "run",
                "name": f"Bash(python {filename})",
                "description": f"执行脚本生成输出",
                "command": f"python {filename}",
                "filename": filename
            })
        else:
            # 默认：只保存文件
            filename = f"{skill.name}-{context_hash}.md"
            steps.append({
                "type": "write",
                "name": f"Write({filename})",
                "description": "将生成的内容保存为文件",
                "filename": filename
            })

        return steps

    async def _execute_step(
        self,
        step: Dict,
        skill,
        context: str,
        file_paths: List[str] = None
    ) -> Dict:
        """
        执行单个步骤 - Claude Code 风格的分步执行

        Write/Bash 步骤需要用户确认后执行
        """
        step_type = step.get("type")
        filename = step.get("filename")  # 从 step 信息获取文件名

        try:
            if step_type == "write":
                # 写入文件
                return await self._step_write_file(skill, filename)

            elif step_type == "run":
                # 执行命令
                return await self._step_run_command(skill, filename)

            else:
                return {"success": False, "output": f"未知步骤类型: {step_type}"}

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "output": str(e)}

    async def _step_generate_ai_content(
        self,
        skill,
        context: str,
        file_paths: List[str] = None
    ) -> Dict:
        """步骤1: 调用 AI 生成代码（不执行）"""
        import re

        skill_folder = SKILLS_STORAGE_DIR / skill.folder_path if skill.folder_path else None
        if not skill_folder or not skill_folder.exists():
            return {"success": False, "output": "技能文件夹不存在"}

        skill_md_path = skill_folder / "SKILL.md"
        if not skill_md_path.exists():
            return {"success": False, "output": "SKILL.md 不存在"}

        try:
            skill_md_content = skill_md_path.read_text(encoding="utf-8")

            # 读取 reference 目录
            reference_content = ""
            reference_dir = skill_folder / "reference"
            if reference_dir.exists():
                for ref_file in reference_dir.glob("*.md"):
                    try:
                        ref_text = ref_file.read_text(encoding="utf-8")
                        if len(ref_text) > 5000:
                            ref_text = ref_text[:5000] + "\n...[truncated]..."
                        reference_content += f"\n\n## Reference: {ref_file.name}\n{ref_text}"
                    except:
                        pass

            # 读取上传的文件
            file_content = ""
            if file_paths:
                file_content = self._read_files_for_ai(file_paths)

            # System prompt
            system_prompt = f"""{skill_md_content[:12000]}
{reference_content[:4000] if reference_content else ""}
"""

            # 用户消息
            user_message = context or "请根据技能说明执行默认任务"
            message_content = self._build_multimodal_content(user_message, file_content)

            # 调用 Claude API（使用线程池避免阻塞事件循环）
            import asyncio
            log_ai_start()

            def call_claude():
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=16000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": message_content}]
                )

            response = await asyncio.to_thread(call_claude)
            log_ai_done()

            ai_output = response.content[0].text

            # 解析输出格式
            output_format, clean_content = self._parse_output_format(ai_output)

            # 保存到实例变量，供后续步骤使用
            self._generated_code = clean_content
            self._generated_output_format = output_format
            self._generated_file_path = None
            self._last_output_file = None

            # 返回生成的代码预览
            code_preview = clean_content[:500] + "..." if len(clean_content) > 500 else clean_content
            return {
                "success": True,
                "output": f"AI 已生成 {output_format} 代码\n\n```\n{code_preview}\n```"
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "output": f"AI 生成失败: {str(e)}"}

    async def _step_write_file(self, skill, filename: str = None) -> Dict:
        """Write 步骤: 将生成的代码写入文件"""

        if not hasattr(self, '_generated_code') or not self._generated_code:
            return {"success": False, "output": "没有生成的代码可写入"}

        output_format = getattr(self, '_generated_output_format', 'text')
        code = self._generated_code

        try:
            # 使用传入的文件名或生成默认文件名
            if not filename:
                import time
                timestamp = int(time.time())
                if output_format == "pptx_code":
                    filename = f"{skill.name}-{timestamp}.js"
                elif output_format in ("png_code", "analysis_code", "img_code"):
                    filename = f"{skill.name}-{timestamp}.py"
                elif output_format == "html":
                    filename = f"{skill.name}-{timestamp}.html"
                else:
                    filename = f"{skill.name}-{timestamp}.md"

            filepath = OUTPUTS_DIR / filename

            # 清理代码中的 markdown 代码块标记
            clean_code = code.strip()
            if clean_code.startswith('```javascript'):
                clean_code = clean_code[len('```javascript'):].strip()
            elif clean_code.startswith('```js'):
                clean_code = clean_code[len('```js'):].strip()
            elif clean_code.startswith('```python'):
                clean_code = clean_code[len('```python'):].strip()
            elif clean_code.startswith('```html'):
                clean_code = clean_code[len('```html'):].strip()
            elif clean_code.startswith('```'):
                clean_code = clean_code[3:].strip()
            if clean_code.endswith('```'):
                clean_code = clean_code[:-3].strip()

            # 写入文件
            filepath.write_text(clean_code, encoding="utf-8")
            self._generated_file_path = filepath
            self._generated_filename = filename

            # 确定文件类型
            if filename.endswith('.js'):
                self._generated_file_type = "js"
            elif filename.endswith('.py'):
                self._generated_file_type = "py"
            elif filename.endswith('.html'):
                self._generated_file_type = "html"
                # HTML 文件直接作为输出
                self._last_output_file = {
                    "path": str(filepath),
                    "type": "html",
                    "name": filename,
                    "url": f"/outputs/{filename}",
                    "size": filepath.stat().st_size
                }
            else:
                self._generated_file_type = "md"
                self._last_output_file = {
                    "path": str(filepath),
                    "type": "markdown",
                    "name": filename,
                    "url": f"/outputs/{filename}",
                    "size": filepath.stat().st_size
                }

            return {
                "success": True,
                "output": f"文件已保存"
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "output": f"写入文件失败: {str(e)}"}

    async def _step_run_command(self, skill, filename: str = None) -> Dict:
        """Bash 步骤: 执行命令生成最终输出"""
        import re
        import subprocess
        import shutil
        import time
        import tempfile

        if not hasattr(self, '_generated_file_path') or not self._generated_file_path:
            return {"success": False, "output": "没有文件可执行"}

        filepath = self._generated_file_path
        file_type = getattr(self, '_generated_file_type', '')
        output_format = getattr(self, '_generated_output_format', 'text')
        input_filename = getattr(self, '_generated_filename', filename or 'script')

        try:
            if output_format == "pptx_code" and file_type == "js":
                # 执行 Node.js 脚本生成 PPT
                node_path = shutil.which('node')
                if not node_path:
                    return {"success": False, "output": "Node.js 未安装"}

                # 检查 pptxgenjs
                node_modules_path = SERVER_DIR / "node_modules" / "pptxgenjs"
                if not node_modules_path.exists():
                    npm_path = shutil.which('npm')
                    if npm_path:
                        import asyncio
                        def run_npm_install():
                            return subprocess.run(
                                [npm_path, "install", "pptxgenjs"],
                                capture_output=True,
                                text=True,
                                timeout=120,
                                cwd=str(SERVER_DIR)
                            )
                        install_result = await asyncio.to_thread(run_npm_install)
                        if install_result.returncode != 0:
                            return {"success": False, "output": f"安装 pptxgenjs 失败: {install_result.stderr}"}

                # 修改代码中的输出路径
                timestamp = int(time.time())
                output_filename = f"{skill.name}_{timestamp}.pptx"
                output_path = OUTPUTS_DIR / output_filename
                output_path_str = str(output_path).replace('\\', '/')

                code = filepath.read_text(encoding="utf-8")

                # 替换 writeFile 路径
                code = re.sub(
                    r'writeFile\s*\(\s*\{[^}]*fileName\s*:\s*["\'][^"\']*["\']',
                    f'writeFile({{ fileName: "{output_path_str}"',
                    code
                )
                code = re.sub(
                    r'writeFile\s*\(\s*["\'][^"\']+\.pptx["\']',
                    f'writeFile("{output_path_str}"',
                    code
                )
                if 'writeFile' not in code:
                    code += f'\npres.writeFile({{ fileName: "{output_path_str}" }});'

                # 包装成可执行的脚本
                if 'require(' not in code:
                    code = f'const pptxgen = require("pptxgenjs");\n\n{code}'

                # 写入临时文件并执行
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
                    # 包装为 async
                    if 'async' not in code:
                        code = re.sub(r'(pres\.writeFile\([^)]+\))', r'await \1', code)
                        wrapped_code = f'''
const pptxgen = require("pptxgenjs");

(async () => {{
{code}
}})().catch(err => {{
    console.error("Error:", err);
    process.exit(1);
}});
'''
                    else:
                        wrapped_code = code

                    f.write(wrapped_code)
                    temp_script = f.name

                # 执行脚本（使用 asyncio.to_thread 避免阻塞事件循环）
                import asyncio
                def run_node():
                    return subprocess.run(
                        [node_path, temp_script],
                        capture_output=True,
                        text=True,
                        timeout=120,
                        cwd=str(SERVER_DIR),
                        env={**os.environ, "NODE_PATH": str(SERVER_DIR / "node_modules")}
                    )
                result = await asyncio.to_thread(run_node)

                # 清理临时文件
                try:
                    os.unlink(temp_script)
                except:
                    pass

                if result.returncode != 0:
                    return {"success": False, "output": f"执行失败: {result.stderr or result.stdout}"}

                # 检查输出文件
                if output_path.exists():
                    self._last_output_file = {
                        "path": str(output_path),
                        "type": "ppt",
                        "name": output_filename,
                        "url": f"/outputs/{output_filename}",
                        "size": output_path.stat().st_size
                    }
                    return {
                        "success": True,
                        "output": f"PPT已生成: {output_filename}",
                        "output_file": self._last_output_file
                    }
                else:
                    return {"success": False, "output": "PPT 文件未生成，请检查代码"}

            elif output_format == "png_code" and file_type == "py":
                # 执行 Python 脚本生成图片
                python_path = shutil.which('python') or shutil.which('python3')
                if not python_path:
                    return {"success": False, "output": "Python 未安装"}

                timestamp = int(time.time())
                output_filename = f"{skill.name}_{timestamp}.png"
                output_path = OUTPUTS_DIR / output_filename

                # 修改代码中的保存路径
                code = filepath.read_text(encoding="utf-8")
                code = re.sub(
                    r"savefig\s*\(['\"]([^'\"]+)['\"]\)",
                    f"savefig(r'{output_path}')",
                    code
                )
                if 'savefig' not in code:
                    code += f"\nplt.savefig(r'{output_path}')"

                # 写入临时文件并执行
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                    f.write(code)
                    temp_script = f.name

                # 使用 asyncio.to_thread 避免阻塞事件循环
                import asyncio
                def run_python():
                    return subprocess.run(
                        [python_path, temp_script],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                result = await asyncio.to_thread(run_python)

                try:
                    os.unlink(temp_script)
                except:
                    pass

                if result.returncode != 0:
                    return {"success": False, "output": f"执行失败: {result.stderr or result.stdout}"}

                if output_path.exists():
                    self._last_output_file = {
                        "path": str(output_path),
                        "type": "png",
                        "name": output_filename,
                        "url": f"/outputs/{output_filename}",
                        "size": output_path.stat().st_size
                    }
                    return {
                        "success": True,
                        "output": f"图片已生成: {output_filename}",
                        "output_file": self._last_output_file
                    }
                else:
                    return {"success": False, "output": "图片文件未生成，请检查代码"}

            else:
                # 其他类型，文件已在 write 步骤保存
                if self._last_output_file:
                    return {
                        "success": True,
                        "output": f"文件已就绪: {self._last_output_file.get('name', '')}",
                        "output_file": self._last_output_file
                    }
                return {"success": True, "output": "执行完成"}

        except subprocess.TimeoutExpired:
            return {"success": False, "output": "执行超时"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "output": f"执行失败: {str(e)}"}

    async def skill_chat_stream(
        self,
        skill_id: str,
        context: str,
        conversation: List[Dict[str, str]] = None,
        file_paths: List[str] = None,
        user_choice: str = None,
        pending_actions: List[Dict] = None,
        current_action_index: int = 0
    ) -> AsyncGenerator[str, None]:
        """
        Claude Code 风格的交互式技能执行

        AI 会输出操作步骤，每个步骤需要用户确认后才执行：
        - <!--ACTION:write--> 写入文件
        - <!--ACTION:run--> 执行命令
        - <!--ACTION:generate--> 生成内容

        Args:
            skill_id: 技能 UUID
            context: 用户原始需求
            conversation: 右侧面板对话历史
            file_paths: 文件路径列表
            user_choice: 用户选择（execute/skip/edit）
            pending_actions: 待执行的操作列表
            current_action_index: 当前操作索引

        Yields:
            SSE 格式的流式响应
        """
        import re

        # 加载技能
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            yield json.dumps({"type": "error", "message": "技能不存在"})
            return

        # 如果有待执行的操作且用户选择了执行
        if pending_actions and user_choice == "execute" and current_action_index < len(pending_actions):
            action = pending_actions[current_action_index]
            yield json.dumps({
                "type": "action_executing",
                "index": current_action_index,
                "action": action
            })

            # 执行操作
            result = await self._execute_action(action, skill.name, file_paths)

            yield json.dumps({
                "type": "action_result",
                "index": current_action_index,
                "success": result.get("success", False),
                "output": result.get("output", ""),
                "output_file": result.get("output_file")
            })

            # 如果还有下一个操作
            if current_action_index + 1 < len(pending_actions):
                next_action = pending_actions[current_action_index + 1]
                yield json.dumps({
                    "type": "action_pending",
                    "index": current_action_index + 1,
                    "action": next_action,
                    "total": len(pending_actions)
                })
            else:
                yield json.dumps({"type": "all_actions_done"})

            return

        # 如果用户选择跳过
        if pending_actions and user_choice == "skip" and current_action_index < len(pending_actions):
            yield json.dumps({
                "type": "action_skipped",
                "index": current_action_index
            })

            # 如果还有下一个操作
            if current_action_index + 1 < len(pending_actions):
                next_action = pending_actions[current_action_index + 1]
                yield json.dumps({
                    "type": "action_pending",
                    "index": current_action_index + 1,
                    "action": next_action,
                    "total": len(pending_actions)
                })
            else:
                yield json.dumps({"type": "all_actions_done"})

            return

        # 读取 SKILL.md 内容
        skill_md_content = ""
        if skill.folder_path:
            skill_folder = SKILLS_STORAGE_DIR / skill.folder_path
            skill_md_path = skill_folder / "SKILL.md"
            if skill_md_path.exists():
                try:
                    skill_md_content = skill_md_path.read_text(encoding="utf-8")
                except Exception:
                    pass

        # 读取文件内容（如果有）
        file_content = ""
        if file_paths:
            file_content = self._read_files_for_ai(file_paths)

        # 构建 system prompt - Claude Code 风格
        # 重要：将执行规则放在最前面，让 AI 优先注意到
        system_prompt = f"""# 最重要的规则 - 必须遵守

你正在一个交互式执行环境中工作。你必须使用 ACTION 标记来定义每个操作步骤，让用户逐个确认后执行。

## 操作标记格式（必须使用）

### 写入文件
<!--ACTION:write-->
{{"file": "文件名.js", "content": "完整文件内容..."}}
<!--END_ACTION-->

### 执行命令
<!--ACTION:run-->
{{"command": "node script.js", "description": "描述这个命令做什么"}}
<!--END_ACTION-->

### 生成内容
<!--ACTION:generate-->
{{"type": "pptx_code", "content": "完整的 pptxgenjs 代码..."}}
<!--END_ACTION-->

## 示例输出

当用户说"帮我生成一个 PPT"时，你应该这样输出：

好的！我来帮你生成 PPT。我将执行以下步骤：

**步骤 1: 创建 PPT 生成脚本**
<!--ACTION:write-->
{{"file": "presentation.js", "content": "const pptxgen = require('pptxgenjs');\\nconst pres = new pptxgen();\\npres.defineLayout({{ name:'LAYOUT', width:10, height:5.625 }});\\n// 添加幻灯片...\\npres.writeFile({{ fileName: '演示文稿.pptx' }});"}}
<!--END_ACTION-->

**步骤 2: 执行脚本生成 PPT 文件**
<!--ACTION:run-->
{{"command": "node presentation.js", "description": "运行脚本生成 演示文稿.pptx"}}
<!--END_ACTION-->

---

## 技能说明（参考信息）

{skill_md_content[:6000] if skill_md_content else skill.description or "通用技能"}

---

## 重要提醒

- **必须使用 ACTION 标记**来定义每个操作
- 每个 ACTION 内的 JSON 必须是有效格式
- 用户会看到每个操作并选择：执行、跳过或取消
- 代码内容必须完整，不能省略"""

        # 构建消息列表
        messages = []

        # 添加初始上下文
        initial_message = context
        if file_content:
            initial_message += f"\n\n## 用户上传的文件内容\n{file_content[:20000]}"

        # 如果有对话历史，使用历史；否则用初始消息
        if conversation and len(conversation) > 0:
            for msg in conversation:
                messages.append({"role": msg["role"], "content": msg["content"]})
        else:
            messages.append({"role": "user", "content": initial_message})

        try:
            # 流式调用 Claude API
            with self.client.messages.stream(
                model=self.model,
                max_tokens=16000,
                system=system_prompt,
                messages=messages
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                    yield json.dumps({"type": "content", "text": text})

                # 解析所有 ACTION 标记
                action_pattern = r'<!--ACTION:(\w+)-->\s*(\{.*?\})\s*<!--END_ACTION-->'
                actions = []
                for match in re.finditer(action_pattern, full_response, re.DOTALL):
                    action_type = match.group(1)
                    try:
                        action_data = json.loads(match.group(2))
                        actions.append({
                            "type": action_type,
                            "data": action_data
                        })
                    except json.JSONDecodeError:
                        pass

                if actions:
                    # 发送所有操作列表
                    yield json.dumps({
                        "type": "actions_planned",
                        "actions": actions,
                        "total": len(actions)
                    })

                    # 发送第一个待确认的操作
                    yield json.dumps({
                        "type": "action_pending",
                        "index": 0,
                        "action": actions[0],
                        "total": len(actions)
                    })
                else:
                    # 没有操作，直接完成
                    yield json.dumps({"type": "done", "full_response": full_response})

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield json.dumps({"type": "error", "message": str(e)})

    async def _execute_action(
        self,
        action: Dict,
        skill_name: str,
        file_paths: List[str] = None
    ) -> Dict:
        """
        执行单个操作

        Args:
            action: {"type": "write/run/generate", "data": {...}}
            skill_name: 技能名称
            file_paths: 文件路径列表

        Returns:
            {"success": bool, "output": str, "output_file": dict|None}
        """
        action_type = action.get("type")
        data = action.get("data", {})

        try:
            if action_type == "write":
                # 写入文件
                filename = data.get("file", "output.txt")
                content = data.get("content", "")
                filepath = OUTPUTS_DIR / filename
                filepath.write_text(content, encoding="utf-8")
                return {
                    "success": True,
                    "output": f"文件已写入: {filename}",
                    "output_file": {
                        "path": str(filepath),
                        "type": filepath.suffix.lstrip(".") or "txt",
                        "name": filename,
                        "url": f"/outputs/{filename}",
                        "size": filepath.stat().st_size
                    }
                }

            elif action_type == "run":
                # 执行命令
                import subprocess
                command = data.get("command", "")
                if not command:
                    return {"success": False, "output": "命令为空"}

                # 安全检查
                dangerous = ["rm -rf", "del /f", "format", "mkfs", "> /dev/"]
                for d in dangerous:
                    if d in command.lower():
                        return {"success": False, "output": f"不允许执行危险命令: {command}"}

                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=str(OUTPUTS_DIR)
                )

                output = result.stdout or result.stderr or "(无输出)"

                # 检查是否生成了文件
                output_file = None
                # 尝试从命令中提取可能的输出文件名
                import re
                pptx_match = re.search(r'([^\s"]+\.pptx)', command)
                if pptx_match:
                    pptx_name = pptx_match.group(1)
                    pptx_path = OUTPUTS_DIR / pptx_name
                    if pptx_path.exists():
                        output_file = {
                            "path": str(pptx_path),
                            "type": "pptx",
                            "name": pptx_name,
                            "url": f"/outputs/{pptx_name}",
                            "size": pptx_path.stat().st_size
                        }

                return {
                    "success": result.returncode == 0,
                    "output": output,
                    "output_file": output_file
                }

            elif action_type == "generate":
                # 生成内容
                gen_type = data.get("type", "")
                content = data.get("content", "")

                if gen_type == "pptx_code":
                    result = self._execute_pptx_code(content, skill_name)
                    if result:
                        return {
                            "success": True,
                            "output": f"PPT 已生成: {result['name']}",
                            "output_file": result
                        }
                    else:
                        return {"success": False, "output": "PPT 生成失败"}

                elif gen_type == "html":
                    from services.file_generator import generate_unique_filename
                    filename = generate_unique_filename(skill_name, "html")
                    filepath = OUTPUTS_DIR / filename
                    filepath.write_text(content, encoding="utf-8")
                    return {
                        "success": True,
                        "output": f"HTML 已生成: {filename}",
                        "output_file": {
                            "path": str(filepath),
                            "type": "html",
                            "name": filename,
                            "url": f"/outputs/{filename}",
                            "size": filepath.stat().st_size
                        }
                    }

                return {"success": False, "output": f"未知生成类型: {gen_type}"}

            else:
                return {"success": False, "output": f"未知操作类型: {action_type}"}

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "output": f"执行失败: {str(e)}"}

    # ========== 真正的 Claude Code 风格：多轮 AI 交互循环 ==========

    def _get_agent_tools(self) -> List[Dict]:
        """定义 Agent 可用的工具"""
        return [
            {
                "name": "write",
                "description": "将内容写入文件。用于创建新文件或覆盖现有文件。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径（相对于 outputs 目录）"
                        },
                        "content": {
                            "type": "string",
                            "description": "要写入的文件内容"
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "bash",
                "description": "执行 bash/shell 命令。可以运行 node、python 等脚本。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的命令"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "read",
                "description": "读取文件内容。支持读取 uploads/ 目录（上传的文件）、outputs/ 目录（生成的文件）以及技能文件夹中的文件（如 SKILL.md 中引用的 editing.md、pptxgenjs.md 等）。对于技能文件夹中的文件，直接使用相对路径即可（如 editing.md）。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径。可以是相对路径（如 editing.md）或带目录前缀的路径（如 uploads/xxx.xlsx）"
                        }
                    },
                    "required": ["path"]
                }
            }
        ]

    async def _execute_tool(self, tool_name: str, params: Dict, skill_folder: Path = None) -> Dict:
        """执行工具并返回结果

        Args:
            tool_name: 工具名称
            params: 工具参数
            skill_folder: 当前技能的文件夹路径（用于解析技能内相对路径）
        """
        import subprocess
        import shutil
        import asyncio
        import time

        try:
            print(f"[_execute_tool] 执行工具: {tool_name}, 参数: {str(params)[:200]}, skill_folder: {skill_folder}")

            if tool_name == "write":
                # 写入文件
                path = params.get("path", "")
                content = params.get("content", "")

                print(f"[_execute_tool] write: path={path}, content长度={len(content)}")

                # 确保路径安全
                if ".." in path or path.startswith("/"):
                    print(f"[_execute_tool] write: 路径不安全")
                    return {"success": False, "output": "不允许的路径"}

                filepath = OUTPUTS_DIR / path
                print(f"[_execute_tool] write: 完整路径={filepath}")
                filepath.parent.mkdir(parents=True, exist_ok=True)

                # 清理 markdown 代码块标记
                clean_content = content.strip()
                for prefix in ['```javascript', '```js', '```python', '```html', '```']:
                    if clean_content.startswith(prefix):
                        clean_content = clean_content[len(prefix):].strip()
                        break
                if clean_content.endswith('```'):
                    clean_content = clean_content[:-3].strip()

                # 修复中文引号（常见的 AI 生成错误）
                clean_content = clean_content.replace('"', '"').replace('"', '"')
                clean_content = clean_content.replace(''', "'").replace(''', "'")

                filepath.write_text(clean_content, encoding="utf-8")
                print(f"[_execute_tool] write: 文件已写入, 大小={filepath.stat().st_size}")

                return {
                    "success": True,
                    "output": f"文件已写入: {path}",
                    "file_path": str(filepath)
                }

            elif tool_name == "bash":
                # 执行命令
                command = params.get("command", "")
                print(f"[_execute_tool] bash: command={command}")

                # 安全检查
                dangerous = ["rm -rf", "rmdir", "del /", "format", "mkfs"]
                for d in dangerous:
                    if d in command.lower():
                        return {"success": False, "output": f"不允许执行危险命令"}

                # 在 outputs 目录执行
                cwd = str(OUTPUTS_DIR)
                print(f"[_execute_tool] bash: cwd={cwd}")

                # 检查是否是 node 命令
                if command.strip().startswith("node "):
                    node_path = shutil.which('node')
                    if not node_path:
                        return {"success": False, "output": "Node.js 未安装"}

                    # 检查并安装必要的 npm 包
                    npm_path = shutil.which('npm')
                    packages_to_install = []

                    # 检查 pptxgenjs (PPT 生成)
                    if not (SERVER_DIR / "node_modules" / "pptxgenjs").exists():
                        packages_to_install.append("pptxgenjs")

                    # 检查 exceljs (Excel 生成)
                    if not (SERVER_DIR / "node_modules" / "exceljs").exists():
                        packages_to_install.append("exceljs")

                    if packages_to_install and npm_path:
                        def install_npm():
                            return subprocess.run(
                                [npm_path, "install"] + packages_to_install,
                                capture_output=True,
                                text=True,
                                timeout=120,
                                cwd=str(SERVER_DIR)
                            )
                        await asyncio.to_thread(install_npm)

                    # 修复 JS 文件中的输出路径
                    script_name = command.strip().split()[1]  # node xxx.js
                    script_path = OUTPUTS_DIR / script_name
                    if script_path.exists():
                        import re
                        script_content = script_path.read_text(encoding="utf-8")
                        outputs_path_str = str(OUTPUTS_DIR).replace('\\', '/')

                        # 替换 writeFile 中的相对路径为绝对路径
                        # 支持 PPT (.pptx) 和 Excel (.xlsx) 文件
                        def fix_path(match):
                            filename = match.group(1)
                            # 如果已经是绝对路径，不修改
                            if '/' in filename or '\\' in filename:
                                return match.group(0)
                            return match.group(0).replace(filename, f"{outputs_path_str}/{filename}")

                        # 修复 PPT 文件路径
                        script_content = re.sub(
                            r'writeFile\s*\(\s*["\']([^"\']+\.pptx)["\']',
                            fix_path,
                            script_content
                        )
                        script_content = re.sub(
                            r'fileName\s*:\s*["\']([^"\']+\.pptx)["\']',
                            fix_path,
                            script_content
                        )

                        # 修复 Excel 文件路径
                        script_content = re.sub(
                            r'writeFile\s*\(\s*["\']([^"\']+\.xlsx)["\']',
                            fix_path,
                            script_content
                        )
                        script_content = re.sub(
                            r'xlsx\.writeFile\s*\(\s*["\']([^"\']+\.xlsx)["\']',
                            fix_path,
                            script_content
                        )

                        script_path.write_text(script_content, encoding="utf-8")

                    # 设置 NODE_PATH
                    env = {**os.environ, "NODE_PATH": str(SERVER_DIR / "node_modules")}

                # 检查是否是 python 命令
                elif command.strip().startswith("python "):
                    # 修复 Python 脚本中的输出路径
                    parts = command.strip().split()
                    if len(parts) >= 2:
                        script_name = parts[1]
                        script_path = OUTPUTS_DIR / script_name
                        if script_path.exists() and script_path.suffix == '.py':
                            import re
                            script_content = script_path.read_text(encoding="utf-8")
                            outputs_path_str = str(OUTPUTS_DIR).replace('\\', '/')

                            # 在脚本开头添加 OUTPUT_DIR 变量
                            if 'OUTPUT_DIR' not in script_content:
                                script_content = f'OUTPUT_DIR = r"{outputs_path_str}"\n' + script_content

                            # 修复常见的输出路径模式
                            def fix_python_path(match):
                                filename = match.group(1)
                                if '/' in filename or '\\' in filename or filename.startswith('OUTPUT_DIR'):
                                    return match.group(0)
                                return match.group(0).replace(f'"{filename}"', f'f"{{OUTPUT_DIR}}/{filename}"')

                            # to_excel, to_csv, to_json 等
                            for method in ['to_excel', 'to_csv', 'to_json', 'to_html', 'savefig', 'write']:
                                script_content = re.sub(
                                    rf'{method}\s*\(\s*["\']([^"\']+)["\']',
                                    fix_python_path,
                                    script_content
                                )

                            # open() 写文件
                            script_content = re.sub(
                                r'open\s*\(\s*["\']([^"\']+)["\'].*["\']w',
                                fix_python_path,
                                script_content
                            )

                            script_path.write_text(script_content, encoding="utf-8")
                            print(f"[_execute_tool] 修复 Python 脚本路径: {script_name}")

                    env = os.environ
                else:
                    env = os.environ

                # 执行命令
                def run_cmd():
                    return subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=120,
                        cwd=cwd,
                        env=env
                    )

                result = await asyncio.to_thread(run_cmd)
                print(f"[_execute_tool] bash: returncode={result.returncode}")
                print(f"[_execute_tool] bash: stdout={result.stdout[:500] if result.stdout else 'None'}")
                print(f"[_execute_tool] bash: stderr={result.stderr[:500] if result.stderr else 'None'}")

                if result.returncode == 0:
                    output = result.stdout or "执行成功"
                    # 检查是否生成了文件（支持更多格式）
                    output_file = None
                    supported_extensions = [
                        # Office 文件
                        '.pptx', '.ppt', '.xlsx', '.xls', '.docx', '.doc',
                        # 数据文件
                        '.csv', '.json',
                        # 文档
                        '.pdf', '.html', '.md', '.txt',
                        # 图片
                        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'
                    ]

                    print(f"[_execute_tool] 检查输出目录: {OUTPUTS_DIR}")
                    print(f"[_execute_tool] 目录内容: {list(OUTPUTS_DIR.iterdir()) if OUTPUTS_DIR.exists() else '目录不存在'}")

                    current_time = time.time()
                    for ext in supported_extensions:
                        # 使用 ** 递归搜索子目录
                        for f in OUTPUTS_DIR.glob(f"**/*{ext}"):
                            file_mtime = f.stat().st_mtime
                            time_diff = current_time - file_mtime
                            print(f"[_execute_tool] 发现文件: {f}, 修改时间差: {time_diff:.1f}秒")
                            if time_diff < 30:  # 30秒内创建的
                                # 根据扩展名确定文件类型
                                file_type = ext[1:]
                                if ext in ['.xlsx', '.xls']:
                                    file_type = 'excel'
                                elif ext in ['.pptx', '.ppt']:
                                    file_type = 'ppt'
                                elif ext in ['.docx', '.doc']:
                                    file_type = 'word'
                                elif ext in ['.jpg', '.jpeg', '.gif', '.svg', '.webp']:
                                    file_type = 'image'

                                # 计算相对路径
                                rel_path = f.relative_to(OUTPUTS_DIR)
                                output_file = {
                                    "path": str(f),
                                    "type": file_type,
                                    "name": f.name,
                                    "url": f"/outputs/{rel_path}".replace('\\', '/'),
                                    "size": f.stat().st_size
                                }
                                print(f"[_execute_tool] 找到输出文件: {output_file}")
                                break
                        if output_file:
                            break

                    if not output_file:
                        print(f"[_execute_tool] 未找到新生成的文件")

                    return {
                        "success": True,
                        "output": output[:2000],
                        "output_file": output_file
                    }
                else:
                    return {
                        "success": False,
                        "output": f"执行失败:\n{result.stderr or result.stdout}"[:2000]
                    }

            elif tool_name == "read":
                # 读取文件
                path = params.get("path", "")
                print(f"[_execute_tool] read: path={path}")

                # 尝试多个位置查找文件
                filepath = None

                # 1. OUTPUTS_DIR
                test_path = OUTPUTS_DIR / path
                if test_path.exists():
                    filepath = test_path
                    print(f"[_execute_tool] read: 在 outputs 找到文件")

                # 2. UPLOADS_DIR
                if not filepath:
                    test_path = UPLOADS_DIR / path
                    if test_path.exists():
                        filepath = test_path
                        print(f"[_execute_tool] read: 在 uploads 找到文件")

                # 3. 尝试去掉路径前缀后查找
                if not filepath and path.startswith("/uploads/"):
                    clean_path = path[len("/uploads/"):]
                    test_path = UPLOADS_DIR / clean_path
                    if test_path.exists():
                        filepath = test_path
                        print(f"[_execute_tool] read: 在 uploads 找到文件 (去掉 /uploads/ 前缀)")

                if not filepath and path.startswith("uploads/"):
                    clean_path = path[len("uploads/"):]
                    test_path = UPLOADS_DIR / clean_path
                    if test_path.exists():
                        filepath = test_path
                        print(f"[_execute_tool] read: 在 uploads 找到文件 (去掉 uploads/ 前缀)")

                if not filepath and path.startswith("/outputs/"):
                    clean_path = path[len("/outputs/"):]
                    test_path = OUTPUTS_DIR / clean_path
                    if test_path.exists():
                        filepath = test_path
                        print(f"[_execute_tool] read: 在 outputs 找到文件 (去掉 /outputs/ 前缀)")

                if not filepath and path.startswith("outputs/"):
                    clean_path = path[len("outputs/"):]
                    test_path = OUTPUTS_DIR / clean_path
                    if test_path.exists():
                        filepath = test_path
                        print(f"[_execute_tool] read: 在 outputs 找到文件 (去掉 outputs/ 前缀)")

                # 4. 技能文件夹（用于读取 SKILL.md 中引用的相对路径文件）
                if not filepath and skill_folder:
                    # 直接使用相对路径
                    test_path = skill_folder / path
                    if test_path.exists():
                        filepath = test_path
                        print(f"[_execute_tool] read: 在技能文件夹找到文件: {test_path}")

                    # 也尝试常见的子目录
                    if not filepath:
                        for subdir in ["scripts", "reference", "templates"]:
                            test_path = skill_folder / subdir / path
                            if test_path.exists():
                                filepath = test_path
                                print(f"[_execute_tool] read: 在技能文件夹/{subdir} 找到文件: {test_path}")
                                break

                # 5. 绝对路径
                if not filepath:
                    test_path = Path(path)
                    if test_path.exists():
                        filepath = test_path
                        print(f"[_execute_tool] read: 使用绝对路径")

                if not filepath:
                    skill_hint = f", 技能文件夹/{path}" if skill_folder else ""
                    print(f"[_execute_tool] read: 文件不存在, 尝试过的路径: OUTPUTS_DIR/{path}, UPLOADS_DIR/{path}{skill_hint}, {path}")
                    return {"success": False, "output": f"文件不存在: {path}\n提示: 上传的文件在 uploads/ 目录, 生成的文件在 outputs/ 目录"}

                # 根据文件类型选择读取方式
                suffix = filepath.suffix.lower()
                print(f"[_execute_tool] read: 文件类型={suffix}")

                if suffix in ['.xlsx', '.xls']:
                    # Excel 文件 - 使用 pandas 读取
                    import pandas as pd
                    try:
                        df = pd.read_excel(filepath)
                        content = f"Excel 文件: {filepath.name}\n"
                        content += f"行数: {len(df)}, 列数: {len(df.columns)}\n"
                        content += f"列名: {list(df.columns)}\n\n"
                        content += df.head(50).to_string()
                        if len(df) > 50:
                            content += f"\n\n... 共 {len(df)} 行，只显示前 50 行"
                    except Exception as e:
                        return {"success": False, "output": f"Excel 读取失败: {str(e)}"}

                elif suffix == '.csv':
                    # CSV 文件 - 使用 pandas 读取
                    import pandas as pd
                    try:
                        df = pd.read_csv(filepath)
                        content = f"CSV 文件: {filepath.name}\n"
                        content += f"行数: {len(df)}, 列数: {len(df.columns)}\n"
                        content += f"列名: {list(df.columns)}\n\n"
                        content += df.head(50).to_string()
                        if len(df) > 50:
                            content += f"\n\n... 共 {len(df)} 行，只显示前 50 行"
                    except Exception as e:
                        return {"success": False, "output": f"CSV 读取失败: {str(e)}"}

                elif suffix == '.json':
                    # JSON 文件
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        content = json.dumps(data, ensure_ascii=False, indent=2)
                        if len(content) > 10000:
                            content = content[:10000] + "\n...[truncated]..."
                    except Exception as e:
                        return {"success": False, "output": f"JSON 读取失败: {str(e)}"}

                elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
                    # 图片文件 - 返回文件信息
                    content = f"图片文件: {filepath.name}\n大小: {filepath.stat().st_size} bytes\n(图片内容无法以文本显示)"

                else:
                    # 其他文件尝试作为文本读取
                    try:
                        content = filepath.read_text(encoding="utf-8")
                        if len(content) > 10000:
                            content = content[:10000] + "\n...[truncated]..."
                    except UnicodeDecodeError:
                        return {"success": False, "output": f"无法读取二进制文件: {filepath.name}"}

                return {"success": True, "output": content}

            else:
                return {"success": False, "output": f"未知工具: {tool_name}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "output": "执行超时"}
        except Exception as e:
            return {"success": False, "output": f"执行失败: {str(e)}"}

    async def agent_loop(
        self,
        skill_id: str,
        context: str,
        file_paths: List[str] = None,
        conversation: List[Dict] = None,
        pending_tool_call: Dict = None,
        tool_confirmed: bool = False,
        tool_rejected: bool = False,
        user_edit: str = None
    ) -> AsyncGenerator[str, None]:
        """
        真正的 Claude Code 风格 Agent 循环

        多轮 AI 交互，每个工具调用都等待用户确认。
        """
        import asyncio
        import time

        # ===== 调试日志 =====
        print(f"[Agent Loop] ========== 开始 ==========")
        print(f"[Agent Loop] skill_id: {skill_id}")
        print(f"[Agent Loop] context: {context[:200] if context else 'None'}...")
        print(f"[Agent Loop] file_paths: {file_paths}")
        print(f"[Agent Loop] conversation 数量: {len(conversation) if conversation else 0}")
        print(f"[Agent Loop] pending_tool_call: {pending_tool_call}")
        print(f"[Agent Loop] tool_confirmed: {tool_confirmed}, tool_rejected: {tool_rejected}")

        # 加载技能
        skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            yield json.dumps({"type": "error", "message": "技能不存在"})
            return

        # 获取技能文件夹路径（用于解析技能内相对路径文件）
        skill_folder = SKILLS_STORAGE_DIR / skill.folder_path if skill.folder_path else None

        # ===== 快速模式：检查 config.json 中的 exec_mode =====
        exec_mode = "ai"  # 默认 AI 模式
        if skill.folder_path:
            config_path = SKILLS_STORAGE_DIR / skill.folder_path / "config.json"
            if config_path.exists():
                try:
                    config_data = json.loads(config_path.read_text(encoding="utf-8"))
                    exec_mode = config_data.get("exec_mode", "ai")
                except:
                    pass

        # 如果是 direct 模式且有脚本，直接执行
        if exec_mode == "direct" and not pending_tool_call and not conversation and skill.folder_path and skill.entry_script:
            skill_folder = SKILLS_STORAGE_DIR / skill.folder_path
            script_path = skill_folder / skill.entry_script

            if script_path.exists() and script_path.suffix == '.py':
                print(f"[Agent Loop] 检测到预定义脚本: {script_path}")

                # 准备参数
                input_file = None
                if file_paths:
                    fp = file_paths[0]
                    if fp.startswith('/uploads/'):
                        input_file = str(UPLOADS_DIR / fp[len('/uploads/'):])
                    elif fp.startswith('uploads/'):
                        input_file = str(UPLOADS_DIR / fp[len('uploads/'):])
                    elif fp.startswith('/outputs/'):
                        input_file = str(OUTPUTS_DIR / fp[len('/outputs/'):])
                    elif fp.startswith('outputs/'):
                        input_file = str(OUTPUTS_DIR / fp[len('outputs/'):])
                    else:
                        input_file = fp

                if not input_file:
                    yield json.dumps({"type": "error", "message": "请上传文件"})
                    return

                # 检查输入文件是否存在
                if not Path(input_file).exists():
                    yield json.dumps({"type": "error", "message": f"文件不存在: {input_file}"})
                    return

                yield json.dumps({
                    "type": "message",
                    "content": f"正在执行 {skill.name}..."
                })
                await asyncio.sleep(0)

                # 执行脚本
                try:
                    import subprocess

                    result = await asyncio.to_thread(
                        lambda: subprocess.run(
                            ["python", str(script_path), input_file],
                            capture_output=True,
                            text=True,
                            timeout=120,
                            cwd=str(skill_folder)
                        )
                    )

                    print(f"[Agent Loop] 脚本执行: returncode={result.returncode}")
                    print(f"[Agent Loop] stdout: {result.stdout[:500] if result.stdout else 'None'}")
                    print(f"[Agent Loop] stderr: {result.stderr[:500] if result.stderr else 'None'}")

                    if result.returncode == 0:
                        # 检查是否生成了文件
                        output_file = None
                        for ext in ['.json', '.xlsx', '.csv', '.pdf', '.html']:
                            for f in OUTPUTS_DIR.glob(f"*{ext}"):
                                mtime = f.stat().st_mtime
                                if time.time() - mtime < 30:
                                    file_type = {
                                        '.json': 'json', '.xlsx': 'excel', '.csv': 'csv',
                                        '.pdf': 'pdf', '.html': 'html'
                                    }.get(ext, 'file')
                                    output_file = {
                                        "path": str(f),
                                        "type": file_type,
                                        "name": f.name,
                                        "url": f"/outputs/{f.name}"
                                    }
                                    break
                            if output_file:
                                break

                        yield json.dumps({
                            "type": "tool_result",
                            "tool": "script",
                            "success": True,
                            "output": result.stdout or "执行成功",
                            "output_file": output_file,
                            "message": result.stdout or "执行成功"
                        })
                        await asyncio.sleep(0)

                        yield json.dumps({
                            "type": "message",
                            "content": f"[OK] {result.stdout.strip() if result.stdout else '执行完成'}"
                        })
                        await asyncio.sleep(0)

                        yield json.dumps({"type": "done", "message": "任务完成"})
                        return

                    else:
                        yield json.dumps({
                            "type": "error",
                            "message": f"执行失败: {result.stderr or result.stdout}"
                        })
                        return

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    yield json.dumps({"type": "error", "message": f"脚本执行错误: {str(e)}"})
                    return

        # 读取 SKILL.md
        skill_md_content = ""
        if skill.folder_path:
            skill_folder = SKILLS_STORAGE_DIR / skill.folder_path
            skill_md_path = skill_folder / "SKILL.md"
            if skill_md_path.exists():
                try:
                    skill_md_content = skill_md_path.read_text(encoding="utf-8")
                    # 替换占位符为实际路径
                    skill_folder_str = str(skill_folder).replace('\\', '/')
                    outputs_str = str(OUTPUTS_DIR).replace('\\', '/')
                    uploads_str = str(UPLOADS_DIR).replace('\\', '/')
                    skill_md_content = skill_md_content.replace('<skill-path>', skill_folder_str)
                    skill_md_content = skill_md_content.replace('"<skill-path>"', f'"{skill_folder_str}"')
                    skill_md_content = skill_md_content.replace('<outputs>', outputs_str)
                    skill_md_content = skill_md_content.replace('<uploads>', uploads_str)
                except:
                    pass

            # 读取 reference 目录
            reference_dir = skill_folder / "reference"
            if reference_dir.exists():
                for ref_file in reference_dir.glob("*.md"):
                    try:
                        ref_text = ref_file.read_text(encoding="utf-8")
                        if len(ref_text) > 5000:
                            ref_text = ref_text[:5000] + "\n...[truncated]..."
                        skill_md_content += f"\n\n## Reference: {ref_file.name}\n{ref_text}"
                    except:
                        pass

        # 构建系统提示（精简版，加快响应）
        # 获取 outputs 目录的绝对路径
        outputs_path = str(OUTPUTS_DIR).replace('\\', '/')

        uploads_path = str(UPLOADS_DIR).replace('\\', '/')

        system_prompt = f"""你是技能执行助手。

{skill_md_content[:5000] if skill_md_content else skill.description}

## 规则
1. write 工具写文件，bash 工具执行，read 工具读取文件
2. 一次只调用一个工具
3. **文件路径（必须使用绝对路径）**：
   - 上传文件目录: {uploads_path}/
   - 输出文件目录: {outputs_path}/
   - bash 命令在 outputs 目录执行，不要 cd 到其他目录
4. 重要：用户上传的文件路径会在消息中给出（如 uploads/xxx.xlsx），转换为绝对路径: {uploads_path}/xxx.xlsx
5. 如果没有提供输入文件，直接生成示例数据
6. 如果 read 工具失败，不要重试，使用示例数据
7. 代码要点（使用英文引号，不要中文引号）：

### PPT 生成 (Node.js)
```javascript
const pptx = require("pptxgenjs");
const pres = new pptx();
// ... 添加幻灯片
pres.writeFile({{ fileName: "{outputs_path}/output.pptx" }});
```

### Excel 生成 (Node.js)
```javascript
const ExcelJS = require("exceljs");
const workbook = new ExcelJS.Workbook();
const sheet = workbook.addWorksheet("Sheet1");
// sheet.columns = [{{ header: "Name", key: "name" }}];
// sheet.addRow({{ name: "Test" }});
workbook.xlsx.writeFile("{outputs_path}/output.xlsx");
```

### Python 生成文件
```python
import pandas as pd
df = pd.DataFrame(data)
df.to_excel("{outputs_path}/output.xlsx", index=False)
# 或 df.to_csv("{outputs_path}/output.csv", index=False)
```

8. 代码出错时，修复后重试
9. **重要**：任务完成后（文件已成功生成），直接返回完成消息，不要再调用任何工具
10. **执行脚本**：先用 write 工具写脚本文件（如 convert.py），再用 bash 工具执行（如 python convert.py）。不要使用 heredoc（<< EOF）
"""

        # 初始化对话历史
        messages = []

        # 添加历史对话
        if conversation:
            for msg in conversation:
                # 支持 Pydantic 模型和字典两种格式
                role = msg.role if hasattr(msg, 'role') else msg.get("role", "")
                content = msg.content if hasattr(msg, 'content') else msg.get("content", "")

                if role == "user":
                    messages.append({"role": "user", "content": content})
                elif role == "assistant":
                    messages.append({"role": "assistant", "content": content})
                elif role == "tool_result":
                    # 工具结果作为 user 消息
                    messages.append({
                        "role": "user",
                        "content": f"工具执行结果:\n{content}"
                    })

        # 如果有待确认的工具调用
        if pending_tool_call:
            # 支持 Pydantic 模型和字典两种格式
            tool_name = pending_tool_call.tool if hasattr(pending_tool_call, 'tool') else pending_tool_call.get("tool", "")
            tool_params = pending_tool_call.params if hasattr(pending_tool_call, 'params') else pending_tool_call.get("params", {})

            if tool_confirmed:
                # 用户确认，执行工具
                yield json.dumps({
                    "type": "tool_executing",
                    "tool": tool_name,
                    "message": f"● **{tool_name.capitalize()}** 执行中..."
                })
                await asyncio.sleep(0)

                result = await self._execute_tool(tool_name, tool_params, skill_folder)
                print(f"[Agent Loop] 工具执行结果: success={result.get('success')}, output_file={result.get('output_file')}")

                yield json.dumps({
                    "type": "tool_result",
                    "tool": tool_name,
                    "success": result.get("success"),
                    "output": result.get("output"),
                    "output_file": result.get("output_file"),
                    "message": f"● **{tool_name.capitalize()}**\n  ⎿  {result.get('output', '')[:500]}"
                })
                await asyncio.sleep(0)

                # 如果成功生成了文件，直接完成任务，不再调用 AI
                if result.get("success") and result.get("output_file"):
                    print(f"[Agent Loop] 文件已生成，直接完成任务")
                    yield json.dumps({
                        "type": "message",
                        "content": f"[OK] 已成功生成文件: {result['output_file'].get('name', 'output')}"
                    })
                    await asyncio.sleep(0)
                    yield json.dumps({
                        "type": "done",
                        "message": "任务完成"
                    })
                    return  # 直接返回，不再继续

                # 否则将结果加入对话历史，继续 AI 循环
                messages.append({
                    "role": "user",
                    "content": f"工具 {tool_name} 执行结果:\n{json.dumps(result, ensure_ascii=False)}"
                })

            elif tool_rejected:
                # 用户拒绝
                messages.append({
                    "role": "user",
                    "content": f"用户拒绝执行 {tool_name}。请尝试其他方式或结束任务。"
                })

            elif user_edit:
                # 用户修改了内容
                messages.append({
                    "role": "user",
                    "content": f"用户修改了 {tool_name} 的内容:\n{user_edit}\n请使用修改后的内容继续。"
                })

        else:
            # 新任务，添加用户输入
            user_input = context
            if file_paths:
                # 明确告诉 AI 文件的实际路径（统一格式为 uploads/xxx 或 outputs/xxx）
                resolved_paths = []
                for fp in file_paths:
                    if fp.startswith("/uploads/"):
                        resolved_paths.append(f"uploads/{fp[len('/uploads/'):]}")
                    elif fp.startswith("uploads/"):
                        resolved_paths.append(fp)  # 已经是正确格式
                    elif fp.startswith("/outputs/"):
                        resolved_paths.append(f"outputs/{fp[len('/outputs/'):]}")
                    elif fp.startswith("outputs/"):
                        resolved_paths.append(fp)  # 已经是正确格式
                    else:
                        resolved_paths.append(fp)

                user_input += f"\n\n输入文件路径（使用 read 工具时请使用这些路径）: {resolved_paths}"
                print(f"[Agent Loop] 文件路径: {resolved_paths}")

                file_content = self._read_files_for_ai(file_paths)
                if file_content:
                    user_input += f"\n\n附件内容:\n{file_content}"

            if not messages or messages[-1].get("role") != "user":
                messages.append({"role": "user", "content": user_input})
                print(f"[Agent Loop] 添加用户消息, 长度: {len(user_input)}")
                print(f"[Agent Loop] 用户消息内容预览: {user_input[:500]}...")

        # 调用 AI
        yield json.dumps({
            "type": "thinking",
            "message": "● AI 正在思考..."
        })
        await asyncio.sleep(0)

        try:
            # 使用工具调用
            print(f"[Agent Loop] 调用 Claude API, messages 数量: {len(messages)}")
            for i, m in enumerate(messages):
                print(f"[Agent Loop] message[{i}]: role={m.get('role')}, content长度={len(m.get('content', ''))}")

            def call_claude():
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=8000,
                    system=system_prompt,
                    tools=self._get_agent_tools(),
                    messages=messages
                )

            response = await asyncio.to_thread(call_claude)

            print(f"[Agent Loop] Claude 响应: stop_reason={response.stop_reason}, content_blocks={len(response.content)}")

            # 解析响应
            text_content = ""
            tool_use = None

            for block in response.content:
                print(f"[Agent Loop] Block type: {block.type}")
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_use = {
                        "tool": block.name,
                        "params": block.input,
                        "id": block.id
                    }
                    print(f"[Agent Loop] Tool use: {block.name}")

            # 如果有文字内容，发送给前端
            if text_content:
                print(f"[Agent Loop] 发送 message 事件, 长度: {len(text_content)}")
                yield json.dumps({
                    "type": "message",
                    "content": text_content
                })
                await asyncio.sleep(0)

            # 如果有工具调用，发送确认请求
            if tool_use:
                tool_name = tool_use["tool"]
                tool_params = tool_use["params"]

                # 构建显示信息
                if tool_name == "write":
                    display_name = f"Write({tool_params.get('path', '')})"
                    preview = tool_params.get("content", "")[:200] + "..."
                elif tool_name == "bash":
                    display_name = f"Bash({tool_params.get('command', '')})"
                    preview = tool_params.get("command", "")
                else:
                    display_name = f"{tool_name.capitalize()}({json.dumps(tool_params)[:50]})"
                    preview = json.dumps(tool_params, ensure_ascii=False)[:200]

                print(f"[Agent Loop] 发送 tool_call 事件: {display_name}")
                yield json.dumps({
                    "type": "tool_call",
                    "tool": tool_name,
                    "params": tool_params,
                    "display_name": display_name,
                    "preview": preview,
                    "message": f"● **{display_name}**\n  ⎿  等待确认..."
                })

            else:
                # 没有工具调用，任务可能完成了
                print(f"[Agent Loop] 无工具调用, stop_reason={response.stop_reason}")
                if response.stop_reason == "end_turn":
                    yield json.dumps({
                        "type": "done",
                        "message": "任务完成"
                    })
                else:
                    # 其他情况也发送完成（比如 stop_reason 是 max_tokens）
                    yield json.dumps({
                        "type": "done",
                        "message": f"AI 响应完成 (stop_reason: {response.stop_reason})"
                    })

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[Agent Loop] 错误: {str(e)}")
            yield json.dumps({
                "type": "error",
                "message": f"AI 调用失败: {str(e)}"
            })
