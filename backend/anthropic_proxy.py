"""
Anthropic API 代理 - 将 Claude API 请求转换为 qwen 调用
让 qwen 模型兼容 Claude Agent SDK

启动方式:
    python anthropic_proxy.py

配置后在 Admin 后台设置:
    Base URL: http://localhost:4000
"""
from fastapi import FastAPI, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import json
import uuid
import time
import os
from typing import AsyncIterator, Optional

app = FastAPI(title="Anthropic API Proxy for Qwen")

# ============ 配置 ============
# 从环境变量读取，或使用默认值
# 注意：如果请求头中有 x-api-key，会优先使用请求头的 Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")

print(f"[Proxy] DashScope Base URL: {DASHSCOPE_BASE_URL}")
print(f"[Proxy] Qwen Model: {QWEN_MODEL}")


def convert_anthropic_to_openai(anthropic_request: dict) -> dict:
    """将 Anthropic 请求格式转换为 OpenAI 格式"""
    messages = []

    # 处理 system prompt
    if "system" in anthropic_request:
        system_content = anthropic_request["system"]
        if isinstance(system_content, list):
            # 处理数组格式的 system
            text_parts = []
            for part in system_content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part["text"])
                elif isinstance(part, str):
                    text_parts.append(part)
            system_content = "\n".join(text_parts)
        messages.append({
            "role": "system",
            "content": system_content
        })

    # 处理消息
    for msg in anthropic_request.get("messages", []):
        role = msg["role"]
        content = msg["content"]

        # Anthropic 的 content 可能是数组
        if isinstance(content, list):
            text_parts = []
            tool_results = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        text_parts.append(part["text"])
                    elif part.get("type") == "tool_result":
                        # 工具结果需要特殊处理
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": part.get("tool_use_id", ""),
                            "content": str(part.get("content", ""))
                        })
                    elif part.get("type") == "tool_use":
                        # 工具调用
                        pass  # OpenAI 格式中这是在 assistant 消息的 tool_calls 中
                elif isinstance(part, str):
                    text_parts.append(part)

            if tool_results:
                # 如果有工具结果，添加为单独的消息
                for tr in tool_results:
                    messages.append(tr)
                continue

            content = "\n".join(text_parts) if text_parts else ""

        if content:  # 只添加有内容的消息
            messages.append({"role": role, "content": content})

    # 构建 OpenAI 请求
    openai_request = {
        "model": QWEN_MODEL,
        "messages": messages,
        "max_tokens": anthropic_request.get("max_tokens", 4096),
        "temperature": anthropic_request.get("temperature", 0.7),
        "stream": anthropic_request.get("stream", False),
    }

    # 处理工具调用
    if "tools" in anthropic_request and anthropic_request["tools"]:
        openai_request["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object", "properties": {}})
                }
            }
            for tool in anthropic_request["tools"]
        ]

        # 处理 tool_choice
        if "tool_choice" in anthropic_request:
            tc = anthropic_request["tool_choice"]
            if isinstance(tc, dict):
                if tc.get("type") == "any":
                    openai_request["tool_choice"] = "required"
                elif tc.get("type") == "tool":
                    openai_request["tool_choice"] = {
                        "type": "function",
                        "function": {"name": tc.get("name", "")}
                    }
                elif tc.get("type") == "auto":
                    openai_request["tool_choice"] = "auto"

    return openai_request


def convert_openai_to_anthropic(openai_response: dict, model_name: str = None) -> dict:
    """将 OpenAI 响应格式转换为 Anthropic 格式"""
    choice = openai_response["choices"][0]
    message = choice["message"]

    content = []
    stop_reason = "end_turn"

    # 处理文本内容
    if message.get("content"):
        content.append({
            "type": "text",
            "text": message["content"]
        })

    # 处理工具调用
    if message.get("tool_calls"):
        stop_reason = "tool_use"
        for tool_call in message["tool_calls"]:
            try:
                arguments = json.loads(tool_call["function"]["arguments"] or "{}")
            except:
                arguments = {}
            content.append({
                "type": "tool_use",
                "id": tool_call["id"],
                "name": tool_call["function"]["name"],
                "input": arguments
            })

    # 如果没有内容，添加空文本
    if not content:
        content.append({"type": "text", "text": ""})

    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": content,
        "model": model_name or openai_response.get("model", QWEN_MODEL),
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": openai_response.get("usage", {}).get("prompt_tokens", 0),
            "output_tokens": openai_response.get("usage", {}).get("completion_tokens", 0)
        }
    }


async def stream_convert(response: httpx.Response, model_name: str = None) -> AsyncIterator[bytes]:
    """转换流式响应从 OpenAI 格式到 Anthropic 格式"""
    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    # 发送 message_start 事件
    start_event = {
        "type": "message_start",
        "message": {
            "id": message_id,
            "type": "message",
            "role": "assistant",
            "content": [],
            "model": model_name or QWEN_MODEL,
            "stop_reason": None,
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0}
        }
    }
    yield f"event: message_start\ndata: {json.dumps(start_event)}\n\n".encode()

    # 发送 content_block_start
    block_start = {
        "type": "content_block_start",
        "index": 0,
        "content_block": {"type": "text", "text": ""}
    }
    yield f"event: content_block_start\ndata: {json.dumps(block_start)}\n\n".encode()

    tool_calls_buffer = {}  # 缓存工具调用
    current_tool_index = 0
    has_text_content = False

    async for line in response.aiter_lines():
        line = line.strip()
        if not line or not line.startswith("data: "):
            continue

        if line == "data: [DONE]":
            break

        try:
            data = json.loads(line[6:])
            delta = data.get("choices", [{}])[0].get("delta", {})

            # 处理文本内容
            if "content" in delta and delta["content"]:
                has_text_content = True
                anthropic_delta = {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": delta["content"]}
                }
                yield f"event: content_block_delta\ndata: {json.dumps(anthropic_delta)}\n\n".encode()

            # 处理工具调用
            if "tool_calls" in delta:
                for tc in delta["tool_calls"]:
                    tc_index = tc.get("index", 0)

                    if tc_index not in tool_calls_buffer:
                        tool_calls_buffer[tc_index] = {
                            "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
                            "name": "",
                            "arguments": ""
                        }

                    if "function" in tc:
                        if "name" in tc["function"]:
                            tool_calls_buffer[tc_index]["name"] = tc["function"]["name"]
                        if "arguments" in tc["function"]:
                            tool_calls_buffer[tc_index]["arguments"] += tc["function"]["arguments"]
        except Exception as e:
            print(f"[Proxy] Stream parse error: {e}, line: {line[:100]}")
            continue

    # 结束文本块
    block_stop = {"type": "content_block_stop", "index": 0}
    yield f"event: content_block_stop\ndata: {json.dumps(block_stop)}\n\n".encode()

    # 如果有工具调用，发送工具调用事件
    for idx, tc in tool_calls_buffer.items():
        tool_index = idx + 1  # 工具块从 index 1 开始

        # content_block_start for tool_use
        tool_start = {
            "type": "content_block_start",
            "index": tool_index,
            "content_block": {
                "type": "tool_use",
                "id": tc["id"],
                "name": tc["name"],
                "input": {}
            }
        }
        yield f"event: content_block_start\ndata: {json.dumps(tool_start)}\n\n".encode()

        # 发送工具参数
        try:
            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
        except:
            args = {}

        tool_delta = {
            "type": "content_block_delta",
            "index": tool_index,
            "delta": {
                "type": "input_json_delta",
                "partial_json": json.dumps(args)
            }
        }
        yield f"event: content_block_delta\ndata: {json.dumps(tool_delta)}\n\n".encode()

        # content_block_stop for tool_use
        tool_stop = {"type": "content_block_stop", "index": tool_index}
        yield f"event: content_block_stop\ndata: {json.dumps(tool_stop)}\n\n".encode()

    # 发送 message_delta（包含 stop_reason）
    stop_reason = "tool_use" if tool_calls_buffer else "end_turn"
    message_delta = {
        "type": "message_delta",
        "delta": {"stop_reason": stop_reason, "stop_sequence": None},
        "usage": {"output_tokens": 0}
    }
    yield f"event: message_delta\ndata: {json.dumps(message_delta)}\n\n".encode()

    # 发送 message_stop
    message_stop = {"type": "message_stop"}
    yield f"event: message_stop\ndata: {json.dumps(message_stop)}\n\n".encode()


@app.post("/v1/messages")
async def create_message(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None)
):
    """处理 Anthropic /v1/messages 请求"""
    body = await request.json()
    is_stream = body.get("stream", False)
    requested_model = body.get("model", "")

    # 调试：打印所有 headers
    print(f"[Proxy] Headers: {dict(request.headers)}")

    # 获取 API Key
    # 优先使用环境变量中的 DASHSCOPE_API_KEY（如果已配置）
    # 这样可以避免 Anthropic SDK 环境变量的干扰
    api_key = x_api_key
    if authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]  # 从 Bearer token 提取

    # 如果请求头的 Key 不是 DashScope 格式（不以 sk- 开头），使用环境变量
    if DASHSCOPE_API_KEY and (not api_key or not api_key.startswith('sk-')):
        print(f"[Proxy] 请求头 Key 无效，使用环境变量 DASHSCOPE_API_KEY")
        api_key = DASHSCOPE_API_KEY

    if not api_key:
        print("[Proxy] 错误: 未提供 API Key")
        return JSONResponse(
            status_code=401,
            content={"error": {"message": "API Key 未配置。请在 Admin 后台填写正确的 DashScope API Key"}}
        )

    print(f"\n[Proxy] ========== 收到请求 ==========")
    print(f"[Proxy] 请求模型: {requested_model}")
    print(f"[Proxy] 流式: {is_stream}")
    print(f"[Proxy] 工具数量: {len(body.get('tools', []))}")
    print(f"[Proxy] API Key: {api_key[:10]}..." if api_key else "[Proxy] API Key: 无")

    # 转换请求格式
    openai_request = convert_anthropic_to_openai(body)
    print(f"[Proxy] 转换后消息数: {len(openai_request['messages'])}")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            if is_stream:
                # 流式响应
                openai_request["stream"] = True
                async with client.stream(
                    "POST",
                    f"{DASHSCOPE_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=openai_request
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"[Proxy] DashScope 错误: {response.status_code} - {error_text}")
                        return JSONResponse(
                            status_code=response.status_code,
                            content={"error": {"message": error_text.decode()}}
                        )

                    return StreamingResponse(
                        stream_convert(response, requested_model),
                        media_type="text/event-stream"
                    )
            else:
                # 非流式响应
                response = await client.post(
                    f"{DASHSCOPE_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=openai_request
                )

                if response.status_code != 200:
                    print(f"[Proxy] DashScope 错误: {response.status_code} - {response.text}")
                    return JSONResponse(
                        status_code=response.status_code,
                        content={"error": {"message": response.text}}
                    )

                openai_response = response.json()
                anthropic_response = convert_openai_to_anthropic(openai_response, requested_model)
                print(f"[Proxy] 响应 stop_reason: {anthropic_response['stop_reason']}")
                return anthropic_response

    except Exception as e:
        import traceback
        print(f"[Proxy] 请求失败: {e}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e)}}
        )


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "model": QWEN_MODEL}


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Anthropic API Proxy for Qwen",
        "status": "running",
        "target_model": QWEN_MODEL,
        "endpoints": {
            "/v1/messages": "Anthropic Messages API",
            "/health": "Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 50)
    print("Anthropic API Proxy for Qwen")
    print("=" * 50)
    print(f"Target: {DASHSCOPE_BASE_URL}")
    print(f"Model:  {QWEN_MODEL}")
    print("=" * 50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=4000)
