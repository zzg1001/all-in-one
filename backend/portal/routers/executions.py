from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from portal.services.execution_service import ExecutionService
from portal.schemas.execution import (
    ExecutionStatus, StartExecutionRequest, InteractionResponse,
    WorkflowPreCheck
)
from portal.routers.logs import log_session_start, log_session_end, log_info

router = APIRouter(prefix="/api/executions", tags=["executions"])


@router.get("/workflow/{workflow_id}/precheck", response_model=WorkflowPreCheck)
async def precheck_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """
    预检查工作流，返回所有需要预收集的交互
    在启动执行前调用，收集 timing=before 的交互输入
    """
    service = ExecutionService(db)
    result = service.precheck_workflow(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.post("/workflow/{workflow_id}/start", response_model=ExecutionStatus)
async def start_execution(
    workflow_id: str,
    request: StartExecutionRequest = None,
    db: Session = Depends(get_db)
):
    """
    启动工作流执行
    pre_inputs: 预收集的交互输入 {"interaction_id": value}
    """
    # 获取工作流信息用于日志
    from portal.models.workflow import Workflow
    from portal.models.skill import Skill

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    workflow_name = workflow.name if workflow else workflow_id

    # 获取工作流中的技能列表
    skill_names = []
    if workflow and workflow.nodes:
        import json
        nodes = json.loads(workflow.nodes) if isinstance(workflow.nodes, str) else workflow.nodes
        skill_ids = [n.get('id') for n in nodes if n.get('type') == 'skill']
        if skill_ids:
            skills = db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
            skill_names = [s.name for s in skills]

    log_session_start(
        api_name="POST /executions/workflow/start",
        api_desc=f"启动工作流 [{workflow_name}]，按顺序执行多个技能完成复杂任务",
        source="工作流执行页面",
        skills=skill_names if skill_names else None
    )

    service = ExecutionService(db)
    try:
        pre_inputs = request.pre_inputs if request else None
        result = service.start_execution(workflow_id, pre_inputs)
        if result.status == 'completed':
            log_session_end(True, f"工作流 {workflow_name} 执行完成")
        elif result.status == 'failed':
            log_session_end(False, result.error or "执行失败")
        return result
    except ValueError as e:
        log_session_end(False, str(e))
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{execution_id}", response_model=ExecutionStatus)
async def get_execution_status(execution_id: str, db: Session = Depends(get_db)):
    """获取执行状态"""
    service = ExecutionService(db)
    status = service.get_execution_status(execution_id)
    if not status:
        raise HTTPException(status_code=404, detail="Execution not found")
    return status


@router.post("/{execution_id}/interact", response_model=ExecutionStatus)
async def submit_interaction(
    execution_id: str,
    response: InteractionResponse,
    db: Session = Depends(get_db)
):
    """
    提交交互响应，恢复执行
    """
    service = ExecutionService(db)
    try:
        return service.resume_execution(execution_id, response)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{execution_id}/cancel")
async def cancel_execution(execution_id: str, db: Session = Depends(get_db)):
    """取消执行"""
    service = ExecutionService(db)
    success = service.cancel_execution(execution_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel execution")
    return {"message": "Execution cancelled"}


@router.get("/", response_model=List[ExecutionStatus])
async def list_executions(
    workflow_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """列出执行记录"""
    service = ExecutionService(db)
    executions = service.list_executions(workflow_id, limit)
    return [service.get_execution_status(e.id) for e in executions]
