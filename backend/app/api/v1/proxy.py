"""
Proxy Config API - 代理配置管理
支持启动独立的代理服务进程，PID 持久化到数据库
"""
import uuid
import httpx
import subprocess
import sys
import os
import signal
import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.core.database import get_db, SessionLocal
from app.models.proxy_config import ProxyConfig

router = APIRouter(prefix="/api/proxy", tags=["Proxy Config"])

# 内存中缓存运行的进程对象（可选，主要用于快速访问）
_running_processes: Dict[str, subprocess.Popen] = {}


def _kill_process_by_pid(pid: int) -> bool:
    """通过 PID 杀死进程"""
    try:
        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=5)
            print(f"[Proxy] 已终止进程 PID={pid}")
            return True
    except psutil.NoSuchProcess:
        print(f"[Proxy] 进程 PID={pid} 不存在")
    except psutil.TimeoutExpired:
        try:
            proc.kill()
            print(f"[Proxy] 强制杀死进程 PID={pid}")
            return True
        except:
            pass
    except Exception as e:
        print(f"[Proxy] 终止进程 PID={pid} 失败: {e}")
    return False


_cleanup_done = False

def _cleanup_orphan_processes():
    """清理孤儿代理进程（首次 API 调用时执行）"""
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True

    print("[Proxy] 检查并清理孤儿代理进程...")
    db = SessionLocal()
    try:
        # 尝试查询，如果 pid 列不存在会报错，直接跳过
        running_configs = db.query(ProxyConfig).filter(ProxyConfig.is_running == True).all()
        for config in running_configs:
            pid = getattr(config, 'pid', None)
            if pid:
                if psutil.pid_exists(pid):
                    print(f"[Proxy] 发现孤儿进程: {config.name} (PID={pid})")
                    _kill_process_by_pid(pid)
            # 重置状态
            config.is_running = False
            config.is_enabled = False
            if hasattr(config, 'pid'):
                config.pid = None
        db.commit()
        print("[Proxy] 孤儿进程清理完成")
    except Exception as e:
        print(f"[Proxy] 清理孤儿进程时出错（可能是首次启动）: {e}")
        db.rollback()
    finally:
        db.close()


# ============ Schemas ============

class ProxyConfigCreate(BaseModel):
    name: str
    description: Optional[str] = None
    proxy_type: str = "anthropic_to_openai"
    target_base_url: str  # 原始API地址
    target_api_key: str
    target_model: str
    proxy_url: Optional[str] = None  # 代理地址
    proxy_model: Optional[str] = None  # 对外模型名
    proxy_port: int = 4000
    max_tokens: int = 4096
    temperature: float = 0.7


class ProxyConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_base_url: Optional[str] = None
    target_api_key: Optional[str] = None
    target_model: Optional[str] = None
    proxy_url: Optional[str] = None
    proxy_model: Optional[str] = None
    proxy_port: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ProxyConfigResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    proxy_type: str
    target_base_url: str  # 原始API地址
    target_api_key: str  # 部分隐藏
    target_model: str
    proxy_url: Optional[str]  # 代理地址
    proxy_model: Optional[str]  # 对外模型名
    proxy_port: int
    max_tokens: int
    temperature: float
    is_enabled: bool
    is_running: bool
    created_at: Optional[str]
    updated_at: Optional[str]


# ============ API ============

@router.get("/configs", response_model=List[ProxyConfigResponse])
async def list_proxy_configs(db: Session = Depends(get_db)):
    """获取所有代理配置"""
    _cleanup_orphan_processes()  # 首次调用时清理孤儿进程
    configs = db.query(ProxyConfig).all()
    return [c.to_dict() for c in configs]


@router.get("/configs/{config_id}")
async def get_proxy_config_by_id(config_id: str, db: Session = Depends(get_db)):
    """获取单个代理配置"""
    config = db.query(ProxyConfig).filter(ProxyConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config.to_dict()


@router.post("/configs")
async def create_proxy_config(data: ProxyConfigCreate, db: Session = Depends(get_db)):
    """创建代理配置"""
    config = ProxyConfig(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        proxy_type=data.proxy_type,
        target_base_url=data.target_base_url,
        target_api_key=data.target_api_key,
        target_model=data.target_model,
        proxy_url=data.proxy_url or "http://localhost:8001/proxy/v1/messages",  # 默认代理地址
        proxy_model=data.proxy_model or "claude-sonnet-4-20250514",  # 默认对外模型名
        proxy_port=data.proxy_port,
        max_tokens=data.max_tokens,
        temperature=data.temperature,
        is_enabled=False,
        is_running=False,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config.to_dict()


@router.put("/configs/{config_id}")
async def update_proxy_config_by_id(
    config_id: str,
    data: ProxyConfigUpdate,
    db: Session = Depends(get_db)
):
    """更新代理配置"""
    config = db.query(ProxyConfig).filter(ProxyConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(config, field, value)

    db.commit()
    db.refresh(config)

    # 如果当前配置正在运行，更新运行时配置
    if config.is_enabled and config.is_running:
        update_proxy_config({
            "enabled": True,
            "target_base_url": config.target_base_url,
            "target_api_key": config.target_api_key,
            "target_model": config.target_model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        })

    return config.to_dict()


@router.delete("/configs/{config_id}")
async def delete_proxy_config(config_id: str, db: Session = Depends(get_db)):
    """删除代理配置"""
    config = db.query(ProxyConfig).filter(ProxyConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 如果正在运行，先停止
    if config.is_running:
        update_proxy_config({"enabled": False})

    db.delete(config)
    db.commit()
    return {"message": "已删除"}


def _stop_process(config_id: str, pid: int = None):
    """停止指定配置的代理进程"""
    global _running_processes

    stopped = False

    # 方式1: 通过内存中的进程对象
    if config_id in _running_processes:
        proc = _running_processes[config_id]
        try:
            proc.terminate()
            proc.wait(timeout=5)
            stopped = True
        except Exception as e:
            print(f"[Proxy] 通过进程对象停止失败: {e}")
            try:
                proc.kill()
                stopped = True
            except:
                pass
        del _running_processes[config_id]

    # 方式2: 通过 PID（即使内存中没有进程对象）
    if not stopped and pid:
        stopped = _kill_process_by_pid(pid)

    if stopped:
        print(f"[Proxy] 进程已停止: {config_id}")
    else:
        print(f"[Proxy] 未找到进程: {config_id}")


@router.post("/configs/{config_id}/start")
async def start_proxy(config_id: str, db: Session = Depends(get_db)):
    """启动独立代理服务"""
    config = db.query(ProxyConfig).filter(ProxyConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 停止其他正在运行的代理
    running_configs = db.query(ProxyConfig).filter(
        ProxyConfig.id != config_id,
        ProxyConfig.is_running == True
    ).all()
    for rc in running_configs:
        _stop_process(rc.id, rc.pid)
        rc.is_running = False
        rc.is_enabled = False
        rc.pid = None

    # 如果当前配置已经在运行，先停止
    if config_id in _running_processes or config.pid:
        _stop_process(config_id, config.pid)
        config.pid = None

    # 启动独立代理进程
    port = config.proxy_port or 4000
    proxy_server_path = os.path.join(os.path.dirname(__file__), "..", "..", "services", "proxy_server.py")
    proxy_server_path = os.path.abspath(proxy_server_path)

    cmd = [
        sys.executable,
        proxy_server_path,
        f"--port={port}",
        f"--target_base_url={config.target_base_url}",
        f"--target_api_key={config.target_api_key}",
        f"--target_model={config.target_model}",
        f"--max_tokens={config.max_tokens or 4096}",
        f"--temperature={config.temperature or 0.7}",
    ]

    print(f"[Proxy] 启动命令: {' '.join(cmd)}")
    print(f"[Proxy] 代理服务脚本路径: {proxy_server_path}")

    # 检查脚本是否存在
    if not os.path.exists(proxy_server_path):
        raise HTTPException(status_code=500, detail=f"代理脚本不存在: {proxy_server_path}")

    try:
        if sys.platform == "win32":
            # Windows: 使用 CREATE_NEW_PROCESS_GROUP，不捕获输出以便看到日志
            proc = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Unix: 使用 preexec_fn
            proc = subprocess.Popen(
                cmd,
                preexec_fn=os.setsid
            )

        # 等待一小段时间让进程启动
        import time
        time.sleep(1.5)

        # 检查进程是否还在运行
        if proc.poll() is not None:
            raise HTTPException(status_code=500, detail=f"代理进程启动后立即退出，退出码: {proc.returncode}")

        # 尝试连接验证
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex(('127.0.0.1', port))
            if result != 0:
                print(f"[Proxy] 警告: 端口 {port} 尚未就绪，但进程已启动")
        finally:
            sock.close()

        _running_processes[config_id] = proc
        print(f"[Proxy] 进程已启动: PID={proc.pid}, Port={port}")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"启动代理失败: {str(e)}")

    # 更新数据库状态（包含 PID）
    config.is_enabled = True
    config.is_running = True
    config.pid = proc.pid
    db.commit()

    # 构建代理地址
    proxy_url = f"http://localhost:{port}"

    return {
        "message": "代理已启动",
        "proxy_url": proxy_url,
        "proxy_model": config.proxy_model or "claude-sonnet-4-20250514",
        "api_key": config.target_api_key or "",
        "port": port,
        "pid": proc.pid,
        "config": config.to_dict()
    }


@router.post("/configs/{config_id}/stop")
async def stop_proxy(config_id: str, db: Session = Depends(get_db)):
    """停止代理服务"""
    config = db.query(ProxyConfig).filter(ProxyConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    # 停止进程（同时使用内存和数据库中的 PID）
    _stop_process(config_id, config.pid)

    # 更新数据库状态
    config.is_enabled = False
    config.is_running = False
    config.pid = None
    db.commit()

    return {"message": "代理已停止", "config": config.to_dict()}


@router.get("/status")
async def get_proxy_status(db: Session = Depends(get_db)):
    """获取代理运行状态"""
    # 获取正在运行的配置
    running_config = db.query(ProxyConfig).filter(ProxyConfig.is_running == True).first()

    # 检查进程是否真的在运行
    is_running = False
    proxy_url = None
    pid = None

    if running_config:
        config_id = running_config.id
        db_pid = running_config.pid

        # 优先检查内存中的进程对象
        if config_id in _running_processes:
            proc = _running_processes[config_id]
            if proc.poll() is None:
                is_running = True
                pid = proc.pid
            else:
                del _running_processes[config_id]
        # 其次检查数据库中的 PID
        elif db_pid and psutil.pid_exists(db_pid):
            is_running = True
            pid = db_pid

        if is_running:
            port = running_config.proxy_port or 4000
            proxy_url = f"http://localhost:{port}"
        else:
            # 进程已退出，清理状态
            running_config.is_running = False
            running_config.is_enabled = False
            running_config.pid = None
            db.commit()
            running_config = None

    return {
        "is_running": is_running,
        "proxy_model": running_config.proxy_model if running_config else None,
        "proxy_url": proxy_url,
        "pid": pid,
        "running_config_id": running_config.id if running_config else None,
        "running_config_name": running_config.name if running_config else None,
    }


class TestConnectionRequest(BaseModel):
    target_base_url: str
    target_api_key: str
    target_model: str


@router.post("/test-connection")
async def test_connection(data: TestConnectionRequest):
    """测试 API 连通性"""
    try:
        test_url = data.target_base_url.rstrip("/")

        async with httpx.AsyncClient(timeout=15.0) as client:
            # 判断是 Anthropic 格式还是 OpenAI 格式
            is_anthropic = "anthropic" in test_url.lower()

            if is_anthropic:
                # Anthropic 格式: /v1/messages
                headers = {
                    "x-api-key": data.target_api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }
                messages_url = f"{test_url}/v1/messages" if "/v1" not in test_url else f"{test_url}/messages"

                response = await client.post(
                    messages_url,
                    headers=headers,
                    json={
                        "model": data.target_model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 5
                    }
                )
            else:
                # OpenAI 格式: /v1/chat/completions
                headers = {
                    "Authorization": f"Bearer {data.target_api_key}",
                    "Content-Type": "application/json",
                }
                chat_url = f"{test_url}/chat/completions" if "/v1" in test_url else f"{test_url}/v1/chat/completions"

                response = await client.post(
                    chat_url,
                    headers=headers,
                    json={
                        "model": data.target_model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 5
                    }
                )

            if response.status_code == 200:
                return {"success": True, "message": "连接成功"}
            elif response.status_code == 401:
                return {"success": False, "message": "API Key 无效"}
            elif response.status_code == 403:
                return {"success": False, "message": "无权访问"}
            elif response.status_code == 404:
                return {"success": False, "message": f"接口不存在，请检查 API 地址"}
            else:
                # 尝试解析错误信息
                try:
                    err = response.json()
                    msg = err.get("error", {}).get("message") or err.get("message") or str(err)
                    return {"success": False, "message": f"请求失败: {msg}"}
                except:
                    return {"success": False, "message": f"请求失败: {response.status_code}"}

    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时"}
    except httpx.ConnectError:
        return {"success": False, "message": "无法连接到服务器"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
