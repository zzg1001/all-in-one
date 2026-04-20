from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from portal.models.workflow import Workflow
from portal.models.skill import Skill
from portal.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, search: Optional[str] = None) -> List[Workflow]:
        query = self.db.query(Workflow)

        # 搜索过滤
        if search and search.strip():
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Workflow.name.ilike(search_term)) |
                (Workflow.description.ilike(search_term))
            )

        workflows = query.all()

        # 调试：打印加载的数据节点信息
        for wf in workflows:
            nodes = wf.nodes or []
            data_nodes = [n for n in nodes if n.get('type') == 'data' or n.get('dataNote')]
            if data_nodes:
                print(f"[WorkflowService.get_all] Workflow '{wf.name}' has {len(data_nodes)} data node(s):")
                for dn in data_nodes:
                    print(f"  - name={dn.get('name')}, dataNote.file_url={dn.get('dataNote', {}).get('file_url')}")

        return workflows

    def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        return self.db.query(Workflow).filter(Workflow.id == workflow_id).first()

    def _compute_io_from_nodes(self, nodes: List[dict], edges: List[dict]) -> Tuple[int, Optional[str]]:
        """从节点和边计算输入数量和输出类型"""
        if not nodes:
            return 0, None

        # 找到所有节点ID
        node_ids = {n.get('id') for n in nodes}
        # 找到有入边的节点
        nodes_with_incoming = {e.get('to') for e in edges}
        # 找到有出边的节点
        nodes_with_outgoing = {e.get('from') for e in edges}

        # 起始节点：没有入边的节点
        start_nodes = [n for n in nodes if n.get('id') not in nodes_with_incoming]
        # 结束节点：没有出边的节点
        end_nodes = [n for n in nodes if n.get('id') not in nodes_with_outgoing]

        input_count = 0
        output_type = None

        # 从起始节点的 skill 获取 interactions 数量
        for node in start_nodes:
            if node.get('type') == 'skill':
                skill_name = node.get('name')
                if skill_name:
                    skill = self.db.query(Skill).filter(
                        Skill.name == skill_name,
                        Skill.status == 'active'
                    ).first()
                    if skill and skill.interactions:
                        input_count += len(skill.interactions)

        # 从结束节点的 skill 获取 output_type
        for node in end_nodes:
            if node.get('type') == 'skill':
                skill_name = node.get('name')
                if skill_name:
                    skill = self.db.query(Skill).filter(
                        Skill.name == skill_name,
                        Skill.status == 'active'
                    ).first()
                    if skill and skill.output_config:
                        output_type = skill.output_config.get('preferred_type')
                        break  # 使用第一个找到的输出类型

        return input_count, output_type

    def create(self, workflow_data: WorkflowCreate) -> Workflow:
        nodes = workflow_data.nodes or []
        edges = workflow_data.edges or []
        input_count, output_type = self._compute_io_from_nodes(nodes, edges)

        # 调试：打印数据节点信息
        data_nodes = [n for n in nodes if n.get('type') == 'data' or n.get('dataNote')]
        if data_nodes:
            print(f"[WorkflowService.create] Creating workflow with {len(data_nodes)} data node(s):")
            for dn in data_nodes:
                print(f"  - name={dn.get('name')}, dataNote.file_url={dn.get('dataNote', {}).get('file_url')}")

        workflow = Workflow(
            id=workflow_data.id,
            name=workflow_data.name,
            description=workflow_data.description,
            icon=workflow_data.icon,
            nodes=nodes,
            edges=edges,
            input_count=input_count,
            output_type=output_type
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def update(self, workflow_id: str, workflow_data: WorkflowUpdate) -> Optional[Workflow]:
        workflow = self.get_by_id(workflow_id)
        if not workflow:
            return None

        update_data = workflow_data.model_dump(exclude_unset=True)

        # 调试：打印更新的数据节点信息
        if 'nodes' in update_data:
            nodes = update_data['nodes'] or []
            data_nodes = [n for n in nodes if n.get('type') == 'data' or n.get('dataNote')]
            if data_nodes:
                print(f"[WorkflowService.update] Updating workflow {workflow_id} with {len(data_nodes)} data node(s):")
                for dn in data_nodes:
                    print(f"  - name={dn.get('name')}, dataNote.file_url={dn.get('dataNote', {}).get('file_url')}")

        for key, value in update_data.items():
            setattr(workflow, key, value)

        # 重新计算输入输出
        nodes = workflow.nodes or []
        edges = workflow.edges or []
        input_count, output_type = self._compute_io_from_nodes(nodes, edges)
        workflow.input_count = input_count
        workflow.output_type = output_type

        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def delete(self, workflow_id: str) -> bool:
        workflow = self.get_by_id(workflow_id)
        if not workflow:
            return False

        self.db.delete(workflow)
        self.db.commit()
        return True
