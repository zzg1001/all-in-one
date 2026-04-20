import uuid
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from portal.models.execution import WorkflowExecution
from portal.models.workflow import Workflow
from portal.models.skill import Skill
from portal.schemas.execution import (
    ExecutionStatus, InteractionRequest, InteractionResponse,
    CompletedStep, WorkflowPreCheck, WorkflowStepInfo, SkillInteraction
)


class ExecutionService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_id(self) -> str:
        return f"exec-{uuid.uuid4().hex[:12]}"

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.db.query(Workflow).filter(Workflow.id == workflow_id).first()

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        # 先尝试精确匹配
        skill = self.db.query(Skill).filter(Skill.name == name).first()
        if skill:
            return skill
        # 再尝试忽略大小写匹配
        from sqlalchemy import func
        skill = self.db.query(Skill).filter(func.lower(Skill.name) == name.lower()).first()
        print(f"[get_skill_by_name] name={name}, found={skill.name if skill else None}")
        return skill

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        return self.db.query(WorkflowExecution).filter(
            WorkflowExecution.id == execution_id
        ).first()

    def list_executions(self, workflow_id: Optional[str] = None, limit: int = 50) -> List[WorkflowExecution]:
        query = self.db.query(WorkflowExecution)
        if workflow_id:
            query = query.filter(WorkflowExecution.workflow_id == workflow_id)
        return query.order_by(WorkflowExecution.created_at.desc()).limit(limit).all()

    def precheck_workflow(self, workflow_id: str) -> Optional[WorkflowPreCheck]:
        """预检查工作流，返回所有需要预收集的交互"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None

        nodes = workflow.nodes or []
        steps = []
        before_interactions = []
        has_during = False

        for i, node in enumerate(nodes):
            skill_name = node.get("name", "")
            skill = self.get_skill_by_name(skill_name)

            step_interactions = []
            if skill and skill.interactions:
                for interaction in skill.interactions:
                    inter = SkillInteraction(**interaction) if isinstance(interaction, dict) else interaction
                    step_interactions.append(inter)

                    if inter.timing == "before":
                        before_interactions.append(InteractionRequest(
                            interaction_id=f"{i}_{inter.id}",
                            skill_id=skill.id if skill else None,
                            skill_name=skill_name,
                            step_index=i,
                            type=inter.type,
                            label=inter.label,
                            description=inter.description,
                            required=inter.required,
                            options=inter.options
                        ))
                    elif inter.timing == "during":
                        has_during = True

            steps.append(WorkflowStepInfo(
                step_index=i,
                skill_name=skill_name,
                icon=node.get("icon"),
                interactions=step_interactions
            ))

        return WorkflowPreCheck(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            total_steps=len(nodes),
            steps=steps,
            before_interactions=before_interactions,
            has_during_interactions=has_during
        )

    def start_execution(
        self,
        workflow_id: str,
        pre_inputs: Optional[Dict[str, Any]] = None
    ) -> ExecutionStatus:
        """启动工作流执行"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        nodes = workflow.nodes or []
        execution_id = self._generate_id()

        # 创建执行实例
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status="running",
            current_step=0,
            total_steps=len(nodes),
            context={"_inputs": pre_inputs or {}},
            completed_steps=[]
        )
        self.db.add(execution)
        self.db.commit()

        # 开始执行
        return self._execute(execution, workflow)

    def _execute(self, execution: WorkflowExecution, workflow: Workflow) -> ExecutionStatus:
        """执行工作流（内部方法）"""
        nodes = workflow.nodes or []
        context = execution.context or {"_inputs": {}}
        completed_steps = execution.completed_steps or []

        for i in range(execution.current_step, len(nodes)):
            node = nodes[i]
            node_type = node.get("type", "skill")
            skill_name = node.get("name", "")

            print(f"\n{'='*50}")
            print(f"[Workflow._execute] === Step {i}: {skill_name} (type={node_type}) ===")
            print(f"[Workflow._execute] Context keys: {list(context.keys())}")

            # 处理数据节点 - 直接将文件信息传递给下一步
            if node_type == "data":
                data_note = node.get("dataNote", {})
                file_url = data_note.get("file_url", "")
                file_type = data_note.get("file_type", "")

                print(f"[Workflow._execute] Data node: file_url={file_url}, file_type={file_type}")

                # 数据节点的结果
                result = {
                    "result": {
                        "_output_file": {
                            "name": skill_name,
                            "url": file_url,
                            "path": file_url,  # 用于传递给下一个节点
                            "type": file_type
                        },
                        "file_url": file_url,
                        "file_type": file_type,
                        "data_note": data_note
                    },
                    "output": f"[数据源] {skill_name}"
                }

                context[f"step_{i}"] = result
                completed_steps.append({
                    "step_index": i,
                    "skill_name": skill_name,
                    "icon": node.get("icon"),
                    "status": "completed",
                    "result": result.get("result"),
                    "output": result.get("output")
                })

                execution.current_step = i + 1
                execution.context = context
                execution.completed_steps = completed_steps
                self.db.commit()
                continue

            # 普通技能节点
            skill = self.get_skill_by_name(skill_name)
            print(f"[Workflow._execute] Skill found: {skill is not None}")

            # 检查是否需要运行时交互
            interaction = self._check_interaction_needed(skill, i, context)
            if interaction:
                # 暂停执行
                execution.status = "paused"
                execution.current_step = i
                execution.context = context
                execution.pending_interaction = interaction.model_dump()
                execution.completed_steps = completed_steps
                self.db.commit()

                return ExecutionStatus(
                    execution_id=execution.id,
                    workflow_id=workflow.id,
                    workflow_name=workflow.name,
                    status="paused",
                    current_step=i,
                    total_steps=len(nodes),
                    completed_steps=[CompletedStep(**s) for s in completed_steps],
                    pending_interaction=interaction,
                    created_at=execution.created_at,
                    updated_at=execution.updated_at
                )

            # 执行 Skill
            try:
                # 将步骤索引添加到 node 中，供 _execute_skill 使用
                node["step_index"] = i
                result = self._execute_skill(skill, node, context)
                context[f"step_{i}"] = result

                step_result = result.get("result")
                print(f"[Workflow._execute] Step {i} result: {step_result}")
                print(f"[Workflow._execute] Has _output_file: {'_output_file' in step_result if isinstance(step_result, dict) else False}")

                completed_steps.append({
                    "step_index": i,
                    "skill_name": skill_name,
                    "icon": node.get("icon"),
                    "status": "completed",
                    "result": step_result,
                    "output": result.get("output")
                })

                # 更新进度
                execution.current_step = i + 1
                execution.context = context
                execution.completed_steps = completed_steps
                self.db.commit()

            except Exception as e:
                execution.status = "failed"
                execution.error = str(e)
                self.db.commit()

                return ExecutionStatus(
                    execution_id=execution.id,
                    workflow_id=workflow.id,
                    workflow_name=workflow.name,
                    status="failed",
                    current_step=i,
                    total_steps=len(nodes),
                    completed_steps=[CompletedStep(**s) for s in completed_steps],
                    error=str(e)
                )

        # 全部完成
        execution.status = "completed"
        execution.current_step = len(nodes)
        self.db.commit()

        return ExecutionStatus(
            execution_id=execution.id,
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            status="completed",
            current_step=len(nodes),
            total_steps=len(nodes),
            completed_steps=[CompletedStep(**s) for s in completed_steps],
            created_at=execution.created_at,
            updated_at=execution.updated_at
        )

    def _check_interaction_needed(
        self,
        skill: Optional[Skill],
        step_index: int,
        context: Dict[str, Any]
    ) -> Optional[InteractionRequest]:
        """检查是否需要运行时交互"""
        if not skill or not skill.interactions:
            return None

        inputs = context.get("_inputs", {})

        for interaction in skill.interactions:
            inter = interaction if isinstance(interaction, dict) else interaction
            inter_id = inter.get("id") if isinstance(inter, dict) else inter.id
            timing = inter.get("timing", "before") if isinstance(inter, dict) else inter.timing

            # 只检查 timing=during 的交互
            if timing == "during":
                full_id = f"{step_index}_{inter_id}"
                if full_id not in inputs:
                    # 构建上下文参考
                    relevant_context = {}
                    for key, value in context.items():
                        if key.startswith("step_"):
                            relevant_context[key] = value

                    return InteractionRequest(
                        interaction_id=full_id,
                        skill_id=skill.id,
                        skill_name=skill.name,
                        step_index=step_index,
                        type=inter.get("type") if isinstance(inter, dict) else inter.type,
                        label=inter.get("label") if isinstance(inter, dict) else inter.label,
                        description=inter.get("description") if isinstance(inter, dict) else inter.description,
                        required=inter.get("required", True) if isinstance(inter, dict) else inter.required,
                        options=inter.get("options") if isinstance(inter, dict) else inter.options,
                        context=relevant_context if relevant_context else None
                    )

        return None

    def _execute_skill(
        self,
        skill: Optional[Skill],
        node: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个 Skill - 真正调用技能脚本"""
        from portal.services.agent_service_sdk import AgentSDKService

        skill_name = node.get("name", "unknown")
        description = node.get("description", "")

        print(f"[Workflow._execute_skill] skill_name={skill_name}, skill={skill}")

        # 获取该步骤的输入
        inputs = context.get("_inputs", {})
        step_index = node.get("step_index", 0)
        step_inputs = {
            k.split("_", 1)[1]: v
            for k, v in inputs.items()
            if k.startswith(f"{step_index}_")
        }

        # 如果有技能，真正执行它
        if skill:
            print(f"[Workflow._execute_skill] Found skill: id={skill.id}, folder_path={skill.folder_path}")
            agent_service = AgentSDKService(self.db)
            params = {
                **step_inputs,
                "context": context.get("user_query", description),
                "skillDescription": description
            }

            # 【关键】将前一步的输出作为当前步骤的输入
            # 查找最近的上一步输出（step_0, step_1, ...）
            current_step = step_index
            print(f"[Workflow._execute_skill] current_step={current_step}, context keys={list(context.keys())}")

            for prev_step in range(current_step - 1, -1, -1):
                prev_result = context.get(f"step_{prev_step}")
                print(f"[Workflow._execute_skill] Checking step_{prev_step}: {type(prev_result)}, value={str(prev_result)[:200] if prev_result else None}")

                if prev_result and isinstance(prev_result, dict):
                    step_result = prev_result.get("result", {})
                    print(f"[Workflow._execute_skill] step_result type={type(step_result)}, keys={list(step_result.keys()) if isinstance(step_result, dict) else 'N/A'}")

                    if isinstance(step_result, dict):
                        # 如果上一步有输出文件，传递给当前步骤
                        output_file = step_result.get("_output_file")
                        print(f"[Workflow._execute_skill] output_file={output_file}")

                        if output_file and isinstance(output_file, dict):
                            file_path = output_file.get("path")
                            if file_path:
                                params["file_path"] = file_path
                                params["files"] = [file_path]
                                params["previous_output"] = step_result
                                print(f"[Workflow._execute_skill] ✓ Passing previous output file: {file_path}")
                                break
                        # 如果上一步有内容输出，也传递
                        content = step_result.get("content")
                        if content:
                            params["previous_content"] = content
                            params["input_data"] = content
                            print(f"[Workflow._execute_skill] ✓ Passing previous content: {str(content)[:100]}...")
                            break

            print(f"[Workflow._execute_skill] Calling execute_skill with params={params}")

            # 调用异步方法
            import asyncio
            exec_result = asyncio.get_event_loop().run_until_complete(
                agent_service.execute_skill(
                    skill_id=skill.id,
                    params=params
                )
            )

            # 解析返回的字典
            success = exec_result.get("success", False)
            result = exec_result.get("result")
            error = exec_result.get("error")
            output = exec_result.get("output")

            print(f"[Workflow._execute_skill] Result: success={success}, result={result}, error={error}")

            if success:
                return {
                    "result": result,
                    "output": output or f"[{skill_name}] 执行完成"
                }
            else:
                raise Exception(error or f"技能 {skill_name} 执行失败")

        # 没有技能，返回模拟结果
        return {
            "result": {
                "skill": skill_name,
                "description": description,
                "inputs": step_inputs,
                "message": f"Skill '{skill_name}' 未找到，已模拟执行"
            },
            "output": f"[{skill_name}] 模拟执行完成"
        }

    def resume_execution(
        self,
        execution_id: str,
        response: InteractionResponse
    ) -> ExecutionStatus:
        """恢复执行（用户响应交互后）"""
        execution = self.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if execution.status != "paused":
            raise ValueError(f"Execution is not paused, current status: {execution.status}")

        workflow = self.get_workflow(execution.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {execution.workflow_id} not found")

        # 保存用户输入
        context = execution.context or {"_inputs": {}}
        context.setdefault("_inputs", {})[response.interaction_id] = response.value

        # 清除等待的交互
        execution.context = context
        execution.pending_interaction = None
        execution.status = "running"
        self.db.commit()

        # 继续执行
        return self._execute(execution, workflow)

    def cancel_execution(self, execution_id: str) -> bool:
        """取消执行"""
        execution = self.get_execution(execution_id)
        if not execution:
            return False

        if execution.status in ["completed", "failed"]:
            return False

        execution.status = "failed"
        execution.error = "用户取消"
        self.db.commit()
        return True

    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """获取执行状态"""
        execution = self.get_execution(execution_id)
        if not execution:
            return None

        workflow = self.get_workflow(execution.workflow_id)
        completed_steps = execution.completed_steps or []

        pending = None
        if execution.pending_interaction:
            pending = InteractionRequest(**execution.pending_interaction)

        return ExecutionStatus(
            execution_id=execution.id,
            workflow_id=execution.workflow_id,
            workflow_name=workflow.name if workflow else None,
            status=execution.status,
            current_step=execution.current_step,
            total_steps=execution.total_steps,
            completed_steps=[CompletedStep(**s) for s in completed_steps],
            pending_interaction=pending,
            error=execution.error,
            created_at=execution.created_at,
            updated_at=execution.updated_at
        )
