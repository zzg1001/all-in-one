"""
Proxy Service - API 代理服务
将 Anthropic API 请求转换为 OpenAI 兼容格式（如 DashScope/Qwen）
"""
import json
import uuid
import time
import httpx
from typing import AsyncIterator, Optional, Dict, Any
from fastapi import APIRouter, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse

# 全局配置（运行时更新）
_proxy_config: Dict[str, Any] = {
    "enabled": False,
    "target_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "target_api_key": "",
    "target_model": "qwen-plus",
    "max_tokens": 4096,
    "temperature": 0.7,
}


def update_proxy_config(config: Dict[str, Any]):
    """更新代理配置"""
    global _proxy_config
    _proxy_config.update(config)
    print(f"[Proxy] 配置已更新: enabled={_proxy_config['enabled']}, model={_proxy_config['target_model']}")


def get_proxy_config() -> Dict[str, Any]:
    """获取当前代理配置"""
    return _proxy_config.copy()


def is_proxy_enabled() -> bool:
    """检查代理是否启用"""
    return _proxy_config.get("enabled", False)


# ============ 格式转换 ============

def convert_anthropic_to_openai(anthropic_request: dict, config: dict) -> dict:
    """将 Anthropic 请求格式转换为 OpenAI 格式"""
    messages = []

    # 处理 system prompt
    if "system" in anthropic_request:
        system_content = anthropic_request["system"]
        if isinstance(system_content, list):
            text_parts = []
            for part in system_content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part["text"])
                elif isinstance(part, str):
                    text_parts.append(part)
            system_content = "\n".join(text_parts)
        messages.append({"role": "system", "content": system_content})

    # 处理消息
    for msg in anthropic_request.get("messages", []):
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, list):
            text_parts = []
            tool_results = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        text_parts.append(part["text"])
                    elif part.get("type") == "tool_result":
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": part.get("tool_use_id", ""),
                            "content": str(part.get("content", ""))
                        })
                elif isinstance(part, str):
                    text_parts.append(part)

            if tool_results:
                for tr in tool_results:
                    messages.append(tr)
                continue

            content = "\n".join(text_parts) if text_parts else ""

        if content:
            messages.append({"role": role, "content": content})

    # 构建 OpenAI 请求
    openai_request = {
        "model": config.get("target_model", "qwen-plus"),
        "messages": messages,
        "max_tokens": anthropic_request.get("max_tokens", config.get("max_tokens", 4096)),
        "temperature": anthropic_request.get("temperature", config.get("temperature", 0.7)),
        "stream": anthropic_request.get("stream", False),
    }

    # 处理工具
    if "tools" in anthropic_request and anthropic_request["tools"]:
        openai_tools = []
        for tool in anthropic_request["tools"]:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            })
        openai_request["tools"] = openai_tools

    return openai_request


def convert_openai_to_anthropic(openai_response: dict, model: str) -> dict:
    """将 OpenAI 响应格式转换为 Anthropic 格式"""
    choice = openai_response.get("choices", [{}])[0]
    message = choice.get("message", {})

    content = []
    if message.get("content"):
        content.append({"type": "text", "text": message["content"]})

    # 处理工具调用
    if message.get("tool_calls"):
        for tc in message["tool_calls"]:
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            content.append({
                "type": "tool_use",
                "id": tc.get("id", str(uuid.uuid4())),
                "name": func.get("name", ""),
                "input": args
            })

    # 确定停止原因
    finish_reason = choice.get("finish_reason", "end_turn")
    stop_reason_map = {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
        "content_filter": "end_turn",
    }
    stop_reason = stop_reason_map.get(finish_reason, "end_turn")

    usage = openai_response.get("usage", {})

    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": model,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        }
    }


async def convert_openai_stream_to_anthropic(
    response: httpx.Response,
    model: str
) -> AsyncIterator[str]:
    """将 OpenAI 流式响应转换为 Anthropic 格式"""
    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    # 发送 message_start
    yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': message_id, 'type': 'message', 'role': 'assistant', 'content': [], 'model': model, 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"

    # 发送 content_block_start
    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"

    buffer = ""
    async for line in response.aiter_lines():
        if not line or not line.startswith("data: "):
            continue

        data = line[6:]
        if data == "[DONE]":
            break

        try:
            chunk = json.loads(data)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            content = delta.get("content", "")

            if content:
                yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': content}})}\n\n"

        except json.JSONDecodeError:
            continue

    # 发送结束事件
    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
    yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 0}})}\n\n"
    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"


# ============ API 路由 ============

router = APIRouter(prefix="/proxy", tags=["API Proxy"])


@router.get("/status")
async def proxy_status():
    """获取代理状态"""
    config = get_proxy_config()
    return {
        "enabled": config.get("enabled", False),
        "target_model": config.get("target_model"),
        "target_base_url": config.get("target_base_url"),
    }


@router.post("/v1/messages")
async def proxy_messages(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None),
):
    """
    Anthropic Messages API 代理
    - 如果目标是 Anthropic 格式（URL 包含 anthropic），直接转发
    - 如果目标是 OpenAI 格式，转换后转发
    """
    config = get_proxy_config()

    if not config.get("enabled"):
        return JSONResponse(
            status_code=503,
            content={"error": {"type": "service_unavailable", "message": "代理服务未启用"}}
        )

    # 获取 API Key
    api_key = config.get("target_api_key", "")
    if x_api_key and x_api_key.startswith("sk-"):
        api_key = x_api_key
    elif authorization and authorization.startswith("Bearer sk-"):
        api_key = authorization[7:]

    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"error": {"type": "authentication_error", "message": "未配置 API Key"}}
        )

    try:
        body = await request.json()
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": {"type": "invalid_request_error", "message": str(e)}}
        )

    base_url = config.get("target_base_url", "").rstrip("/")
    is_anthropic_api = "anthropic" in base_url.lower()
    is_stream = body.get("stream", False)

    print(f"\n[Proxy] ========== 请求 ==========")
    print(f"[Proxy] 目标: {base_url}")
    print(f"[Proxy] 格式: {'Anthropic' if is_anthropic_api else 'OpenAI'}")
    print(f"[Proxy] 流式: {is_stream}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            if is_anthropic_api:
                # Anthropic 格式：直接转发，不转换
                url = f"{base_url}/v1/messages"
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }
                # 替换模型为目标模型
                forward_body = {**body, "model": config.get("target_model", body.get("model"))}

                if is_stream:
                    async with client.stream("POST", url, json=forward_body, headers=headers) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            print(f"[Proxy] 错误: {response.status_code} - {error_text.decode()}")
                            return JSONResponse(
                                status_code=response.status_code,
                                content={"error": {"type": "api_error", "message": error_text.decode()}}
                            )

                        # 直接转发流式响应
                        async def forward_stream():
                            async for line in response.aiter_lines():
                                yield line + "\n"

                        return StreamingResponse(
                            forward_stream(),
                            media_type="text/event-stream",
                            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                        )
                else:
                    response = await client.post(url, json=forward_body, headers=headers)
                    if response.status_code != 200:
                        print(f"[Proxy] 错误: {response.status_code} - {response.text}")
                        return JSONResponse(
                            status_code=response.status_code,
                            content={"error": {"type": "api_error", "message": response.text}}
                        )
                    print(f"[Proxy] 响应成功")
                    return JSONResponse(content=response.json())

            else:
                # OpenAI 格式：需要转换
                openai_request = convert_anthropic_to_openai(body, config)
                url = f"{base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                print(f"[Proxy] 模型: {openai_request['model']}")

                if is_stream:
                    async with client.stream("POST", url, json=openai_request, headers=headers) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            print(f"[Proxy] 错误: {response.status_code} - {error_text.decode()}")
                            return JSONResponse(
                                status_code=response.status_code,
                                content={"error": {"type": "api_error", "message": error_text.decode()}}
                            )

                        return StreamingResponse(
                            convert_openai_stream_to_anthropic(response, config["target_model"]),
                            media_type="text/event-stream",
                            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
                        )
                else:
                    response = await client.post(url, json=openai_request, headers=headers)
                    if response.status_code != 200:
                        print(f"[Proxy] 错误: {response.status_code} - {response.text}")
                        return JSONResponse(
                            status_code=response.status_code,
                            content={"error": {"type": "api_error", "message": response.text}}
                        )

                    openai_response = response.json()
                    anthropic_response = convert_openai_to_anthropic(openai_response, config["target_model"])
                    print(f"[Proxy] 响应成功")
                    return JSONResponse(content=anthropic_response)

    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": {"type": "timeout_error", "message": "请求超时"}}
        )
    except Exception as e:
        print(f"[Proxy] 异常: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"type": "internal_error", "message": str(e)}}
        )
