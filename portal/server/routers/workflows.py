from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


@router.get("", response_model=List[WorkflowResponse])
async def get_workflows(
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all workflows

    Args:
        q: 搜索关键词（搜索名称和描述）
    """
    service = WorkflowService(db)
    return service.get_all(search=q)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Get a single workflow by ID"""
    service = WorkflowService(db)
    workflow = service.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(workflow_data: WorkflowCreate, db: Session = Depends(get_db)):
    """Create a new workflow"""
    service = WorkflowService(db)
    # Check if workflow with same ID already exists
    existing = service.get_by_id(workflow_data.id)
    if existing:
        raise HTTPException(status_code=400, detail="Workflow with this ID already exists")
    return service.create(workflow_data)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, workflow_data: WorkflowUpdate, db: Session = Depends(get_db)):
    """Update a workflow"""
    service = WorkflowService(db)
    workflow = service.update(workflow_id, workflow_data)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Delete a workflow"""
    service = WorkflowService(db)
    if not service.delete(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return None
