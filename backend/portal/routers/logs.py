"""
日志系统 - 详细可读的实时日志
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Set, Optional, List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from collections import deque

router = APIRouter(prefix="/api/logs", tags=["Logs"])

# 存储日志
recent_logs: deque = deque(maxlen=500)
active_connections: Set[WebSocket] = set()
_log_id = 0


def _create_log(
    level: str,
    title: str,
    detail: str = None,
    data: Any = None,
    step: str = None
) -> dict:
    """
    创建日志条目

    Args:
        level: 级别 info/success/warn/error
        title: 标题（简短描述）
        detail: 详情文本
        data: 结构化数据（会被JSON序列化）
        step: 步骤标识 如 "1/3"
    """
    global _log_id
    _log_id += 1

    # 序列化 data
    data_str = None
    if data is not None:
        try:
            if isinstance(data, str):
                data_str = data
            else:
                data_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        except:
            data_str = str(data)

    return {
        "id": _log_id,
        "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": level,
        "title": title,
        "detail": detail,
        "data": data_str,
        "step": step
    }


async def _broadcast(log: dict):
    """广播日志"""
    if not active_connections:
        return

    msg = json.dumps(log, ensure_ascii=False)
    dead = set()

    for conn in active_connections:
        try:
            await conn.send_text(msg)
        except:
            dead.add(conn)

    for c in dead:
        active_connections.discard(c)


def _send(log: dict):
    """发送日志"""
    recent_logs.append(log)
    # 同时打印到控制台（终端风格）
    level = log['level'].upper()
    title = log['title']

    # 根据级别选择颜色代码
    colors = {
        'INFO': '\033[32m',      # 绿色
        'SUCCESS': '\033[92m',   # 亮绿色
        'WARN': '\033[33m',      # 黄色
        'ERROR': '\033[91m',     # 红色
    }
    reset = '\033[0m'
    color = colors.get(level, '\033[32m')

    print(f"{color}[{log['time']}] [{level}] {title}{reset}")
    if log.get('detail'):
        print(f"{color}    └─ {log['detail']}{reset}")
    if log.get('data'):
        for line in str(log['data']).split('\n')[:5]:
            print(f"{color}       {line}{reset}")

    # 广播到 WebSocket
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_broadcast(log))
    except RuntimeError:
        # 没有运行中的事件循环
        pass


# ============================================================
# 分隔符 - 让日志更清晰
# ============================================================

def log_section(title: str, style: str = "="):
    """
    输出分隔区块，让日志更清晰
    style: "=" 主要分隔, "-" 次要分隔, "." 细节分隔
    """
    if style == "=":
        line = "═" * 50
        _send(_create_log("info", f"╔{line}╗"))
        _send(_create_log("info", f"║  {title.center(46)}  ║"))
        _send(_create_log("info", f"╚{line}╝"))
        print(f"\033[36m╔{'═'*50}╗\033[0m")
        print(f"\033[36m║  {title.center(46)}  ║\033[0m")
        print(f"\033[36m╚{'═'*50}╝\033[0m")
    elif style == "-":
        line = "─" * 40
        _send(_create_log("info", f"┌{line}┐"))
        _send(_create_log("info", f"│ {title.ljust(38)} │"))
        _send(_create_log("info", f"└{line}┘"))
        print(f"\033[33m┌{'─'*40}┐\033[0m")
        print(f"\033[33m│ {title.ljust(38)} │\033[0m")
        print(f"\033[33m└{'─'*40}┘\033[0m")
    else:
        _send(_create_log("info", f"··· {title} ···"))
        print(f"\033[90m··· {title} ···\033[0m")


def log_step_start(step_num: int, total: int, name: str, desc: str = None):
    """步骤开始 - 清晰的步骤提示"""
    header = f"步骤 {step_num}/{total}: {name}"
    _send(_create_log("info", f"▶ {header}", detail=desc, step=f"{step_num}/{total}"))
    print(f"\033[96m{'─'*40}\033[0m")
    print(f"\033[96m▶ {header}\033[0m")
    if desc:
        print(f"\033[90m  {desc}\033[0m")


def log_step_done(step_num: int, total: int, name: str, result: str = None):
    """步骤完成"""
    header = f"步骤 {step_num}/{total}: {name} - 完成"
    _send(_create_log("success", f"✓ {header}", detail=result, step=f"{step_num}/{total}"))
    print(f"\033[92m✓ {header}\033[0m")
    if result:
        print(f"\033[92m  └─ {result}\033[0m")


def log_progress(current: int, total: int, message: str = None):
    """进度日志"""
    percent = int(current / total * 100) if total > 0 else 0
    bar_len = 20
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    progress_str = f"[{bar}] {percent}% ({current}/{total})"

    _send(_create_log("info", progress_str, detail=message))
    print(f"\033[94m{progress_str}\033[0m")
    if message:
        print(f"\033[90m  {message}\033[0m")


# ============================================================
# 日志 API
# ============================================================

def log_info(title: str, detail: str = None, data: Any = None, step: str = None):
    """信息日志"""
    _send(_create_log("info", title, detail, data, step))

def log_success(title: str, detail: str = None, data: Any = None, step: str = None):
    """成功日志"""
    _send(_create_log("success", title, detail, data, step))

def log_warn(title: str, detail: str = None, data: Any = None, step: str = None):
    """警告日志"""
    _send(_create_log("warn", title, detail, data, step))

def log_error(title: str, detail: str = None, data: Any = None, step: str = None):
    """错误日志"""
    _send(_create_log("error", title, detail, data, step))


# ============================================================
# 业务日志 - 请求/响应
# ============================================================

def log_request(endpoint: str, method: str = "POST", desc: str = None, params: Dict = None):
    """记录请求"""
    title = f"→ {method} {endpoint}"
    if desc:
        title += f" ({desc})"
    _send(_create_log(
        "info",
        title,
        detail=None,
        data=params
    ))

def log_response(endpoint: str, success: bool, desc: str = None, result: Any = None, error: str = None):
    """记录响应"""
    if success:
        title = f"← {endpoint} 成功"
        if desc:
            title += f" ({desc})"
        _send(_create_log(
            "success",
            title,
            detail=None,
            data=result
        ))
    else:
        title = f"← {endpoint} 失败"
        if desc:
            title += f" ({desc})"
        _send(_create_log(
            "error",
            title,
            detail=error,
            data=None
        ))


# ============================================================
# 业务日志 - 技能执行
# ============================================================

def log_skill_start(name: str, params: Dict = None):
    """技能开始 - 带分隔符"""
    line = "─" * 48

    print(f"\033[96m┌{line}┐\033[0m")
    print(f"\033[96m│ 🚀 开始执行技能: {name.ljust(28)} │\033[0m")
    print(f"\033[96m│    技能是一段自动化脚本，用于完成特定任务  │\033[0m")

    _send(_create_log(
        "info",
        f"┌{'─'*48}┐",
        step="开始"
    ))
    _send(_create_log(
        "info",
        f"│ 🚀 开始执行技能: {name}",
        detail="技能是一段自动化脚本，用于完成特定任务",
        step="开始"
    ))
    if params:
        # 显示输入参数
        params_preview = ", ".join([f"{k}={str(v)[:20]}" for k, v in list(params.items())[:3]])
        _send(_create_log(
            "info",
            f"│ 📥 输入参数: {params_preview}",
            data=params,
            step="参数"
        ))

def log_skill_step(name: str, step: str, detail: str = None, data: Any = None):
    """技能步骤 - 带进度指示"""
    # 给步骤添加更友好的说明
    step_desc = {
        "执行脚本": "正在运行Python脚本处理数据...",
        "生成文件": "正在生成输出文件...",
        "读取文件": "正在读取输入文件...",
        "处理数据": "正在处理数据...",
        "执行测试": "正在测试技能脚本...",
    }
    friendly_detail = step_desc.get(step, detail) or detail

    print(f"\033[93m  ├─ {step}\033[0m")
    if friendly_detail:
        print(f"\033[90m     {friendly_detail}\033[0m")

    _send(_create_log(
        "info",
        f"├─ 步骤: {step}",
        detail=friendly_detail,
        data=data,
        step=step
    ))

def log_skill_success(name: str, result: Any = None):
    """技能成功 - 带结束分隔符"""
    line = "─" * 48

    print(f"\033[92m  └─ ✅ 执行成功!\033[0m")
    print(f"\033[92m└{line}┘\033[0m")

    _send(_create_log(
        "success",
        f"│ ✅ 技能 [{name}] 执行成功",
        detail="任务已完成，可以查看结果",
        step="完成"
    ))
    if result:
        result_preview = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
        _send(_create_log(
            "success",
            f"│ 📤 输出结果: {result_preview}",
            data=result,
            step="结果"
        ))
    _send(_create_log(
        "success",
        f"└{'─'*48}┘",
        step="完成"
    ))

def log_skill_error(name: str, error: str, detail: str = None):
    """技能失败 - 带错误分隔符"""
    line = "─" * 48

    print(f"\033[91m  └─ ❌ 执行失败: {error}\033[0m")
    print(f"\033[91m└{line}┘\033[0m")

    _send(_create_log(
        "error",
        f"│ ❌ 技能 [{name}] 执行失败",
        detail=f"错误原因: {error}",
        step="错误"
    ))
    if detail:
        _send(_create_log(
            "error",
            f"│ 📋 错误详情: {detail[:200]}",
            step="详情"
        ))
    _send(_create_log(
        "error",
        f"└{'─'*48}┘",
        step="错误"
    ))


# ============================================================
# 业务日志 - AI
# ============================================================

def log_ai_start(prompt_preview: str = None):
    """AI 开始 - 带分隔符"""
    print(f"\033[35m╭{'─'*44}╮\033[0m")
    print(f"\033[35m│ 🤖 正在调用 Claude AI 大模型...         │\033[0m")
    print(f"\033[35m│    AI正在理解您的问题并生成回答        │\033[0m")

    _send(_create_log(
        "info",
        "╭" + "─"*44 + "╮"
    ))
    _send(_create_log(
        "info",
        "│ 🤖 正在调用 Claude AI 大模型...",
        detail="AI正在理解您的问题并生成回答"
    ))
    if prompt_preview:
        preview = prompt_preview[:80] + "..." if len(prompt_preview) > 80 else prompt_preview
        _send(_create_log(
            "info",
            f"│ 📨 发送内容: {preview}"
        ))

def log_ai_done(response_preview: str = None):
    """AI 完成 - 带结束分隔符"""
    print(f"\033[35m│ ✨ AI 已生成回答                        │\033[0m")
    print(f"\033[35m╰{'─'*44}╯\033[0m")

    _send(_create_log(
        "success",
        "│ ✨ AI 回答生成完成",
        detail="大模型已返回结果"
    ))
    if response_preview:
        preview = response_preview[:100] + "..." if len(response_preview) > 100 else response_preview
        _send(_create_log(
            "success",
            f"│ 📩 回答预览: {preview}"
        ))
    _send(_create_log(
        "success",
        "╰" + "─"*44 + "╯"
    ))


# ============================================================
# 业务日志 - 文件
# ============================================================

def log_file_read(path: str, size: int = None):
    """读取文件"""
    import os
    filename = os.path.basename(path) if path else path
    size_str = f"，大小: {_format_size(size)}" if size else ""
    _send(_create_log(
        "info",
        f"📄 读取文件: {filename}",
        detail=f"正在读取输入文件{size_str}"
    ))

def log_file_write(path: str, size: int = None):
    """写入文件"""
    import os
    filename = os.path.basename(path) if path else path
    size_str = f"，大小: {_format_size(size)}" if size else ""
    _send(_create_log(
        "success",
        f"📄 生成文件: {filename}",
        detail=f"输出文件已生成{size_str}，可以下载"
    ))

def _format_size(size: int) -> str:
    """格式化文件大小"""
    if size is None:
        return "未知"
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / 1024 / 1024:.1f} MB"


# ============================================================
# WebSocket 端点
# ============================================================

@router.websocket("/ws")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    print(f"[LOG] WebSocket 客户端连接，当前: {len(active_connections)}")

    try:
        # 发送最近日志
        logs_to_send = list(recent_logs)[-100:]
        for log in logs_to_send:
            await websocket.send_text(json.dumps(log, ensure_ascii=False))

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except asyncio.TimeoutError:
                await websocket.send_text('{"type":"heartbeat"}')
    except WebSocketDisconnect:
        pass
    finally:
        active_connections.discard(websocket)
        print(f"[LOG] WebSocket 客户端断开，剩余: {len(active_connections)}")


@router.get("/recent")
async def get_recent(limit: int = 100):
    return {"logs": list(recent_logs)[-limit:]}


@router.delete("/clear")
async def clear():
    recent_logs.clear()
    return {"ok": True}


# ============================================================
# 兼容 Python logging
# ============================================================

class LogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            if any(x in msg for x in ["GET /api/logs", "WebSocket", "uvicorn.access"]):
                return

            level = record.levelname.lower()
            if level == "warning":
                level = "warn"

            _send(_create_log(level, msg))
        except:
            pass


def setup_log_handler():
    handler = LogHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(name)s: %(message)s'))
    logging.getLogger().addHandler(handler)
    return handler


# ============================================================
# 会话/操作上下文日志
# ============================================================

def log_session_start(
    api_name: str,
    api_desc: str,
    source: str = None,
    skills: list = None,
    user_input: str = None
):
    """
    记录会话/操作开始的上下文信息

    api_name: 接口名称 (如 "/agent/chat/stream")
    api_desc: 接口功能说明 (如 "与AI助手对话，AI会根据你的问题给出回答")
    source: 来源页面 (如 "Agent对话页面")
    skills: 涉及的技能列表
    user_input: 用户输入预览
    """
    line = "═" * 56

    # 控制台输出
    print(f"\033[96m╔{line}╗\033[0m")
    print(f"\033[96m║  🌐 接口: {api_name.ljust(44)}  ║\033[0m")
    print(f"\033[96m║  📝 说明: {api_desc.ljust(44)}  ║\033[0m")
    if source:
        print(f"\033[96m║  📍 来源: {source.ljust(44)}  ║\033[0m")
    if skills:
        skills_str = ", ".join(skills[:3])
        if len(skills) > 3:
            skills_str += f" (+{len(skills)-3}个)"
        print(f"\033[96m║  🔧 技能: {skills_str.ljust(44)}  ║\033[0m")
    if user_input:
        preview = user_input[:40] + "..." if len(user_input) > 40 else user_input
        print(f"\033[96m║  💬 输入: {preview.ljust(44)}  ║\033[0m")
    print(f"\033[96m╚{line}╝\033[0m")

    # WebSocket 推送
    _send(_create_log("info", f"╔{'═'*56}╗"))
    _send(_create_log("info", f"║  🌐 调用接口: {api_name}"))
    _send(_create_log("info", f"║  📝 功能说明: {api_desc}"))
    if source:
        _send(_create_log("info", f"║  📍 来源页面: {source}"))
    if skills:
        skills_str = ", ".join(skills[:5])
        if len(skills) > 5:
            skills_str += f" 等{len(skills)}个"
        _send(_create_log("info", f"║  🔧 使用技能: {skills_str}"))
    if user_input:
        preview = user_input[:50] + "..." if len(user_input) > 50 else user_input
        _send(_create_log("info", f"║  💬 用户输入: {preview}"))
    _send(_create_log("info", f"╚{'═'*56}╝"))


def log_session_end(success: bool, summary: str = None):
    """记录会话/操作结束"""
    line = "─" * 52

    if success:
        print(f"\033[92m╰{line}╯\033[0m")
        print(f"\033[92m  ✅ 操作完成 {summary or ''}\033[0m")
        _send(_create_log("success", f"╰{'─'*52}╯"))
        _send(_create_log("success", f"  ✅ 操作完成", detail=summary))
    else:
        print(f"\033[91m╰{line}╯\033[0m")
        print(f"\033[91m  ❌ 操作失败 {summary or ''}\033[0m")
        _send(_create_log("error", f"╰{'─'*52}╯"))
        _send(_create_log("error", f"  ❌ 操作失败", detail=summary))


# ============================================================
# 系统日志
# ============================================================

def sys_ready():
    """系统就绪 - 带启动横幅"""
    banner = """
╔════════════════════════════════════════════════════════╗
║                                                        ║
║      🚀 AI Skills Platform 后端服务启动成功!           ║
║                                                        ║
║      📡 API服务: 已就绪，等待前端请求                  ║
║      🔌 WebSocket: 已开启，实时日志推送中              ║
║      🤖 AI服务: Claude大模型已连接                     ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
"""
    print(f"\033[92m{banner}\033[0m")

    _send(_create_log("success", "╔" + "═"*56 + "╗"))
    _send(_create_log("success", "║  🚀 AI Skills Platform 后端服务启动成功!"))
    _send(_create_log("success", "║  📡 API服务已就绪，等待前端请求"))
    _send(_create_log("success", "║  🔌 WebSocket已开启，实时日志推送中"))
    _send(_create_log("success", "║  🤖 AI服务已连接，可以开始对话"))
    _send(_create_log("success", "╚" + "═"*56 + "╝"))
