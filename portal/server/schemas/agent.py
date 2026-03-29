from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []
    skill_ids: Optional[List[str]] = None  # Available skills for this conversation
    agent_id: Optional[str] = None  # Agent ID for RAG data isolation
    enable_rag: bool = True  # Enable RAG retrieval from vector database


class ChatResponse(BaseModel):
    message: str
    skill_suggestions: Optional[List[Dict[str, Any]]] = None


class SkillPlanItem(BaseModel):
    skill_id: str  # UUID
    skill_name: str
    reason: str
    params: Optional[Dict[str, Any]] = {}


class PlanRequest(BaseModel):
    user_input: str
    available_skills: Optional[List[str]] = None


class PlanResponse(BaseModel):
    plan: List[SkillPlanItem]
    explanation: str


class ExecuteRequest(BaseModel):
    skill_id: str  # UUID
    script_name: Optional[str] = None  # If not specified, use entry_script
    params: Optional[Dict[str, Any]] = {}
    agent_id: Optional[str] = None  # Agent ID for RAG data isolation


class OutputFile(BaseModel):
    """输出文件信息"""
    name: str  # 文件名
    type: str  # 文件类型: pdf, excel, word, html, png, markdown, code, file
    url: str   # 下载URL
    size: Optional[str] = None  # 文件大小描述


class ExecuteResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    output: Optional[str] = None
    output_file: Optional[OutputFile] = None  # 输出文件


class AnalyzeRequest(BaseModel):
    """迭代分析请求"""
    file_paths: List[str]  # 要分析的文件路径列表
    context: Optional[str] = ""  # 用户需求描述
    skill_id: Optional[str] = None  # 可选的技能ID
    max_iterations: Optional[int] = 5  # 最大迭代次数


class AnalyzeCodeResult(BaseModel):
    """代码执行结果"""
    code: str  # 执行的代码
    success: bool
    stdout: str
    stderr: Optional[str] = None
    generated_files: Optional[List[Dict[str, Any]]] = []


class AnalyzeResponse(BaseModel):
    """迭代分析响应"""
    success: bool
    iterations: List[AnalyzeCodeResult] = []  # 每轮迭代结果
    final_report: Optional[str] = None  # 最终报告
    generated_files: Optional[List[Dict[str, Any]]] = []  # 所有生成的文件
    error: Optional[str] = None


# ========== Claude Code 风格：步骤化技能执行 ==========

class SkillChatMessage(BaseModel):
    """技能对话消息"""
    role: str  # "user" or "assistant"
    content: str


class SkillChatAction(BaseModel):
    """操作步骤"""
    type: str  # write, run, generate
    data: Dict[str, Any]  # 操作数据


class SkillChatRequest(BaseModel):
    """步骤化技能执行请求"""
    skill_id: str  # 技能 UUID
    context: str  # 用户原始需求
    conversation: List[SkillChatMessage] = []  # 右侧面板对话历史
    file_paths: Optional[List[str]] = []  # 文件路径
    user_choice: Optional[str] = None  # 用户选择（execute/skip/edit）
    pending_actions: Optional[List[SkillChatAction]] = None  # 待执行的操作列表
    current_action_index: int = 0  # 当前操作索引
    agent_id: Optional[str] = None  # Agent ID for RAG data isolation


class SkillExecuteInteractiveRequest(BaseModel):
    """Claude Code 风格交互式执行请求 - 系统级工具调用确认"""
    skill_id: str  # 技能 UUID
    context: str  # 用户原始需求
    file_paths: Optional[List[str]] = []  # 文件路径
    confirmed_step: int = -1  # 已确认执行到哪一步，-1 表示还没开始
    auto_confirm: bool = False  # 自动确认所有步骤（全部执行）
    skip_current: bool = False  # 跳过当前步骤（不执行 confirmed_step）


# ========== 真正的 Claude Code 风格：多轮 AI 交互 ==========

class ToolCall(BaseModel):
    """工具调用"""
    tool: str  # write, bash, read, edit
    params: Dict[str, Any]  # 工具参数
    description: Optional[str] = None  # 描述（显示给用户）
    display_name: Optional[str] = None  # 显示名称
    preview: Optional[str] = None  # 预览


class AgentLoopMessage(BaseModel):
    """Agent 循环中的消息"""
    role: str  # user, assistant, tool_result
    content: str
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[Dict[str, Any]] = None


class AgentLoopRequest(BaseModel):
    """Agent 循环请求"""
    skill_id: str  # 技能 UUID
    context: str  # 用户原始需求
    file_paths: Optional[List[str]] = []  # 文件路径
    conversation: List[AgentLoopMessage] = []  # 对话历史
    # 工具确认
    pending_tool_call: Optional[ToolCall] = None  # 待确认的工具调用
    tool_confirmed: bool = False  # 用户是否确认
    tool_rejected: bool = False  # 用户是否拒绝
    user_edit: Optional[str] = None  # 用户修改的内容
